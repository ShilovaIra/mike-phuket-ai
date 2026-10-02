"""Tracked partner offer for the mini app. Identity comes from signed Telegram init data."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from partner_dashboard.offers import wrap_partners_for_user
from partners import build_partner_button_text
from tma_chat import TMA_CHANNEL, telegram_user_id


async def open_partner_offer(
    store: Any,
    *,
    init_data: str,
    bot_token: str,
    partner_id: UUID,
    public_base: str,
) -> dict[str, str]:
    external_id = telegram_user_id(init_data, bot_token)
    user_id = await store.ensure_identity(TMA_CHANNEL, external_id, source="tma")
    partner = next(
        (
            item
            for item in await store.list_partners()
            if item.id == partner_id and item.is_active
        ),
        None,
    )
    if partner is None:
        raise KeyError(partner_id)
    partner_type = await store.get_partner_type(partner.type)
    if partner_type is None:
        raise KeyError(partner.type)
    wrapped = await wrap_partners_for_user(
        store.pool, [partner], user_id, public_base=public_base
    )
    return {
        "url": wrapped[0].referral_url,
        "label": build_partner_button_text(partner, partner_type),
    }
