"""Mini-app chat with Mike. Identity comes from signed Telegram init data."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any, Awaitable, Callable
from urllib.parse import parse_qsl

import httpx

from lead_contact import OPERATOR_REPLY_HINT
from maps_links import sanitize_map_links

logger = logging.getLogger(__name__)

TMA_CHANNEL = "tma"

MikeModel = Callable[[list[dict[str, str]]], Awaitable[str]]
LeadNotice = Callable[[str], Awaitable[None]]


class InvalidInitData(Exception):
    pass


class MikeUnavailable(Exception):
    pass


class ReplyInFlight(Exception):
    pass


_inflight: set[str] = set()


def telegram_user(init_data: str, bot_token: str) -> dict[str, str]:
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    received = fields.pop("hash", None)
    if not received or not bot_token:
        raise InvalidInitData
    data_check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, received):
        raise InvalidInitData
    try:
        user = json.loads(fields["user"])
        return {
            "id": str(user["id"]),
            "first_name": str(user.get("first_name") or ""),
            "username": str(user.get("username") or ""),
        }
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidInitData from exc


def telegram_user_id(init_data: str, bot_token: str) -> str:
    return telegram_user(init_data, bot_token)["id"]


def lead_notice(user: dict[str, str], dialogue: list[dict[str, str]]) -> str:
    username = f"@{user['username']}" if user["username"] else "не указан"
    lines = []
    for message in dialogue:
        role = "Клиент" if message["role"] == "user" else "Майк"
        lines.append(f"{role}: {message['content']}")
    return (
        "🏠 Новая заявка на недвижимость\n\n"
        "Источник: tma\n\n"
        f"Имя в Telegram: {user['first_name'] or 'не указано'}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user['id']}\n\n"
        f"{OPERATOR_REPLY_HINT}\n\n"
        "Диалог:\n"
        f"{chr(10).join(lines)}"
    )


def ensure_place_search() -> None:
    import bot
    from places import PlacesClient

    key = (os.environ.get("GOOGLE_PLACES_API_KEY") or "").strip()
    if bot.places is None and key:
        bot.places = PlacesClient(key)


async def default_mike_model(messages: list[dict[str, str]]) -> str:
    from bot import run_model

    return await run_model(messages)


async def notify_admins(text: str) -> None:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    admin_ids = [
        part.strip()
        for part in (os.environ.get("ADMIN_CHAT_ID") or "").split(",")
        if part.strip()
    ]
    if not token or not admin_ids:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        for admin_id in admin_ids:
            try:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": admin_id, "text": text},
                )
                response.raise_for_status()
            except httpx.HTTPError:
                logger.exception("lead notice to %s failed", admin_id)


async def send(
    store: Any,
    model: MikeModel,
    *,
    init_data: str,
    bot_token: str,
    text: str,
    notify: LeadNotice | None = None,
) -> str:
    user = telegram_user(init_data, bot_token)
    external_id = user["id"]
    if external_id in _inflight:
        raise ReplyInFlight
    _inflight.add(external_id)
    try:
        from bot import system_prompt

        ensure_place_search()
        history = await store.get_ai_context(TMA_CHANNEL, external_id)
        try:
            answer = await model(
                [{"role": "system", "content": system_prompt()}]
                + history
                + [{"role": "user", "content": text}]
            )
        except Exception as exc:
            raise MikeUnavailable from exc
        lead_ready = "ЗАЯВКА_ГОТОВА" in answer
        reply = sanitize_map_links(answer.replace("ЗАЯВКА_ГОТОВА", "").strip())
        await store.append_message(TMA_CHANNEL, external_id, role="user", content=text)
        await store.append_message(TMA_CHANNEL, external_id, role="assistant", content=reply)
        if lead_ready:
            dialogue = await store.get_ai_context(TMA_CHANNEL, external_id)
            lead = await store.create_lead(
                TMA_CHANNEL,
                external_id,
                snapshot={
                    "telegram_id": external_id,
                    "telegram_username": f"@{user['username']}" if user["username"] else None,
                    "telegram_first_name": user["first_name"],
                    "dialogue": dialogue,
                },
            )
            if lead and lead.created and notify is not None:
                try:
                    await notify(lead_notice(user, dialogue))
                except Exception:
                    logger.exception("lead notice failed")
        return reply
    finally:
        _inflight.discard(external_id)


async def history(store: Any, *, init_data: str, bot_token: str) -> list[dict[str, str]]:
    external_id = telegram_user_id(init_data, bot_token)
    return await store.get_ai_context(TMA_CHANNEL, external_id)
