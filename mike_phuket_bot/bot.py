import os
import asyncio
import requests
from dotenv import load_dotenv
from openai import OpenAI

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

MIKE_PROMPT = """
Ты Майк — дружелюбный AI-гид по Пхукету и помощник Phuket ProMax.

Говори на русском языке коротко, понятно и живо.

Помогай туристам с пляжами, ресторанами, маршрутами, экскурсиями, транспортом, закатами и недвижимостью.

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
    ["🍜 Где поесть", "🏖 Пляжи"],
    [KeyboardButton("📍 Что рядом", request_location=True), "🌅 Закат"],
    ["🏠 Недвижимость"],
    ["💬 Спросить Майка"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


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
    source = "unknown"

    if context.args:
        source = context.args[0]

    context.user_data["source"] = source
    context.user_data["history"] = []
    context.user_data["lead_sent"] = False

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
    context.user_data["history"] = []
    context.user_data["lead_sent"] = False

    await update.message.reply_text(
        "Память диалога очищена. Начинаем заново 👌",
        reply_markup=reply_markup
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location

    if not location:
        await update.message.reply_text(
            "Не получил геопозицию. Нажми 📍 Что рядом и разреши отправку локации.",
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

    await ask_openai(update, context, user_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await ask_openai(update, context, user_text)


async def ask_openai(update: Update, context: ContextTypes.DEFAULT_TYPE, user_text: str):
    if "history" not in context.user_data:
        context.user_data["history"] = []

    if "lead_sent" not in context.user_data:
        context.user_data["lead_sent"] = False

    if "source" not in context.user_data:
        context.user_data["source"] = "unknown"

    history = context.user_data["history"]

    history.append({
        "role": "user",
        "content": user_text
    })

    messages = [
        {"role": "system", "content": MIKE_PROMPT}
    ] + history

    await update.message.reply_text("Думаю как местный 😎")

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=messages
        )

        answer = response.output_text

        lead_ready = "ЗАЯВКА_ГОТОВА" in answer
        answer = answer.replace("ЗАЯВКА_ГОТОВА", "").strip()

        history.append({
            "role": "assistant",
            "content": answer
        })

        if len(history) > 20:
            history = history[-20:]

        context.user_data["history"] = history

        if lead_ready and not context.user_data["lead_sent"]:
            await send_lead_to_admin(update, context)
            context.user_data["lead_sent"] = True

    except Exception as e:
        answer = f"Ошибка OpenAI:\n{e}"

    await update.message.reply_text(answer, reply_markup=reply_markup)


async def send_lead_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_CHAT_ID:
        return

    user = update.effective_user
    history = context.user_data.get("history", [])
    source = context.user_data.get("source", "unknown")

    dialogue = ""

    for message in history[-16:]:
        role = "Клиент" if message["role"] == "user" else "Майк"
        dialogue += f"{role}: {message['content']}\n\n"

    username = f"@{user.username}" if user.username else "не указан"

    lead_text = (
        "🏠 Новая заявка на недвижимость\n\n"
        f"Источник: {source}\n\n"
        f"Имя в Telegram: {user.first_name or 'не указано'}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n\n"
        "Диалог:\n"
        f"{dialogue}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=lead_text
    )


async def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: не найден TELEGRAM_BOT_TOKEN в файле .env")
        return

    if not OPENAI_API_KEY:
        print("Ошибка: не найден OPENAI_API_KEY в файле .env")
        return

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

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
