# Mike Phuket AI Bot

Telegram bot — AI guide for Phuket. Persists sessions in PostgreSQL.

## Setup

```bash
cd mike-ai-bot-hkt
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in tokens and DATABASE_URL
```

## Run

```bash
python bot.py
```

## Database

See **[docs/DATABASE.md](docs/DATABASE.md)** for schema, cutover from RAM export, and tests.

Quick cutover:

```bash
python scripts/import_sessions.py ../mike_sessions_export.json
```

## Tests

```bash
export TEST_DATABASE_URL=postgresql://localhost/mike_test
pytest
```
