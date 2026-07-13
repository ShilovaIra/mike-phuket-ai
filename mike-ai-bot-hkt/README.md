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

## Staging (Docker + DigitalOcean)

Staging runs from the **`staging` Git branch only**.

```bash
cp .env.staging.example .env   # fill in staging tokens
./scripts/deploy_staging.sh    # pulls staging + rebuilds (refuses other branches)
```

Full setup guide: **[docs/STAGING.md](docs/STAGING.md)**

## Production (Docker + DigitalOcean)

Production runs from the **`main` Git branch only**. Promote by merging `staging` → `main`, then redeploy.

```bash
cp .env.production.example .env   # fill in production tokens
./scripts/deploy_production.sh    # pulls main + rebuilds (refuses other branches)
```

Full setup guide: **[docs/PRODUCTION.md](docs/PRODUCTION.md)**
