from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from db.migrate import apply_schema
from tests.conftest import requires_db

DIVING = {
    "slug": "diving",
    "is_menu_visible": True,
    "sort_order": 40,
    "button_label": "Дайвинг",
    "topic_label": "Дайвинг",
    "intro": "Партнёры по дайвингу:",
    "fallback": "Пока нет партнёров.",
    "caption_emoji": "🤿",
    "caption_cta": "Записаться",
    "button_template": "Записаться у {name}",
}


@pytest.fixture(autouse=True)
def _admin_jwt_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")


@asynccontextmanager
async def authed_client(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        yield client


@requires_db
@pytest.mark.asyncio
async def test_list_partner_types_includes_seeded_slugs(store):
    async with authed_client(store) as client:
        listed = await client.get("/api/partner-types")
    assert listed.status_code == 200
    slugs = {item["slug"] for item in listed.json()}
    assert slugs >= {"money_exchange", "vehicle_rental", "excursions", "esim"}


@requires_db
@pytest.mark.asyncio
async def test_list_partner_types_trailing_slash_returns_same_payload(store):
    async with authed_client(store) as client:
        listed = await client.get("/api/partner-types/")
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)
    slugs = {item["slug"] for item in listed.json()}
    assert slugs >= {"money_exchange", "vehicle_rental", "excursions", "esim"}


@requires_db
@pytest.mark.asyncio
async def test_list_partner_types_requires_admin(store):
    from admin_api.app import create_app

    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get("/api/partner-types")
    assert listed.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_create_partner_type_appears_in_list(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/partner-types",
            json={**DIVING, "choice_phrase": "дайвинг"},
        )
        assert created.status_code == 201
        listed = await client.get("/api/partner-types")
        assert listed.status_code == 200
        slugs = [item["slug"] for item in listed.json()]
        assert "diving" in slugs


@requires_db
@pytest.mark.asyncio
async def test_rename_partner_type_slug_cascades_to_partners(store):
    await store.create_partner(
        name="Money Shop",
        type="money_exchange",
        referral_url="https://example.com/money",
    )
    await store.create_partner(
        name="Ex24.pro",
        type="money_exchange",
        referral_url="https://example.com/ex24",
    )
    await store.create_partner(
        name="Остров Сокровищ",
        type="excursions",
        referral_url="https://example.com/excurs",
    )

    async with authed_client(store) as client:
        rename = await client.patch(
            "/api/partner-types/money_exchange",
            json={
                "slug": "fx_exchange",
                "is_menu_visible": True,
                "sort_order": 10,
                "button_label": "Обмен",
                "topic_label": "Обмен",
                "intro": "intro",
                "fallback": "fallback",
                "caption_emoji": "💰",
                "caption_cta": "cta",
                "button_template": "кнопка {name}",
                "choice_phrase": "обмен рублей",
            },
        )
        assert rename.status_code == 200
        assert rename.json()["slug"] == "fx_exchange"

        partners = await client.get("/api/partners")
        assert partners.status_code == 200
        types = {p["name"]: p["type"] for p in partners.json()}
        assert types["Money Shop"] == "fx_exchange"
        assert types["Ex24.pro"] == "fx_exchange"
        assert types["Остров Сокровищ"] == "excursions"


@requires_db
@pytest.mark.asyncio
async def test_list_partner_types_includes_seeded_choice_phrases(store):
    async with authed_client(store) as client:
        listed = await client.get("/api/partner-types")

    assert listed.status_code == 200
    phrases = {item["slug"]: item["choice_phrase"] for item in listed.json()}
    assert phrases["money_exchange"] == "обмен рублей"
    assert phrases["vehicle_rental"] == "аренду транспорта"
    assert phrases["excursions"] == "экскурсии"
    assert phrases["esim"] == "eSIM"


@requires_db
@pytest.mark.asyncio
async def test_create_partner_type_requires_choice_phrase(store):
    async with authed_client(store) as client:
        missing = await client.post("/api/partner-types", json=DIVING)
        blank = await client.post(
            "/api/partner-types",
            json={**DIVING, "choice_phrase": "   "},
        )
        created = await client.post(
            "/api/partner-types",
            json={**DIVING, "slug": "snorkeling", "choice_phrase": "снорклинг"},
        )
        listed = await client.get("/api/partner-types")

    assert missing.status_code == 422
    assert blank.status_code == 422
    assert created.status_code == 201
    assert created.json()["choice_phrase"] == "снорклинг"
    phrases = {item["slug"]: item["choice_phrase"] for item in listed.json()}
    assert phrases["snorkeling"] == "снорклинг"


@requires_db
@pytest.mark.asyncio
async def test_schema_apply_keeps_an_edited_choice_phrase(store):
    async with authed_client(store) as client:
        updated = await client.patch(
            "/api/partner-types/money_exchange",
            json={
                "slug": "money_exchange",
                "is_menu_visible": True,
                "sort_order": 10,
                "button_label": "Обмен",
                "topic_label": "Обмен",
                "intro": "intro",
                "fallback": "fallback",
                "caption_emoji": "💰",
                "caption_cta": "cta",
                "button_template": "кнопка {name}",
                "choice_phrase": "обмен валюты",
            },
        )
        assert updated.status_code == 200
        async with store.pool.acquire() as conn:
            await apply_schema(conn)
        listed = await client.get("/api/partner-types")

    phrases = {item["slug"]: item["choice_phrase"] for item in listed.json()}
    assert phrases["money_exchange"] == "обмен валюты"
    assert phrases["vehicle_rental"] == "аренду транспорта"
