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
    interval_broadcasts,
    broadcast_list_messages,
    broadcast_lists,
    broadcasts,
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
    knowledge_base,
    partners,
    admin_users
RESTART IDENTITY CASCADE
"""

RESET_PARTNER_TYPES_SQL = """
DELETE FROM partner_types
WHERE slug NOT IN ('money_exchange', 'vehicle_rental', 'excursions', 'esim')
"""

RESET_PLACE_CATEGORIES_SQL = """
DELETE FROM place_categories
WHERE slug NOT IN ('cafe', 'restaurant', 'bar', 'beach', 'shop')
"""

RESEED_CHOICE_PHRASES_SQL = """
UPDATE partner_types
SET choice_phrase = CASE slug
    WHEN 'money_exchange' THEN 'обмен рублей'
    WHEN 'vehicle_rental' THEN 'аренду транспорта'
    WHEN 'excursions' THEN 'экскурсии'
    WHEN 'esim' THEN 'eSIM'
    ELSE choice_phrase
END
WHERE slug IN ('money_exchange', 'vehicle_rental', 'excursions', 'esim')
"""

RESEED_PLACE_CATEGORIES_SQL = """
INSERT INTO place_categories (slug, label, sort_order)
VALUES
    ('cafe', 'Кафе', 10),
    ('restaurant', 'Ресторан', 20),
    ('bar', 'Бар', 30),
    ('beach', 'Пляж', 40),
    ('shop', 'Магазин', 50)
ON CONFLICT (slug) DO UPDATE SET
    label = EXCLUDED.label,
    sort_order = EXCLUDED.sort_order
"""


@pytest_asyncio.fixture
async def store() -> SessionStore:
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            DO $$
            BEGIN
                IF to_regclass('public.knowledge_base') IS NOT NULL THEN
                    DELETE FROM knowledge_base;
                END IF;
                IF to_regclass('public.places') IS NOT NULL THEN
                    DELETE FROM place_assets;
                    DELETE FROM places;
                END IF;
            END $$;
            """
        )
        await apply_schema(conn)
        await conn.execute(TRUNCATE_SQL)
        await conn.execute(RESET_PARTNER_TYPES_SQL)
        await conn.execute(RESET_PLACE_CATEGORIES_SQL)
        await apply_schema(conn)
        await conn.execute(TRUNCATE_SQL)
        await conn.execute(RESET_PLACE_CATEGORIES_SQL)
        await conn.execute(RESEED_PLACE_CATEGORIES_SQL)
        await conn.execute(RESEED_CHOICE_PHRASES_SQL)

    session_store = SessionStore(pool)
    yield session_store
    await session_store.close()


S3_ENDPOINT = "https://sgp1.digitaloceanspaces.com"
S3_BUCKET = "mike-phuket-test"
S3_ENV = {
    "S3_ENDPOINT_URL": S3_ENDPOINT,
    "S3_REGION": "sgp1",
    "S3_BUCKET": S3_BUCKET,
    "S3_ACCESS_KEY_ID": "test-key",
    "S3_SECRET_ACCESS_KEY": "test-secret",
    "S3_PUBLIC_BASE_URL": "https://cdn-test.mikephuketai.com",
}


@pytest.fixture
def s3(monkeypatch):
    """In-memory S3 (moto) with an empty test bucket; yields a raw boto3 client."""
    import boto3
    from moto import mock_aws

    monkeypatch.setenv("MOTO_S3_CUSTOM_ENDPOINTS", S3_ENDPOINT)
    with mock_aws():
        client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            region_name="us-east-1",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )
        client.create_bucket(Bucket=S3_BUCKET)
        yield client


@pytest.fixture
def asset_storage(s3):
    from storage import AssetStorage

    return AssetStorage.from_env(S3_ENV)
