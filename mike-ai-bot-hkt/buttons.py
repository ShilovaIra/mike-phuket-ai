"""Reply keyboard button labels for the Telegram bot.

Demo nudge: emoji and caption separated by \\n so many Telegram clients
stack them. This is still plain text, not real icon layout.
"""

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
