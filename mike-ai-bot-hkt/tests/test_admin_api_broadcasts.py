from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

import bot
from broadcasts import create_broadcast
from tests.conftest import requires_db

PROMTEP_MAPS = (
    "https://www.google.com/maps/place/Promthep+Cape/"
    "@7.7600,98.3000,17z/data=!4m6!3m5!1s0x0!8m2!3d7.7622!4d98.3055"
)


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
async def test_admin_can_schedule_a_broadcast_and_see_it_listed(store):
    scheduled_at = "2026-12-01T10:00:00+07:00"
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={"text": "Как вам Пхукет?", "scheduled_at": scheduled_at},
        )
        assert created.status_code == 201
        body = created.json()
        assert body["text"] == "Как вам Пхукет?"
        assert body["status"] == "scheduled"
        assert body["scheduled_at"] == scheduled_at

        listed = await client.get("/api/broadcasts")
        assert listed.status_code == 200
        match = next(item for item in listed.json() if item["id"] == body["id"])
        assert match["text"] == "Как вам Пхукет?"
        assert match["status"] == "scheduled"
        assert match["scheduled_at"] == scheduled_at


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_schedule_a_broadcast_in_the_past(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={"text": "Уже прошло", "scheduled_at": "2020-01-01T10:00:00+07:00"},
        )
        assert created.status_code == 400

        listed = await client.get("/api/broadcasts")
        assert listed.status_code == 200
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_schedule_a_broadcast_without_text(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={"text": "   ", "scheduled_at": "2026-12-01T10:00:00+07:00"},
        )
        assert created.status_code == 400

        listed = await client.get("/api/broadcasts")
        assert listed.status_code == 200
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_admin_cannot_schedule_a_broadcast_with_a_maps_link_without_a_pin(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={
                "text": "Смотри место",
                "scheduled_at": "2026-12-01T10:00:00+07:00",
                "button_url": "https://www.google.com/maps/search/?api=1&query=Phuket",
            },
        )
        assert created.status_code == 400

        listed = await client.get("/api/broadcasts")
        assert listed.status_code == 200
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_broadcast_without_a_link_has_no_button(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={"text": "Как вам Пхукет?", "scheduled_at": "2026-12-01T10:00:00+07:00"},
        )
        assert created.status_code == 201
        body = created.json()
        assert body["button_url"] is None
        assert body["button_label"] is None

        listed = await client.get("/api/broadcasts")
        match = next(item for item in listed.json() if item["id"] == body["id"])
        assert match["button_url"] is None
        assert match["button_label"] is None


@requires_db
@pytest.mark.asyncio
async def test_blank_button_label_defaults_to_route_label(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={
                "text": "Загляни на мыс",
                "scheduled_at": "2026-12-01T10:00:00+07:00",
                "button_url": PROMTEP_MAPS,
                "button_label": "  ",
            },
        )
        assert created.status_code == 201
        body = created.json()
        assert body["button_url"] == PROMTEP_MAPS
        assert body["button_label"] == "Проложить маршрут"


@requires_db
@pytest.mark.asyncio
async def test_admin_can_edit_a_scheduled_broadcast(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={"text": "Как вам Пхукет?", "scheduled_at": "2026-12-01T10:00:00+07:00"},
        )
        broadcast_id = created.json()["id"]
        edited = await client.patch(
            f"/api/broadcasts/{broadcast_id}",
            json={
                "text": "Новый текст",
                "scheduled_at": "2026-12-02T11:30:00+07:00",
                "button_url": PROMTEP_MAPS,
                "button_label": "На карте",
            },
        )
        assert edited.status_code == 200
        body = edited.json()
        assert body["text"] == "Новый текст"
        assert body["scheduled_at"] == "2026-12-02T11:30:00+07:00"
        assert body["button_url"] == PROMTEP_MAPS
        assert body["button_label"] == "На карте"
        assert body["status"] == "scheduled"

        listed = await client.get("/api/broadcasts")
        match = next(item for item in listed.json() if item["id"] == broadcast_id)
        assert match["text"] == "Новый текст"
        assert match["button_label"] == "На карте"


@requires_db
@pytest.mark.asyncio
async def test_admin_can_delete_a_scheduled_broadcast(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={"text": "Как вам Пхукет?", "scheduled_at": "2026-12-01T10:00:00+07:00"},
        )
        broadcast_id = created.json()["id"]
        deleted = await client.delete(f"/api/broadcasts/{broadcast_id}")
        assert deleted.status_code == 204

        listed = await client.get("/api/broadcasts")
        assert listed.status_code == 200
        assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_started_broadcast_is_sent_and_cannot_be_changed(store):
    scheduled_at = "2026-12-01T10:00:00+07:00"
    async with authed_client(store) as client:
        created = await client.post(
            "/api/broadcasts",
            json={"text": "Как вам Пхукет?", "scheduled_at": scheduled_at},
        )
        broadcast_id = created.json()["id"]
        await store.claim_due_jobs(now=datetime.fromisoformat(scheduled_at))

        listed = await client.get("/api/broadcasts")
        match = next(item for item in listed.json() if item["id"] == broadcast_id)
        assert match["status"] == "sent"
        assert match["text"] == "Как вам Пхукет?"

        edited = await client.patch(
            f"/api/broadcasts/{broadcast_id}",
            json={"text": "Другой текст", "scheduled_at": "2026-12-03T10:00:00+07:00"},
        )
        assert edited.status_code == 409
        deleted = await client.delete(f"/api/broadcasts/{broadcast_id}")
        assert deleted.status_code == 409

        listed_again = await client.get("/api/broadcasts")
        match_again = next(
            item for item in listed_again.json() if item["id"] == broadcast_id
        )
        assert match_again["status"] == "sent"
        assert match_again["text"] == "Как вам Пхукет?"


@requires_db
@pytest.mark.asyncio
async def test_due_broadcast_goes_to_each_open_telegram_chat(store):
    opened = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    await store.start_conversation("telegram", "early", source="unknown")
    await store.start_conversation("telegram", "writer", source="unknown")
    await store.record_inbound("telegram", "writer", at=opened)
    await store.start_conversation("tma", "mini-only", source="tma")
    await store.start_conversation("telegram", "blocked", source="unknown")
    await store.schedule_partner_follow_up("telegram", "blocked", "money_exchange", at=opened)
    blocked_jobs = await store.claim_due_jobs(now=opened + timedelta(hours=24))
    await store.mark_job_failed(blocked_jobs[0].id, permanent=True)

    scheduled_at = opened + timedelta(days=2)
    await create_broadcast(store.pool, text="Как вам Пхукет?", scheduled_at=scheduled_at)
    await store.start_conversation("telegram", "late", source="unknown")

    due = await store.claim_due_jobs(now=scheduled_at)
    broadcasts = [job for job in due if job.kind == "broadcast"]

    assert {job.external_id for job in broadcasts} == {"early", "writer", "late"}
    assert {job.channel for job in broadcasts} == {"telegram"}
    assert {job.message_text for job in broadcasts} == {"Как вам Пхукет?"}


@requires_db
@pytest.mark.asyncio
async def test_sent_broadcast_is_stored_as_mike_without_the_link(store):
    await store.start_conversation("telegram", "4001", source="unknown")
    scheduled_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    await create_broadcast(store.pool, 
        text="Как вам Пхукет?",
        scheduled_at=scheduled_at,
        button_url=PROMTEP_MAPS,
        button_label="Проложить маршрут",
    )

    due = await store.claim_due_jobs(now=scheduled_at)
    job = next(job for job in due if job.kind == "broadcast" and job.external_id == "4001")
    await store.mark_job_sent(job.id, message_text=job.message_text)

    context = await store.get_ai_context("telegram", "4001")
    assert context[-1] == {"role": "assistant", "content": "Как вам Пхукет?"}
    assert PROMTEP_MAPS not in context[-1]["content"]


class _BlockedBot:
    async def send_message(self, **_kwargs):
        from telegram.error import Forbidden

        raise Forbidden("bot was blocked by the user")


@requires_db
@pytest.mark.asyncio
async def test_blocked_broadcast_send_leaves_nudges_unchanged(store):
    opened = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    await store.start_conversation("telegram", "5001", source="unknown")
    await store.schedule_partner_follow_up("telegram", "5001", "money_exchange", at=opened)
    scheduled_at = opened + timedelta(hours=1)
    await create_broadcast(store.pool, text="Как вам Пхукет?", scheduled_at=scheduled_at)

    previous = bot.store
    bot.store = store
    try:
        await bot.process_due_follow_ups(_BlockedBot(), now=scheduled_at)
    finally:
        bot.store = previous

    later = await store.claim_due_jobs(now=opened + timedelta(hours=24))
    assert any(job.kind == "partner_topic" and job.external_id == "5001" for job in later)
    assert not any(job.kind == "broadcast" for job in later)


@requires_db
@pytest.mark.asyncio
async def test_broadcast_job_includes_the_saved_button(store):
    await store.start_conversation("telegram", "6001", source="unknown")
    scheduled_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    await create_broadcast(store.pool, 
        text="С кнопкой",
        scheduled_at=scheduled_at,
        button_url=PROMTEP_MAPS,
        button_label="На карте",
    )
    await create_broadcast(store.pool, text="Без кнопки", scheduled_at=scheduled_at)

    due = [
        job
        for job in await store.claim_due_jobs(now=scheduled_at)
        if job.kind == "broadcast" and job.external_id == "6001"
    ]
    with_button = next(job for job in due if job.message_text == "С кнопкой")
    without_button = next(job for job in due if job.message_text == "Без кнопки")
    assert with_button.button_url == PROMTEP_MAPS
    assert with_button.button_label == "На карте"
    assert without_button.button_url is None
    assert without_button.button_label is None


class _RecordingBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, **kwargs):
        self.sent.append(kwargs)


@requires_db
@pytest.mark.asyncio
async def test_broadcast_with_a_link_is_sent_with_a_route_button(store):
    await store.start_conversation("telegram", "7001", source="unknown")
    scheduled_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    await create_broadcast(store.pool, 
        text="С кнопкой",
        scheduled_at=scheduled_at,
        button_url=PROMTEP_MAPS,
        button_label="На карте",
    )
    await create_broadcast(store.pool, text="Без кнопки", scheduled_at=scheduled_at)

    recorder = _RecordingBot()
    previous = bot.store
    bot.store = store
    try:
        await bot.process_due_follow_ups(recorder, now=scheduled_at)
    finally:
        bot.store = previous

    with_button = next(item for item in recorder.sent if item["text"] == "С кнопкой")
    without_button = next(item for item in recorder.sent if item["text"] == "Без кнопки")
    button = with_button["reply_markup"].inline_keyboard[0][0]
    assert button.text == "На карте"
    assert button.url == PROMTEP_MAPS
    assert without_button.get("reply_markup") is None
