"""bot.py must route lead-contact traffic before Mike's AI sees it."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from telegram import Chat, Contact, Message, Update, User

import bot
import lead_contact
from tests.test_lead_contact import ADMIN_ID, BOT_USER, TOURIST_ID, FakeBot, lead_notice

TOURIST = User(id=TOURIST_ID, first_name="Василь", is_bot=False)
OPERATOR = User(id=ADMIN_ID, first_name="Оператор", is_bot=False)


class FakeStore:
    def __init__(self):
        self.inbound = []
        self.messages = []

    async def get_ai_context(self, *args, **kwargs):
        return [{"role": "user", "content": "Купить"}]

    async def list_partner_types(self):
        return []

    async def record_inbound(self, channel, tid):
        self.inbound.append(tid)

    async def append_message(self, channel, tid, *, role, content, metadata=None):
        self.messages.append({"tid": tid, "role": role, "content": content})


def update_for(message: Message) -> Update:
    return Update(update_id=1, message=message)


def text_message(*, text, chat_id, sender, reply_to=None, message_id=1) -> Message:
    return Message(
        message_id=message_id,
        date=datetime.now(timezone.utc),
        chat=Chat(id=chat_id, type="private"),
        from_user=sender,
        text=text,
        reply_to_message=reply_to,
    )


def wire(monkeypatch):
    fake_bot = FakeBot()
    fake_store = FakeStore()
    monkeypatch.setattr(bot, "store", fake_store)
    monkeypatch.setattr(bot, "ADMIN_IDS", frozenset({str(ADMIN_ID)}))

    async def no_ai(*args, **kwargs):
        raise AssertionError("Mike's AI must not answer relayed messages")

    monkeypatch.setattr(bot, "ask_openai", no_ai)
    return fake_bot, fake_store, SimpleNamespace(bot=fake_bot)


async def test_admin_reply_to_lead_notice_goes_to_tourist_not_ai(monkeypatch):
    fake_bot, _, context = wire(monkeypatch)
    reply = text_message(
        text="Здравствуйте!", chat_id=ADMIN_ID, sender=OPERATOR, reply_to=lead_notice()
    )

    await bot.handle_message(update_for(reply), context)

    assert fake_bot.sent[0]["chat_id"] == TOURIST_ID
    assert "Здравствуйте!" in fake_bot.sent[0]["text"]


async def test_tourist_reply_to_operator_goes_to_admins_not_ai(monkeypatch):
    fake_bot, _, context = wire(monkeypatch)
    operator_msg = text_message(
        text=f"{lead_contact.OPERATOR_PREFIX}\n\nЗдравствуйте!",
        chat_id=TOURIST_ID,
        sender=BOT_USER,
        message_id=8,
    )
    reply = text_message(
        text="Жду варианты", chat_id=TOURIST_ID, sender=TOURIST, reply_to=operator_msg
    )

    await bot.handle_message(update_for(reply), context)

    assert any(m["chat_id"] == ADMIN_ID and "Жду варианты" in m["text"] for m in fake_bot.sent)


async def test_lead_notice_forwards_tourist_message_and_explains_reply(monkeypatch):
    fake_bot, _, context = wire(monkeypatch)
    lead_msg = text_message(text="Купить", chat_id=TOURIST_ID, sender=TOURIST, message_id=42)

    await bot.send_lead_to_admin(update_for(lead_msg), context, "unknown")

    notice = fake_bot.sent[0]
    assert notice["chat_id"] == ADMIN_ID
    assert f"Telegram ID: {TOURIST_ID}" in notice["text"]
    assert "Ответь на это сообщение" in notice["text"]
    assert fake_bot.forwarded == [
        {"chat_id": ADMIN_ID, "from_chat_id": TOURIST_ID, "message_id": 42}
    ]


async def test_finished_lead_without_username_asks_tourist_for_contact(monkeypatch):
    fake_bot, fake_store, context = wire(monkeypatch)
    monkeypatch.undo()
    monkeypatch.setattr(bot, "store", fake_store)
    monkeypatch.setattr(bot, "ADMIN_IDS", frozenset({str(ADMIN_ID)}))

    async def create_lead(channel, tid, *, snapshot):
        return SimpleNamespace(created=True, source="unknown")

    async def lead_answer(messages):
        return "Отлично, передаю менеджеру! ЗАЯВКА_ГОТОВА"

    fake_store.create_lead = create_lead
    monkeypatch.setattr(bot, "run_model", lead_answer)
    lead_msg = text_message(text="Через месяц", chat_id=TOURIST_ID, sender=TOURIST, message_id=42)
    lead_msg.set_bot(fake_bot)

    await bot.ask_openai(update_for(lead_msg), context, "Через месяц")

    to_tourist = [m for m in fake_bot.sent if m["chat_id"] == TOURIST_ID]
    assert "передаю менеджеру" in to_tourist[-2]["text"]
    buttons = [b for row in to_tourist[-1]["reply_markup"].keyboard for b in row]
    assert any(b.request_contact for b in buttons)


async def test_shared_contact_reaches_admins_and_is_kept_in_history(monkeypatch):
    fake_bot, fake_store, context = wire(monkeypatch)
    shared = Message(
        message_id=3,
        date=datetime.now(timezone.utc),
        chat=Chat(id=TOURIST_ID, type="private"),
        from_user=TOURIST,
        contact=Contact(phone_number="+66812345678", first_name="Василь", user_id=TOURIST_ID),
    )

    await bot.handle_contact(update_for(shared), context)

    assert any(m["chat_id"] == ADMIN_ID and "+66812345678" in m["text"] for m in fake_bot.sent)
    assert any("+66812345678" in m["content"] for m in fake_store.messages)
    thanks = [m for m in fake_bot.sent if m["chat_id"] == TOURIST_ID]
    assert thanks and "Спасибо" in thanks[0]["text"]
