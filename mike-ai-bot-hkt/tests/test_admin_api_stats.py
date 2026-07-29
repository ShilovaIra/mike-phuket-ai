from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import requires_db


@pytest.fixture(autouse=True)
def _admin_jwt_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")


async def _login(client: AsyncClient) -> str:
    response = await client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@requires_db
@pytest.mark.asyncio
async def test_unauthenticated_stats_returns_401(store):
    from admin_api.app import create_app

    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/stats")

    assert response.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_authenticated_stats_includes_kpis_and_first_source(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    await store.start_conversation("telegram", "1001", source="instagram")
    await store.start_conversation("telegram", "1002", source="unknown")

    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        response = await client.get(
            "/api/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_users"] == 2
    assert "users_by_first_source" in body
    assert body["users_by_first_source"]["instagram"] == 1
    assert body["users_by_first_source"]["unknown"] == 1
    assert "topics_all_time" in body
    assert "leads_all_time" in body
