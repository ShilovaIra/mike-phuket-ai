from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from db.migrate import apply_schema
from tests.conftest import requires_db

VIEWPOINT = {
    "slug": "viewpoint",
    "label": "Смотровая",
    "sort_order": 60,
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
async def test_list_place_categories_requires_admin(store):
    from admin_api.app import create_app

    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get("/api/place-categories")
    assert listed.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_create_place_category_appears_in_list(store):
    async with authed_client(store) as client:
        created = await client.post("/api/place-categories", json=VIEWPOINT)
        assert created.status_code == 201
        assert created.json()["slug"] == "viewpoint"
        assert created.json()["label"] == "Смотровая"
        assert created.json()["sort_order"] == 60

        listed = await client.get("/api/place-categories")
        assert listed.status_code == 200
        match = next(item for item in listed.json() if item["slug"] == "viewpoint")
        assert match["label"] == "Смотровая"
        assert match["sort_order"] == 60


@requires_db
@pytest.mark.asyncio
async def test_update_place_category_changes_label_and_keeps_slug(store):
    async with authed_client(store) as client:
        created = await client.post("/api/place-categories", json=VIEWPOINT)
        assert created.status_code == 201

        updated = await client.patch(
            "/api/place-categories/viewpoint",
            json={"slug": "renamed", "label": "Смотровая площадка", "sort_order": 15},
        )
        assert updated.status_code == 200
        assert updated.json()["slug"] == "viewpoint"
        assert updated.json()["label"] == "Смотровая площадка"
        assert updated.json()["sort_order"] == 15

        listed = await client.get("/api/place-categories")
        slugs = {item["slug"] for item in listed.json()}
        assert "renamed" not in slugs
        match = next(item for item in listed.json() if item["slug"] == "viewpoint")
        assert match["label"] == "Смотровая площадка"
        assert match["sort_order"] == 15


@requires_db
@pytest.mark.asyncio
async def test_delete_empty_place_category_removes_it(store):
    async with authed_client(store) as client:
        created = await client.post("/api/place-categories", json=VIEWPOINT)
        assert created.status_code == 201

        deleted = await client.delete("/api/place-categories/viewpoint")
        assert deleted.status_code == 204

        listed = await client.get("/api/place-categories")
        slugs = {item["slug"] for item in listed.json()}
        assert "viewpoint" not in slugs


@requires_db
@pytest.mark.asyncio
async def test_delete_place_category_with_a_place_keeps_it(store):
    async with authed_client(store) as client:
        created = await client.post("/api/place-categories", json=VIEWPOINT)
        assert created.status_code == 201
        await store.create_place(
            name="Мыс Промтеп",
            category_id=UUID(created.json()["id"]),
            google_place_id="ChIJ_promthep",
            latitude=7.76,
            longitude=98.30,
        )

        deleted = await client.delete("/api/place-categories/viewpoint")
        assert deleted.status_code == 409

        listed = await client.get("/api/place-categories")
        slugs = {item["slug"] for item in listed.json()}
        assert "viewpoint" in slugs


@requires_db
@pytest.mark.asyncio
async def test_schema_apply_keeps_deleted_builtin_place_category_deleted(store):
    async with authed_client(store) as client:
        deleted = await client.delete("/api/place-categories/cafe")
        assert deleted.status_code == 204

        async with store._pool.acquire() as conn:
            await apply_schema(conn)

        listed = await client.get("/api/place-categories")
        slugs = {item["slug"] for item in listed.json()}
        assert "cafe" not in slugs


@requires_db
@pytest.mark.asyncio
async def test_schema_apply_keeps_edited_place_category_label(store):
    async with authed_client(store) as client:
        updated = await client.patch(
            "/api/place-categories/beach",
            json={"label": "Пляжи", "sort_order": 45},
        )
        assert updated.status_code == 200

        async with store._pool.acquire() as conn:
            await apply_schema(conn)

        listed = await client.get("/api/place-categories")
        match = next(item for item in listed.json() if item["slug"] == "beach")
        assert match["label"] == "Пляжи"
        assert match["sort_order"] == 45
