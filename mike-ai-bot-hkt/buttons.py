"""Reply keyboard button labels for the Telegram bot.

Demo nudge: emoji and caption separated by \\n so many Telegram clients
stack them. This is still plain text, not real icon layout.
"""

from __future__ import annotations

from collections.abc import Sequence

from partners import PartnerType
from topics import (
    TOPIC_ASK_MIKE,
    TOPIC_BEACHES,
    TOPIC_REAL_ESTATE,
    TOPIC_WHERE_TO_EAT,
)

WHERE_TO_EAT_BUTTON = "🍜 \nГде поесть"
BEACHES_BUTTON = "🏖 \nПляжи"
NEARBY_BUTTON = "📍 \nЧто рядом"
REAL_ESTATE_BUTTON = "🏠 \nНедвижимость"
ASK_MIKE_BUTTON = "💬 \nСпросить Майка"

BUTTON_TO_TOPIC = {
    WHERE_TO_EAT_BUTTON: TOPIC_WHERE_TO_EAT,
    BEACHES_BUTTON: TOPIC_BEACHES,
    REAL_ESTATE_BUTTON: TOPIC_REAL_ESTATE,
    ASK_MIKE_BUTTON: TOPIC_ASK_MIKE,
}


def build_reply_keyboard_rows(
    partner_types: Sequence[PartnerType],
) -> list[list[str]]:
    """Pack main menu 2-up; Ask Mike always alone on the last row."""
    ordered_partners = sorted(partner_types, key=lambda t: (t.sort_order, t.slug))
    before_ask_mike = [
        WHERE_TO_EAT_BUTTON,
        BEACHES_BUTTON,
        NEARBY_BUTTON,
        *[t.button_label for t in ordered_partners],
        REAL_ESTATE_BUTTON,
    ]
    rows: list[list[str]] = [
        before_ask_mike[i : i + 2] for i in range(0, len(before_ask_mike), 2)
    ]
    rows.append([ASK_MIKE_BUTTON])
    return rows
