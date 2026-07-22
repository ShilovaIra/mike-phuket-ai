from __future__ import annotations

from uuid import uuid4

import asyncpg
import pytest

from db.migrate import apply_schema
from db.store import SessionStore
from partners import PartnerType
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
async def test_list_partner_types_returns_seeded_in_sort_order():
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    try:
        async with pool.acquire() as conn:
            await apply_schema(conn)
            await conn.execute(
                "TRUNCATE TABLE partners, partner_types RESTART IDENTITY CASCADE"
            )
            await apply_schema(conn)

        store = SessionStore(pool)
        types = await store.list_partner_types()

        assert [t.slug for t in types] == [
            "money_exchange",
            "vehicle_rental",
            "excursions",
        ]
        assert all(isinstance(t, PartnerType) for t in types)
        assert types[0].button_label == "💰 \nОбмен Рублей"
        assert types[1].button_label == "🛵 \nАренда транспорта"
        assert types[2].button_label == "🇹🇭 \nЭкскурсии"
        assert types[0].intro == "Вот партнёры для обмена рублей:"
        assert types[1].button_template == "Арендовать у {name}"
        assert types[2].caption_emoji == "🇹🇭"
    finally:
        await pool.close()


@requires_db
async def test_get_partner_type_returns_copy_for_slug():
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    try:
        async with pool.acquire() as conn:
            await apply_schema(conn)

        store = SessionStore(pool)
        partner_type = await store.get_partner_type("excursions")

        assert partner_type is not None
        assert partner_type.slug == "excursions"
        assert partner_type.fallback.startswith("Пока нет доступных партнёров по экскурсиям")
        assert await store.get_partner_type("missing") is None
    finally:
        await pool.close()


@requires_db
async def test_insert_partner_rejects_unknown_type(store):
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        await _insert_partner(store, name="Orphan", partner_type="not_a_real_type")


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
    await _insert_partner(store, name="Bike", partner_type="vehicle_rental", is_active=True)

    partners = await store.list_active_partners("money_exchange")

    assert [p.name for p in partners] == ["Active FX"]


@requires_db
async def test_schema_seed_includes_money_exchange_partners():
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    try:
        async with pool.acquire() as conn:
            await apply_schema(conn)
            await conn.execute(
                "TRUNCATE TABLE partners, partner_types RESTART IDENTITY CASCADE"
            )
            await apply_schema(conn)

        store = SessionStore(pool)
        partners = await store.list_active_partners("money_exchange")

        assert [p.name for p in partners] == ["Money Shop", "Ex24.pro"]
        money, ex24 = partners
        assert money.referral_url == "https://moneyshopphuket.online/links/pp413"
        assert money.logo_path == "media/partners/moneyshop.jpeg"
        assert money.blurb == "Money Shop - Сеть обменных офисов на Пхукете!"
        assert ex24.referral_url == "https://ex24qr.com/epihelgnld"
        assert ex24.logo_path == "media/partners/ex24pro.png"
        assert "Лицензированный обмен валюты" in (ex24.blurb or "")
    finally:
        await pool.close()


@requires_db
async def test_schema_seed_upsert_replaces_test_exchange_placeholder():
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    try:
        async with pool.acquire() as conn:
            await apply_schema(conn)
            await conn.execute(
                "TRUNCATE TABLE partners, partner_types RESTART IDENTITY CASCADE"
            )
            await apply_schema(conn)
            await conn.execute(
                """
                INSERT INTO partners (id, name, type, referral_url, blurb, is_active, sort_order)
                VALUES (
                    '00000000-0000-4000-8000-000000000001',
                    'Test Exchange',
                    'money_exchange',
                    'https://t.me/example_exchange_bot?start=test_ref',
                    'Тестовый партнёр',
                    true,
                    1
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    referral_url = EXCLUDED.referral_url,
                    blurb = EXCLUDED.blurb
                """
            )
            await apply_schema(conn)

        store = SessionStore(pool)
        partners = await store.list_active_partners("money_exchange")
        names = [p.name for p in partners]
        assert "Test Exchange" not in names
        assert names[0] == "Money Shop"
    finally:
        await pool.close()
