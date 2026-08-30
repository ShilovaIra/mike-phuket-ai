from __future__ import annotations

import secrets
from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

import asyncpg

from partners import Partner


async def wrap_offer_for_user(
    pool: asyncpg.Pool, *, partner: Partner, user_id: UUID
) -> str:
    token = secrets.token_urlsafe(24)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO partner_views (partner_id, user_id, token)
            VALUES ($1, $2, $3)
            """,
            partner.id,
            user_id,
            token,
        )
    return f"/r/{token}"


def _http_public_base(public_base: str) -> str | None:
    base = public_base.strip().rstrip("/")
    if base.startswith("http://") or base.startswith("https://"):
        return base
    return None


async def wrap_partners_for_user(
    pool: asyncpg.Pool,
    partners: Sequence[Partner],
    user_id: UUID,
    *,
    public_base: str,
) -> list[Partner]:
    base = _http_public_base(public_base)
    if base is None:
        # Telegram url buttons require http(s). Empty PARTNER_OFFER_BASE_URL
        # would produce "/r/…" and the API drops every card after the intro.
        return list(partners)
    wrapped: list[Partner] = []
    for partner in partners:
        path = await wrap_offer_for_user(pool, partner=partner, user_id=user_id)
        wrapped.append(replace(partner, referral_url=f"{base}{path}"))
    return wrapped


async def record_referral_click(pool: asyncpg.Pool, token: str) -> str | None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT v.id, p.referral_url
                FROM partner_views v
                JOIN partners p ON p.id = v.partner_id
                WHERE v.token = $1
                """,
                token,
            )
            if row is None:
                return None
            await conn.execute(
                "INSERT INTO partner_referral_clicks (view_id) VALUES ($1)",
                row["id"],
            )
            return row["referral_url"]
