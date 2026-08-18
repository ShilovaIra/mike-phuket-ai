from tgtrack import TgTrack

API_KEY = "test-key"
WEBHOOK_URL = f"https://bot-api.tgtrack.ru/v1/{API_KEY}/on_telegram_webhook"

START_UPDATE = {
    "update_id": 1,
    "message": {
        "message_id": 1,
        "date": 1,
        "chat": {"id": 1, "type": "private"},
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
        "text": "/start",
        "entities": [{"offset": 0, "length": 6, "type": "bot_command"}],
    },
}

KICKED_UPDATE = {
    "update_id": 2,
    "my_chat_member": {
        "chat": {"id": 1, "type": "private"},
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
        "date": 1,
        "old_chat_member": {
            "user": {"id": 99, "is_bot": True, "first_name": "Mike"},
            "status": "member",
        },
        "new_chat_member": {
            "user": {"id": 99, "is_bot": True, "first_name": "Mike"},
            "status": "kicked",
        },
    },
}

TEXT_UPDATE = {
    "update_id": 3,
    "message": {
        "message_id": 2,
        "date": 1,
        "chat": {"id": 1, "type": "private"},
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
        "text": "Привет",
    },
}

MEMBER_UPDATE = {
    "update_id": 4,
    "my_chat_member": {
        "chat": {"id": 1, "type": "private"},
        "from": {"id": 1, "is_bot": False, "first_name": "A"},
        "date": 1,
        "old_chat_member": {
            "user": {"id": 99, "is_bot": True, "first_name": "Mike"},
            "status": "kicked",
        },
        "new_chat_member": {
            "user": {"id": 99, "is_bot": True, "first_name": "Mike"},
            "status": "member",
        },
    },
}


def _recording_post():
    posted = []

    async def post(url, json):
        posted.append((url, json))

    return posted, post


async def test_notify_does_nothing_when_api_key_missing():
    posted, post = _recording_post()

    await TgTrack(None, post=post).notify(START_UPDATE)
    await TgTrack("", post=post).notify(START_UPDATE)
    await TgTrack("   ", post=post).notify(START_UPDATE)

    assert posted == []


async def test_notify_posts_start_update_unchanged():
    posted, post = _recording_post()

    await TgTrack(API_KEY, post=post).notify(START_UPDATE)

    assert posted == [(WEBHOOK_URL, START_UPDATE)]


async def test_notify_posts_kicked_update_unchanged():
    posted, post = _recording_post()

    await TgTrack(API_KEY, post=post).notify(KICKED_UPDATE)

    assert posted == [(WEBHOOK_URL, KICKED_UPDATE)]


async def test_notify_ignores_ordinary_text_message():
    posted, post = _recording_post()

    await TgTrack(API_KEY, post=post).notify(TEXT_UPDATE)

    assert posted == []


async def test_notify_ignores_chat_member_becoming_member():
    posted, post = _recording_post()

    await TgTrack(API_KEY, post=post).notify(MEMBER_UPDATE)

    assert posted == []


async def test_notify_does_not_raise_when_post_fails():
    async def post(url, json):
        raise ConnectionError("tgtrack down")

    await TgTrack(API_KEY, post=post).notify(START_UPDATE)
