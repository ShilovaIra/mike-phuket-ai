"""How the bot sends a partner card: CDN logo, bundled logo, or text only."""

from __future__ import annotations

from telegram.error import BadRequest

import bot
from partners import PartnerCard
from storage import AssetStorage
from tests.conftest import S3_ENV

CDN = S3_ENV["S3_PUBLIC_BASE_URL"]


class FakeMessage:
    def __init__(self, *, photo_error: Exception | None = None):
        self.photo_error = photo_error
        self.photos: list[dict] = []
        self.texts: list[dict] = []

    async def reply_photo(self, **kwargs):
        if self.photo_error is not None:
            raise self.photo_error
        photo = kwargs["photo"]
        kwargs["photo"] = photo if isinstance(photo, str) else ("file", photo.name)
        self.photos.append(kwargs)

    async def reply_text(self, text, **kwargs):
        self.texts.append({"text": text, **kwargs})


def card(logo_path: str | None) -> PartnerCard:
    return PartnerCard(
        caption_html="<b>Money Shop</b>",
        button_text="Перейти",
        referral_url="https://example.com/go",
        logo_path=logo_path,
    )


async def test_uploaded_logo_is_sent_by_cdn_url(monkeypatch):
    monkeypatch.setattr(bot, "storage", AssetStorage.from_env(S3_ENV))
    message = FakeMessage()

    await bot.send_partner_card(message, card("partners/1/logo-abc.png"))

    assert [p["photo"] for p in message.photos] == [f"{CDN}/partners/1/logo-abc.png"]
    assert message.photos[0]["caption"] == "<b>Money Shop</b>"
    assert message.texts == []


def _button_urls(reply: dict) -> list[str]:
    return [b.url for row in reply["reply_markup"].inline_keyboard for b in row]


async def test_card_falls_back_to_text_when_telegram_cannot_fetch_logo(monkeypatch):
    monkeypatch.setattr(bot, "storage", AssetStorage.from_env(S3_ENV))
    message = FakeMessage(photo_error=BadRequest("Wrong file identifier/http url specified"))

    await bot.send_partner_card(message, card("partners/1/logo-gone.png"))

    assert [t["text"] for t in message.texts] == ["<b>Money Shop</b>"]
    assert _button_urls(message.texts[0]) == ["https://example.com/go"]


async def test_uploaded_logo_without_storage_config_sends_text_card(monkeypatch):
    monkeypatch.setattr(bot, "storage", None)
    message = FakeMessage()

    await bot.send_partner_card(message, card("partners/1/logo-abc.png"))

    assert message.photos == []
    assert [t["text"] for t in message.texts] == ["<b>Money Shop</b>"]


async def test_bundled_logo_is_still_sent_as_file(monkeypatch):
    monkeypatch.setattr(bot, "storage", AssetStorage.from_env(S3_ENV))
    message = FakeMessage()

    await bot.send_partner_card(message, card("media/partners/moneyshop.jpeg"))

    assert len(message.photos) == 1
    kind, name = message.photos[0]["photo"]
    assert kind == "file" and name.endswith("media/partners/moneyshop.jpeg")
    assert message.texts == []
