from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncpg
import pytest
import pytest_asyncio

from db.migrate import apply_schema
from db.store import SessionStore

pytest_plugins = ("pytest_asyncio",)


def database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


requires_db = pytest.mark.skipif(
    not database_url(),
    reason="Set TEST_DATABASE_URL or DATABASE_URL to run database tests",
)


TRUNCATE_SQL = """
TRUNCATE TABLE
    follow_up_jobs,
    webhook_events,
    leads,
    topic_events,
    messages,
    conversations,
    identities,
    users,
    partner_referral_clicks,
    partner_views,
    partner_access,
    partner_users,
    partners,
    admin_users
RESTART IDENTITY CASCADE
"""

RESET_PARTNER_TYPES_SQL = """
DELETE FROM partner_types
WHERE slug NOT IN ('money_exchange', 'vehicle_rental', 'excursions', 'esim')
"""


@pytest_asyncio.fixture
async def store() -> SessionStore:
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await apply_schema(conn)
        await conn.execute(TRUNCATE_SQL)
        await conn.execute(RESET_PARTNER_TYPES_SQL)
        await apply_schema(conn)
        await conn.execute(TRUNCATE_SQL)

    session_store = SessionStore(pool)
    yield session_store
    await session_store.close()
