from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

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
async def test_operator_adds_a_partner_and_sees_name_and_referral_link(store):
    async with authed_client(store) as client:
        created_partner = await client.post(
            "/api/partners",
            json={
                "name": "Reef Divers",
                "type": "excursions",
                "referral_url": "https://example.com/reef",
                "blurb": "Дайвинг у кораллов",
                "is_active": True,
                "sort_order": 1,
            },
        )
        assert created_partner.status_code == 201
        partner_id = created_partner.json()["id"]

        added = await client.post("/api/knowledge-base", json={"partner_id": partner_id})
        assert added.status_code == 201

        listed = await client.get("/api/knowledge-base")
        assert listed.status_code == 200
        match = next(row for row in listed.json() if row["partner_id"] == partner_id)
        assert match["name"] == "Reef Divers"
        assert match["referral_url"] == "https://example.com/reef"


@requires_db
@pytest.mark.asyncio
async def test_operator_removes_a_knowledge_base_row(store):
    async with authed_client(store) as client:
        created_partner = await client.post(
            "/api/partners",
            json={
                "name": "Reef Divers",
                "type": "excursions",
                "referral_url": "https://example.com/reef",
                "blurb": "Дайвинг у кораллов",
                "is_active": True,
                "sort_order": 1,
            },
        )
        partner_id = created_partner.json()["id"]
        added = await client.post("/api/knowledge-base", json={"partner_id": partner_id})
        row_id = added.json()["id"]

        deleted = await client.delete(f"/api/knowledge-base/{row_id}")
        assert deleted.status_code == 204

        listed = await client.get("/api/knowledge-base")
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_adding_the_same_partner_again_is_rejected(store):
    async with authed_client(store) as client:
        created_partner = await client.post(
            "/api/partners",
            json={
                "name": "Reef Divers",
                "type": "excursions",
                "referral_url": "https://example.com/reef",
                "blurb": "",
                "is_active": True,
                "sort_order": 1,
            },
        )
        partner_id = created_partner.json()["id"]
        first = await client.post("/api/knowledge-base", json={"partner_id": partner_id})
        assert first.status_code == 201

        second = await client.post("/api/knowledge-base", json={"partner_id": partner_id})
        assert second.status_code == 409


REEF_MAPS = (
    "https://www.google.com/maps/place/Reef/"
    "@7.7600,98.3000,17z/data=!4m6!3m5!1s0x0!8m2!3d7.7622!4d98.3055"
)


@requires_db
@pytest.mark.asyncio
async def test_adding_a_place_tied_to_a_listed_partner_is_rejected(store):
    async with authed_client(store) as client:
        created_partner = await client.post(
            "/api/partners",
            json={
                "name": "Reef Divers",
                "type": "excursions",
                "referral_url": "https://example.com/reef",
                "blurb": "",
                "is_active": True,
                "sort_order": 1,
            },
        )
        partner_id = created_partner.json()["id"]
        created_place = await client.post(
            "/api/places",
            json={
                "name": "Reef Divers Pier",
                "category": "shop",
                "maps_url": REEF_MAPS,
                "partner_id": partner_id,
            },
        )
        assert created_place.status_code == 201
        place_id = created_place.json()["id"]
        added_partner = await client.post(
            "/api/knowledge-base", json={"partner_id": partner_id}
        )
        assert added_partner.status_code == 201

        added_place = await client.post("/api/knowledge-base", json={"place_id": place_id})
        assert added_place.status_code == 409


@requires_db
@pytest.mark.asyncio
async def test_adding_a_partner_tied_to_a_listed_place_is_rejected(store):
    async with authed_client(store) as client:
        created_partner = await client.post(
            "/api/partners",
            json={
                "name": "Reef Divers",
                "type": "excursions",
                "referral_url": "https://example.com/reef",
                "blurb": "",
                "is_active": True,
                "sort_order": 1,
            },
        )
        partner_id = created_partner.json()["id"]
        created_place = await client.post(
            "/api/places",
            json={
                "name": "Reef Divers Pier",
                "category": "shop",
                "maps_url": REEF_MAPS,
                "partner_id": partner_id,
            },
        )
        place_id = created_place.json()["id"]
        added_place = await client.post("/api/knowledge-base", json={"place_id": place_id})
        assert added_place.status_code == 201

        added_partner = await client.post(
            "/api/knowledge-base", json={"partner_id": partner_id}
        )
        assert added_partner.status_code == 409


@requires_db
@pytest.mark.asyncio
async def test_adding_a_place_shows_map_link_and_listed_partner_referral(store):
    async with authed_client(store) as client:
        created_partner = await client.post(
            "/api/partners",
            json={
                "name": "Reef Divers",
                "type": "excursions",
                "referral_url": "https://example.com/reef",
                "blurb": "Дайвинг у кораллов",
                "is_active": True,
                "sort_order": 1,
            },
        )
        partner_id = created_partner.json()["id"]
        created_place = await client.post(
            "/api/places",
            json={
                "name": "Reef Divers Pier",
                "category": "shop",
                "maps_url": REEF_MAPS,
                "partner_id": partner_id,
            },
        )
        place_id = created_place.json()["id"]

        added = await client.post("/api/knowledge-base", json={"place_id": place_id})
        assert added.status_code == 201

        listed = await client.get("/api/knowledge-base")
        match = next(row for row in listed.json() if row["place_id"] == place_id)
        assert match["name"] == "Reef Divers Pier"
        assert match["maps_url"] == REEF_MAPS
        assert match["referral_url"] == "https://example.com/reef"
