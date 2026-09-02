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

if [[ "${SKIP_GIT_PULL:-}" != "1" ]]; then
  git config --global --add safe.directory "$REPO_ROOT" || true
  current="$(git rev-parse --abbrev-ref HEAD)"
  if [[ "$current" != "$STAGING_BRANCH" ]]; then
    echo "Refusing to deploy: current branch is '$current', expected '$STAGING_BRANCH'."
    echo "Run: git fetch origin && git checkout $STAGING_BRANCH"
    exit 1
  fi
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

PARTNER_WEB_PORT="$(awk -F= '/^PARTNER_WEB_PORT=/{v=substr($0, index($0,$2))} END{print v}' .env)"
PARTNER_WEB_PORT="${PARTNER_WEB_PORT:-8081}"
PARTNER_OFFER_BASE_WRITTEN=0
current_offer_base="$(awk -F= '/^PARTNER_OFFER_BASE_URL=/{v=substr($0, index($0,$2))} END{print v}' .env)"
case "$current_offer_base" in
  http://*|https://*)
    echo "→ PARTNER_OFFER_BASE_URL is ${current_offer_base}"
    ;;
  *)
    droplet_ip="$(curl -fsS --max-time 2 http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address 2>/dev/null || true)"
    if [[ -z "$droplet_ip" ]]; then
      echo "PARTNER_OFFER_BASE_URL is not http(s); Telegram wrap stays off."
      echo "Set PARTNER_OFFER_BASE_URL=http://DROPLET_IP:${PARTNER_WEB_PORT} in .env"
    else
      offer_url="http://${droplet_ip}:${PARTNER_WEB_PORT}"
      offer_tmp="$(mktemp)"
      awk -v url="$offer_url" '
        BEGIN { found=0 }
        /^PARTNER_OFFER_BASE_URL=/ { print "PARTNER_OFFER_BASE_URL=" url; found=1; next }
        { print }
        END { if (!found) print "PARTNER_OFFER_BASE_URL=" url }
      ' .env > "$offer_tmp"
      mv "$offer_tmp" .env
      PARTNER_OFFER_BASE_WRITTEN=1
      echo "→ Set PARTNER_OFFER_BASE_URL=${offer_url} so Telegram cards can count clicks"
    fi
    ;;
esac

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
if [[ "${PARTNER_OFFER_BASE_WRITTEN}" == 1 ]]; then
  docker compose up -d --force-recreate bot
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
curl -fsS "http://127.0.0.1:${ADMIN_WEB_PORT}/" >/dev/null
# Unauthenticated stats must reject (proves API proxy is up).
stats_code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${ADMIN_WEB_PORT}/api/stats" || true)"
if [[ "$stats_code" != "401" ]]; then
  echo "Expected /api/stats → 401, got ${stats_code}"
  docker compose logs --tail=80 admin-api admin-web
  exit 1
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
  exit 1
fi

if [[ "${SKIP_GIT_PULL:-}" != "1" ]]; then
  echo "→ Branch: $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
else
  echo "→ CI pack deploy (git skipped)"
fi
docker compose ps
echo "Done."
echo "  Bot logs:        docker compose logs -f bot"
echo "  Admin API logs:  docker compose logs -f admin-api"
echo "  Admin UI:        http://<droplet-ip>:${ADMIN_WEB_PORT}/"
echo "  Partner UI:      http://<droplet-ip>:${PARTNER_WEB_PORT}/"
echo "  Create admin:    docker compose run --rm bot python scripts/create_admin_user.py --email you@example.com --password '…'"
