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

Push or merge to `staging` auto-deploys via GitHub Actions (SSH → `deploy_staging.sh`). Manual fallback:

```bash
cp .env.staging.example .env   # fill in staging tokens
./scripts/deploy_staging.sh    # pulls staging + rebuilds (refuses other branches)
```

Full setup guide (including domain, CI secrets, firewall): **[docs/STAGING.md](docs/STAGING.md)**

Partner Dashboard (staging): `https://partners-staging.mikephuketai.com/`
Operator admin (staging): `https://admin-staging.mikephuketai.com/`

## Production (Docker + DigitalOcean)

Production runs from the **`main` Git branch only**. Promote by merging `staging` → `main`, then redeploy.

```bash
cp .env.production.example .env   # fill in production tokens
./scripts/deploy_production.sh    # pulls main + rebuilds (refuses other branches)
```

Full setup guide (including domain and firewall): **[docs/PRODUCTION.md](docs/PRODUCTION.md)**

Partner Dashboard (production): `https://partners.mikephuketai.com/`
Operator admin (production): `https://admin.mikephuketai.com/`
