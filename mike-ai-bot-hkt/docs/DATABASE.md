# Database architecture

Mike Phuket AI persists chat state in **managed PostgreSQL** instead of in-memory `user_data`. This document describes the schema, runtime behavior, and cutover from the RAM export.

## Overview

| Concern | Approach |
|---|---|
| Users | Channel-agnostic `users` + `identities` |
| Conversations | Multiple per user; exactly one `active` at a time |
| Messages | One row per message (`role`, `content`, `metadata` JSONB) |
| AI context | Query last 20 messages per turn |
| Leads | First-class `leads` table, one per conversation |
| Attribution | `conversations.source` per thread; `users.first_source` on first `/start` |
| `/reset` source | New conversation with `source = unknown` |
| Lead source | `conversation.source`, fallback to `users.first_source` |
| Webhooks | `webhook_events` outbox (worker not implemented yet) |

## Entity diagram

```
users
  └── identities (channel, external_id)   e.g. telegram / 417936797
  └── conversations (source, status, started_at, ended_at)
        └── messages (role, content, metadata, created_at)
        └── leads (source, snapshot)    max one per conversation

webhook_events (event_type, payload_ref, payload, status, …)
```

## Public interface

All persistence goes through `SessionStore` in `db/store.py`:

| Method | Use |
|---|---|
| `start_conversation(channel, external_id, source=…)` | `/start` — closes active thread, opens new one |
| `reset_conversation(channel, external_id)` | `/reset` — new thread with `source = unknown` |
| `get_active_conversation(…)` | Read current thread |
| `append_message(…)` | Store user/assistant turn |
| `get_ai_context(…, limit=20)` | Build OpenAI message list |
| `create_lead(…, snapshot=…)` | Idempotent lead + outbox row |
| `has_lead(…)` | Check if active conversation already has a lead |

Tests exercise **only** this interface (see `tests/`).

## Schema

SQL lives in `db/schema.sql`. Applied automatically on `SessionStore.create()` and in tests.

Indexes that matter for the hot path:

- `one_active_conversation_per_user` — partial unique on `user_id WHERE status = 'active'`
- `messages_conversation_created` — `(conversation_id, created_at DESC, id DESC)`

## Environment variables

```env
DATABASE_URL=postgresql://user:pass@host:5432/mike
TEST_DATABASE_URL=postgresql://user:pass@host:5432/mike_test   # optional, for pytest
```

Also required for the bot: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `GOOGLE_PLACES_API_KEY`,
`ADMIN_CHAT_ID` (optional).

Without `GOOGLE_PLACES_API_KEY` the bot still runs, but Mike answers about places
from model memory instead of looking them up, so he can name a place that does not
exist. See "Place search" in the [README](../README.md).

## Running tests

```bash
cd mike-ai-bot-hkt
pip install -r requirements.txt
export TEST_DATABASE_URL=postgresql://localhost/mike_test
pytest
```

Tests skip if no database URL is set. Use a **separate** test database; the test fixture truncates all tables.

## Cutover from RAM export

1. Provision managed Postgres (Neon, Supabase, Railway, etc.) near your bot VPS.
2. Set `DATABASE_URL` in `.env`.
3. Import existing sessions:

   ```bash
   cd mike-ai-bot-hkt
   python scripts/import_sessions.py ../mike_sessions_export.json
   ```

4. Verify counts (sessions with history, messages, leads).
5. Deploy bot with `DATABASE_URL`; stop the old in-memory bot.

Import behavior:

- Skips sessions with empty `history`.
- Each imported session → one **active** conversation + message rows.
- `lead_sent: true` → `leads` row + `webhook_events` row.

## Webhook outbox (v1 schema, worker later)

On `create_lead`, a row is inserted into `webhook_events`:

- `event_type = 'lead.created'`
- `payload_ref` = lead UUID
- `status = 'pending'`

A future worker polls `WHERE status = 'pending'`, POSTs to CRM, sets `sent` or retries with `attempts` / `next_retry_at`.

## Bot flow (per message)

```
append_message(user)
get_ai_context(limit=20)
OpenAI
append_message(assistant)
if lead trigger → create_lead → notify admin Telegram
```

Location messages store coordinates in `messages.metadata`; `content` remains the expanded text sent to the model.

## Files

| Path | Purpose |
|---|---|
| `db/schema.sql` | DDL |
| `db/store.py` | `SessionStore` public API |
| `db/migrate.py` | Apply schema |
| `db/import_sessions.py` | Import logic |
| `scripts/import_sessions.py` | CLI wrapper |
| `tests/test_session_store.py` | Store behavior tests |
| `tests/test_import_sessions.py` | Import behavior tests |
