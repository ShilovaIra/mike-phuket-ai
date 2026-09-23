"""Ways for an Operator to reach a lead Tourist, with or without a @username.

Telegram usernames are optional and the Bot API cannot turn a numeric id into
one, so the bot itself is the channel: it forwards the Tourist's message,
relays replies both ways, and asks for a phone contact when no handle exists.
"""

from __future__ import annotations

import logging
import re

from telegram import KeyboardButton, Message, MessageOriginUser, ReplyKeyboardMarkup
from telegram.error import Forbidden, TelegramError

logger = logging.getLogger(__name__)

# Admin messages carry this line; replying to one tells the bot who to write to.
TOURIST_ID_LINE = "Telegram ID: {tourist_id}"
_TOURIST_ID_PATTERN = re.compile(r"Telegram ID: (\d+)")

OPERATOR_PREFIX = "💬 Сообщение от менеджера Phuket ProMax:"
_TOURIST_REPLY_HINT = "Чтобы ответить менеджеру, ответь на это сообщение (свайп влево)."
OPERATOR_REPLY_HINT = "Ответь на это сообщение — бот передаст текст клиенту."


async def _send_to_admins(bot, admin_ids: frozenset[str], text: str) -> None:
    for admin_id in admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=text)
        except TelegramError:
            logger.exception("Sending to admin %s failed", admin_id)


def public_telegram_username(user) -> str | None:
    """Return @username when Telegram sent one; otherwise None."""
    raw = getattr(user, "username", None)
    if not raw:
        return None
    return raw if str(raw).startswith("@") else f"@{raw}"


def _tourist_id_from(replied: Message | None) -> int | None:
    if replied is None:
        return None
    match = _TOURIST_ID_PATTERN.search(replied.text or replied.caption or "")
    if match:
        return int(match.group(1))
    # A forward only names its sender if the Tourist's privacy settings allow it.
    origin = replied.forward_origin
    if isinstance(origin, MessageOriginUser):
        return origin.sender_user.id
    return None


async def relay_operator_reply(bot, message: Message) -> bool:
    """Send an Operator's reply to the Tourist named in the replied-to message.

    Returns False when the reply does not point at a Tourist, so the caller
    can treat the text as an ordinary chat message.
    """
    tourist_id = _tourist_id_from(message.reply_to_message)
    if tourist_id is None or not message.text:
        return False

    try:
        await bot.send_message(
            chat_id=tourist_id,
            text=f"{OPERATOR_PREFIX}\n\n{message.text}\n\n{_TOURIST_REPLY_HINT}",
        )
    except Forbidden:
        status = "❌ Не доставлено: клиент заблокировал бота"
    except TelegramError as exc:
        status = f"❌ Не доставлено: {exc}"
    else:
        status = "✅ Отправлено клиенту"
    await bot.send_message(chat_id=message.chat_id, text=status)
    return True


def tourist_identity_lines(user) -> str:
    """Name, @username (if any) and the id line Operators reply to."""
    return (
        f"Имя в Telegram: {getattr(user, 'first_name', None) or 'не указано'}\n"
        f"Username: {public_telegram_username(user) or 'не указан'}\n"
        f"{TOURIST_ID_LINE.format(tourist_id=user.id)}"
    )


def _is_reply_to_operator(message: Message) -> bool:
    replied = message.reply_to_message
    if replied is None or replied.from_user is None or not replied.from_user.is_bot:
        return False
    return (replied.text or "").startswith(OPERATOR_PREFIX)


async def relay_tourist_reply(bot, admin_ids: frozenset[str], message: Message) -> bool:
    """Pass a Tourist's reply to an Operator message on to every admin.

    Returns False for ordinary messages, which stay with Mike.
    """
    if not message.text or not _is_reply_to_operator(message):
        return False

    text = (
        "💬 Ответ клиента\n\n"
        f"{tourist_identity_lines(message.from_user)}\n\n"
        f"{message.text}\n\n"
        f"{OPERATOR_REPLY_HINT}"
    )
    await _send_to_admins(bot, admin_ids, text)
    await bot.send_message(chat_id=message.chat_id, text="Передал менеджеру 👌")
    return True


SHARE_CONTACT_BUTTON = "📱 Поделиться контактом"


async def ask_for_contact_if_unreachable(bot, user) -> bool:
    """Ask a Tourist with no @username for a phone contact. Returns True if asked."""
    if public_telegram_username(user):
        return False
    await bot.send_message(
        chat_id=user.id,
        text=(
            "Чтобы менеджер точно смог с тобой связаться, поделись контактом — "
            "нажми кнопку ниже 👇"
        ),
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(SHARE_CONTACT_BUTTON, request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return True


async def send_contact_to_admins(bot, admin_ids: frozenset[str], message: Message) -> None:
    contact = message.contact
    name = " ".join(filter(None, [contact.first_name, contact.last_name]))
    text = (
        "📱 Клиент поделился контактом\n\n"
        f"Телефон: {contact.phone_number}\n"
        f"Имя в контакте: {name or 'не указано'}\n"
        f"{tourist_identity_lines(message.from_user)}\n\n"
        f"{OPERATOR_REPLY_HINT}"
    )
    await _send_to_admins(bot, admin_ids, text)


async def forward_to_admins(bot, admin_ids: frozenset[str], message: Message) -> None:
    for admin_id in admin_ids:
        try:
            await bot.forward_message(
                chat_id=admin_id,
                from_chat_id=message.chat_id,
                message_id=message.message_id,
            )
        except TelegramError:
            logger.exception("Forwarding lead message to admin %s failed", admin_id)
