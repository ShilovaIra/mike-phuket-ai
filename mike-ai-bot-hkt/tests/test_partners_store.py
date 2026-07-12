from __future__ import annotations

from uuid import uuid4

import asyncpg

from db.migrate import apply_schema
from db.store import SessionStore
from tests.conftest import database_url, requires_db


async def _insert_partner(
    store,
    *,
    name: str,
    partner_type: str = "money_exchange",
    referral_url: str = "https://t.me/example_exchange_bot?start=test_ref",
    blurb: str | None = None,
    is_active: bool = True,
    sort_order: int = 0,
):
    async with store._pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO partners (id, name, type, referral_url, blurb, is_active, sort_order)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            uuid4(),
            name,
            partner_type,
            referral_url,
            blurb,
            is_active,
            sort_order,
        )


@requires_db
async def test_list_active_partners_returns_type_in_sort_order(store):
    await _insert_partner(store, name="Second", sort_order=2)
    await _insert_partner(store, name="First", sort_order=1)

    partners = await store.list_active_partners("money_exchange")

    assert [p.name for p in partners] == ["First", "Second"]


@requires_db
async def test_list_active_partners_excludes_inactive_and_other_types(store):
    await _insert_partner(store, name="Active FX", partner_type="money_exchange", is_active=True)
    await _insert_partner(store, name="Off FX", partner_type="money_exchange", is_active=False)
    await _insert_partner(store, name="Cafe", partner_type="cafe", is_active=True)

    partners = await store.list_active_partners("money_exchange")

    assert [p.name for p in partners] == ["Active FX"]


@requires_db
async def test_schema_seed_includes_placeholder_money_exchange_partner():
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    try:
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE TABLE partners RESTART IDENTITY CASCADE")
            await apply_schema(conn)

        store = SessionStore(pool)
        partners = await store.list_active_partners("money_exchange")

        assert len(partners) >= 1
        seed = next(p for p in partners if p.name == "Test Exchange")
        assert seed.type == "money_exchange"
        assert seed.referral_url == "https://t.me/example_exchange_bot?start=test_ref"
        assert seed.blurb == "Тестовый партнёр"
    finally:
        await pool.close()
