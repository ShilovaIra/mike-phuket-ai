"""Operators must be able to reach a lead tourist even without a @username."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from telegram import Chat, Contact, Message, MessageOriginUser, User
from telegram.error import Forbidden

import lead_contact

TOURIST_ID = 1779117720
ADMIN_ID = 99
BOT_USER = User(id=5000, first_name="Mike", is_bot=True, username="MikePhuketAIBot")


@dataclass
class FakeBot:
    """Stands in for the Telegram Bot API and records every call."""

    sent: list = field(default_factory=list)
    forwarded: list = field(default_factory=list)
    fail_for: dict = field(default_factory=dict)

    async def send_message(self, chat_id, text, **kwargs):
        error = self.fail_for.get(int(chat_id))
        if error is not None:
            raise error
        self.sent.append({"chat_id": int(chat_id), "text": text, **kwargs})

    async def forward_message(self, chat_id, from_chat_id, message_id):
        self.forwarded.append(
            {"chat_id": int(chat_id), "from_chat_id": int(from_chat_id), "message_id": message_id}
        )


def tourist(username: str | None = None) -> User:
    return User(id=TOURIST_ID, first_name="Василь", is_bot=False, username=username)


def message(
    *,
    text: str,
    chat_id: int,
    sender: User,
    message_id: int = 1,
    reply_to: Message | None = None,
    **kwargs,
) -> Message:
    return Message(
        message_id=message_id,
        date=datetime.now(timezone.utc),
        chat=Chat(id=chat_id, type="private"),
        from_user=sender,
        text=text,
        reply_to_message=reply_to,
        **kwargs,
    )


async def test_lead_message_is_forwarded_to_every_admin():
    bot = FakeBot()
    lead_message = message(text="Купить", chat_id=TOURIST_ID, sender=tourist(), message_id=42)

    await lead_contact.forward_to_admins(bot, frozenset({"99", "100"}), lead_message)

    assert sorted(f["chat_id"] for f in bot.forwarded) == [99, 100]
    assert all(f["from_chat_id"] == TOURIST_ID for f in bot.forwarded)
    assert all(f["message_id"] == 42 for f in bot.forwarded)


def operator() -> User:
    return User(id=ADMIN_ID, first_name="Оператор", is_bot=False)


def lead_notice() -> Message:
    return message(
        text=(
            "🏠 Новая заявка на недвижимость\n\n"
            "Имя в Telegram: Василь\n"
            "Username: не указан\n"
            f"Telegram ID: {TOURIST_ID}\n"
        ),
        chat_id=ADMIN_ID,
        sender=BOT_USER,
        message_id=7,
    )


async def test_operator_reply_to_lead_notice_reaches_tourist():
    bot = FakeBot()
    reply = message(
        text="Здравствуйте! Подберу варианты в Раваи.",
        chat_id=ADMIN_ID,
        sender=operator(),
        reply_to=lead_notice(),
    )

    handled = await lead_contact.relay_operator_reply(bot, reply)

    assert handled is True
    to_tourist = [m for m in bot.sent if m["chat_id"] == TOURIST_ID]
    assert len(to_tourist) == 1
    assert "Здравствуйте! Подберу варианты в Раваи." in to_tourist[0]["text"]
    assert to_tourist[0]["text"].startswith(lead_contact.OPERATOR_PREFIX)
    to_operator = [m for m in bot.sent if m["chat_id"] == ADMIN_ID]
    assert "Отправлено" in to_operator[-1]["text"]


async def test_operator_reply_to_forwarded_tourist_message_reaches_tourist():
    bot = FakeBot()
    forwarded = message(
        text="Купить",
        chat_id=ADMIN_ID,
        sender=BOT_USER,
        forward_origin=MessageOriginUser(
            date=datetime.now(timezone.utc), sender_user=tourist()
        ),
    )
    reply = message(text="Добрый день!", chat_id=ADMIN_ID, sender=operator(), reply_to=forwarded)

    assert await lead_contact.relay_operator_reply(bot, reply) is True
    assert [m["chat_id"] for m in bot.sent][0] == TOURIST_ID


async def test_operator_reply_to_unrelated_message_is_not_relayed():
    bot = FakeBot()
    unrelated = message(text="Статистика за неделю", chat_id=ADMIN_ID, sender=BOT_USER)
    reply = message(text="ок", chat_id=ADMIN_ID, sender=operator(), reply_to=unrelated)

    assert await lead_contact.relay_operator_reply(bot, reply) is False
    assert bot.sent == []


async def test_operator_learns_when_tourist_blocked_the_bot():
    bot = FakeBot(fail_for={TOURIST_ID: Forbidden("bot was blocked by the user")})
    reply = message(text="Алло?", chat_id=ADMIN_ID, sender=operator(), reply_to=lead_notice())

    assert await lead_contact.relay_operator_reply(bot, reply) is True
    assert "заблокировал" in bot.sent[-1]["text"]
    assert bot.sent[-1]["chat_id"] == ADMIN_ID


def operator_message_in_tourist_chat() -> Message:
    return message(
        text=f"{lead_contact.OPERATOR_PREFIX}\n\nЗдравствуйте!",
        chat_id=TOURIST_ID,
        sender=BOT_USER,
        message_id=8,
    )


async def test_tourist_reply_to_operator_reaches_every_admin():
    bot = FakeBot()
    reply = message(
        text="Бюджет до 10 млн бат",
        chat_id=TOURIST_ID,
        sender=tourist(),
        reply_to=operator_message_in_tourist_chat(),
    )

    handled = await lead_contact.relay_tourist_reply(bot, frozenset({"99", "100"}), reply)

    assert handled is True
    to_admins = [m for m in bot.sent if m["chat_id"] in (99, 100)]
    assert len(to_admins) == 2
    for sent in to_admins:
        assert "Бюджет до 10 млн бат" in sent["text"]
        assert f"Telegram ID: {TOURIST_ID}" in sent["text"]
    assert "Передал менеджеру" in bot.sent[-1]["text"]
    assert bot.sent[-1]["chat_id"] == TOURIST_ID


async def test_admin_can_reply_again_to_relayed_tourist_message():
    bot = FakeBot()
    reply = message(
        text="Бюджет до 10 млн бат",
        chat_id=TOURIST_ID,
        sender=tourist(),
        reply_to=operator_message_in_tourist_chat(),
    )
    await lead_contact.relay_tourist_reply(bot, frozenset({"99"}), reply)
    relayed = message(
        text=bot.sent[0]["text"], chat_id=ADMIN_ID, sender=BOT_USER, message_id=9
    )
    bot.sent.clear()

    answer = message(text="Есть три виллы", chat_id=ADMIN_ID, sender=operator(), reply_to=relayed)

    assert await lead_contact.relay_operator_reply(bot, answer) is True
    assert bot.sent[0]["chat_id"] == TOURIST_ID


async def test_ordinary_tourist_message_is_left_for_mike():
    bot = FakeBot()
    plain = message(text="Где поесть в Раваи?", chat_id=TOURIST_ID, sender=tourist())
    reply_to_mike = message(
        text="А какой бюджет?",
        chat_id=TOURIST_ID,
        sender=tourist(),
        reply_to=message(text="Какой район?", chat_id=TOURIST_ID, sender=BOT_USER),
    )

    assert await lead_contact.relay_tourist_reply(bot, frozenset({"99"}), plain) is False
    assert await lead_contact.relay_tourist_reply(bot, frozenset({"99"}), reply_to_mike) is False
    assert bot.sent == []


async def test_tourist_without_username_is_asked_to_share_contact():
    bot = FakeBot()

    asked = await lead_contact.ask_for_contact_if_unreachable(bot, tourist(username=None))

    assert asked is True
    assert bot.sent[0]["chat_id"] == TOURIST_ID
    buttons = [b for row in bot.sent[0]["reply_markup"].keyboard for b in row]
    assert any(b.request_contact for b in buttons)


async def test_tourist_with_username_is_not_asked_for_contact():
    bot = FakeBot()

    asked = await lead_contact.ask_for_contact_if_unreachable(bot, tourist(username="vasil"))

    assert asked is False
    assert bot.sent == []


async def test_shared_contact_reaches_every_admin_with_phone_and_id():
    bot = FakeBot()
    shared = Message(
        message_id=3,
        date=datetime.now(timezone.utc),
        chat=Chat(id=TOURIST_ID, type="private"),
        from_user=tourist(),
        contact=Contact(phone_number="+66812345678", first_name="Василь", user_id=TOURIST_ID),
    )

    await lead_contact.send_contact_to_admins(bot, frozenset({"99", "100"}), shared)

    to_admins = [m for m in bot.sent if m["chat_id"] in (99, 100)]
    assert len(to_admins) == 2
    for sent in to_admins:
        assert "+66812345678" in sent["text"]
        assert f"Telegram ID: {TOURIST_ID}" in sent["text"]
