"""Saved places for the mini app. Identity comes from signed Telegram init data."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from place_catalog import Place
from tma_chat import TMA_CHANNEL, telegram_user_id


async def open_session(store: Any, *, init_data: str, bot_token: str) -> None:
    external_id = telegram_user_id(init_data, bot_token)
    await store.ensure_identity(TMA_CHANNEL, external_id, source="tma")


async def save_partner(
    store: Any,
    *,
    init_data: str,
    bot_token: str,
    partner_id: UUID,
    saved: bool,
) -> bool:
    external_id = telegram_user_id(init_data, bot_token)
    await store.set_partner_favourite(TMA_CHANNEL, external_id, partner_id, saved=saved)
    return saved


async def list_saved(
    store: Any,
    *,
    init_data: str,
    bot_token: str,
) -> list[tuple[str, UUID]]:
    external_id = telegram_user_id(init_data, bot_token)
    return await store.list_favourite_refs(TMA_CHANNEL, external_id)


async def save_place(
    store: Any,
    *,
    init_data: str,
    bot_token: str,
    place_id: UUID,
    saved: bool,
) -> bool:
    external_id = telegram_user_id(init_data, bot_token)
    await store.set_place_favourite(TMA_CHANNEL, external_id, place_id, saved=saved)
    return saved


async def list_places(
    store: Any,
    *,
    init_data: str,
    bot_token: str,
) -> list[Place]:
    external_id = telegram_user_id(init_data, bot_token)
    return await store.list_favourite_places(TMA_CHANNEL, external_id)
