from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import asyncpg


class BroadcastLocked(Exception):
    pass


@dataclass(frozen=True)
class Broadcast:
    id: UUID
    text: str
    scheduled_at: datetime
    status: str
    button_url: str | None
    button_label: str | None


def _broadcast(row: asyncpg.Record) -> Broadcast:
    return Broadcast(
        id=row["id"],
        text=row["text"],
        scheduled_at=row["scheduled_at"],
        status=row["status"],
        button_url=row["button_url"],
        button_label=row["button_label"],
    )


_RETURNING = "id, text, scheduled_at, status, button_url, button_label"


async def create_broadcast(
    pool: asyncpg.Pool,
    *,
    text: str,
    scheduled_at: datetime,
    button_url: str | None = None,
    button_label: str | None = None,
) -> Broadcast:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            INSERT INTO broadcasts (text, scheduled_at, button_url, button_label)
            VALUES ($1, $2, $3, $4)
            RETURNING {_RETURNING}
            """,
            text,
            scheduled_at,
            button_url,
            button_label,
        )
    return _broadcast(row)


async def list_broadcasts(pool: asyncpg.Pool) -> list[Broadcast]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT {_RETURNING}
            FROM broadcasts
            ORDER BY scheduled_at ASC, created_at ASC
            """
        )
    return [_broadcast(row) for row in rows]


async def update_broadcast(
    pool: asyncpg.Pool,
    broadcast_id: UUID,
    *,
    text: str,
    scheduled_at: datetime,
    button_url: str | None,
    button_label: str | None,
) -> Broadcast | None:
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT status FROM broadcasts WHERE id = $1",
            broadcast_id,
        )
        if existing is None:
            return None
        if existing["status"] != "scheduled":
            raise BroadcastLocked
        row = await conn.fetchrow(
            f"""
            UPDATE broadcasts
            SET text = $2,
                scheduled_at = $3,
                button_url = $4,
                button_label = $5
            WHERE id = $1 AND status = 'scheduled'
            RETURNING {_RETURNING}
            """,
            broadcast_id,
            text,
            scheduled_at,
            button_url,
            button_label,
        )
    if row is None:
        raise BroadcastLocked
    return _broadcast(row)


async def delete_broadcast(pool: asyncpg.Pool, broadcast_id: UUID) -> bool:
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT status FROM broadcasts WHERE id = $1",
            broadcast_id,
        )
        if existing is None:
            return False
        if existing["status"] != "scheduled":
            raise BroadcastLocked
        result = await conn.execute(
            "DELETE FROM broadcasts WHERE id = $1 AND status = 'scheduled'",
            broadcast_id,
        )
    return result == "DELETE 1"


async def claim_due_broadcasts(conn: asyncpg.Connection, claim_at: datetime) -> list:
    from db.store import DueFollowUpJob

    claimed = await conn.fetch(
        """
        UPDATE broadcasts
        SET status = 'sent'
        WHERE status = 'scheduled' AND scheduled_at <= $1
        RETURNING id, text, button_url, button_label
        """,
        claim_at,
    )
    if not claimed:
        return []
    recipients = await conn.fetch(
        """
        SELECT u.id AS user_id, i.external_id
        FROM identities i
        JOIN users u ON u.id = i.user_id
        WHERE i.channel = 'telegram'
          AND u.follow_up_blocked_at IS NULL
        ORDER BY i.created_at ASC
        """
    )
    jobs = []
    for broadcast in claimed:
        for recipient in recipients:
            job_id = await conn.fetchval(
                """
                INSERT INTO follow_up_jobs (
                    user_id, kind, topic, scheduled_at, status
                )
                VALUES ($1, 'broadcast', NULL, $2, 'claimed')
                RETURNING id
                """,
                recipient["user_id"],
                claim_at,
            )
            jobs.append(
                DueFollowUpJob(
                    id=job_id,
                    kind="broadcast",
                    topic=None,
                    message_text=broadcast["text"],
                    channel="telegram",
                    external_id=recipient["external_id"],
                    button_url=broadcast["button_url"],
                    button_label=broadcast["button_label"],
                )
            )
    return jobs
