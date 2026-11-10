"""A reply that names several places leaves Telegram as one message per place."""

from __future__ import annotations

import bot
from tests.test_lead_contact import TOURIST_ID
from tests.test_lead_contact_wiring import TOURIST, text_message, update_for, wire

TOM = "https://www.google.com/maps/search/?api=1&query=Tom+Yum+Phuket"
SMILE = "https://www.google.com/maps/search/?api=1&query=Smile+Bar+Phuket"


async def test_each_place_gets_the_menu_keyboard_and_the_closer_is_plain(monkeypatch):
    fake_bot, fake_store, context = wire(monkeypatch)
    monkeypatch.undo()
    monkeypatch.setattr(bot, "store", fake_store)
    monkeypatch.setattr(bot, "ADMIN_IDS", frozenset())

    async def answer(_messages):
        return (
            "Вот ссылки:\n\n"
            f"Tom Yum:\n{TOM}\n\n"
            f"Smile Bar:\n{SMILE}\n\n"
            "Сказать, как доехать?"
        )

    monkeypatch.setattr(bot, "run_model", answer)
    incoming = text_message(text="Где поесть?", chat_id=TOURIST_ID, sender=TOURIST)
    incoming.set_bot(fake_bot)

    await bot.ask_openai(update_for(incoming), context, "Где поесть?")

    sent = [message for message in fake_bot.sent if message["chat_id"] == TOURIST_ID]
    assert [message["text"] for message in sent] == [
        "Думаю как местный 😎",
        f"Tom Yum:\n{TOM}",
        f"Smile Bar:\n{SMILE}",
        "Сказать, как доехать?",
    ]
    assert sent[1]["reply_markup"] is not None
    assert sent[2]["reply_markup"] is not None
    assert sent[3]["reply_markup"] is None
    assert [message["content"] for message in fake_store.messages if message["role"] == "assistant"] == [
        f"Tom Yum:\n{TOM}",
        f"Smile Bar:\n{SMILE}",
        "Сказать, как доехать?",
    ]
