#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTRY="$SCRIPT_DIR/../skills/goldenwave-init/scripts/goldenwave_init.py"
PYTHON_BIN="${GW_INIT_PYTHON:-python3.11}"

if [ ! -f "$ENTRY" ]; then
  echo "goldenwave init entrypoint not found: $ENTRY" >&2
  exit 1
fi

if [ "$#" -gt 0 ]; then
  case "$1" in
    plan|apply|doctor|adopt)
      exec "$PYTHON_BIN" "$ENTRY" "$@"
      ;;
  esac
fi

TARGET="${1:-$HOME/KnowledgeBase}"
GIT_MODE="${GW_INIT_GIT_MODE:-off}"

exec "$PYTHON_BIN" "$ENTRY" apply --target "$TARGET" --mode new --git "$GIT_MODE" --format json
