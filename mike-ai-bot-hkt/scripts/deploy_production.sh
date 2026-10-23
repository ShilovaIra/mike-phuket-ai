#!/usr/bin/env bash
# Deploy (or redeploy) this app on the production Droplet from the main branch only.
#
# Usage (on the Droplet, from repo root or mike-ai-bot-hkt):
#   ./mike-ai-bot-hkt/scripts/deploy_production.sh
#
# GitHub Actions builds the images on the runner and runs:
#   SKIP_GIT_PULL=1 SKIP_IMAGE_BUILD=1 ./mike-ai-bot-hkt/scripts/deploy_production.sh
#
set -euo pipefail

PRODUCTION_BRANCH="main"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$APP_DIR/.." && pwd)"
ADMIN_WEB_PORT="${ADMIN_WEB_PORT:-8080}"

cd "$APP_DIR"

echo "→ Stopping leftover containers"
docker compose --profile tls stop || true

cd "$REPO_ROOT"

if [[ "${SKIP_GIT_PULL:-}" != "1" ]]; then
  git config --global --add safe.directory "$REPO_ROOT" || true
  current="$(git rev-parse --abbrev-ref HEAD)"
  if [[ "$current" != "$PRODUCTION_BRANCH" ]]; then
    echo "Refusing to deploy: current branch is '$current', expected '$PRODUCTION_BRANCH'."
    echo "Run: git fetch origin && git checkout $PRODUCTION_BRANCH"
    exit 1
  fi

  echo "→ Fetching origin/$PRODUCTION_BRANCH"
  git fetch origin "$PRODUCTION_BRANCH"
  git pull --ff-only origin "$PRODUCTION_BRANCH"
fi

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from template first:"
  echo "  cp .env.production.example .env && nano .env"
  exit 1
fi

if ! grep -qE '^ADMIN_JWT_SECRET=.+' .env; then
  echo "Missing ADMIN_JWT_SECRET in .env — admin-api will not start."
  echo "Add a long random value, e.g.:"
  echo "  ADMIN_JWT_SECRET=\$(openssl rand -hex 32)"
  exit 1
fi

PARTNER_WEB_PORT="$(awk -F= '/^PARTNER_WEB_PORT=/{v=substr($0, index($0,$2))} END{print v}' .env)"
PARTNER_WEB_PORT="${PARTNER_WEB_PORT:-8081}"
TMA_WEB_PORT="$(awk -F= '/^TMA_WEB_PORT=/{v=substr($0, index($0,$2))} END{print v}' .env)"
TMA_WEB_PORT="${TMA_WEB_PORT:-8082}"
PARTNER_PUBLIC_HOST="$(awk -F= '/^PARTNER_PUBLIC_HOST=/{v=substr($0, index($0,$2))} END{print v}' .env)"
PARTNER_PUBLIC_HOST="${PARTNER_PUBLIC_HOST:-partners.mikephuketai.com}"
ADMIN_PUBLIC_HOST="$(awk -F= '/^ADMIN_PUBLIC_HOST=/{v=substr($0, index($0,$2))} END{print v}' .env)"
ADMIN_PUBLIC_HOST="${ADMIN_PUBLIC_HOST:-admin.mikephuketai.com}"
TMA_PUBLIC_HOST="$(awk -F= '/^TMA_PUBLIC_HOST=/{v=substr($0, index($0,$2))} END{print v}' .env)"
TMA_PUBLIC_HOST="${TMA_PUBLIC_HOST:-app.mikephuketai.com}"
desired_offer_url="https://${PARTNER_PUBLIC_HOST}"
PARTNER_OFFER_BASE_WRITTEN=0
current_offer_base="$(awk -F= '/^PARTNER_OFFER_BASE_URL=/{v=substr($0, index($0,$2))} END{print v}' .env)"
if [[ "$current_offer_base" == "$desired_offer_url" ]]; then
  echo "→ PARTNER_OFFER_BASE_URL is ${current_offer_base}"
elif [[ "$current_offer_base" =~ ^https?://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$ ]] || [[ ! "$current_offer_base" =~ ^https?:// ]]; then
  offer_tmp="$(mktemp)"
  awk -v url="$desired_offer_url" '
    BEGIN { found=0 }
    /^PARTNER_OFFER_BASE_URL=/ { print "PARTNER_OFFER_BASE_URL=" url; found=1; next }
    { print }
    END { if (!found) print "PARTNER_OFFER_BASE_URL=" url }
  ' .env > "$offer_tmp"
  mv "$offer_tmp" .env
  PARTNER_OFFER_BASE_WRITTEN=1
  echo "→ Set PARTNER_OFFER_BASE_URL=${desired_offer_url} so Telegram cards can count clicks"
else
  echo "→ PARTNER_OFFER_BASE_URL is ${current_offer_base}"
fi

if ! grep -qE '^PARTNER_PUBLIC_HOST=' .env; then
  echo "PARTNER_PUBLIC_HOST=${PARTNER_PUBLIC_HOST}" >> .env
fi
if ! grep -qE '^ADMIN_PUBLIC_HOST=' .env; then
  echo "ADMIN_PUBLIC_HOST=${ADMIN_PUBLIC_HOST}" >> .env
fi
if ! grep -qE '^TMA_PUBLIC_HOST=' .env; then
  echo "TMA_PUBLIC_HOST=${TMA_PUBLIC_HOST}" >> .env
fi
if ! grep -qE '^COMPOSE_PROFILES=' .env; then
  echo 'COMPOSE_PROFILES=tls' >> .env
fi

if [[ "${SKIP_IMAGE_BUILD:-}" != "1" ]]; then
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

  # One image at a time: pip + two npm builds in parallel OOMs a 1 GB Droplet.
  echo "→ Building images (bot, admin-web, partner-web, tma-web)"
  docker compose build bot
  docker compose build admin-web
  docker compose build partner-web
  docker compose build tma-web
fi
echo "→ Starting containers"
if ! docker compose --profile tls up -d; then
  echo "docker compose up failed."
  docker compose --profile tls ps || true
  exit 2
fi
if [[ "${PARTNER_OFFER_BASE_WRITTEN}" == 1 ]]; then
  if ! docker compose --profile tls up -d --force-recreate bot; then
    echo "docker compose up failed."
    exit 2
  fi
fi

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
if ! curl -fsS "http://127.0.0.1:${ADMIN_WEB_PORT}/" >/dev/null; then
  echo "Expected admin / to respond"
  docker compose logs --tail=80 admin-api admin-web
  exit 2
fi
stats_code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${ADMIN_WEB_PORT}/api/stats" || true)"
if [[ "$stats_code" != "401" ]]; then
  echo "Expected /api/stats → 401, got ${stats_code}"
  docker compose logs --tail=80 admin-api admin-web
  exit 2
fi
wrap_code=""
for _ in $(seq 1 15); do
  wrap_code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PARTNER_WEB_PORT}/r/missing-token" || true)"
  if [[ "$wrap_code" == "404" ]]; then
    break
  fi
  sleep 2
done
if [[ "$wrap_code" != "404" ]]; then
  echo "Expected /r/missing-token → 404, got ${wrap_code}"
  docker compose logs --tail=80 admin-api partner-web
  exit 2
fi
tma_code=""
for _ in $(seq 1 15); do
  tma_code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${TMA_WEB_PORT}/" || true)"
  if [[ "$tma_code" == "200" ]]; then
    break
  fi
  sleep 2
done
if [[ "$tma_code" != "200" ]]; then
  echo "Expected Mini App / → 200, got ${tma_code}"
  docker compose logs --tail=80 tma-web
  exit 2
fi
if curl -fsS --max-time 8 "https://${PARTNER_PUBLIC_HOST}/" >/dev/null 2>&1; then
  echo "→ Partner Dashboard https://${PARTNER_PUBLIC_HOST}/ is up"
else
  echo "→ https://${PARTNER_PUBLIC_HOST}/ not reachable yet (add the A record and open firewall TCP 80/443)"
fi
if curl -fsS --max-time 8 "https://${TMA_PUBLIC_HOST}/" >/dev/null 2>&1; then
  echo "→ Mini App https://${TMA_PUBLIC_HOST}/ is up"
else
  echo "→ https://${TMA_PUBLIC_HOST}/ not reachable yet (add the app A record)"
fi

if [[ "${SKIP_GIT_PULL:-}" != "1" ]]; then
  echo "→ Branch: $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
else
  echo "→ CI pack deploy (git skipped)"
fi
docker compose --profile tls ps
echo "Done."
echo "  Bot logs:        docker compose logs -f bot"
echo "  Admin API logs:  docker compose logs -f admin-api"
echo "  Caddy logs:      docker compose --profile tls logs -f caddy"
echo "  Admin UI:        https://${ADMIN_PUBLIC_HOST}/"
echo "  Partner UI:      https://${PARTNER_PUBLIC_HOST}/"
