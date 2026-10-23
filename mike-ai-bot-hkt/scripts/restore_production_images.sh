#!/usr/bin/env bash
# Point the production :local image tags back at :previous.
#
# Usage (on the Droplet, from anywhere):
#   ./mike-ai-bot-hkt/scripts/restore_production_images.sh
#   ./mike-ai-bot-hkt/scripts/restore_production_images.sh --up
#
# Image rollback does not restore the Postgres volume.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

up=0
if [[ "${1:-}" == "--up" ]]; then
  up=1
elif [[ -n "${1:-}" ]]; then
  echo "Usage: $0 [--up]"
  exit 1
fi

missing=0
for name in mike-phuket-app mike-phuket-admin-web mike-phuket-partner-web mike-phuket-tma-web; do
  if docker image inspect "${name}:previous" >/dev/null 2>&1; then
    docker tag "${name}:previous" "${name}:local"
    echo "Restored ${name}:local from ${name}:previous"
  else
    echo "No ${name}:previous image to restore."
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "Could not restore a full previous release."
  exit 1
fi

if [[ "$up" -eq 1 ]]; then
  docker compose --profile tls up -d --force-recreate
  echo "Previous release is running again."
fi
