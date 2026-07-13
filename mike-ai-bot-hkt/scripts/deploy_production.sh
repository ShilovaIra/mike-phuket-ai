#!/usr/bin/env bash
# Deploy (or redeploy) this app on the production Droplet from the main branch only.
#
# Usage (on the Droplet, from repo root or mike-ai-bot-hkt):
#   ./mike-ai-bot-hkt/scripts/deploy_production.sh
#
set -euo pipefail

PRODUCTION_BRANCH="main"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$APP_DIR/.." && pwd)"

cd "$REPO_ROOT"

current="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current" != "$PRODUCTION_BRANCH" ]]; then
  echo "Refusing to deploy: current branch is '$current', expected '$PRODUCTION_BRANCH'."
  echo "Run: git fetch origin && git checkout $PRODUCTION_BRANCH"
  exit 1
fi

echo "→ Fetching origin/$PRODUCTION_BRANCH"
git fetch origin "$PRODUCTION_BRANCH"
git pull --ff-only origin "$PRODUCTION_BRANCH"

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from template first:"
  echo "  cp .env.production.example .env && nano .env"
  exit 1
fi

echo "→ Building and starting containers"
docker compose up -d --build

echo "→ Branch: $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
docker compose ps
echo "Done. Logs: docker compose logs -f bot"
