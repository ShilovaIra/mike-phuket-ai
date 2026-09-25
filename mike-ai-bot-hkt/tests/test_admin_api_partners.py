from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from db.migrate import apply_schema
from tests.conftest import requires_db


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
async def test_create_partner_saves_empty_logo_path(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/partners",
            json={
                "name": "Test Dive",
                "type": "excursions",
                "referral_url": "https://example.com/dive",
                "blurb": "Дайвинг",
                "is_active": True,
                "sort_order": 5,
            },
        )
        assert created.status_code == 201
        body = created.json()
        assert body["name"] == "Test Dive"
        assert body["logo_path"] == ""

        listed = await client.get("/api/partners")
        names = [p["name"] for p in listed.json()]
        assert "Test Dive" in names


@requires_db
@pytest.mark.asyncio
async def test_deactivate_partner(store):
    partner = await store.create_partner(
        name="Active Co",
        type="excursions",
        referral_url="https://example.com/a",
        is_active=True,
    )
    async with authed_client(store) as client:
        updated = await client.patch(
            f"/api/partners/{partner.id}",
            json={
                "name": "Active Co",
                "type": "excursions",
                "referral_url": "https://example.com/a",
                "blurb": "",
                "is_active": False,
                "sort_order": 0,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["is_active"] is False
        assert updated.json()["logo_path"] == ""


@requires_db
@pytest.mark.asyncio
async def test_editing_seeded_partner_keeps_its_logo(store):
    async with store._pool.acquire() as conn:
        await apply_schema(conn)
    money_shop_id = "00000000-0000-4000-8000-000000000001"

    async with authed_client(store) as client:
        updated = await client.patch(
            f"/api/partners/{money_shop_id}",
            json={
                "name": "Money Shop",
                "type": "money_exchange",
                "referral_url": "https://moneyshopphuket.online/links/pp413",
                "blurb": "Новый текст",
                "is_active": True,
                "sort_order": 1,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["blurb"] == "Новый текст"
        assert updated.json()["logo_path"] == "media/partners/moneyshop.jpeg"

    partners = await store.list_active_partners("money_exchange")
    assert partners[0].logo_path == "media/partners/moneyshop.jpeg"
