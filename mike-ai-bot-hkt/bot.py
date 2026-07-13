import os
import asyncio
import sys
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from openai import OpenAI

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from db.store import SessionStore
from partners import (
    MONEY_EXCHANGE_TYPE,
    build_partner_cards,
    resolve_logo_path,
)
from buttons import (
    ASK_MIKE_BUTTON,
    BEACHES_BUTTON,
    MONEY_EXCHANGE_BUTTON,
    NEARBY_BUTTON,
    REAL_ESTATE_BUTTON,
    WHERE_TO_EAT_BUTTON,
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

CHANNEL = "telegram"

client = OpenAI(api_key=OPENAI_API_KEY)
store: SessionStore | None = None

MIKE_PROMPT = """
Ты Майк — дружелюбный AI-гид по Пхукету и помощник Phuket ProMax.

Говори на русском языке коротко, понятно и живо.

Помогай туристам с пляжами, ресторанами, маршрутами, экскурсиями, транспортом и недвижимостью.

Если человек интересуется недвижимостью, мягко выясняй:
1. Покупка или аренда?
2. Район
3. Бюджет
4. Количество спален
5. Когда планирует покупку или аренду
6. Имя
7. WhatsApp или Telegram для связи

Не задавай всё сразу. Задавай по одному-два вопроса.
Если пользователь уже что-то сказал раньше — учитывай это и не спрашивай повторно.

Когда собрал достаточно данных для заявки, напиши в ответе фразу:
ЗАЯВКА_ГОТОВА

Если получаешь геолокацию, не выдумывай район сам. Используй только район и адрес, которые переданы в сообщении.
"""

keyboard = [
    [WHERE_TO_EAT_BUTTON, BEACHES_BUTTON],
    [KeyboardButton(NEARBY_BUTTON, request_location=True), MONEY_EXCHANGE_BUTTON],
    [REAL_ESTATE_BUTTON],
    [ASK_MIKE_BUTTON],
]

# Demo nudge: resize_keyboard=False → taller reply buttons in most clients.
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=False)


def telegram_id(update: Update) -> str:
    return str(update.effective_user.id)


def get_location_name(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "accept-language": "ru"
        }
        headers = {
            "User-Agent": "MikePhuketAI/1.0"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        address = data.get("address", {})

        area = (
            address.get("suburb")
            or address.get("village")
            or address.get("town")
            or address.get("city")
            or address.get("municipality")
            or address.get("county")
            or "район не определён"
        )

        full_address = data.get("display_name", "адрес не определён")

        return area, full_address

    except Exception as e:
        return "район не определён", f"Ошибка определения адреса: {e}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    source = context.args[0] if context.args else "unknown"
    await store.start_conversation(CHANNEL, telegram_id(update), source=source)

    await update.message.reply_text(
        "Привет! Я Майк — AI-гид по Пхукету.\n\n"
        "Могу помочь с пляжами, ресторанами, маршрутами, районами и недвижимостью.",
        reply_markup=reply_markup
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Chat ID:\n{update.effective_chat.id}"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await store.reset_conversation(CHANNEL, telegram_id(update))

    await update.message.reply_text(
        "Память диалога очищена. Начинаем заново 👌",
        reply_markup=reply_markup
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location

    if not location:
        await update.message.reply_text(
            "Не получил геопозицию. Нажми «Что рядом» и разреши отправку локации.",
            reply_markup=reply_markup
        )
        return

    lat = location.latitude
    lon = location.longitude

    area, full_address = get_location_name(lat, lon)

    user_text = f"""
Пользователь отправил геолокацию.

Координаты:
Широта: {lat}
Долгота: {lon}

Определённый район:
{area}

Адрес по карте:
{full_address}

Подскажи, что находится рядом.
Не угадывай район сам.
Используй только определённый район и адрес.
Дай короткий ответ: где человек находится, что рядом посмотреть, где поесть и куда съездить.
"""

    metadata = {
        "message_type": "location",
        "lat": lat,
        "lon": lon,
        "area": area,
        "full_address": full_address,
    }
    await ask_openai(update, context, user_text, metadata=metadata)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text == MONEY_EXCHANGE_BUTTON:
        await handle_money_exchange(update)
        return
    await ask_openai(update, context, user_text)


async def handle_money_exchange(update: Update):
    partners = await store.list_active_partners(MONEY_EXCHANGE_TYPE)
    intro_or_fallback, cards = build_partner_cards(partners)

    await update.message.reply_text(intro_or_fallback, reply_markup=reply_markup)
    if not cards:
        return

    for card in cards:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(card.button_text, url=card.referral_url)]]
        )
        logo = resolve_logo_path(card.logo_path)
        if logo is not None:
            with logo.open("rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=card.caption_html,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
        else:
            await update.message.reply_text(
                card.caption_html,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )


async def ask_openai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_text: str,
    *,
    metadata: dict | None = None,
):
    tid = telegram_id(update)

    await store.append_message(
        CHANNEL,
        tid,
        role="user",
        content=user_text,
        metadata=metadata,
    )

    history = await store.get_ai_context(CHANNEL, tid)
    messages = [{"role": "system", "content": MIKE_PROMPT}] + history

    await update.message.reply_text("Думаю как местный 😎")

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=messages
        )

        answer = response.output_text

        lead_ready = "ЗАЯВКА_ГОТОВА" in answer
        answer = answer.replace("ЗАЯВКА_ГОТОВА", "").strip()

        await store.append_message(CHANNEL, tid, role="assistant", content=answer)

        if lead_ready:
            lead = await store.create_lead(
                CHANNEL,
                tid,
                snapshot=await build_lead_snapshot(update),
            )
            if lead and lead.created:
                await send_lead_to_admin(update, context, lead.source)

    except Exception as e:
        answer = f"Ошибка OpenAI:\n{e}"

    await update.message.reply_text(answer, reply_markup=reply_markup)


async def build_lead_snapshot(update: Update) -> dict:
    tid = telegram_id(update)
    user = update.effective_user
    history = await store.get_ai_context(CHANNEL, tid, limit=16)
    username = f"@{user.username}" if user.username else None

    return {
        "telegram_id": tid,
        "telegram_username": username,
        "telegram_first_name": user.first_name,
        "dialogue": history,
    }


async def send_lead_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, source: str):
    if not ADMIN_CHAT_ID:
        return

    user = update.effective_user
    tid = telegram_id(update)
    history = await store.get_ai_context(CHANNEL, tid, limit=16)

    dialogue = ""
    for message in history:
        role = "Клиент" if message["role"] == "user" else "Майк"
        dialogue += f"{role}: {message['content']}\n\n"

    username = f"@{user.username}" if user.username else "не указан"

    lead_text = (
        "🏠 Новая заявка на недвижимость\n\n"
        f"Источник: {source}\n\n"
        f"Имя в Telegram: {user.first_name or 'не указано'}\n"
        f"Username: {username}\n"
        f"Telegram ID: {tid}\n\n"
        "Диалог:\n"
        f"{dialogue}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=lead_text
    )


async def main():
    global store

    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: не найден TELEGRAM_BOT_TOKEN в файле .env")
        return

    if not OPENAI_API_KEY:
        print("Ошибка: не найден OPENAI_API_KEY в файле .env")
        return

    if not DATABASE_URL:
        print("Ошибка: не найден DATABASE_URL в файле .env")
        return

    store = await SessionStore.create(DATABASE_URL)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("myid", myid))

    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Mike Phuket AI запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("Бот работает. Не закрывай это окно.")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await store.close()


if __name__ == "__main__":
    asyncio.run(main())
