#!/usr/bin/env bash
# Inject export_live_ram.py into a running Python bot without restarting it.
#
# Usage:
#   ./scripts/export_via_gdb.sh <PID> [/path/to/export_live_ram.py]
#
# Prerequisites on server:
#   sudo apt install -y gdb python3
#   Bot must be running (python ... bot.py)

set -euo pipefail

PID="${1:?Usage: $0 <PID> [export_script_path]}"
SCRIPT="${2:-$(cd "$(dirname "$0")" && pwd)/export_live_ram.py}"

if [[ ! -f "$SCRIPT" ]]; then
  echo "ERROR: export script not found: $SCRIPT" >&2
  exit 1
fi

if ! kill -0 "$PID" 2>/dev/null; then
  echo "ERROR: no process with PID $PID" >&2
  exit 1
fi

SCRIPT_ABS="$(readlink -f "$SCRIPT")"
PY_CMD="exec(open('${SCRIPT_ABS}').read())"

echo "Injecting export into PID $PID (bot keeps running)..."
echo "Script: $SCRIPT_ABS"

sudo gdb -p "$PID" -batch \
  -ex "set pagination off" \
  -ex "call (void)PyGILState_Ensure()" \
  -ex "call (int)PyRun_SimpleString(\"${PY_CMD}\")" \
  -ex "detach" \
  -ex "quit"

echo ""
echo "Check output:"
echo "  python3 scripts/verify_export.py /tmp/mike_sessions_export.json"
