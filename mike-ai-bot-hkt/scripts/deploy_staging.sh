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

cd "$APP_DIR"

echo "→ Stopping leftover containers"
docker compose stop || true

if [[ "$(id -u)" -eq 0 ]]; then
  if [[ -z "$(swapon --show 2>/dev/null || true)" ]]; then
    echo "→ Adding 1G swap so image builds do not OOM systemd-resolved"
    if [[ ! -f /swapfile ]]; then
      fallocate -l 1G /swapfile
      chmod 600 /swapfile
      mkswap /swapfile
    fi
    swapon /swapfile || true
  fi
  echo "→ Repairing DNS"
  systemctl restart systemd-resolved 2>/dev/null || true
  sleep 2
  if ! getent hosts registry-1.docker.io >/dev/null 2>&1; then
    echo "Docker Hub still does not resolve; writing public nameservers"
    if [[ -L /etc/resolv.conf ]]; then
      rm -f /etc/resolv.conf
    fi
    printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' >/etc/resolv.conf
  fi
fi

cd "$REPO_ROOT"

current="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current" != "$STAGING_BRANCH" ]]; then
  echo "Refusing to deploy: current branch is '$current', expected '$STAGING_BRANCH'."
  echo "Run: git fetch origin && git checkout $STAGING_BRANCH"
  exit 1
fi

if [[ "${SKIP_GIT_PULL:-}" != "1" ]]; then
  echo "→ Fetching origin/$STAGING_BRANCH"
  pulled=0
  for attempt in 1 2 3 4 5 6; do
    if timeout 25 git fetch origin "$STAGING_BRANCH"; then
      git merge --ff-only "origin/$STAGING_BRANCH"
      pulled=1
      break
    fi
    echo "git fetch failed (attempt ${attempt}/6); retrying in 15s"
    sleep 15
  done
  if [[ "$pulled" != 1 ]]; then
    echo "Could not fetch origin/${STAGING_BRANCH} (DNS?)."
    echo "On the Droplet: getent hosts github.com && systemctl restart systemd-resolved"
    exit 1
  fi
fi

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

if [[ "${SKIP_IMAGE_BUILD:-}" != "1" ]]; then
  # One image at a time: pip + two npm builds in parallel OOMs a 1 GB Droplet
  # and takes down systemd-resolved ("Temporary failure in name resolution").
  echo "→ Building images (bot, admin-web, partner-web)"
  docker compose build bot
  docker compose build admin-web
  docker compose build partner-web
fi
echo "→ Starting containers"
docker compose up -d

echo "→ Waiting for admin panel"
stats_code=""
for _ in $(seq 1 45); do
  if curl -fsS "http://127.0.0.1:${ADMIN_WEB_PORT}/" >/dev/null 2>&1; then
    stats_code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${ADMIN_WEB_PORT}/api/stats" || true)"
    if [[ "$stats_code" == "401" ]]; then
      break
    fi
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
