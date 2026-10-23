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

## Place search

Mike looks restaurants, cafes and beaches up in the Google Places API instead of
naming them from model memory, and quotes back the map link Google returns for
that place. Set `GOOGLE_PLACES_API_KEY` to a Google Cloud key with **Places API
(New)** enabled and billing on.

Leaving it empty is supported but degraded: Mike answers from model memory, so he
may name a place that does not exist. The link is still built in a format that
opens (`maps/search/?api=1&query=…`); Mike never sends shortened links, because
those are guessed and `goo.gl` has been retired.

To check the live behaviour after touching `MIKE_PROMPT`, `places.py` or
`maps_links.py` (this spends OpenAI and Places quota):

```bash
python scripts/diag_maps_links.py --runs 4
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

Production runs from the **`main` Git branch only**. Promote by merging `staging` → `main`. A push does not deploy. Run **Deploy production** by hand from `main` after pytest is green.

On the Droplet, from a `main` checkout, this still pulls and rebuilds. It refuses other branches:

```bash
cp .env.production.example .env   # fill in production tokens
./scripts/deploy_production.sh
```

Full setup guide (including domain, CI secrets, and firewall): **[docs/PRODUCTION.md](docs/PRODUCTION.md)**

Partner Dashboard (production): `https://partners.mikephuketai.com/`
Operator admin (production): `https://admin.mikephuketai.com/`
Mini App (production): `https://app.mikephuketai.com/`
