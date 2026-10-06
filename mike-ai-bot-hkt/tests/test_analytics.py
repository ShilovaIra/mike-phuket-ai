from tests.conftest import requires_db


@requires_db
async def test_bot_and_mini_app_count_as_one_user(store):
    await store.start_conversation("telegram", "42", source="instagram")
    await store.ensure_identity("tma", "42", source="tma")
    await store.record_inbound("telegram", "42")
    await store.record_inbound("tma", "42")

    stats = await store.get_bot_stats()

    assert stats.total_users == 1
    assert stats.new_users_today == 1
    assert stats.new_users_7d == 1
    assert stats.active_today == 1
    assert stats.users_by_first_source == {"instagram": 1}


@requires_db
async def test_record_topic_event_counts_unique_users_and_taps_all_time(store):
    await store.start_conversation("telegram", "800", source="unknown")
    await store.record_topic_event("telegram", "800", topic="beaches")
    await store.record_topic_event("telegram", "800", topic="beaches")

    await store.start_conversation("telegram", "801", source="unknown")
    await store.record_topic_event("telegram", "801", topic="beaches")

    stats = await store.get_bot_stats()

    beaches = stats.topics_all_time["beaches"]
    assert beaches.unique_users == 2
    assert beaches.taps == 3


@requires_db
async def test_get_bot_stats_excludes_topic_events_older_than_7_days(store):
    await store.start_conversation("telegram", "802", source="unknown")
    await store.record_topic_event("telegram", "802", topic="beaches")

    async with store._pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE topic_events
            SET created_at = now() - interval '10 days'
            WHERE topic = 'beaches'
            """
        )

    await store.start_conversation("telegram", "803", source="unknown")
    await store.record_topic_event("telegram", "803", topic="money_exchange")

    stats = await store.get_bot_stats()

    assert "beaches" not in stats.topics_7d
    assert stats.topics_7d["money_exchange"].unique_users == 1
    assert stats.topics_all_time["beaches"].unique_users == 1
    assert stats.topics_all_time["money_exchange"].unique_users == 1


@requires_db
async def test_get_bot_stats_counts_new_users_today_and_last_7_days(store):
    await store.start_conversation("telegram", "804", source="unknown")
    await store.start_conversation("telegram", "805", source="unknown")

    stats = await store.get_bot_stats()

    assert stats.new_users_today >= 2
    assert stats.new_users_7d >= 2


@requires_db
async def test_get_bot_stats_counts_leads_all_time_and_last_7_days(store):
    await store.start_conversation("telegram", "806", source="unknown")
    await store.create_lead("telegram", "806", snapshot={"name": "Anna"})

    stats = await store.get_bot_stats()

    assert stats.leads_all_time >= 1
    assert stats.leads_7d >= 1
