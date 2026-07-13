from __future__ import annotations

from pathlib import Path

import asyncpg

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


async def apply_schema(conn: asyncpg.Connection) -> None:
    await conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


async def apply_schema_pool(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await apply_schema(conn)
