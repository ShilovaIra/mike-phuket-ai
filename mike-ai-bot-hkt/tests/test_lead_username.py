"""Leads must keep a Telegram @username when Telegram actually sent one."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from telegram import Chat, Message, Update, User

import bot
from bot import public_telegram_username


def make_update(*, tid: int, first_name: str, username: str | None) -> Update:
    user = User(id=tid, first_name=first_name, is_bot=False, username=username)
    chat = Chat(id=tid, type="private", first_name=first_name, username=username)
    message = Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=chat,
        from_user=user,
        text="Купить",
    )
    return Update(update_id=1, message=message)


@pytest.mark.parametrize(
    ("username", "expected"),
    [
        (None, None),
        ("", None),
        ("vasil", "@vasil"),
        ("@vasil", "@vasil"),
    ],
)
def test_public_telegram_username(username, expected):
    user = User(id=1779117720, first_name="Василь", is_bot=False, username=username)
    assert public_telegram_username(user) == expected


def test_public_telegram_username_none_user():
    assert public_telegram_username(None) is None


@pytest.mark.asyncio
async def test_lead_snapshot_keeps_username_when_telegram_sends_it(monkeypatch):
    update = make_update(tid=111, first_name="Anna", username="anna_phuket")

    class FakeStore:
        async def get_ai_context(self, *args, **kwargs):
            return [{"role": "user", "content": "Купить"}]

    monkeypatch.setattr(bot, "store", FakeStore())
    snapshot = await bot.build_lead_snapshot(update)

    assert snapshot["telegram_id"] == "111"
    assert snapshot["telegram_username"] == "@anna_phuket"
    assert snapshot["telegram_first_name"] == "Anna"


@pytest.mark.asyncio
async def test_lead_snapshot_username_is_none_when_telegram_omits_it(monkeypatch):
    update = make_update(tid=1779117720, first_name="Василь", username=None)

    class FakeStore:
        async def get_ai_context(self, *args, **kwargs):
            return [{"role": "user", "content": "Купить"}]

    monkeypatch.setattr(bot, "store", FakeStore())
    snapshot = await bot.build_lead_snapshot(update)

    assert snapshot["telegram_username"] is None


@pytest.mark.asyncio
async def test_admin_lead_text_shows_handle_or_fallback(monkeypatch):
    sent: list[tuple[str, str]] = []

    class FakeStore:
        async def get_ai_context(self, *args, **kwargs):
            return [{"role": "user", "content": "Купить"}]

    class FakeBot:
        async def send_message(self, chat_id, text):
            sent.append((chat_id, text))

        async def forward_message(self, chat_id, from_chat_id, message_id):
            pass

    monkeypatch.setattr(bot, "store", FakeStore())
    monkeypatch.setattr(bot, "ADMIN_IDS", frozenset({"99"}))
    context = SimpleNamespace(bot=FakeBot())

    with_handle = make_update(tid=111, first_name="Anna", username="anna_phuket")
    await bot.send_lead_to_admin(with_handle, context, "instagram")
    assert "Username: @anna_phuket" in sent[-1][1]
    assert "Telegram ID: 111" in sent[-1][1]

    without_handle = make_update(tid=1779117720, first_name="Василь", username=None)
    await bot.send_lead_to_admin(without_handle, context, "unknown")
    assert "Username: не указан" in sent[-1][1]
    assert "Telegram ID: 1779117720" in sent[-1][1]
