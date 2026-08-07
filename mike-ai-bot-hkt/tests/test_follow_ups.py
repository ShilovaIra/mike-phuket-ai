from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tests.conftest import requires_db

MONEY_EXCHANGE_FOLLOW_UP = "Как прошел обмен? Нужна ли ещё помощь? 😊"
EXCURSIONS_FOLLOW_UP = (
    "Как все прошло? Получилось ли воспользоваться рекомендацией? 😊"
)


@requires_db
async def test_partner_tap_schedules_follow_up_due_in_24h(store):
    await store.start_conversation("telegram", "1001", source="unknown")
    tapped_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.schedule_partner_follow_up(
        "telegram", "1001", "money_exchange", at=tapped_at
    )

    due = await store.claim_due_jobs(now=tapped_at + timedelta(hours=24), limit=10)

    assert len(due) == 1
    job = due[0]
    assert job.kind == "partner_topic"
    assert job.topic == "money_exchange"
    assert job.message_text == MONEY_EXCHANGE_FOLLOW_UP
    assert job.channel == "telegram"
    assert job.external_id == "1001"


@requires_db
async def test_newer_partner_tap_replaces_pending_follow_up(store):
    await store.start_conversation("telegram", "1002", source="unknown")
    first_tap = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    second_tap = first_tap + timedelta(hours=2)

    await store.schedule_partner_follow_up(
        "telegram", "1002", "money_exchange", at=first_tap
    )
    await store.schedule_partner_follow_up(
        "telegram", "1002", "excursions", at=second_tap
    )

    early = await store.claim_due_jobs(now=first_tap + timedelta(hours=24), limit=10)
    assert early == []

    due = await store.claim_due_jobs(now=second_tap + timedelta(hours=24), limit=10)
    assert len(due) == 1
    assert due[0].topic == "excursions"
    assert due[0].message_text == EXCURSIONS_FOLLOW_UP


@requires_db
async def test_non_partner_inbound_cancels_pending_partner_follow_up(store):
    await store.start_conversation("telegram", "1003", source="unknown")
    tapped_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.schedule_partner_follow_up(
        "telegram", "1003", "money_exchange", at=tapped_at
    )
    await store.record_inbound(
        "telegram", "1003", at=tapped_at + timedelta(hours=1)
    )

    due = await store.claim_due_jobs(now=tapped_at + timedelta(hours=24), limit=10)
    assert due == []


@requires_db
async def test_empty_follow_up_text_does_not_schedule_partner_job(store):
    await store.start_conversation("telegram", "1004", source="unknown")
    tapped_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.schedule_partner_follow_up(
        "telegram", "1004", "vehicle_rental", at=tapped_at
    )

    due = await store.claim_due_jobs(now=tapped_at + timedelta(hours=24), limit=10)
    assert due == []


@requires_db
async def test_partner_follow_up_cooldown_blocks_reschedule_for_7_days(store):
    await store.start_conversation("telegram", "1005", source="unknown")
    first_tap = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.schedule_partner_follow_up(
        "telegram", "1005", "money_exchange", at=first_tap
    )
    due = await store.claim_due_jobs(now=first_tap + timedelta(hours=24), limit=10)
    assert len(due) == 1
    await store.mark_job_sent(
        due[0].id,
        message_text=due[0].message_text,
        at=first_tap + timedelta(hours=24),
    )

    second_tap = first_tap + timedelta(days=3)
    await store.schedule_partner_follow_up(
        "telegram", "1005", "excursions", at=second_tap
    )
    assert await store.claim_due_jobs(now=second_tap + timedelta(hours=24), limit=10) == []

    after_cooldown = first_tap + timedelta(days=7, hours=25)
    await store.schedule_partner_follow_up(
        "telegram", "1005", "excursions", at=after_cooldown
    )
    due_again = await store.claim_due_jobs(
        now=after_cooldown + timedelta(hours=24), limit=10
    )
    assert len(due_again) == 1
    assert due_again[0].topic == "excursions"


@requires_db
async def test_inbound_schedules_win_back_due_in_7_days(store):
    from db.store import WIN_BACK_TEXT

    await store.start_conversation("telegram", "2001", source="unknown")
    inbound_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.record_inbound("telegram", "2001", at=inbound_at)

    early = await store.claim_due_jobs(now=inbound_at + timedelta(days=6), limit=10)
    assert early == []

    due = await store.claim_due_jobs(now=inbound_at + timedelta(days=7), limit=10)
    assert len(due) == 1
    assert due[0].kind == "win_back"
    assert due[0].message_text == WIN_BACK_TEXT
    assert due[0].external_id == "2001"


@requires_db
async def test_second_inbound_reschedules_win_back(store):
    await store.start_conversation("telegram", "2002", source="unknown")
    first = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    second = first + timedelta(days=2)

    await store.record_inbound("telegram", "2002", at=first)
    await store.record_inbound("telegram", "2002", at=second)

    assert await store.claim_due_jobs(now=first + timedelta(days=7), limit=10) == []
    due = await store.claim_due_jobs(now=second + timedelta(days=7), limit=10)
    assert len(due) == 1
    assert due[0].kind == "win_back"


@requires_db
async def test_win_back_sends_at_most_once_per_user(store):
    await store.start_conversation("telegram", "2003", source="unknown")
    first = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.record_inbound("telegram", "2003", at=first)
    due = await store.claim_due_jobs(now=first + timedelta(days=7), limit=10)
    assert len(due) == 1
    await store.mark_job_sent(
        due[0].id, message_text=due[0].message_text, at=first + timedelta(days=7)
    )

    later = first + timedelta(days=30)
    await store.record_inbound("telegram", "2003", at=later)
    assert await store.claim_due_jobs(now=later + timedelta(days=7), limit=10) == []


@requires_db
async def test_assistant_messages_do_not_reschedule_win_back(store):
    await store.start_conversation("telegram", "2004", source="unknown")
    inbound_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.record_inbound("telegram", "2004", at=inbound_at)
    await store.append_message(
        "telegram",
        "2004",
        role="assistant",
        content="bot ping",
    )

    due = await store.claim_due_jobs(now=inbound_at + timedelta(days=7), limit=10)
    assert len(due) == 1
    assert due[0].kind == "win_back"


@requires_db
async def test_mark_job_sent_persists_assistant_message_in_ai_context(store):
    await store.start_conversation("telegram", "3001", source="unknown")
    tapped_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.schedule_partner_follow_up(
        "telegram", "3001", "money_exchange", at=tapped_at
    )
    due = await store.claim_due_jobs(now=tapped_at + timedelta(hours=24), limit=10)
    await store.mark_job_sent(
        due[0].id,
        message_text=due[0].message_text,
        at=tapped_at + timedelta(hours=24),
    )

    context = await store.get_ai_context("telegram", "3001")
    assert context[-1] == {
        "role": "assistant",
        "content": MONEY_EXCHANGE_FOLLOW_UP,
    }


@requires_db
async def test_permanent_failure_blocks_further_follow_up_scheduling(store):
    await store.start_conversation("telegram", "3002", source="unknown")
    first = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.schedule_partner_follow_up(
        "telegram", "3002", "money_exchange", at=first
    )
    due = await store.claim_due_jobs(now=first + timedelta(hours=24), limit=10)
    assert len(due) == 1
    await store.mark_job_failed(due[0].id, permanent=True)

    later = first + timedelta(days=10)
    await store.schedule_partner_follow_up(
        "telegram", "3002", "money_exchange", at=later
    )
    await store.record_inbound("telegram", "3002", at=later)
    assert await store.claim_due_jobs(now=later + timedelta(days=7), limit=10) == []


@requires_db
async def test_record_inbound_after_start_makes_user_eligible_for_win_back(store):
    await store.start_conversation("telegram", "3003", source="instagram")
    started_at = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    await store.record_inbound("telegram", "3003", at=started_at)

    due = await store.claim_due_jobs(now=started_at + timedelta(days=7), limit=10)
    assert len(due) == 1
    assert due[0].kind == "win_back"
