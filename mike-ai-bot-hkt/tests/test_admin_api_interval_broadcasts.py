from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import requires_db
from tests.test_admin_api_broadcasts import PROMTEP_MAPS, authed_client


@pytest.fixture(autouse=True)
def _admin_jwt_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")


@requires_db
@pytest.mark.asyncio
async def test_admin_can_create_a_message_list_and_see_messages_in_order(store):
    async with authed_client(store) as client:
        created = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        assert created.status_code == 201
        body = created.json()
        assert body["name"] == "Прогрев"
        assert body["messages"] == []
        list_id = body["id"]

        first = await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Первое"},
        )
        second = await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Второе"},
        )
        assert first.status_code == 201
        assert second.status_code == 201

        listed = await client.get("/api/broadcast-lists")
        assert listed.status_code == 200
        match = next(item for item in listed.json() if item["id"] == list_id)
        assert [message["text"] for message in match["messages"]] == ["Первое", "Второе"]


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_add_a_blank_message_to_a_list(store):
    async with authed_client(store) as client:
        created = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created.json()["id"]

        added = await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "   "},
        )
        assert added.status_code == 400

        listed = await client.get("/api/broadcast-lists")
        match = next(item for item in listed.json() if item["id"] == list_id)
        assert match["messages"] == []


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_add_a_message_whose_maps_link_has_no_pin(store):
    async with authed_client(store) as client:
        created = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created.json()["id"]

        added = await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={
                "text": "Смотри место",
                "button_url": "https://www.google.com/maps/search/?api=1&query=Phuket",
            },
        )
        assert added.status_code == 400

        listed = await client.get("/api/broadcast-lists")
        match = next(item for item in listed.json() if item["id"] == list_id)
        assert match["messages"] == []


@requires_db
@pytest.mark.asyncio
async def test_list_message_without_a_link_has_no_button(store):
    async with authed_client(store) as client:
        created = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created.json()["id"]

        added = await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Первое"},
        )
        assert added.status_code == 201
        assert added.json()["button_url"] is None
        assert added.json()["button_label"] is None

        listed = await client.get("/api/broadcast-lists")
        match = next(item for item in listed.json() if item["id"] == list_id)
        assert match["messages"][0]["button_url"] is None
        assert match["messages"][0]["button_label"] is None


@requires_db
@pytest.mark.asyncio
async def test_empty_button_label_with_a_valid_link_uses_the_route_label(store):
    async with authed_client(store) as client:
        created = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created.json()["id"]

        added = await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Смотри место", "button_url": PROMTEP_MAPS, "button_label": "  "},
        )
        assert added.status_code == 201
        assert added.json()["button_url"] == PROMTEP_MAPS
        assert added.json()["button_label"] == "Проложить маршрут"

        listed = await client.get("/api/broadcast-lists")
        match = next(item for item in listed.json() if item["id"] == list_id)
        assert match["messages"][0]["button_url"] == PROMTEP_MAPS
        assert match["messages"][0]["button_label"] == "Проложить маршрут"


@requires_db
@pytest.mark.asyncio
async def test_moving_a_message_up_changes_the_listed_order(store):
    async with authed_client(store) as client:
        created = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created.json()["id"]
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Первое"},
        )
        second = await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Второе"},
        )

        moved = await client.post(
            f"/api/broadcast-lists/{list_id}/messages/{second.json()['id']}/move",
            json={"direction": "up"},
        )
        assert moved.status_code == 200

        listed = await client.get("/api/broadcast-lists")
        match = next(item for item in listed.json() if item["id"] == list_id)
        assert [message["text"] for message in match["messages"]] == ["Второе", "Первое"]


@requires_db
@pytest.mark.asyncio
async def test_admin_can_schedule_an_interval_broadcast_and_see_the_first_message(store):
    scheduled_at = "2026-12-01T10:00:00+07:00"
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created_list.json()["id"]
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Первое"},
        )
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Второе"},
        )

        created = await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": list_id,
                "scheduled_at": scheduled_at,
                "interval_days": 3,
            },
        )
        assert created.status_code == 201
        body = created.json()
        assert body["list_name"] == "Прогрев"
        assert body["interval_days"] == 3
        assert body["scheduled_at"] == scheduled_at
        assert body["next_message"]["text"] == "Первое"

        listed = await client.get("/api/interval-broadcasts")
        match = next(item for item in listed.json() if item["id"] == body["id"])
        assert match["list_name"] == "Прогрев"
        assert match["interval_days"] == 3
        assert match["scheduled_at"] == scheduled_at
        assert match["next_message"]["text"] == "Первое"


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_schedule_an_interval_broadcast_in_the_past(store):
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        created = await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": created_list.json()["id"],
                "scheduled_at": "2020-01-01T10:00:00+07:00",
                "interval_days": 3,
            },
        )
        assert created.status_code == 400

        listed = await client.get("/api/interval-broadcasts")
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_schedule_an_interval_below_one_day(store):
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        created = await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": created_list.json()["id"],
                "scheduled_at": "2026-12-01T10:00:00+07:00",
                "interval_days": 0,
            },
        )
        assert created.status_code == 400

        listed = await client.get("/api/interval-broadcasts")
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_changing_the_interval_leaves_the_next_send_time(store):
    scheduled_at = "2026-12-01T10:00:00+07:00"
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        created = await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": created_list.json()["id"],
                "scheduled_at": scheduled_at,
                "interval_days": 3,
            },
        )
        broadcast_id = created.json()["id"]

        updated = await client.patch(
            f"/api/interval-broadcasts/{broadcast_id}",
            json={"interval_days": 7},
        )
        assert updated.status_code == 200
        assert updated.json()["interval_days"] == 7
        assert updated.json()["scheduled_at"] == scheduled_at

        listed = await client.get("/api/interval-broadcasts")
        match = next(item for item in listed.json() if item["id"] == broadcast_id)
        assert match["interval_days"] == 7
        assert match["scheduled_at"] == scheduled_at


@requires_db
@pytest.mark.asyncio
async def test_changing_the_next_send_time_updates_it(store):
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        created = await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": created_list.json()["id"],
                "scheduled_at": "2026-12-01T10:00:00+07:00",
                "interval_days": 3,
            },
        )
        broadcast_id = created.json()["id"]
        moved_to = "2026-12-05T15:00:00+07:00"

        updated = await client.patch(
            f"/api/interval-broadcasts/{broadcast_id}",
            json={"scheduled_at": moved_to},
        )
        assert updated.status_code == 200
        assert updated.json()["scheduled_at"] == moved_to
        assert updated.json()["interval_days"] == 3


@requires_db
@pytest.mark.asyncio
async def test_due_interval_broadcast_sends_the_first_message_then_advances(store):
    opened = datetime(2026, 8, 5, 3, 0, tzinfo=timezone.utc)
    await store.start_conversation("telegram", "early", source="unknown")
    await store.start_conversation("tma", "mini-only", source="tma")
    await store.start_conversation("telegram", "blocked", source="unknown")
    await store.schedule_partner_follow_up("telegram", "blocked", "money_exchange", at=opened)
    blocked_jobs = await store.claim_due_jobs(now=opened + timedelta(hours=24))
    await store.mark_job_failed(blocked_jobs[0].id, permanent=True)

    scheduled_at = datetime(2026, 12, 1, 10, 0, tzinfo=timezone(timedelta(hours=7)))
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created_list.json()["id"]
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Первое"},
        )
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Второе"},
        )
        created = await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": list_id,
                "scheduled_at": scheduled_at.isoformat(),
                "interval_days": 3,
            },
        )
        broadcast_id = created.json()["id"]
        await store.start_conversation("telegram", "late", source="unknown")

        due = await store.claim_due_jobs(now=scheduled_at)
        sent = [job for job in due if job.kind == "broadcast" and job.message_text == "Первое"]
        assert {job.external_id for job in sent} == {"early", "late"}
        assert {job.channel for job in sent} == {"telegram"}

        listed = await client.get("/api/interval-broadcasts")
        match = next(item for item in listed.json() if item["id"] == broadcast_id)
        assert match["next_message"]["text"] == "Второе"
        assert match["scheduled_at"] == "2026-12-04T10:00:00+07:00"


@requires_db
@pytest.mark.asyncio
async def test_after_the_last_message_the_schedule_returns_to_the_first(store):
    scheduled_at = datetime(2026, 12, 1, 10, 0, tzinfo=timezone(timedelta(hours=7)))
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created_list.json()["id"]
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Первое"},
        )
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Второе"},
        )
        created = await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": list_id,
                "scheduled_at": scheduled_at.isoformat(),
                "interval_days": 3,
            },
        )
        broadcast_id = created.json()["id"]
        await store.start_conversation("telegram", "early", source="unknown")
        await store.claim_due_jobs(now=scheduled_at)
        await store.claim_due_jobs(now=scheduled_at + timedelta(days=3))

        listed = await client.get("/api/interval-broadcasts")
        match = next(item for item in listed.json() if item["id"] == broadcast_id)
        assert match["next_message"]["text"] == "Первое"


@requires_db
@pytest.mark.asyncio
async def test_admin_can_delete_an_unused_message_list(store):
    async with authed_client(store) as client:
        created = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created.json()["id"]
        await client.post(
            f"/api/broadcast-lists/{list_id}/messages",
            json={"text": "Первое"},
        )

        deleted = await client.delete(f"/api/broadcast-lists/{list_id}")
        assert deleted.status_code == 204

        listed = await client.get("/api/broadcast-lists")
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_delete_a_list_used_by_a_schedule(store):
    async with authed_client(store) as client:
        created_list = await client.post("/api/broadcast-lists", json={"name": "Прогрев"})
        list_id = created_list.json()["id"]
        await client.post(
            "/api/interval-broadcasts",
            json={
                "list_id": list_id,
                "scheduled_at": "2026-12-01T10:00:00+07:00",
                "interval_days": 3,
            },
        )

        deleted = await client.delete(f"/api/broadcast-lists/{list_id}")
        assert deleted.status_code == 409

        listed = await client.get("/api/broadcast-lists")
        match = next(item for item in listed.json() if item["id"] == list_id)
        assert match["name"] == "Прогрев"
