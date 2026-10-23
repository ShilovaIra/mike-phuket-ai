from __future__ import annotations

import os
import asyncio
import json
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
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import BadRequest, Forbidden, TelegramError

from db.store import SessionStore
from db.url import resolve_database_url
from knowledge_base import format_for_prompt
from partner_dashboard.offers import wrap_partners_for_channel_user
from partners import (
    PartnerCard,
    PartnerType,
    build_partner_cards,
    is_bundled_logo,
    resolve_logo_path,
)
from storage import AssetStorage
from buttons import (
    BUTTON_TO_TOPIC,
    NEARBY_BUTTON,
    build_reply_keyboard_rows,
)
import lead_contact
from lead_contact import public_telegram_username
from maps_links import sanitize_map_links
from places import PlacesClient
from stats_report import format_bot_stats
from topics import TOPIC_NEARBY
from tgtrack import TgTrack

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DATABASE_URL = resolve_database_url()
FOLLOW_UP_POLL_SECONDS = 60


def parse_admin_ids(raw: str | None) -> frozenset[str]:
    """Comma-separated Telegram user/chat ids, e.g. '111,222'."""
    if not raw:
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


ADMIN_IDS = parse_admin_ids(os.getenv("ADMIN_CHAT_ID"))
tgtrack = TgTrack(os.getenv("TGTRACK_API_KEY"))

CHANNEL = "telegram"

client = OpenAI(api_key=OPENAI_API_KEY or "not-set")
store: SessionStore | None = None
places: PlacesClient | None = None
storage = AssetStorage.from_env(os.environ)

FIND_PLACES_TOOL = {
    "type": "function",
    "name": "find_places",
    "description": (
        "Search real places on Phuket (restaurants, cafes, beaches, bars, shops) "
        "in Google Maps. Call this before naming a specific place or giving any "
        "map link. Returns real names, addresses and working map links."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "What to look for, in English, with the area if known, "
                    "e.g. 'thai seafood restaurant Rawai' or 'Surf Point cafe'."
                ),
            },
            "open_now": {
                "type": "boolean",
                "description": (
                    "Keep only places open right now. Set true ONLY if the user "
                    "explicitly asked for somewhere open now; it hides good "
                    "places that happen to be closed."
                ),
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}
MAX_TOOL_ROUNDS = 3

MIKE_PROMPT = """
Ты Майк — дружелюбный AI-гид по Пхукету и помощник Phuket ProMax.

Говори на русском языке коротко, понятно и живо.

Помогай туристам с пляжами, ресторанами, маршрутами, экскурсиями, транспортом и арендой или покупкой жилья.

Если чат начинается с отеля или работы, не задавай ни одного вопроса.
Весь ответ — только эта фраза:
Беру заявки только на аренду или покупку виллы, квартиры, дома или комнаты.

Если во время аренды или покупки просят отель или работу, скажи эту фразу, затем задай следующий вопрос про жильё.

Если человек просит работу, вакансию, подработку или хочет устроиться — не помогай.
Не спрашивай сферу, опыт или должность.

Той же одной фразой отвечай на отель, хостел, гестхаус, землю, магазин или офис.
Название отеля как ориентир — не запрос отеля: отвечай на сам вопрос.

Заявку собирай только когда человек хочет снять или купить жильё
(вилла, квартира, дом, комната или просто жильё). Срок проживания не важен.
Не спрашивай тип жилья. Для комнаты не спрашивай число спален.
ЗАЯВКА_ГОТОВА пиши только для такой заявки.

Если человек хочет снять или купить жильё, мягко выясняй:
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

Никогда не выдумывай ссылки и никогда не давай сокращённые ссылки
(goo.gl, maps.app.goo.gl, g.page, bit.ly и любые другие короткие адреса).
Ты не можешь знать их и не можешь проверить — такие ссылки не открываются.

Если человек просит ссылку на место в Google Картах, собирай её по шаблону:
https://www.google.com/maps/search/?api=1&query=НАЗВАНИЕ+МЕСТА+Phuket

Название пиши латиницей, пробелы заменяй на +.
Пример: https://www.google.com/maps/search/?api=1&query=Kan+Eang+at+Pier+Phuket

Ссылки присылай обычным текстом, без markdown — квадратные скобки не работают.
"""

# Appended only when place search is configured, otherwise Mike would promise
# a lookup he cannot make.
PLACE_SEARCH_PROMPT = """
У тебя есть поиск реальных мест на Пхукете в Google Картах.

Не называй конкретное заведение по памяти. Когда нужен конкретный ресторан,
кафе, бар, пляж или магазин — сначала найди его поиском и говори только о том,
что вернул поиск.

Ссылку давай ровно ту, что пришла в поле maps_url, символ в символ.
Не сокращай её и не собирай свою.

Если поиск ничего не нашёл, честно скажи, что не нашёл такого места, и предложи
поискать по-другому. Не придумывай замену.

Никогда не упоминай названия инструментов и не спрашивай разрешения на поиск —
просто ищи и отвечай.
"""


def system_prompt(knowledge_base: str = "") -> str:
    prompt = MIKE_PROMPT
    if places is not None:
        prompt += PLACE_SEARCH_PROMPT
    if knowledge_base:
        prompt += "\n" + knowledge_base
    return prompt


async def build_reply_markup() -> ReplyKeyboardMarkup:
    partner_types = await store.list_partner_types()
    keyboard = [
        [
            KeyboardButton(label, request_location=(label == NEARBY_BUTTON))
            for label in row
        ]
        for row in build_reply_keyboard_rows(partner_types)
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=False)


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


def schedule_tgtrack(update: Update) -> None:
    asyncio.create_task(tgtrack.notify(update.to_dict()))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule_tgtrack(update)
    source = context.args[0] if context.args else "unknown"
    tid = telegram_id(update)
    await store.start_conversation(CHANNEL, tid, source=source)
    await store.record_inbound(CHANNEL, tid)

    await update.message.reply_text(
        "Привет! Я Майк — AI-гид по Пхукету.\n\n"
        "Могу помочь с пляжами, ресторанами, маршрутами, районами и недвижимостью.",
        reply_markup=await build_reply_markup(),
    )


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule_tgtrack(update)


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Chat ID:\n{update.effective_chat.id}"
    )


def is_admin(update: Update) -> bool:
    if not ADMIN_IDS:
        return False
    return (
        str(update.effective_user.id) in ADMIN_IDS
        or str(update.effective_chat.id) in ADMIN_IDS
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    bot_stats = await store.get_bot_stats()
    partner_types = await store.list_partner_types()
    await update.message.reply_text(
        format_bot_stats(bot_stats, partner_types=partner_types)
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = telegram_id(update)
    await store.reset_conversation(CHANNEL, tid)
    await store.record_inbound(CHANNEL, tid)

    await update.message.reply_text(
        "Память диалога очищена. Начинаем заново 👌",
        reply_markup=await build_reply_markup(),
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location

    if not location:
        await update.message.reply_text(
            "Не получил геопозицию. Нажми «Что рядом» и разреши отправку локации.",
            reply_markup=await build_reply_markup(),
        )
        return

    tid = telegram_id(update)
    await store.record_inbound(CHANNEL, tid)
    await store.record_topic_event(CHANNEL, tid, topic=TOPIC_NEARBY)

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
    if is_admin(update) and await lead_contact.relay_operator_reply(
        context.bot, update.message
    ):
        return
    if await lead_contact.relay_tourist_reply(context.bot, ADMIN_IDS, update.message):
        await store.record_inbound(CHANNEL, telegram_id(update))
        return

    user_text = update.message.text
    partner_types = await store.list_partner_types()
    partner_by_label = {t.button_label: t for t in partner_types}
    tid = telegram_id(update)

    topic = BUTTON_TO_TOPIC.get(user_text)
    partner_type = partner_by_label.get(user_text)
    if partner_type is not None:
        topic = partner_type.slug
    await store.record_inbound(CHANNEL, tid)
    if topic:
        await store.record_topic_event(CHANNEL, tid, topic=topic)
    if partner_type is not None:
        await store.schedule_partner_follow_up(CHANNEL, tid, partner_type.slug)
        await handle_partner_topic(update, partner_type)
        return
    await ask_openai(update, context, user_text)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = telegram_id(update)
    contact = update.message.contact
    await store.record_inbound(CHANNEL, tid)
    await store.append_message(
        CHANNEL,
        tid,
        role="user",
        content=f"Поделился контактом: {contact.phone_number}",
        metadata={"message_type": "contact", "phone_number": contact.phone_number},
    )
    await lead_contact.send_contact_to_admins(context.bot, ADMIN_IDS, update.message)
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Спасибо! Передал контакт менеджеру, он скоро напишет 👌",
        reply_markup=await build_reply_markup(),
    )


async def handle_partner_topic(update: Update, partner_type: PartnerType):
    partners = await store.list_active_partners(partner_type.slug)
    partners = await wrap_partners_for_channel_user(
        store,
        partners,
        CHANNEL,
        telegram_id(update),
        public_base=os.environ.get("PARTNER_OFFER_BASE_URL", ""),
    )
    intro_or_fallback, cards = build_partner_cards(partners, partner_type)

    await update.message.reply_text(
        intro_or_fallback,
        reply_markup=await build_reply_markup(),
    )
    if not cards:
        return

    for card in cards:
        await send_partner_card(update.message, card)


async def send_partner_card(message, card: PartnerCard) -> None:
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(card.button_text, url=card.referral_url)]]
    )
    if card.logo_path and not is_bundled_logo(card.logo_path) and storage is not None:
        logo_url = storage.public_url(card.logo_path)
        try:
            await message.reply_photo(
                photo=logo_url,
                caption=card.caption_html,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return
        except BadRequest as exc:
            print(f"Partner logo {logo_url} not sent, falling back to text: {exc}")
    else:
        logo = resolve_logo_path(card.logo_path)
        if logo is not None:
            with logo.open("rb") as photo:
                await message.reply_photo(
                    photo=photo,
                    caption=card.caption_html,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            return
    await message.reply_text(
        card.caption_html,
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


async def find_places(arguments: dict) -> dict:
    """Body of the find_places tool. Never raises: the reply must still go out."""
    if places is None:
        return {"places": [], "error": "place search unavailable"}

    results = await places.search(
        str(arguments.get("query") or ""),
        open_now=bool(arguments.get("open_now")),
    )
    return {"places": [place.for_model() for place in results]}


TOOL_IMPLEMENTATIONS = {"find_places": find_places}


async def run_model(messages: list[dict]) -> str:
    """Ask the model, servicing any tool calls it makes along the way."""
    tools = [FIND_PLACES_TOOL] if places is not None else []
    conversation = list(messages)

    for _ in range(MAX_TOOL_ROUNDS):
        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-4.1-mini",
            input=conversation,
            tools=tools,
        )

        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text

        for call in calls:
            implementation = TOOL_IMPLEMENTATIONS.get(call.name)
            try:
                arguments = json.loads(call.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = (
                await implementation(arguments)
                if implementation is not None
                else {"error": f"unknown tool {call.name}"}
            )
            conversation.append(call.model_dump(exclude_none=True))
            conversation.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )

    # Tool budget spent: answer with what the lookups already returned.
    response = await asyncio.to_thread(
        client.responses.create, model="gpt-4.1-mini", input=conversation
    )
    return response.output_text


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
    knowledge = format_for_prompt(await store.list_knowledge_base())
    messages = [{"role": "system", "content": system_prompt(knowledge)}] + history

    await update.message.reply_text("Думаю как местный 😎")

    new_lead = False
    try:
        answer = await run_model(messages)

        lead_ready = "ЗАЯВКА_ГОТОВА" in answer
        answer = sanitize_map_links(answer.replace("ЗАЯВКА_ГОТОВА", "").strip())

        await store.append_message(CHANNEL, tid, role="assistant", content=answer)

        if lead_ready:
            lead = await store.create_lead(
                CHANNEL,
                tid,
                snapshot=await build_lead_snapshot(update),
            )
            if lead and lead.created:
                new_lead = True
                await send_lead_to_admin(update, context, lead.source)

    except Exception as e:
        answer = f"Ошибка OpenAI:\n{e}"

    await update.message.reply_text(answer, reply_markup=await build_reply_markup())
    if new_lead:
        await lead_contact.ask_for_contact_if_unreachable(context.bot, update.effective_user)


async def build_lead_snapshot(update: Update) -> dict:
    tid = telegram_id(update)
    user = update.effective_user
    history = await store.get_ai_context(CHANNEL, tid, limit=16)

    return {
        "telegram_id": tid,
        "telegram_username": public_telegram_username(user),
        "telegram_first_name": user.first_name,
        "dialogue": history,
    }


async def send_lead_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, source: str):
    if not ADMIN_IDS:
        return

    user = update.effective_user
    tid = telegram_id(update)
    history = await store.get_ai_context(CHANNEL, tid, limit=16)

    dialogue = ""
    for message in history:
        role = "Клиент" if message["role"] == "user" else "Майк"
        dialogue += f"{role}: {message['content']}\n\n"

    lead_text = (
        "🏠 Новая заявка на недвижимость\n\n"
        f"Источник: {source}\n\n"
        f"{lead_contact.tourist_identity_lines(user)}\n\n"
        f"{lead_contact.OPERATOR_REPLY_HINT}\n\n"
        "Диалог:\n"
        f"{dialogue}"
    )

    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=lead_text
        )
    await lead_contact.forward_to_admins(context.bot, ADMIN_IDS, update.message)


async def process_due_follow_ups(bot) -> None:
    jobs = await store.claim_due_jobs(limit=20)
    for job in jobs:
        try:
            await bot.send_message(chat_id=int(job.external_id), text=job.message_text)
            await store.mark_job_sent(job.id, message_text=job.message_text)
        except Forbidden as exc:
            await store.mark_job_failed(
                job.id, permanent=True, error=str(exc)
            )
        except (TelegramError, ValueError) as exc:
            await store.mark_job_failed(
                job.id, permanent=False, error=str(exc)
            )


async def main():
    global store, places

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

    if GOOGLE_PLACES_API_KEY:
        places = PlacesClient(GOOGLE_PLACES_API_KEY)
    else:
        print(
            "Внимание: нет GOOGLE_PLACES_API_KEY — Майк будет отвечать "
            "без поиска реальных мест в Google Картах."
        )

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(
        ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Mike Phuket AI запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    print("Бот работает. Не закрывай это окно.")

    try:
        while True:
            try:
                await process_due_follow_ups(app.bot)
            except Exception as exc:
                print(f"Follow-up poll error: {exc}")
            await asyncio.sleep(FOLLOW_UP_POLL_SECONDS)
    finally:
        if places is not None:
            await places.close()
        await store.close()


if __name__ == "__main__":
    asyncio.run(main())
