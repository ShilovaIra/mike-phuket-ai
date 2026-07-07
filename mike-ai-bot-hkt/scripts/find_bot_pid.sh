#!/usr/bin/env bash
# Find the running Mike bot Python process (does not stop it).

set -euo pipefail

echo "Looking for bot.py processes..."
ps aux | grep -E '[p]ython.*bot\.py' || true

PIDS=$(pgrep -f 'python.*bot\.py' || true)
if [[ -z "$PIDS" ]]; then
  echo ""
  echo "No bot.py process found. Also checking generic python in common paths:"
  ps aux | grep -E '[p]ython' | grep -v grep || true
  exit 1
fi

for PID in $PIDS; do
  echo ""
  echo "PID: $PID"
  echo "  cmd:  $(tr '\0' ' ' < /proc/$PID/cmdline 2>/dev/null || echo '?')"
  echo "  cwd:  $(readlink -f /proc/$PID/cwd 2>/dev/null || echo '?')"
done
