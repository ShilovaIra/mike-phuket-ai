from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import asyncpg

from admin_api.passwords import hash_password, verify_password


def _counts(views: int, clicks: int, opened: int) -> dict:
    return {"views": views, "referral_clicks": clicks, "opened_views": opened}


@dataclass(frozen=True)
class PartnerUser:
    id: UUID
    email: str
    password_hash: str


async def create_partner_user(
    pool: asyncpg.Pool,
    *,
    email: str,
    password: str,
    partner_ids: list[UUID],
) -> PartnerUser:
    password_hash = hash_password(password)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO partner_users (email, password_hash)
                VALUES ($1, $2)
                RETURNING id, email, password_hash
                """,
                email.lower().strip(),
                password_hash,
            )
            await conn.executemany(
                """
                INSERT INTO partner_access (partner_user_id, partner_id)
                VALUES ($1, $2)
                """,
                [(row["id"], partner_id) for partner_id in partner_ids],
            )
    return PartnerUser(id=row["id"], email=row["email"], password_hash=row["password_hash"])


async def get_partner_user_by_email(pool: asyncpg.Pool, email: str) -> PartnerUser | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, password_hash
            FROM partner_users
            WHERE email = $1
            """,
            email.lower().strip(),
        )
    if row is None:
        return None
    return PartnerUser(id=row["id"], email=row["email"], password_hash=row["password_hash"])


async def has_partner_access(
    pool: asyncpg.Pool, *, partner_user_id: UUID, partner_id: UUID
) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchval(
            """
            SELECT 1
            FROM partner_access
            WHERE partner_user_id = $1 AND partner_id = $2
            """,
            partner_user_id,
            partner_id,
        )
    return row is not None


def authenticate_partner_user(user: PartnerUser | None, password: str) -> PartnerUser | None:
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def get_partner_stats(pool: asyncpg.Pool, partner_id: UUID) -> dict:
    async with pool.acquire() as conn:
        all_time = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM partner_views WHERE partner_id = $1) AS views,
                (
                    SELECT COUNT(*)
                    FROM partner_referral_clicks c
                    JOIN partner_views v ON v.id = c.view_id
                    WHERE v.partner_id = $1
                ) AS clicks,
                (
                    SELECT COUNT(*)
                    FROM partner_views v
                    WHERE v.partner_id = $1
                      AND EXISTS (
                          SELECT 1 FROM partner_referral_clicks c WHERE c.view_id = v.id
                      )
                ) AS opened
            """,
            partner_id,
        )
        last_30 = await conn.fetchrow(
            """
            SELECT
                (
                    SELECT COUNT(*) FROM partner_views
                    WHERE partner_id = $1 AND created_at >= now() - interval '30 days'
                ) AS views,
                (
                    SELECT COUNT(*)
                    FROM partner_referral_clicks c
                    JOIN partner_views v ON v.id = c.view_id
                    WHERE v.partner_id = $1
                      AND c.created_at >= now() - interval '30 days'
                ) AS clicks,
                (
                    SELECT COUNT(*)
                    FROM partner_views v
                    WHERE v.partner_id = $1
                      AND v.created_at >= now() - interval '30 days'
                      AND EXISTS (
                          SELECT 1 FROM partner_referral_clicks c WHERE c.view_id = v.id
                      )
                ) AS opened
            """,
            partner_id,
        )
        category = await conn.fetchrow(
            """
            SELECT
                partner_type.choice_phrase AS phrase,
                (
                    SELECT COUNT(DISTINCT topic_event.user_id)::int
                    FROM topic_events AS topic_event
                    WHERE topic_event.topic = partner_type.slug
                ) AS all_time,
                (
                    SELECT COUNT(DISTINCT topic_event.user_id)::int
                    FROM topic_events AS topic_event
                    WHERE topic_event.topic = partner_type.slug
                      AND topic_event.created_at >= now() - interval '30 days'
                ) AS last_30_days
            FROM partners AS partner
            JOIN partner_types AS partner_type
                ON partner_type.id = partner.partner_type_id
            WHERE partner.id = $1
            """,
            partner_id,
        )
        favourite_users = await conn.fetchval(
            """
            SELECT COUNT(*)::int
            FROM partner_favourites
            WHERE partner_id = $1
            """,
            partner_id,
        )
    return {
        "partner_id": str(partner_id),
        "all_time": _counts(all_time["views"], all_time["clicks"], all_time["opened"]),
        "last_30_days": _counts(last_30["views"], last_30["clicks"], last_30["opened"]),
        "category_users": {
            "phrase": category["phrase"],
            "all_time": category["all_time"],
            "last_30_days": category["last_30_days"],
        },
        "favourite_users": favourite_users,
    }


async def list_accessible_partners(pool: asyncpg.Pool, partner_user_id: UUID) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, p.name
            FROM partner_access a
            JOIN partners p ON p.id = a.partner_id
            WHERE a.partner_user_id = $1
            ORDER BY p.name ASC
            """,
            partner_user_id,
        )
    return [{"id": str(row["id"]), "name": row["name"]} for row in rows]


async def delete_partner_user(pool: asyncpg.Pool, partner_user_id: UUID) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM partner_users WHERE id = $1",
            partner_user_id,
        )
    return result == "DELETE 1"


async def replace_partner_access(
    pool: asyncpg.Pool, *, partner_user_id: UUID, partner_ids: list[UUID]
) -> bool:
    async with pool.acquire() as conn:
        async with conn.transaction():
            exists = await conn.fetchval(
                "SELECT 1 FROM partner_users WHERE id = $1",
                partner_user_id,
            )
            if exists is None:
                return False
            await conn.execute(
                "DELETE FROM partner_access WHERE partner_user_id = $1",
                partner_user_id,
            )
            if partner_ids:
                await conn.executemany(
                    """
                    INSERT INTO partner_access (partner_user_id, partner_id)
                    VALUES ($1, $2)
                    """,
                    [(partner_user_id, partner_id) for partner_id in partner_ids],
                )
    return True


async def set_partner_user_password(
    pool: asyncpg.Pool, *, partner_user_id: UUID, password: str
) -> bool:
    password_hash = hash_password(password)
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE partner_users SET password_hash = $2 WHERE id = $1",
            partner_user_id,
            password_hash,
        )
    return result == "UPDATE 1"



async def list_partner_users(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT u.id, u.email, u.created_at, p.id AS partner_id, p.name AS partner_name
            FROM partner_users u
            LEFT JOIN partner_access a ON a.partner_user_id = u.id
            LEFT JOIN partners p ON p.id = a.partner_id
            ORDER BY u.email ASC, p.name ASC
            """
        )
    users: dict[str, dict] = {}
    for row in rows:
        entry = users.setdefault(
            str(row["id"]),
            {
                "id": str(row["id"]),
                "email": row["email"],
                "created_at": row["created_at"].isoformat(),
                "partners": [],
            },
        )
        if row["partner_id"] is not None:
            entry["partners"].append(
                {"id": str(row["partner_id"]), "name": row["partner_name"]}
            )
    return list(users.values())
