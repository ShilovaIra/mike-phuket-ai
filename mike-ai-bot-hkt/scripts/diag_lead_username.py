"""Throwaway loop: why lead admin texts show Username: не указан.

1. Replay the exact snapshot/admin-text logic on synthetic Telegram User objects.
2. Call Telegram getChat for a real tourist id from a lead (does Telegram have a username now?).
3. If DATABASE_URL is reachable, count stored lead snapshots with/without telegram_username.

Does not print secrets. Safe to run against staging or production tokens.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from telegram import Chat, Message, Update, User
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SCREENSHOT_TID = int(os.environ.get("DIAG_TELEGRAM_ID", "1779117720"))


def format_admin_username(user: User) -> str:
    # Copied from bot.send_lead_to_admin — keep in lockstep for this diagnosis.
    return f"@{user.username}" if user.username else "не указан"


def format_snapshot_username(user: User) -> str | None:
    return f"@{user.username}" if user.username else None


def make_update(*, tid: int, first_name: str, username: str | None) -> Update:
    user = User(id=tid, first_name=first_name, is_bot=False, username=username)
    chat = Chat(id=tid, type="private", first_name=first_name, username=username)
    message = Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=chat,
        from_user=user,
        text="Купить",
    )
    return Update(update_id=1, message=message)


def redact_db_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "?"
    db = (parsed.path or "/").lstrip("/") or "?"
    return f"{parsed.scheme}://{parsed.username or ''}:***@{host}:{parsed.port or ''}/{db}"


def run_synthetic_loop() -> None:
    missing = make_update(tid=SCREENSHOT_TID, first_name="Василь", username=None)
    present = make_update(tid=SCREENSHOT_TID, first_name="Василь", username="vasil_phuket")

    assert missing.effective_user is not None
    assert present.effective_user is not None

    missing_text = format_admin_username(missing.effective_user)
    present_text = format_admin_username(present.effective_user)
    missing_snap = format_snapshot_username(missing.effective_user)
    present_snap = format_snapshot_username(present.effective_user)

    print("=== synthetic Update replay ===")
    print(f"no username -> admin={missing_text!r} snapshot={missing_snap!r}")
    print(f"has username -> admin={present_text!r} snapshot={present_snap!r}")
    if missing_text != "не указан" or present_text != "@vasil_phuket":
        raise SystemExit("FAIL: formatting does not match bot.py")
    print("PASS: missing username becomes 'не указан'; present username is kept")


async def telegram_get_chat(token: str, chat_id: int) -> dict:
    url = f"https://api.telegram.org/bot{token}/getChat"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, data={"chat_id": chat_id})
        return response.json()


async def telegram_get_me(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getMe"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url)
        return response.json()


async def run_live_telegram_loop() -> None:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    print("\n=== live Telegram getChat ===")
    if not token:
        print("SKIP: TELEGRAM_BOT_TOKEN missing")
        return

    me = await telegram_get_me(token)
    if not me.get("ok"):
        print(f"FAIL: getMe rejected token: {me}")
        return
    bot_username = (me.get("result") or {}).get("username")
    print(f"bot=@{bot_username}  target_id={SCREENSHOT_TID}")

    payload = await telegram_get_chat(token, SCREENSHOT_TID)
    if not payload.get("ok"):
        print(f"getChat not ok: {payload.get('description') or payload}")
        print("INTERPRET: this bot has no chat with that user (wrong env token), not proof of username.")
        return

    chat = payload["result"]
    keys = sorted(chat.keys())
    has_username = bool(chat.get("username"))
    print(f"chat_keys={keys}")
    print(f"type={chat.get('type')} first_name={chat.get('first_name')!r} has_username={has_username}")
    if has_username:
        print(f"USERNAME PRESENT NOW: @{chat['username']}")
        print("INTERPRET: Telegram knows a username for this id. Lead text dropped it (bug).")
    else:
        print("USERNAME ABSENT NOW")
        print("INTERPRET: Telegram has no public @username for this user. Not a parse bug.")


async def run_db_loop() -> None:
    print("\n=== stored lead snapshots ===")
    url = os.getenv("DATABASE_URL")
    if not url:
        print("SKIP: DATABASE_URL missing")
        return
    print(f"db={redact_db_url(url)}")
    try:
        import asyncpg
    except ImportError:
        print("SKIP: asyncpg not installed")
        return
    try:
        conn = await asyncpg.connect(url, timeout=5)
    except Exception as exc:
        print(f"SKIP: cannot connect ({type(exc).__name__})")
        return
    try:
        total = await conn.fetchval("SELECT count(*) FROM leads")
        with_username = await conn.fetchval(
            """
            SELECT count(*) FROM leads
            WHERE coalesce(snapshot->>'telegram_username', '') <> ''
            """
        )
        without = await conn.fetchval(
            """
            SELECT count(*) FROM leads
            WHERE coalesce(snapshot->>'telegram_username', '') = ''
            """
        )
        print(f"leads total={total} with_username={with_username} without_username={without}")
        sample = await conn.fetch(
            """
            SELECT created_at,
                   snapshot->>'telegram_id' AS tid,
                   snapshot->>'telegram_username' AS username,
                   snapshot->>'telegram_first_name' AS first_name
            FROM leads
            ORDER BY created_at DESC
            LIMIT 15
            """
        )
        for row in sample:
            flag = "HAS" if row["username"] else "MISSING"
            print(
                f"  {flag} {row['created_at']} id={row['tid']} "
                f"name={row['first_name']!r} username={row['username']!r}"
            )
        target = await conn.fetchrow(
            """
            SELECT created_at, snapshot
            FROM leads
            WHERE snapshot->>'telegram_id' = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            str(SCREENSHOT_TID),
        )
        if target:
            snap = target["snapshot"]
            print(
                f"screenshot id row: created={target['created_at']} "
                f"username={snap.get('telegram_username')!r} "
                f"first_name={snap.get('telegram_first_name')!r}"
            )
        else:
            print(f"screenshot id {SCREENSHOT_TID} not in this database")
    finally:
        await conn.close()


async def main() -> None:
    run_synthetic_loop()
    await run_live_telegram_loop()
    await run_db_loop()


if __name__ == "__main__":
    # Keep a cheap grep-able prefix if we add logs later.
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
