from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

import asyncpg

from . import queries


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
            queries.INSERT_BROADCAST_RETURNING,
            text,
            scheduled_at,
            button_url,
            button_label,
        )
    return _broadcast(row)


async def list_broadcasts(pool: asyncpg.Pool) -> list[Broadcast]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(queries.SELECT_BROADCASTS_ORDERED_BY_SCHEDULE)
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
        existing = await conn.fetchrow(queries.SELECT_BROADCAST_STATUS_BY_ID, broadcast_id)
        if existing is None:
            return None
        if existing["status"] != "scheduled":
            raise BroadcastLocked
        row = await conn.fetchrow(
            queries.UPDATE_SCHEDULED_BROADCAST,
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
        result = await conn.execute(queries.DELETE_BROADCAST_BY_ID, broadcast_id)
    return result == "DELETE 1"


async def claim_due_broadcasts(conn: asyncpg.Connection, claim_at: datetime) -> list:
    from db.store import DueFollowUpJob

    claimed = await conn.fetch(queries.MARK_DUE_SCHEDULED_BROADCASTS_SENT, claim_at)
    if not claimed:
        return []
    recipients = await conn.fetch(queries.SELECT_UNBLOCKED_TELEGRAM_IDENTITIES)
    jobs = []
    for broadcast in claimed:
        for recipient in recipients:
            job_id = await conn.fetchval(
                queries.INSERT_CLAIMED_BROADCAST_FOLLOW_UP_JOB,
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


@dataclass(frozen=True)
class BroadcastListMessage:
    id: UUID
    text: str
    button_url: str | None = None
    button_label: str | None = None


@dataclass(frozen=True)
class BroadcastList:
    id: UUID
    name: str
    messages: list[BroadcastListMessage]


async def create_broadcast_list(pool: asyncpg.Pool, *, name: str) -> BroadcastList:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(queries.INSERT_BROADCAST_LIST_RETURNING, name)
    return BroadcastList(id=row["id"], name=row["name"], messages=[])


async def add_broadcast_list_message(
    pool: asyncpg.Pool,
    list_id: UUID,
    *,
    text: str,
    button_url: str | None = None,
    button_label: str | None = None,
) -> BroadcastListMessage | None:
    async with pool.acquire() as conn:
        exists = await conn.fetchval(queries.SELECT_BROADCAST_LIST_EXISTS, list_id)
        if exists is None:
            return None
        row = await conn.fetchrow(
            queries.INSERT_BROADCAST_LIST_MESSAGE_AT_END,
            list_id,
            text,
            button_url,
            button_label,
        )
    return BroadcastListMessage(
        id=row["id"],
        text=row["text"],
        button_url=row["button_url"],
        button_label=row["button_label"],
    )


async def list_broadcast_lists(pool: asyncpg.Pool) -> list[BroadcastList]:
    async with pool.acquire() as conn:
        lists = await conn.fetch(queries.SELECT_BROADCAST_LISTS_BY_CREATED_AT)
        messages = await conn.fetch(queries.SELECT_BROADCAST_LIST_MESSAGES_IN_ORDER)
    by_list: dict[UUID, list[BroadcastListMessage]] = {}
    for row in messages:
        by_list.setdefault(row["list_id"], []).append(
            BroadcastListMessage(
                id=row["id"],
                text=row["text"],
                button_url=row["button_url"],
                button_label=row["button_label"],
            )
        )
    return [
        BroadcastList(
            id=row["id"],
            name=row["name"],
            messages=by_list.get(row["id"], []),
        )
        for row in lists
    ]


async def move_broadcast_list_message(
    pool: asyncpg.Pool,
    list_id: UUID,
    message_id: UUID,
    *,
    direction: str,
) -> bool:
    async with pool.acquire() as conn:
        async with conn.transaction():
            current = await conn.fetchrow(
                queries.SELECT_BROADCAST_LIST_MESSAGE_IN_LIST,
                message_id,
                list_id,
            )
            if current is None:
                return False
            neighbor_query = (
                queries.SELECT_BROADCAST_LIST_MESSAGE_WITH_LOWER_POSITION
                if direction == "up"
                else queries.SELECT_BROADCAST_LIST_MESSAGE_WITH_HIGHER_POSITION
            )
            neighbor = await conn.fetchrow(
                neighbor_query,
                list_id,
                current["position"],
            )
            if neighbor is None:
                return True
            await conn.execute(
                queries.UPDATE_BROADCAST_LIST_MESSAGE_POSITION,
                current["id"],
                neighbor["position"],
            )
            await conn.execute(
                queries.UPDATE_BROADCAST_LIST_MESSAGE_POSITION,
                neighbor["id"],
                current["position"],
            )
    return True


@dataclass(frozen=True)
class IntervalBroadcast:
    id: UUID
    list_id: UUID
    list_name: str
    interval_days: int
    scheduled_at: datetime
    next_message: BroadcastListMessage | None


def _choose_next_message(messages, last_message_id):
    if not messages:
        return None
    if last_message_id is None:
        return messages[0]
    ids = [message["id"] for message in messages]
    try:
        index = ids.index(last_message_id)
    except ValueError:
        return messages[0]
    return messages[(index + 1) % len(messages)]


def _next_interval_at(scheduled_at: datetime, interval_days: int, claim_at: datetime) -> datetime:
    step = timedelta(days=interval_days)
    candidate = scheduled_at + step
    while candidate <= claim_at:
        candidate += step
    return candidate


def _message_from_row(row) -> BroadcastListMessage:
    return BroadcastListMessage(
        id=row["id"],
        text=row["text"],
        button_url=row["button_url"],
        button_label=row["button_label"],
    )


async def _load_interval_broadcasts(conn, broadcast_id: UUID | None = None) -> list[IntervalBroadcast]:
    if broadcast_id is None:
        rows = await conn.fetch(queries.SELECT_INTERVAL_BROADCASTS_WITH_LIST)
    else:
        rows = await conn.fetch(queries.SELECT_INTERVAL_BROADCAST_WITH_LIST_BY_ID, broadcast_id)
    if not rows:
        return []
    messages = await conn.fetch(
        queries.SELECT_MESSAGES_FOR_LISTS_IN_ORDER,
        list({row["list_id"] for row in rows}),
    )
    by_list: dict[UUID, list] = {}
    for message in messages:
        by_list.setdefault(message["list_id"], []).append(message)
    loaded = []
    for row in rows:
        chosen = _choose_next_message(by_list.get(row["list_id"], []), row["last_message_id"])
        loaded.append(
            IntervalBroadcast(
                id=row["id"],
                list_id=row["list_id"],
                list_name=row["list_name"],
                interval_days=row["interval_days"],
                scheduled_at=row["scheduled_at"],
                next_message=None if chosen is None else _message_from_row(chosen),
            )
        )
    return loaded


async def create_interval_broadcast(
    pool: asyncpg.Pool,
    *,
    list_id: UUID,
    scheduled_at: datetime,
    interval_days: int,
) -> IntervalBroadcast | None:
    async with pool.acquire() as conn:
        exists = await conn.fetchval(queries.SELECT_BROADCAST_LIST_EXISTS, list_id)
        if exists is None:
            return None
        created_id = await conn.fetchval(
            queries.INSERT_INTERVAL_BROADCAST_RETURNING_ID,
            list_id,
            scheduled_at,
            interval_days,
        )
        loaded = await _load_interval_broadcasts(conn, created_id)
    return loaded[0]


def _interval_update_query(interval_days: int | None, scheduled_at: datetime | None):
    if interval_days is not None and scheduled_at is not None:
        return queries.UPDATE_INTERVAL_BROADCAST_DAYS_AND_SCHEDULED_AT, [interval_days, scheduled_at]
    if interval_days is not None:
        return queries.UPDATE_INTERVAL_BROADCAST_DAYS, [interval_days]
    if scheduled_at is not None:
        return queries.UPDATE_INTERVAL_BROADCAST_SCHEDULED_AT, [scheduled_at]
    return None, []


async def update_interval_broadcast(
    pool: asyncpg.Pool,
    broadcast_id: UUID,
    *,
    interval_days: int | None = None,
    scheduled_at: datetime | None = None,
) -> IntervalBroadcast | None:
    query, extra = _interval_update_query(interval_days, scheduled_at)
    async with pool.acquire() as conn:
        if query is not None:
            updated = await conn.fetchval(query, broadcast_id, *extra)
            if updated is None:
                return None
        elif await conn.fetchval(queries.SELECT_INTERVAL_BROADCAST_EXISTS, broadcast_id) is None:
            return None
        loaded = await _load_interval_broadcasts(conn, broadcast_id)
    return loaded[0]


async def delete_interval_broadcast(pool: asyncpg.Pool, broadcast_id: UUID) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute(queries.DELETE_INTERVAL_BROADCAST, broadcast_id)
    return result == "DELETE 1"


async def list_interval_broadcasts(pool: asyncpg.Pool) -> list[IntervalBroadcast]:
    async with pool.acquire() as conn:
        return await _load_interval_broadcasts(conn)


async def claim_due_interval_broadcasts(conn: asyncpg.Connection, claim_at: datetime) -> list:
    from db.store import DueFollowUpJob

    due = await conn.fetch(queries.LOCK_DUE_INTERVAL_BROADCASTS, claim_at)
    if not due:
        return []
    recipients = await conn.fetch(queries.SELECT_UNBLOCKED_TELEGRAM_IDENTITIES)
    messages = await conn.fetch(
        queries.SELECT_MESSAGES_FOR_LISTS_IN_ORDER,
        list({row["list_id"] for row in due}),
    )
    by_list: dict[UUID, list] = {}
    for message in messages:
        by_list.setdefault(message["list_id"], []).append(message)
    jobs = []
    for item in due:
        chosen = _choose_next_message(by_list.get(item["list_id"], []), item["last_message_id"])
        next_at = _next_interval_at(item["scheduled_at"], item["interval_days"], claim_at)
        if chosen is None:
            await conn.execute(
                queries.UPDATE_INTERVAL_BROADCAST_SCHEDULED_AT_ONLY,
                item["id"],
                next_at,
            )
            continue
        for recipient in recipients:
            job_id = await conn.fetchval(
                queries.INSERT_CLAIMED_BROADCAST_FOLLOW_UP_JOB,
                recipient["user_id"],
                claim_at,
            )
            jobs.append(
                DueFollowUpJob(
                    id=job_id,
                    kind="broadcast",
                    topic=None,
                    message_text=chosen["text"],
                    channel="telegram",
                    external_id=recipient["external_id"],
                    button_url=chosen["button_url"],
                    button_label=chosen["button_label"],
                )
            )
        await conn.execute(
            queries.UPDATE_INTERVAL_BROADCAST_LAST_MESSAGE_AND_SCHEDULED_AT,
            item["id"],
            chosen["id"],
            next_at,
        )
    return jobs
