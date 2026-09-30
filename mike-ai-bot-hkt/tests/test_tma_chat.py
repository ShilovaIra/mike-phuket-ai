from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from contextlib import asynccontextmanager
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import requires_db

BOT_TOKEN = "123456:test-bot-token"
MAPS_URL = "https://www.google.com/maps/search/?api=1&query=Kata+Beach+Phuket"


@pytest.fixture(autouse=True)
def _tma_env(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)


def signed_init_data(*, token: str = BOT_TOKEN, user_id: int = 42) -> str:
    user = json.dumps(
        {"id": user_id, "first_name": "Анна", "username": "anna"},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    fields = {
        "auth_date": str(int(time.time())),
        "user": user,
    }
    data_check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def tma_headers(init_data: str | None = None) -> dict[str, str]:
    return {"Authorization": f"tma {init_data if init_data is not None else signed_init_data()}"}


@asynccontextmanager
async def tma_client(store, model, notify=None):
    from admin_api.app import create_app

    app = create_app(store=store, mike_model=model, notify_lead=notify)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@requires_db
@pytest.mark.asyncio
async def test_signed_user_reads_back_mikes_reply_without_the_lead_marker(store):
    async def model(_messages):
        return f"Пляж Ката. {MAPS_URL}\nЗАЯВКА_ГОТОВА"

    async with tma_client(store, model) as client:
        sent = await client.post(
            "/api/tma/messages",
            headers=tma_headers(),
            json={"text": "Где пляж в Кате?"},
        )

        assert sent.status_code == 200
        reply = sent.json()["reply"]
        assert MAPS_URL in reply
        assert "ЗАЯВКА_ГОТОВА" not in reply

        history = await client.get("/api/tma/messages", headers=tma_headers())

    assert history.status_code == 200
    assert history.json()["messages"] == [
        {"role": "user", "content": "Где пляж в Кате?"},
        {"role": "assistant", "content": reply},
    ]


@requires_db
@pytest.mark.asyncio
async def test_bad_or_missing_signature_is_rejected_and_stores_nothing(store):
    async def model(_messages):
        raise AssertionError("model should not run")

    forged = signed_init_data().replace("hash=", "hash=00", 1)

    async with tma_client(store, model) as client:
        forged_post = await client.post(
            "/api/tma/messages",
            headers={"Authorization": f"tma {forged}"},
            json={"text": "Привет"},
        )
        missing = await client.post(
            "/api/tma/messages",
            json={"text": "Привет"},
        )
        history = await client.get("/api/tma/messages", headers=tma_headers())

    assert forged_post.status_code == 401
    assert missing.status_code == 401
    assert history.status_code == 200
    assert history.json()["messages"] == []


@requires_db
@pytest.mark.asyncio
async def test_tma_thread_does_not_include_the_telegram_bot_thread(store):
    await store.append_message("telegram", "42", role="user", content="Из бота")
    await store.append_message("telegram", "42", role="assistant", content="Ответ бота")

    async def model(_messages):
        return "Ответ мини-приложения"

    async with tma_client(store, model) as client:
        await client.post(
            "/api/tma/messages",
            headers=tma_headers(),
            json={"text": "Из мини-приложения"},
        )
        history = await client.get("/api/tma/messages", headers=tma_headers())

    contents = [message["content"] for message in history.json()["messages"]]
    assert contents == ["Из мини-приложения", "Ответ мини-приложения"]


@requires_db
@pytest.mark.asyncio
async def test_model_failure_saves_nothing(store):
    async def model(_messages):
        raise RuntimeError("openai down")

    async with tma_client(store, model) as client:
        failed = await client.post(
            "/api/tma/messages",
            headers=tma_headers(),
            json={"text": "Где поесть?"},
        )
        history = await client.get("/api/tma/messages", headers=tma_headers())

    assert failed.status_code == 502
    assert history.json()["messages"] == []


@requires_db
@pytest.mark.asyncio
async def test_ready_lead_notifies_admins_and_hides_the_marker(store):
    notices = []

    async def model(_messages):
        return f"Заявка принята. {MAPS_URL}\nЗАЯВКА_ГОТОВА"

    async def notify(text):
        notices.append(text)

    await store.create_admin_user(email="admin@example.com", password="admin123")

    async with tma_client(store, model, notify=notify) as client:
        sent = await client.post(
            "/api/tma/messages",
            headers=tma_headers(),
            json={"text": "Хочу квартиру в Кате"},
        )
        login = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        stats = await client.get(
            "/api/stats",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )

    reply = sent.json()["reply"]
    assert "ЗАЯВКА_ГОТОВА" not in reply
    assert MAPS_URL in reply
    assert stats.json()["leads_all_time"] == 1
    assert len(notices) == 1
    assert "Хочу квартиру в Кате" in notices[0]
    assert "ЗАЯВКА_ГОТОВА" not in notices[0]
    assert "Анна" in notices[0]
    assert "Telegram ID: 42" in notices[0]


@requires_db
@pytest.mark.asyncio
async def test_second_send_while_a_reply_is_in_flight_is_refused(store):
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def model(_messages):
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            await release.wait()
        return "Готово"

    async with tma_client(store, model) as client:
        first = asyncio.create_task(
            client.post(
                "/api/tma/messages",
                headers=tma_headers(),
                json={"text": "первый"},
            )
        )
        await started.wait()
        second = await client.post(
            "/api/tma/messages",
            headers=tma_headers(),
            json={"text": "второй"},
        )
        release.set()
        first_response = await first
        history = await client.get("/api/tma/messages", headers=tma_headers())

    assert second.status_code == 409
    assert first_response.status_code == 200
    assert calls == 1
    assert [message["content"] for message in history.json()["messages"]] == [
        "первый",
        "Готово",
    ]


@requires_db
@pytest.mark.asyncio
async def test_mike_hears_the_same_system_prompt_as_the_bot(store):
    from bot import system_prompt

    seen = []

    async def model(messages):
        seen.append(list(messages))
        return "Ок"

    async with tma_client(store, model) as client:
        await client.post(
            "/api/tma/messages",
            headers=tma_headers(),
            json={"text": "Привет"},
        )

    assert seen[0][0] == {"role": "system", "content": system_prompt()}
    assert seen[0][-1] == {"role": "user", "content": "Привет"}


@requires_db
@pytest.mark.asyncio
async def test_mike_can_search_places_when_the_key_is_set(store, monkeypatch):
    import bot

    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-places-key")
    previous = bot.places
    bot.places = None
    seen = []

    async def model(messages):
        seen.append(list(messages))
        return "Ок"

    try:
        async with tma_client(store, model) as client:
            await client.post(
                "/api/tma/messages",
                headers=tma_headers(),
                json={"text": "Где поесть?"},
            )
    finally:
        bot.places = previous

    assert "У тебя есть поиск реальных мест" in seen[0][0]["content"]
