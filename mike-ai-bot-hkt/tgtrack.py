from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

import httpx

HttpPost = Callable[..., Awaitable[None]]

logger = logging.getLogger(__name__)

_WEBHOOK_URL = "https://bot-api.tgtrack.ru/v1/{key}/on_telegram_webhook"
_POST_TIMEOUT_SECONDS = 2.0


async def _default_post(url: str, json: dict[str, Any]) -> None:
    async with httpx.AsyncClient(timeout=_POST_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=json)
        response.raise_for_status()


def _should_forward(update: dict[str, Any]) -> bool:
    text = str((update.get("message") or {}).get("text") or "")
    if text.startswith("/start"):
        return True
    member = (update.get("my_chat_member") or {}).get("new_chat_member") or {}
    return member.get("status") == "kicked"


class TgTrack:
    def __init__(self, api_key: str | None, *, post: HttpPost | None = None) -> None:
        self._api_key = (api_key or "").strip()
        self._post = post or _default_post

    async def notify(self, update: dict[str, Any]) -> None:
        if not self._api_key or not _should_forward(update):
            return
        try:
            await self._post(
                _WEBHOOK_URL.format(key=self._api_key),
                json=update,
            )
        except Exception:
            logger.exception("TGTrack notify failed")
