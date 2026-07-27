#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)"
COVERAGE_BIN="${GW_COVERAGE_BIN:-coverage}"
COVERAGE_FILE="${COVERAGE_FILE:-/tmp/goldenwave-phase1a-coverage}"
export COVERAGE_FILE

exec "$COVERAGE_BIN" run \
  --branch \
  --parallel-mode \
  --source="$REPO_ROOT/skills/goldenwave-init/scripts" \
  "$@"
