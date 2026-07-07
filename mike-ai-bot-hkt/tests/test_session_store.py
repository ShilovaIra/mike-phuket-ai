from tests.conftest import requires_db


@requires_db
async def test_new_telegram_user_gets_active_conversation_on_start(store):
    ctx = await store.start_conversation("telegram", "417936797", source="instagram")

    assert ctx.source == "instagram"
    assert ctx.first_source == "instagram"

    active = await store.get_active_conversation("telegram", "417936797")
    assert active is not None
    assert active.conversation_id == ctx.conversation_id
    assert active.source == "instagram"


@requires_db
async def test_append_messages_returns_ai_context_in_chronological_order(store):
    await store.start_conversation("telegram", "100", source="unknown")
    await store.append_message("telegram", "100", role="user", content="Привет")
    await store.append_message("telegram", "100", role="assistant", content="Здравствуй")

    context = await store.get_ai_context("telegram", "100")

    assert context == [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Здравствуй"},
    ]


@requires_db
async def test_get_ai_context_returns_only_last_twenty_messages(store):
    await store.start_conversation("telegram", "101", source="unknown")
    for i in range(25):
        role = "user" if i % 2 == 0 else "assistant"
        await store.append_message("telegram", "101", role=role, content=f"msg-{i}")

    context = await store.get_ai_context("telegram", "101", limit=20)

    assert len(context) == 20
    assert context[0]["content"] == "msg-5"
    assert context[-1]["content"] == "msg-24"


@requires_db
async def test_reset_starts_new_conversation_with_unknown_source(store):
    first = await store.start_conversation("telegram", "200", source="instagram")
    await store.append_message("telegram", "200", role="user", content="old")

    second = await store.reset_conversation("telegram", "200")

    assert second.conversation_id != first.conversation_id
    assert second.source == "unknown"
    assert second.first_source == "instagram"
    assert await store.get_ai_context("telegram", "200") == []


@requires_db
async def test_start_preserves_first_source_for_returning_user(store):
    await store.start_conversation("telegram", "300", source="instagram")
    ctx = await store.start_conversation("telegram", "300", source="facebook")

    assert ctx.source == "facebook"
    assert ctx.first_source == "instagram"


@requires_db
async def test_create_lead_uses_conversation_source_when_set(store):
    await store.start_conversation("telegram", "400", source="facebook")
    lead = await store.create_lead("telegram", "400", snapshot={"name": "Anna"})

    assert lead is not None
    assert lead.created is True
    assert lead.source == "facebook"


@requires_db
async def test_create_lead_falls_back_to_first_source_when_conversation_unknown(store):
    await store.start_conversation("telegram", "401", source="instagram")
    await store.reset_conversation("telegram", "401")

    lead = await store.create_lead("telegram", "401", snapshot={"name": "Boris"})

    assert lead is not None
    assert lead.source == "instagram"


@requires_db
async def test_create_lead_is_idempotent_per_conversation(store):
    await store.start_conversation("telegram", "500", source="instagram")

    first = await store.create_lead("telegram", "500", snapshot={"step": 1})
    second = await store.create_lead("telegram", "500", snapshot={"step": 2})

    assert first is not None and first.created is True
    assert first.webhook_enqueued is True
    assert second is not None and second.created is False
    assert second.id == first.id
    assert await store.has_lead("telegram", "500") is True


@requires_db
async def test_first_source_set_on_first_start_after_message_without_start(store):
    await store.append_message("telegram", "600", role="user", content="hi")
    ctx = await store.start_conversation("telegram", "600", source="instagram")

    assert ctx.first_source == "instagram"
