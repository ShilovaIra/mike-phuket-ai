from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import asyncpg

from db.migrate import apply_schema_pool
from partners import Partner, PartnerType


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


@dataclass(frozen=True)
class UserStats:
    total_users: int
    active_today: int
    new_users_today: int = 0
    new_users_7d: int = 0


def _partner_type_from_row(row: asyncpg.Record) -> PartnerType:
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

    async def get_user_stats(self, *, timezone: str = "Asia/Bangkok") -> UserStats:
        async with self._pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT count(*) FROM users")
            active_today = await conn.fetchval(
                """
                SELECT count(DISTINCT c.user_id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE m.role = 'user'
                  AND (m.created_at AT TIME ZONE $1)::date
                      = (now() AT TIME ZONE $1)::date
                """,
                timezone,
            )
            new_users_today = await conn.fetchval(
                """
                SELECT count(*)
                FROM users
                WHERE (created_at AT TIME ZONE $1)::date
                      = (now() AT TIME ZONE $1)::date
                """,
                timezone,
            )
            new_users_7d = await conn.fetchval(
                """
                SELECT count(*)
                FROM users
                WHERE created_at >= now() - interval '7 days'
                """
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
        return BotStats(
            total_users=user_stats.total_users,
            new_users_today=user_stats.new_users_today,
            active_today=user_stats.active_today,
            new_users_7d=user_stats.new_users_7d,
            topics_all_time=topics_all_time,
            topics_7d=topics_7d,
            leads_all_time=int(leads_all_time or 0),
            leads_7d=int(leads_7d or 0),
        )

    async def list_partner_types(self) -> list[PartnerType]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT slug, is_menu_visible, sort_order, button_label, topic_label,
                       intro, fallback, caption_emoji, caption_cta, button_template
                FROM partner_types
                ORDER BY sort_order ASC, slug ASC
                """
            )
            return [_partner_type_from_row(row) for row in rows]

    async def get_partner_type(self, slug: str) -> PartnerType | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT slug, is_menu_visible, sort_order, button_label, topic_label,
                       intro, fallback, caption_emoji, caption_cta, button_template
                FROM partner_types
                WHERE slug = $1
                """,
                slug,
            )
            if row is None:
                return None
            return _partner_type_from_row(row)

    async def list_active_partners(self, partner_type: str) -> list[Partner]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, type, referral_url, blurb, logo_path, sort_order
                FROM partners
                WHERE type = $1 AND is_active = true
                ORDER BY sort_order ASC, name ASC
                """,
                partner_type,
            )
            return [
                Partner(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    referral_url=row["referral_url"],
                    blurb=row["blurb"],
                    sort_order=row["sort_order"],
                    logo_path=row["logo_path"],
                )
                for row in rows
            ]

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
