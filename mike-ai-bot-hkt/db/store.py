from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import asyncpg

from db.migrate import apply_schema_pool
from knowledge_base import KnowledgeBaseEntry
from partners import Partner, PartnerType
from place_catalog import Place, PlaceAsset, PlaceCategory

PARTNER_FOLLOW_UP_DELAY = timedelta(hours=24)
WIN_BACK_DELAY = timedelta(days=7)
PARTNER_FOLLOW_UP_COOLDOWN = timedelta(days=7)
# Bot chat and the mini app store the same Telegram user id on different channels.
TELEGRAM_CHANNELS = ("telegram", "tma")
WIN_BACK_TEXT = (
    "Привет! Как дела? Что-то давно тебя не было! Хочешь узнать что-то новенькое?😊"
)


@dataclass(frozen=True)
class ConversationContext:
    user_id: UUID
    conversation_id: UUID
    source: str
    first_source: str


@dataclass(frozen=True)
class LeadRecord:
    id: UUID
    conversation_id: UUID
    source: str
    created: bool
    webhook_enqueued: bool


@dataclass(frozen=True)
class TopicCount:
    unique_users: int
    taps: int


@dataclass(frozen=True)
class BotStats:
    total_users: int
    new_users_today: int
    active_today: int
    new_users_7d: int
    topics_all_time: dict[str, TopicCount]
    topics_7d: dict[str, TopicCount]
    leads_all_time: int
    leads_7d: int
    users_by_first_source: dict[str, int]


@dataclass(frozen=True)
class UserStats:
    total_users: int
    active_today: int
    new_users_today: int = 0
    new_users_7d: int = 0


@dataclass(frozen=True)
class AdminUser:
    id: UUID
    email: str
    password_hash: str


@dataclass(frozen=True)
class DueFollowUpJob:
    id: UUID
    kind: str
    topic: str | None
    message_text: str
    channel: str
    external_id: str
    button_url: str | None = None
    button_label: str | None = None


def _partner_type_from_row(row: asyncpg.Record) -> PartnerType:
    names = set(row.keys())
    follow = row["follow_up_text"] if "follow_up_text" in names else ""
    choice_phrase = row["choice_phrase"] if "choice_phrase" in names else ""
    return PartnerType(
        slug=row["slug"],
        is_menu_visible=row["is_menu_visible"],
        sort_order=row["sort_order"],
        button_label=row["button_label"],
        topic_label=row["topic_label"],
        intro=row["intro"],
        fallback=row["fallback"],
        caption_emoji=row["caption_emoji"],
        caption_cta=row["caption_cta"],
        button_template=row["button_template"],
        follow_up_text=follow or "",
        choice_phrase=choice_phrase or "",
        id=row["id"] if "id" in names else None,
    )


def _knowledge_base_entry(row: asyncpg.Record) -> KnowledgeBaseEntry:
    return KnowledgeBaseEntry(
        id=row["id"],
        name=row["name"],
        partner_id=row["partner_id"],
        place_id=row["place_id"],
        referral_url=row["referral_url"] or "",
        maps_url=row["maps_url"] or "",
        blurb=row["blurb"] or "",
        kind=row["kind"] or "",
        is_visible=row["is_visible"],
    )


_KNOWLEDGE_BASE_ROWS = """
SELECT knowledge_base.id,
       knowledge_base.partner_id,
       knowledge_base.place_id,
       COALESCE(place.name, partner.name) AS name,
       COALESCE(place_partner.referral_url, partner.referral_url) AS referral_url,
       place.maps_url,
       COALESCE(place.blurb, partner.blurb) AS blurb,
       COALESCE(category.label, partner_type.topic_label, '') AS kind,
       COALESCE(place.is_active, partner.is_active) AS is_visible
FROM knowledge_base
LEFT JOIN partners AS partner ON partner.id = knowledge_base.partner_id
LEFT JOIN partner_types AS partner_type ON partner_type.id = partner.partner_type_id
LEFT JOIN places AS place ON place.id = knowledge_base.place_id
LEFT JOIN place_categories AS category ON category.id = place.category_id
LEFT JOIN partners AS place_partner
    ON place_partner.id = place.partner_id
   AND place_partner.is_active
"""


def _partner_from_row(row: asyncpg.Record, *, is_active: bool | None = None) -> Partner:
    return Partner(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        referral_url=row["referral_url"],
        blurb=row["blurb"],
        sort_order=row["sort_order"],
        logo_path=row["logo_path"],
        is_active=row["is_active"] if is_active is None else is_active,
    )


def _place_from_row(row: asyncpg.Record) -> Place:
    return Place(
        id=row["id"],
        name=row["name"],
        category_id=row["category_id"],
        partner_id=row["partner_id"],
        google_place_id=row["google_place_id"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        blurb=row["blurb"],
        is_active=row["is_active"],
        maps_url=row["maps_url"],
        mike_recommends=row["mike_recommends"],
    )


_PLACE_COLUMNS = """
    id, name, category_id, partner_id, google_place_id,
    latitude, longitude, blurb, is_active, maps_url, mike_recommends
"""


def _place_category_from_row(row: asyncpg.Record) -> PlaceCategory:
    return PlaceCategory(
        id=row["id"],
        slug=row["slug"],
        label=row["label"],
        sort_order=row["sort_order"],
    )


def _place_asset_from_row(row: asyncpg.Record) -> PlaceAsset:
    return PlaceAsset(
        id=row["id"],
        place_id=row["place_id"],
        path=row["path"],
        sort_order=row["sort_order"],
    )


class SessionStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, database_url: str, *, min_size: int = 1, max_size: int = 5) -> SessionStore:
        pool = await asyncpg.create_pool(database_url, min_size=min_size, max_size=max_size)
        await apply_schema_pool(pool)
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        return self._pool

    async def create_admin_user(self, *, email: str, password: str) -> AdminUser:
        from admin_api.passwords import hash_password

        password_hash = hash_password(password)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO admin_users (email, password_hash)
                VALUES ($1, $2)
                RETURNING id, email, password_hash
                """,
                email.lower().strip(),
                password_hash,
            )
        return AdminUser(id=row["id"], email=row["email"], password_hash=row["password_hash"])

    async def get_admin_by_email(self, email: str) -> AdminUser | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, password_hash
                FROM admin_users
                WHERE email = $1
                """,
                email.lower().strip(),
            )
        if row is None:
            return None
        return AdminUser(id=row["id"], email=row["email"], password_hash=row["password_hash"])

    async def start_conversation(
        self,
        channel: str,
        external_id: str,
        *,
        source: str = "unknown",
    ) -> ConversationContext:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                user_id, first_source = await self._ensure_user(conn, channel, external_id, source)
                await self._close_active_conversation(conn, user_id)
                conversation_id = await self._open_conversation(conn, user_id, source)
                return ConversationContext(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    source=source,
                    first_source=first_source,
                )

    async def reset_conversation(self, channel: str, external_id: str) -> ConversationContext:
        return await self.start_conversation(channel, external_id, source="unknown")

    async def get_active_conversation(self, channel: str, external_id: str) -> ConversationContext | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT u.id AS user_id,
                       c.id AS conversation_id,
                       c.source,
                       u.first_source
                FROM identities i
                JOIN users u ON u.id = i.user_id
                JOIN conversations c ON c.user_id = u.id AND c.status = 'active'
                WHERE i.channel = $1 AND i.external_id = $2
                """,
                channel,
                external_id,
            )
            if row is None:
                return None
            return ConversationContext(
                user_id=row["user_id"],
                conversation_id=row["conversation_id"],
                source=row["source"],
                first_source=row["first_source"],
            )

    async def append_message(
        self,
        channel: str,
        external_id: str,
        *,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationContext:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                ctx = await self._get_or_create_active(conn, channel, external_id)
                await conn.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, metadata)
                    VALUES ($1, $2, $3, $4::jsonb)
                    """,
                    ctx.conversation_id,
                    role,
                    content,
                    json.dumps(metadata or {}),
                )
                return ctx

    async def get_ai_context(
        self,
        channel: str,
        external_id: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, str]]:
        async with self._pool.acquire() as conn:
            ctx = await self._fetch_active(conn, channel, external_id)
            if ctx is None:
                return []

            rows = await conn.fetch(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC, id DESC
                LIMIT $2
                """,
                ctx.conversation_id,
                limit,
            )
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    async def create_lead(
        self,
        channel: str,
        external_id: str,
        *,
        snapshot: dict[str, Any],
    ) -> LeadRecord | None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                ctx = await self._fetch_active(conn, channel, external_id)
                if ctx is None:
                    return None

                lead_source = ctx.source if ctx.source != "unknown" else ctx.first_source
                existing = await conn.fetchrow(
                    "SELECT id, conversation_id, source FROM leads WHERE conversation_id = $1",
                    ctx.conversation_id,
                )
                if existing:
                    return LeadRecord(
                        id=existing["id"],
                        conversation_id=existing["conversation_id"],
                        source=existing["source"],
                        created=False,
                        webhook_enqueued=False,
                    )

                lead_id = await conn.fetchval(
                    """
                    INSERT INTO leads (conversation_id, source, snapshot)
                    VALUES ($1, $2, $3::jsonb)
                    RETURNING id
                    """,
                    ctx.conversation_id,
                    lead_source,
                    json.dumps(snapshot),
                )
                await conn.execute(
                    """
                    INSERT INTO webhook_events (event_type, payload_ref, payload)
                    VALUES ('lead.created', $1, $2::jsonb)
                    """,
                    str(lead_id),
                    json.dumps(
                        {"lead_id": str(lead_id), "source": lead_source, "snapshot": snapshot}
                    ),
                )
                return LeadRecord(
                    id=lead_id,
                    conversation_id=ctx.conversation_id,
                    source=lead_source,
                    created=True,
                    webhook_enqueued=True,
                )

    async def has_lead(self, channel: str, external_id: str) -> bool:
        async with self._pool.acquire() as conn:
            ctx = await self._fetch_active(conn, channel, external_id)
            if ctx is None:
                return False
            exists = await conn.fetchval(
                "SELECT 1 FROM leads WHERE conversation_id = $1",
                ctx.conversation_id,
            )
            return exists is not None

    async def record_topic_event(
        self,
        channel: str,
        external_id: str,
        *,
        topic: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                user_id, _ = await self._ensure_user(conn, channel, external_id, "unknown")
                await conn.execute(
                    """
                    INSERT INTO topic_events (user_id, topic)
                    VALUES ($1, $2)
                    """,
                    user_id,
                    topic,
                )

    async def schedule_partner_follow_up(
        self,
        channel: str,
        external_id: str,
        topic: str,
        *,
        at: datetime | None = None,
    ) -> None:
        tapped_at = at or datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                follow_up_text = await conn.fetchval(
                    "SELECT follow_up_text FROM partner_types WHERE slug = $1",
                    topic,
                )
                if not follow_up_text:
                    return

                user_id, _ = await self._ensure_user(conn, channel, external_id, "unknown")
                blocked = await conn.fetchval(
                    "SELECT follow_up_blocked_at FROM users WHERE id = $1",
                    user_id,
                )
                if blocked is not None:
                    return

                await conn.execute(
                    """
                    UPDATE users
                    SET last_inbound_at = $2
                    WHERE id = $1
                    """,
                    user_id,
                    tapped_at,
                )

                recent_sent = await conn.fetchval(
                    """
                    SELECT 1
                    FROM follow_up_jobs
                    WHERE user_id = $1
                      AND kind = 'partner_topic'
                      AND status = 'sent'
                      AND sent_at > $2
                    LIMIT 1
                    """,
                    user_id,
                    tapped_at - PARTNER_FOLLOW_UP_COOLDOWN,
                )
                if recent_sent is not None:
                    await self._reschedule_win_back(conn, user_id, tapped_at)
                    return

                await conn.execute(
                    """
                    UPDATE follow_up_jobs
                    SET status = 'cancelled'
                    WHERE user_id = $1
                      AND kind = 'partner_topic'
                      AND status = 'pending'
                    """,
                    user_id,
                )
                await conn.execute(
                    """
                    INSERT INTO follow_up_jobs (user_id, kind, topic, scheduled_at)
                    VALUES ($1, 'partner_topic', $2, $3)
                    """,
                    user_id,
                    topic,
                    tapped_at + PARTNER_FOLLOW_UP_DELAY,
                )
                await self._reschedule_win_back(conn, user_id, tapped_at)

    async def record_inbound(
        self,
        channel: str,
        external_id: str,
        *,
        at: datetime | None = None,
    ) -> None:
        inbound_at = at or datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                user_id, _ = await self._ensure_user(conn, channel, external_id, "unknown")
                await conn.execute(
                    """
                    UPDATE users
                    SET last_inbound_at = $2
                    WHERE id = $1
                    """,
                    user_id,
                    inbound_at,
                )
                await conn.execute(
                    """
                    UPDATE follow_up_jobs
                    SET status = 'cancelled'
                    WHERE user_id = $1
                      AND kind = 'partner_topic'
                      AND status = 'pending'
                    """,
                    user_id,
                )
                await self._reschedule_win_back(conn, user_id, inbound_at)

    async def _reschedule_win_back(
        self,
        conn: asyncpg.Connection,
        user_id: UUID,
        inbound_at: datetime,
    ) -> None:
        blocked = await conn.fetchval(
            "SELECT follow_up_blocked_at FROM users WHERE id = $1",
            user_id,
        )
        if blocked is not None:
            return
        already_sent = await conn.fetchval(
            """
            SELECT 1
            FROM follow_up_jobs
            WHERE user_id = $1
              AND kind = 'win_back'
              AND status = 'sent'
            LIMIT 1
            """,
            user_id,
        )
        if already_sent is not None:
            return
        await conn.execute(
            """
            UPDATE follow_up_jobs
            SET status = 'cancelled'
            WHERE user_id = $1
              AND kind = 'win_back'
              AND status = 'pending'
            """,
            user_id,
        )
        await conn.execute(
            """
            INSERT INTO follow_up_jobs (user_id, kind, topic, scheduled_at)
            VALUES ($1, 'win_back', NULL, $2)
            """,
            user_id,
            inbound_at + WIN_BACK_DELAY,
        )

    async def claim_due_jobs(
        self,
        *,
        now: datetime | None = None,
        limit: int = 50,
    ) -> list[DueFollowUpJob]:
        claim_at = now or datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                from broadcasts import claim_due_broadcasts, claim_due_interval_broadcasts

                rows = await conn.fetch(
                    """
                    WITH due AS (
                        SELECT j.id
                        FROM follow_up_jobs j
                        WHERE j.status = 'pending'
                          AND j.scheduled_at <= $1
                        ORDER BY
                            CASE j.kind WHEN 'partner_topic' THEN 0 ELSE 1 END,
                            j.scheduled_at ASC
                        LIMIT $2
                        FOR UPDATE OF j SKIP LOCKED
                    )
                    UPDATE follow_up_jobs AS j
                    SET status = 'claimed'
                    FROM due
                    WHERE j.id = due.id
                    RETURNING j.id, j.kind, j.topic, j.user_id
                    """,
                    claim_at,
                    limit,
                )
                jobs: list[DueFollowUpJob] = []
                for row in rows:
                    identity = await conn.fetchrow(
                        """
                        SELECT channel, external_id
                        FROM identities
                        WHERE user_id = $1
                        ORDER BY created_at ASC
                        LIMIT 1
                        """,
                        row["user_id"],
                    )
                    if identity is None:
                        continue
                    if row["kind"] == "partner_topic":
                        message_text = await conn.fetchval(
                            "SELECT follow_up_text FROM partner_types WHERE slug = $1",
                            row["topic"],
                        )
                        message_text = message_text or ""
                    else:
                        message_text = WIN_BACK_TEXT
                    if not message_text:
                        await conn.execute(
                            """
                            UPDATE follow_up_jobs
                            SET status = 'cancelled'
                            WHERE id = $1
                            """,
                            row["id"],
                        )
                        continue
                    jobs.append(
                        DueFollowUpJob(
                            id=row["id"],
                            kind=row["kind"],
                            topic=row["topic"],
                            message_text=message_text,
                            channel=identity["channel"],
                            external_id=identity["external_id"],
                        )
                    )
                jobs.extend(await claim_due_broadcasts(conn, claim_at))
                jobs.extend(await claim_due_interval_broadcasts(conn, claim_at))
                return jobs

    async def mark_job_sent(
        self,
        job_id: UUID,
        *,
        message_text: str,
        at: datetime | None = None,
    ) -> None:
        sent_at = at or datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT j.user_id, i.channel, i.external_id
                    FROM follow_up_jobs j
                    JOIN identities i ON i.user_id = j.user_id
                    WHERE j.id = $1
                    ORDER BY i.created_at ASC
                    LIMIT 1
                    """,
                    job_id,
                )
                if row is None:
                    raise KeyError(job_id)
                await conn.execute(
                    """
                    UPDATE follow_up_jobs
                    SET status = 'sent', sent_at = $2, last_error = NULL
                    WHERE id = $1
                    """,
                    job_id,
                    sent_at,
                )
                ctx = await self._get_or_create_active(
                    conn, row["channel"], row["external_id"]
                )
                await conn.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, metadata)
                    VALUES ($1, 'assistant', $2, '{}'::jsonb)
                    """,
                    ctx.conversation_id,
                    message_text,
                )

    async def mark_job_failed(
        self,
        job_id: UUID,
        *,
        permanent: bool = False,
        error: str | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT user_id FROM follow_up_jobs WHERE id = $1",
                    job_id,
                )
                if row is None:
                    raise KeyError(job_id)
                await conn.execute(
                    """
                    UPDATE follow_up_jobs
                    SET status = 'failed', last_error = $2
                    WHERE id = $1
                    """,
                    job_id,
                    error,
                )
                if permanent:
                    await conn.execute(
                        """
                        UPDATE users
                        SET follow_up_blocked_at = COALESCE(follow_up_blocked_at, now())
                        WHERE id = $1
                        """,
                        row["user_id"],
                    )
                    await conn.execute(
                        """
                        UPDATE follow_up_jobs
                        SET status = 'cancelled'
                        WHERE user_id = $1
                          AND status = 'pending'
                        """,
                        row["user_id"],
                    )

    async def get_user_stats(self, *, timezone: str = "Asia/Bangkok") -> UserStats:
        channels = list(TELEGRAM_CHANNELS)
        async with self._pool.acquire() as conn:
            total_users = await conn.fetchval(
                """
                SELECT count(DISTINCT external_id)
                FROM identities
                WHERE channel = ANY($1::text[])
                """,
                channels,
            )
            active_today = await conn.fetchval(
                """
                SELECT count(DISTINCT i.external_id)
                FROM identities i
                WHERE i.channel = ANY($2::text[])
                  AND i.user_id IN (
                    SELECT c.user_id
                    FROM messages m
                    JOIN conversations c ON c.id = m.conversation_id
                    WHERE m.role = 'user'
                      AND (m.created_at AT TIME ZONE $1)::date
                          = (now() AT TIME ZONE $1)::date
                    UNION
                    SELECT id
                    FROM users
                    WHERE last_inbound_at IS NOT NULL
                      AND (last_inbound_at AT TIME ZONE $1)::date
                          = (now() AT TIME ZONE $1)::date
                    UNION
                    SELECT user_id
                    FROM topic_events
                    WHERE (created_at AT TIME ZONE $1)::date
                          = (now() AT TIME ZONE $1)::date
                  )
                """,
                timezone,
                channels,
            )
            new_users_today = await conn.fetchval(
                """
                SELECT count(*)
                FROM (
                    SELECT i.external_id
                    FROM identities i
                    JOIN users u ON u.id = i.user_id
                    WHERE i.channel = ANY($2::text[])
                    GROUP BY i.external_id
                    HAVING (min(u.created_at) AT TIME ZONE $1)::date
                           = (now() AT TIME ZONE $1)::date
                ) people
                """,
                timezone,
                channels,
            )
            new_users_7d = await conn.fetchval(
                """
                SELECT count(*)
                FROM (
                    SELECT i.external_id
                    FROM identities i
                    JOIN users u ON u.id = i.user_id
                    WHERE i.channel = ANY($1::text[])
                    GROUP BY i.external_id
                    HAVING min(u.created_at) >= now() - interval '7 days'
                ) people
                """,
                channels,
            )
            return UserStats(
                total_users=int(total_users or 0),
                active_today=int(active_today or 0),
                new_users_today=int(new_users_today or 0),
                new_users_7d=int(new_users_7d or 0),
            )

    async def get_bot_stats(self, *, timezone: str = "Asia/Bangkok") -> BotStats:
        user_stats = await self.get_user_stats(timezone=timezone)
        async with self._pool.acquire() as conn:
            topics_all_time = await self._fetch_topic_counts(conn)
            topics_7d = await self._fetch_topic_counts(
                conn,
                since_interval="7 days",
            )
            leads_all_time = await conn.fetchval("SELECT count(*) FROM leads")
            leads_7d = await conn.fetchval(
                """
                SELECT count(*)
                FROM leads
                WHERE created_at >= now() - interval '7 days'
                """
            )
            source_rows = await conn.fetch(
                """
                SELECT first_source, count(*)::int AS count
                FROM (
                    SELECT DISTINCT ON (i.external_id) u.first_source
                    FROM identities i
                    JOIN users u ON u.id = i.user_id
                    WHERE i.channel = ANY($1::text[])
                    ORDER BY i.external_id, u.created_at ASC, u.id ASC
                ) people
                GROUP BY first_source
                ORDER BY count DESC, first_source ASC
                """,
                list(TELEGRAM_CHANNELS),
            )
        return BotStats(
            total_users=user_stats.total_users,
            new_users_today=user_stats.new_users_today,
            active_today=user_stats.active_today,
            new_users_7d=user_stats.new_users_7d,
            topics_all_time=topics_all_time,
            topics_7d=topics_7d,
            leads_all_time=int(leads_all_time or 0),
            leads_7d=int(leads_7d or 0),
            users_by_first_source={row["first_source"]: int(row["count"]) for row in source_rows},
        )

    async def list_place_categories(self) -> list[PlaceCategory]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, slug, label, sort_order
                FROM place_categories
                ORDER BY sort_order ASC, slug ASC
                """
            )
            return [_place_category_from_row(row) for row in rows]

    async def create_place_category(
        self, *, slug: str, label: str, sort_order: int
    ) -> PlaceCategory:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO place_categories (slug, label, sort_order)
                VALUES ($1, $2, $3)
                RETURNING id, slug, label, sort_order
                """,
                slug,
                label,
                sort_order,
            )
        return _place_category_from_row(row)

    async def update_place_category(
        self, slug: str, *, label: str, sort_order: int
    ) -> PlaceCategory:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE place_categories
                SET label = $2, sort_order = $3
                WHERE slug = $1
                RETURNING id, slug, label, sort_order
                """,
                slug,
                label,
                sort_order,
            )
        return _place_category_from_row(row)

    async def delete_place_category(self, slug: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM place_categories WHERE slug = $1",
                slug,
            )

    async def create_place(
        self,
        *,
        name: str,
        category_id: UUID,
        google_place_id: str | None,
        latitude: float,
        longitude: float,
        partner_id: UUID | None = None,
        blurb: str | None = None,
        is_active: bool = True,
        maps_url: str | None = None,
        mike_recommends: bool = False,
    ) -> Place:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                INSERT INTO places (
                    name, category_id, partner_id, google_place_id,
                    latitude, longitude, blurb, is_active, maps_url, mike_recommends
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING {_PLACE_COLUMNS}
                """,
                name,
                category_id,
                partner_id,
                google_place_id,
                latitude,
                longitude,
                blurb,
                is_active,
                maps_url,
                mike_recommends,
            )
        return _place_from_row(row)

    async def update_place(
        self,
        place_id: UUID,
        *,
        name: str,
        category_id: UUID,
        google_place_id: str | None,
        latitude: float,
        longitude: float,
        partner_id: UUID | None = None,
        blurb: str | None = None,
        is_active: bool = True,
        maps_url: str | None = None,
        mike_recommends: bool = False,
    ) -> Place:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                UPDATE places SET
                    name = $2,
                    category_id = $3,
                    partner_id = $4,
                    google_place_id = $5,
                    latitude = $6,
                    longitude = $7,
                    blurb = $8,
                    is_active = $9,
                    maps_url = $10,
                    mike_recommends = $11
                WHERE id = $1
                RETURNING {_PLACE_COLUMNS}
                """,
                place_id,
                name,
                category_id,
                partner_id,
                google_place_id,
                latitude,
                longitude,
                blurb,
                is_active,
                maps_url,
                mike_recommends,
            )
        if row is None:
            raise KeyError(place_id)
        return _place_from_row(row)

    async def list_visible_places(self) -> list[Place]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT place.id, place.name, place.category_id, place.partner_id,
                       place.google_place_id, place.latitude, place.longitude,
                       place.blurb, place.is_active, place.maps_url,
                       place.mike_recommends
                FROM places AS place
                LEFT JOIN partners AS partner ON partner.id = place.partner_id
                WHERE place.is_active
                  AND (place.partner_id IS NULL OR partner.is_active)
                ORDER BY place.mike_recommends DESC, place.name ASC
                """
            )
        return [_place_from_row(row) for row in rows]

    async def ensure_identity(self, channel: str, external_id: str, *, source: str) -> UUID:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                user_id, _ = await self._ensure_user(conn, channel, external_id, source)
                return user_id

    async def set_place_favourite(
        self,
        channel: str,
        external_id: str,
        place_id: UUID,
        *,
        saved: bool,
    ) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                user_id, _ = await self._ensure_user(conn, channel, external_id, "tma")
                if saved:
                    await conn.execute(
                        """
                        INSERT INTO place_favourites (user_id, place_id)
                        VALUES ($1, $2)
                        ON CONFLICT (user_id, place_id) DO NOTHING
                        """,
                        user_id,
                        place_id,
                    )
                    return
                await conn.execute(
                    """
                    DELETE FROM place_favourites
                    WHERE user_id = $1 AND place_id = $2
                    """,
                    user_id,
                    place_id,
                )

    async def set_partner_favourite(
        self,
        channel: str,
        external_id: str,
        partner_id: UUID,
        *,
        saved: bool,
    ) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                user_id, _ = await self._ensure_user(conn, channel, external_id, "tma")
                if saved:
                    await conn.execute(
                        """
                        INSERT INTO partner_favourites (user_id, partner_id)
                        VALUES ($1, $2)
                        ON CONFLICT (user_id, partner_id) DO NOTHING
                        """,
                        user_id,
                        partner_id,
                    )
                    return
                await conn.execute(
                    """
                    DELETE FROM partner_favourites
                    WHERE user_id = $1 AND partner_id = $2
                    """,
                    user_id,
                    partner_id,
                )

    async def list_favourite_refs(
        self, channel: str, external_id: str
    ) -> list[tuple[str, UUID]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT kind, id
                FROM (
                    SELECT 'place' AS kind, fav.place_id AS id, fav.created_at
                    FROM place_favourites AS fav
                    JOIN identities AS i ON i.user_id = fav.user_id
                    JOIN places AS place ON place.id = fav.place_id
                    LEFT JOIN partners AS partner ON partner.id = place.partner_id
                    WHERE i.channel = $1
                      AND i.external_id = $2
                      AND place.is_active
                      AND (place.partner_id IS NULL OR partner.is_active)
                    UNION ALL
                    SELECT 'partner' AS kind, fav.partner_id AS id, fav.created_at
                    FROM partner_favourites AS fav
                    JOIN identities AS i ON i.user_id = fav.user_id
                    JOIN partners AS partner ON partner.id = fav.partner_id
                    WHERE i.channel = $1
                      AND i.external_id = $2
                      AND partner.is_active
                ) AS saved
                ORDER BY created_at DESC, id
                """,
                channel,
                external_id,
            )
        return [(row["kind"], row["id"]) for row in rows]

    async def list_favourite_places(self, channel: str, external_id: str) -> list[Place]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT place.id, place.name, place.category_id, place.partner_id,
                       place.google_place_id, place.latitude, place.longitude,
                       place.blurb, place.is_active, place.maps_url,
                       place.mike_recommends
                FROM place_favourites AS fav
                JOIN identities AS i ON i.user_id = fav.user_id
                JOIN places AS place ON place.id = fav.place_id
                LEFT JOIN partners AS partner ON partner.id = place.partner_id
                WHERE i.channel = $1
                  AND i.external_id = $2
                  AND place.is_active
                  AND (place.partner_id IS NULL OR partner.is_active)
                ORDER BY fav.created_at DESC, place.id
                """,
                channel,
                external_id,
            )
        return [_place_from_row(row) for row in rows]

    async def list_places(self) -> list[Place]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT {_PLACE_COLUMNS}
                FROM places
                ORDER BY name ASC
                """
            )
        return [_place_from_row(row) for row in rows]

    async def add_place_asset(
        self, place_id: UUID, path: str, sort_order: int = 0
    ) -> PlaceAsset:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO place_assets (place_id, path, sort_order)
                VALUES ($1, $2, $3)
                RETURNING id, place_id, path, sort_order
                """,
                place_id,
                path,
                sort_order,
            )
        return _place_asset_from_row(row)

    async def list_place_assets(self, place_id: UUID) -> list[PlaceAsset]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, place_id, path, sort_order
                FROM place_assets
                WHERE place_id = $1
                ORDER BY sort_order ASC, id ASC
                """,
                place_id,
            )
        return [_place_asset_from_row(row) for row in rows]

    async def delete_place_assets(self, asset_ids: list[UUID]) -> None:
        if not asset_ids:
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM place_assets WHERE id = ANY($1::uuid[])",
                asset_ids,
            )

    async def list_partner_types(self) -> list[PartnerType]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *
                FROM partner_types
                ORDER BY sort_order ASC, slug ASC
                """
            )
            return [_partner_type_from_row(row) for row in rows]

    async def get_partner_type(self, slug: str) -> PartnerType | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM partner_types WHERE slug = $1",
                slug,
            )
            if row is None:
                return None
            return _partner_type_from_row(row)

    async def create_partner_type(self, partner_type: PartnerType) -> PartnerType:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO partner_types (
                    slug, is_menu_visible, sort_order, button_label, topic_label,
                    intro, fallback, caption_emoji, caption_cta, button_template,
                    follow_up_text, choice_phrase
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                partner_type.slug,
                partner_type.is_menu_visible,
                partner_type.sort_order,
                partner_type.button_label,
                partner_type.topic_label,
                partner_type.intro,
                partner_type.fallback,
                partner_type.caption_emoji,
                partner_type.caption_cta,
                partner_type.button_template,
                partner_type.follow_up_text,
                partner_type.choice_phrase,
            )
        return partner_type

    async def update_partner_type(self, slug: str, partner_type: PartnerType) -> PartnerType:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchrow(
                    "SELECT slug FROM partner_types WHERE slug = $1",
                    slug,
                )
                if existing is None:
                    raise KeyError(slug)

                if partner_type.slug != slug:
                    conflict = await conn.fetchrow(
                        "SELECT slug FROM partner_types WHERE slug = $1",
                        partner_type.slug,
                    )
                    if conflict is not None:
                        raise ValueError("partner type slug already exists")

                await conn.execute(
                    """
                    UPDATE partner_types SET
                        slug = $2,
                        is_menu_visible = $3,
                        sort_order = $4,
                        button_label = $5,
                        topic_label = $6,
                        intro = $7,
                        fallback = $8,
                        caption_emoji = $9,
                        caption_cta = $10,
                        button_template = $11,
                        follow_up_text = $12,
                        choice_phrase = $13
                    WHERE slug = $1
                    """,
                    slug,
                    partner_type.slug,
                    partner_type.is_menu_visible,
                    partner_type.sort_order,
                    partner_type.button_label,
                    partner_type.topic_label,
                    partner_type.intro,
                    partner_type.fallback,
                    partner_type.caption_emoji,
                    partner_type.caption_cta,
                    partner_type.button_template,
                    partner_type.follow_up_text,
                    partner_type.choice_phrase,
                )
                return partner_type

    async def list_partners(self) -> list[Partner]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT partner.id, partner.name, partner_type.slug AS type,
                       partner.referral_url, partner.blurb, partner.logo_path,
                       partner.is_active, partner.sort_order
                FROM partners AS partner
                JOIN partner_types AS partner_type
                    ON partner_type.id = partner.partner_type_id
                ORDER BY partner_type.slug ASC, partner.sort_order ASC, partner.name ASC
                """
            )
            return [_partner_from_row(row) for row in rows]

    async def list_active_partners(self, partner_type: str) -> list[Partner]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT partner.id, partner.name, partner_type.slug AS type,
                       partner.referral_url, partner.blurb, partner.logo_path,
                       partner.sort_order
                FROM partners AS partner
                JOIN partner_types AS partner_type
                    ON partner_type.id = partner.partner_type_id
                WHERE partner_type.slug = $1 AND partner.is_active = true
                ORDER BY partner.sort_order ASC, partner.name ASC
                """,
                partner_type,
            )
            return [_partner_from_row(row, is_active=True) for row in rows]

    async def create_partner(
        self,
        *,
        name: str,
        type: str,
        referral_url: str,
        blurb: str = "",
        is_active: bool = True,
        sort_order: int = 0,
    ) -> Partner:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH inserted AS (
                    INSERT INTO partners (
                        name, partner_type_id, referral_url, blurb, logo_path,
                        is_active, sort_order
                    )
                    SELECT $1, id, $3, $4, '', $5, $6
                    FROM partner_types
                    WHERE slug = $2
                    RETURNING id, name, partner_type_id, referral_url, blurb,
                        logo_path, is_active, sort_order
                )
                SELECT inserted.id, inserted.name, partner_type.slug AS type,
                       inserted.referral_url, inserted.blurb, inserted.logo_path,
                       inserted.is_active, inserted.sort_order
                FROM inserted
                JOIN partner_types AS partner_type
                    ON partner_type.id = inserted.partner_type_id
                """,
                name,
                type,
                referral_url,
                blurb,
                is_active,
                sort_order,
            )
        if row is None:
            raise KeyError(type)
        return _partner_from_row(row)

    async def update_partner(
        self,
        partner_id: UUID,
        *,
        name: str,
        type: str,
        referral_url: str,
        blurb: str = "",
        is_active: bool = True,
        sort_order: int = 0,
    ) -> Partner:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH updated AS (
                    UPDATE partners SET
                        name = $2,
                        partner_type_id = (
                            SELECT id FROM partner_types WHERE slug = $3
                        ),
                        referral_url = $4,
                        blurb = $5,
                        is_active = $6,
                        sort_order = $7
                    WHERE id = $1
                    RETURNING id, name, partner_type_id, referral_url, blurb,
                        logo_path, is_active, sort_order
                )
                SELECT updated.id, updated.name, partner_type.slug AS type,
                       updated.referral_url, updated.blurb, updated.logo_path,
                       updated.is_active, updated.sort_order
                FROM updated
                JOIN partner_types AS partner_type
                    ON partner_type.id = updated.partner_type_id
                """,
                partner_id,
                name,
                type,
                referral_url,
                blurb,
                is_active,
                sort_order,
            )
        if row is None:
            raise KeyError(partner_id)
        return _partner_from_row(row)

    async def set_partner_logo(
        self, partner_id: UUID, logo_path: str | None
    ) -> tuple[str | None, Partner]:
        """Replace a partner's logo; returns (previous logo_path, updated partner)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH old AS (
                    SELECT logo_path FROM partners WHERE id = $1 FOR UPDATE
                ),
                updated AS (
                    UPDATE partners SET logo_path = $2
                    FROM old
                    WHERE partners.id = $1
                    RETURNING partners.id, partners.name, partners.partner_type_id,
                        partners.referral_url, partners.blurb, partners.logo_path,
                        partners.is_active, partners.sort_order,
                        old.logo_path AS previous_logo_path
                )
                SELECT updated.id, updated.name, partner_type.slug AS type,
                       updated.referral_url, updated.blurb, updated.logo_path,
                       updated.is_active, updated.sort_order, updated.previous_logo_path
                FROM updated
                JOIN partner_types AS partner_type
                    ON partner_type.id = updated.partner_type_id
                """,
                partner_id,
                logo_path,
            )
        if row is None:
            raise KeyError(partner_id)
        return row["previous_logo_path"], _partner_from_row(row)

    async def _fetch_topic_counts(
        self,
        conn: asyncpg.Connection,
        *,
        since_interval: str | None = None,
    ) -> dict[str, TopicCount]:
        if since_interval:
            rows = await conn.fetch(
                """
                SELECT topic,
                       count(*)::int AS taps,
                       count(DISTINCT user_id)::int AS unique_users
                FROM topic_events
                WHERE created_at >= now() - ($1::text)::interval
                GROUP BY topic
                """,
                since_interval,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT topic,
                       count(*)::int AS taps,
                       count(DISTINCT user_id)::int AS unique_users
                FROM topic_events
                GROUP BY topic
                """
            )
        return {
            row["topic"]: TopicCount(
                unique_users=row["unique_users"],
                taps=row["taps"],
            )
            for row in rows
        }

    async def _ensure_user(
        self,
        conn: asyncpg.Connection,
        channel: str,
        external_id: str,
        source: str,
    ) -> tuple[UUID, str]:
        row = await conn.fetchrow(
            """
            SELECT u.id, u.first_source
            FROM identities i
            JOIN users u ON u.id = i.user_id
            WHERE i.channel = $1 AND i.external_id = $2
            """,
            channel,
            external_id,
        )
        if row:
            if row["first_source"] == "unknown" and source != "unknown":
                await conn.execute(
                    "UPDATE users SET first_source = $1 WHERE id = $2",
                    source,
                    row["id"],
                )
                return row["id"], source
            return row["id"], row["first_source"]

        user_id = await conn.fetchval(
            """
            INSERT INTO users (first_source)
            VALUES ($1)
            RETURNING id
            """,
            source,
        )
        await conn.execute(
            """
            INSERT INTO identities (user_id, channel, external_id)
            VALUES ($1, $2, $3)
            """,
            user_id,
            channel,
            external_id,
        )
        return user_id, source

    async def _close_active_conversation(self, conn: asyncpg.Connection, user_id: UUID) -> None:
        await conn.execute(
            """
            UPDATE conversations
            SET status = 'closed', ended_at = now()
            WHERE user_id = $1 AND status = 'active'
            """,
            user_id,
        )

    async def _open_conversation(
        self,
        conn: asyncpg.Connection,
        user_id: UUID,
        source: str,
    ) -> UUID:
        return await conn.fetchval(
            """
            INSERT INTO conversations (user_id, source, status)
            VALUES ($1, $2, 'active')
            RETURNING id
            """,
            user_id,
            source,
        )

    async def place_partner_is_in_knowledge_base(self, place_id: UUID) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 1
                FROM places
                JOIN knowledge_base ON knowledge_base.partner_id = places.partner_id
                WHERE places.id = $1
                """,
                place_id,
            )
        return row is not None

    async def partner_place_is_in_knowledge_base(self, partner_id: UUID) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 1
                FROM knowledge_base
                JOIN places ON places.id = knowledge_base.place_id
                WHERE places.partner_id = $1
                """,
                partner_id,
            )
        return row is not None

    async def _knowledge_base_entry_by_id(
        self, conn: asyncpg.Connection, entry_id: UUID
    ) -> KnowledgeBaseEntry:
        row = await conn.fetchrow(
            _KNOWLEDGE_BASE_ROWS + " WHERE knowledge_base.id = $1",
            entry_id,
        )
        return _knowledge_base_entry(row)

    async def add_knowledge_base_partner(self, partner_id: UUID) -> KnowledgeBaseEntry:
        async with self._pool.acquire() as conn:
            entry_id = await conn.fetchval(
                """
                INSERT INTO knowledge_base (partner_id)
                VALUES ($1)
                RETURNING id
                """,
                partner_id,
            )
            return await self._knowledge_base_entry_by_id(conn, entry_id)

    async def add_knowledge_base_place(self, place_id: UUID) -> KnowledgeBaseEntry:
        async with self._pool.acquire() as conn:
            entry_id = await conn.fetchval(
                """
                INSERT INTO knowledge_base (place_id)
                VALUES ($1)
                RETURNING id
                """,
                place_id,
            )
            return await self._knowledge_base_entry_by_id(conn, entry_id)

    async def list_knowledge_base(self) -> list[KnowledgeBaseEntry]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                _KNOWLEDGE_BASE_ROWS + " ORDER BY name ASC"
            )
        return [_knowledge_base_entry(row) for row in rows]

    async def delete_knowledge_base_entry(self, entry_id: UUID) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM knowledge_base WHERE id = $1",
                entry_id,
            )

    async def _fetch_active(
        self,
        conn: asyncpg.Connection,
        channel: str,
        external_id: str,
    ) -> ConversationContext | None:
        row = await conn.fetchrow(
            """
            SELECT u.id AS user_id,
                   c.id AS conversation_id,
                   c.source,
                   u.first_source
            FROM identities i
            JOIN users u ON u.id = i.user_id
            JOIN conversations c ON c.user_id = u.id AND c.status = 'active'
            WHERE i.channel = $1 AND i.external_id = $2
            """,
            channel,
            external_id,
        )
        if row is None:
            return None
        return ConversationContext(
            user_id=row["user_id"],
            conversation_id=row["conversation_id"],
            source=row["source"],
            first_source=row["first_source"],
        )

    async def _get_or_create_active(
        self,
        conn: asyncpg.Connection,
        channel: str,
        external_id: str,
    ) -> ConversationContext:
        ctx = await self._fetch_active(conn, channel, external_id)
        if ctx is not None:
            return ctx

        user_id, first_source = await self._ensure_user(conn, channel, external_id, "unknown")
        conversation_id = await self._open_conversation(conn, user_id, "unknown")
        return ConversationContext(
            user_id=user_id,
            conversation_id=conversation_id,
            source="unknown",
            first_source=first_source,
        )
