#!/usr/bin/env bash
# Deploy (or redeploy) this app on the staging Droplet from the staging branch only.
#
# Usage (on the Droplet, from repo root or mike-ai-bot-hkt):
#   ./mike-ai-bot-hkt/scripts/deploy_staging.sh
#
set -euo pipefail

STAGING_BRANCH="staging"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$APP_DIR/.." && pwd)"
ADMIN_WEB_PORT="${ADMIN_WEB_PORT:-8080}"

cd "$REPO_ROOT"

current="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current" != "$STAGING_BRANCH" ]]; then
  echo "Refusing to deploy: current branch is '$current', expected '$STAGING_BRANCH'."
  echo "Run: git fetch origin && git checkout $STAGING_BRANCH"
  exit 1
fi

echo "→ Fetching origin/$STAGING_BRANCH"
git fetch origin "$STAGING_BRANCH"
git pull --ff-only origin "$STAGING_BRANCH"

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from template first:"
  echo "  cp .env.staging.example .env && nano .env"
  exit 1
fi

if ! grep -qE '^ADMIN_JWT_SECRET=.+' .env; then
  echo "Missing ADMIN_JWT_SECRET in .env — admin-api will not start."
  echo "Add a long random value, e.g.:"
  echo "  ADMIN_JWT_SECRET=\$(openssl rand -hex 32)"
  exit 1
fi

echo "→ Building and starting containers (bot, admin-api, admin-web, db)"
docker compose up -d --build

echo "→ Waiting for admin panel"
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${ADMIN_WEB_PORT}/" >/dev/null; then
    break
  fi
  sleep 2
done

echo "→ Health checks"
curl -fsS "http://127.0.0.1:${ADMIN_WEB_PORT}/" >/dev/null
# Unauthenticated stats must reject (proves API proxy is up).
stats_code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${ADMIN_WEB_PORT}/api/stats" || true)"
if [[ "$stats_code" != "401" ]]; then
  echo "Expected /api/stats → 401, got ${stats_code}"
  docker compose logs --tail=80 admin-api admin-web
  exit 1
fi

echo "→ Branch: $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
docker compose ps
echo "Done."
echo "  Bot logs:        docker compose logs -f bot"
echo "  Admin API logs:  docker compose logs -f admin-api"
echo "  Admin UI:        http://<droplet-ip>:${ADMIN_WEB_PORT}/"
echo "  Create admin:    docker compose run --rm bot python scripts/create_admin_user.py --email you@example.com --password '…'"
