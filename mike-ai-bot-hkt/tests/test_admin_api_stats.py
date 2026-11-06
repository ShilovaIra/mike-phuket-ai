from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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


@requires_db
@pytest.mark.asyncio
async def test_authenticated_stats_includes_topic_labels(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    await store.start_conversation("telegram", "1101", source="unknown")
    await store.record_topic_event("telegram", "1101", topic="beaches")
    await store.record_topic_event("telegram", "1101", topic="money_exchange")

    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        response = await client.get(
            "/api/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    by_slug = {row["slug"]: row for row in response.json()["topics_all_time"]}
    assert by_slug["beaches"]["label"] == "🏖 Пляжи"
    assert by_slug["beaches"]["unique_users"] == 1
    assert by_slug["beaches"]["taps"] == 1
    assert by_slug["money_exchange"]["label"] == "💰 Обмен"
    assert by_slug["money_exchange"]["unique_users"] == 1
    assert by_slug["money_exchange"]["taps"] == 1


def _last_seven_bangkok_dates() -> list[str]:
    today = datetime.now(ZoneInfo("Asia/Bangkok")).date()
    start = today - timedelta(days=6)
    return [(start + timedelta(days=offset)).isoformat() for offset in range(7)]


@requires_db
@pytest.mark.asyncio
async def test_stats_activity_is_seven_bangkok_days_ending_today(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    await store.start_conversation("telegram", "1201", source="unknown")
    await store.record_inbound("telegram", "1201")

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
    assert body["active_today"] == 1
    assert [point["date"] for point in body["activity"]] == _last_seven_bangkok_dates()
    assert body["activity"][-1]["active_users"] == body["active_today"]


@requires_db
@pytest.mark.asyncio
async def test_stats_activity_counts_a_user_on_the_day_they_were_active(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    await store.start_conversation("telegram", "1202", source="unknown")
    yesterday = datetime.now(ZoneInfo("Asia/Bangkok")) - timedelta(days=1)
    await store.record_inbound(
        "telegram",
        "1202",
        at=yesterday.replace(hour=12, minute=0, second=0, microsecond=0),
    )

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
    by_date = {point["date"]: point["active_users"] for point in body["activity"]}
    assert body["active_today"] == 0
    assert by_date[yesterday.date().isoformat()] == 1
    assert by_date[_last_seven_bangkok_dates()[-1]] == 0


@requires_db
@pytest.mark.asyncio
async def test_stats_deltas_measure_seven_day_growth_against_earlier_stock(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    earlier = ["1301", "1302", "1303"]
    for external_id in (*earlier, "1304"):
        await store.start_conversation("telegram", external_id, source="unknown")
        await store.create_lead("telegram", external_id, snapshot={"name": external_id})

    async with store._pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET created_at = now() - interval '10 days'
            WHERE id IN (
                SELECT user_id FROM identities WHERE external_id = ANY($1::text[])
            )
            """,
            earlier,
        )
        await conn.execute(
            """
            UPDATE leads
            SET created_at = now() - interval '10 days'
            WHERE conversation_id IN (
                SELECT c.id
                FROM conversations c
                JOIN identities i ON i.user_id = c.user_id
                WHERE i.external_id = ANY($1::text[])
            )
            """,
            earlier,
        )

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
    assert body["total_users"] == 4
    assert body["leads_all_time"] == 4
    assert body["deltas"]["total_users"] == 33
    assert body["deltas"]["leads_all_time"] == 33


@requires_db
@pytest.mark.asyncio
async def test_stats_deltas_are_zero_with_no_stock_and_100_when_rising_from_zero(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client)
        empty = await client.get("/api/stats", headers={"Authorization": f"Bearer {token}"})
        assert empty.status_code == 200
        assert empty.json()["deltas"]["total_users"] == 0
        assert empty.json()["deltas"]["leads_all_time"] == 0

        await store.start_conversation("telegram", "1401", source="unknown")
        await store.create_lead("telegram", "1401", snapshot={"name": "Ada"})
        risen = await client.get("/api/stats", headers={"Authorization": f"Bearer {token}"})

    assert risen.status_code == 200
    assert risen.json()["total_users"] == 1
    assert risen.json()["leads_all_time"] == 1
    assert risen.json()["deltas"]["total_users"] == 100
    assert risen.json()["deltas"]["leads_all_time"] == 100


@requires_db
@pytest.mark.asyncio
async def test_stats_period_deltas_compare_with_the_previous_window(store):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    prior = ["1501", "1502", "1503", "1504"]
    yesterday_ids = ["1505", "1506"]
    today_id = "1507"
    for external_id in (*prior, *yesterday_ids, today_id):
        await store.start_conversation("telegram", external_id, source="unknown")
        await store.create_lead("telegram", external_id, snapshot={"name": external_id})

    yesterday_noon = (datetime.now(ZoneInfo("Asia/Bangkok")) - timedelta(days=1)).replace(
        hour=12, minute=0, second=0, microsecond=0
    )
    async with store._pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET created_at = now() - interval '10 days'
            WHERE id IN (
                SELECT user_id FROM identities WHERE external_id = ANY($1::text[])
            )
            """,
            prior,
        )
        await conn.execute(
            """
            UPDATE leads
            SET created_at = now() - interval '10 days'
            WHERE conversation_id IN (
                SELECT c.id
                FROM conversations c
                JOIN identities i ON i.user_id = c.user_id
                WHERE i.external_id = ANY($1::text[])
            )
            """,
            prior,
        )
        await conn.execute(
            """
            UPDATE users
            SET created_at = $2
            WHERE id IN (
                SELECT user_id FROM identities WHERE external_id = ANY($1::text[])
            )
            """,
            yesterday_ids,
            yesterday_noon,
        )
        await conn.execute(
            """
            UPDATE leads
            SET created_at = $2
            WHERE conversation_id IN (
                SELECT c.id
                FROM conversations c
                JOIN identities i ON i.user_id = c.user_id
                WHERE i.external_id = ANY($1::text[])
            )
            """,
            yesterday_ids,
            yesterday_noon,
        )
    for external_id in yesterday_ids:
        await store.record_inbound("telegram", external_id, at=yesterday_noon)
    await store.record_inbound("telegram", today_id)

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
    assert body["new_users_today"] == 1
    assert body["active_today"] == 1
    assert body["new_users_7d"] == 3
    assert body["leads_7d"] == 3
    assert body["deltas"]["new_users_today"] == -50
    assert body["deltas"]["active_today"] == -50
    assert body["deltas"]["new_users_7d"] == -25
    assert body["deltas"]["leads_7d"] == -25
