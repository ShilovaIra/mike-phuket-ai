from __future__ import annotations

from uuid import uuid4

import asyncpg
import pytest

from buttons import ASK_MIKE_BUTTON, REAL_ESTATE_BUTTON, build_reply_keyboard_rows
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
            "esim",
        ]
        assert all(isinstance(t, PartnerType) for t in types)
        assert types[0].button_label == "💰 \nОбмен Рублей"
        assert types[1].button_label == "🛵 \nАренда транспорта"
        assert types[2].button_label == "🇹🇭 \nЭкскурсии"
        assert types[3].button_label == "📱 \neSIM"
        assert types[0].is_menu_visible is True
        assert types[1].is_menu_visible is True
        assert types[2].is_menu_visible is True
        assert types[3].is_menu_visible is True
        assert types[0].intro == "Вот партнёры для обмена рублей:"
        assert types[1].button_template == "Арендовать у {name}"
        assert types[2].caption_emoji == "🇹🇭"
    finally:
        await pool.close()


@requires_db
async def test_list_partner_types_works_without_follow_up_text_column():
    url = database_url()
    assert url is not None
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
    try:
        async with pool.acquire() as conn:
            await apply_schema(conn)
            await conn.execute(
                "ALTER TABLE partner_types DROP COLUMN IF EXISTS follow_up_text"
            )

        store = SessionStore(pool)
        types = await store.list_partner_types()
        assert {t.slug for t in types} >= {
            "money_exchange",
            "vehicle_rental",
            "excursions",
            "esim",
        }
        assert all(t.follow_up_text == "" for t in types)
    finally:
        async with pool.acquire() as conn:
            await apply_schema(conn)
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
async def test_schema_seed_includes_esim_partner_type():
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
        esim = await store.get_partner_type("esim")

        assert [t.slug for t in types] == [
            "money_exchange",
            "vehicle_rental",
            "excursions",
            "esim",
        ]
        assert esim is not None
        assert esim.is_menu_visible is True
        assert esim.sort_order == 40
        assert esim.button_label == "📱 \neSIM"
        assert esim.topic_label == "📱 eSIM"
        assert esim.intro == (
            "Чтобы в любой стране оставаться на связи, "
            "можно приобрести eSIM в этом боте:"
        )
        assert esim.fallback == (
            "Пока нет доступного бота для покупки eSIM. "
            "Напишите Майку — подскажу, что можно сделать."
        )
        assert esim.caption_emoji == "📱"
        assert esim.caption_cta == "⬇️ Купить eSIM ⬇️"
        assert esim.button_template == "Купить eSIM"
        assert esim.follow_up_text == ""
    finally:
        await pool.close()


@requires_db
async def test_seeded_partner_types_place_esim_beside_real_estate():
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
        rows = build_reply_keyboard_rows(await store.list_partner_types())

        assert ["📱 \neSIM", REAL_ESTATE_BUTTON] in rows
        assert rows[-1] == [ASK_MIKE_BUTTON]
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
async def test_schema_seed_includes_excursions_partner():
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
        partners = await store.list_active_partners("excursions")

        assert [p.name for p in partners] == ["Остров Сокровищ"]
        partner = partners[0]
        assert partner.referral_url == "https://tisland.link/excurs?ref=72s5z3yp3jb79r7"
        assert partner.logo_path == "media/partners/excursions.png"
        assert partner.blurb == (
            "С 2003 года в туризме. Авторские групповые и индивидуальные экскурсии."
        )
    finally:
        await pool.close()


@requires_db
async def test_schema_seed_includes_vehicle_rental_partner():
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
        partners = await store.list_active_partners("vehicle_rental")

        assert [p.name for p in partners] == ["Boomerang"]
        partner = partners[0]
        assert partner.referral_url == (
            "https://boomerang.rent/catalog/?utm_source=MikePhuketAIBot"
        )
        assert partner.logo_path == "media/partners/boomerang.jpeg"
        assert partner.blurb == (
            "Boomerang - надежный сервис аренды автомобилей и мотобайков "
            "на Пхукете. Доставка по всему острову."
        )
    finally:
        await pool.close()


@requires_db
async def test_schema_seed_includes_esim_partner():
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
        partners = await store.list_active_partners("esim")

        assert [p.name for p in partners] == ["Mike eSIM"]
        partner = partners[0]
        assert partner.referral_url == "https://t.me/Mike_esim_bot"
        assert partner.logo_path == "media/partners/esim.jpeg"
        assert partner.blurb in (None, "")
    finally:
        await pool.close()


@requires_db
async def test_schema_apply_keeps_operator_edits_to_seeded_partner(store):
    async with store._pool.acquire() as conn:
        await apply_schema(conn)
    money_shop, ex24 = await store.list_active_partners("money_exchange")

    await store.update_partner(
        money_shop.id,
        name="Money Shop Phuket",
        type="money_exchange",
        referral_url="https://moneyshopphuket.online/links/new",
        blurb="Обновлено оператором",
        sort_order=3,
    )
    await store.update_partner(
        ex24.id,
        name=ex24.name,
        type=ex24.type,
        referral_url=ex24.referral_url,
        blurb=ex24.blurb or "",
        is_active=False,
        sort_order=ex24.sort_order,
    )
    async with store._pool.acquire() as conn:
        await apply_schema(conn)

    partners = await store.list_active_partners("money_exchange")
    assert [p.name for p in partners] == ["Money Shop Phuket"]
    edited = partners[0]
    assert edited.referral_url == "https://moneyshopphuket.online/links/new"
    assert edited.blurb == "Обновлено оператором"
    assert edited.sort_order == 3
    assert edited.logo_path == "media/partners/moneyshop.jpeg"


@requires_db
async def test_schema_apply_restores_esim_partner_logo_path(store):
    async with store._pool.acquire() as conn:
        await conn.execute("UPDATE partners SET logo_path = '' WHERE type = 'esim'")
        await apply_schema(conn)

    partners = await store.list_active_partners("esim")
    assert [p.name for p in partners] == ["Mike eSIM"]
    assert partners[0].logo_path == "media/partners/esim.jpeg"


@requires_db
async def test_schema_apply_keeps_operator_uploaded_logos(store):
    uploaded = {
        "money_exchange": "partners/money/logo-aaa.png",
        "esim": "partners/esim/logo-bbb.jpg",
    }
    async with store._pool.acquire() as conn:
        await apply_schema(conn)
        for partner_type, key in uploaded.items():
            await conn.execute(
                "UPDATE partners SET logo_path = $2 WHERE type = $1",
                partner_type,
                key,
            )
        await apply_schema(conn)

    for partner_type, key in uploaded.items():
        partners = await store.list_active_partners(partner_type)
        assert {p.logo_path for p in partners} == {key}
