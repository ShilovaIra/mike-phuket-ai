from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import requires_db


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _admin_jwt_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")


@requires_db
@pytest.mark.asyncio
async def test_login_with_valid_admin_returns_access_token(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")

    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 10


@requires_db
@pytest.mark.asyncio
async def test_me_returns_email_for_operator_token(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        me = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )

    assert me.status_code == 200
    assert me.json() == {"email": "admin@example.com"}


@requires_db
@pytest.mark.asyncio
async def test_expired_operator_token_returns_session_expired(store):
    from admin_api.app import create_app
    from admin_api.tokens import create_access_token

    admin = await store.create_admin_user(email="admin@example.com", password="admin123")
    token = create_access_token(admin_id=admin.id, email=admin.email, ttl_hours=-1)
    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        me = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert me.status_code == 401
    assert me.json()["detail"] == "Сессия истекла"


@requires_db
@pytest.mark.asyncio
async def test_login_with_invalid_credentials_returns_401(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")

    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "wrong"},
        )

    assert response.status_code == 401
