#!/usr/bin/env python3
"""GoldenWave Phase 1A initializer entrypoint."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _runtime_unsupported() -> int:
    payload = {
        "ok": False,
        "command": "runtime",
        "result_version": "gw-init/v1",
        "initializer_version": "0.1.0",
        "format_version": None,
        "target": {
            "display_path": "target",
            "root_token": "kb:runtime-unsupported",
        },
        "summary": {
            "status": "failed",
            "message": "python 3.11 or newer is required",
        },
        "warnings": [],
        "conflicts": [],
        "findings": [
            {
                "code": "GW_RUNTIME_UNSUPPORTED",
                "level": "invalid",
                "severity": "error",
                "path": "",
                "message": "python 3.11 or newer is required",
            }
        ],
        "artifacts": {},
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return 1


if sys.version_info < (3, 11):
    raise SystemExit(_runtime_unsupported())

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gw_init.cli import main  # noqa: E402


if __name__ == "__main__":
    try:
        exit_code = main(sys.argv[1:])
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        command = " ".join(sys.argv[1:3]) if sys.argv[1:2] == ["adopt"] else (sys.argv[1] if len(sys.argv) > 1 else "unknown")
        payload = {
            "ok": False,
            "command": command,
            "result_version": "gw-init/v1",
            "initializer_version": "0.1.0",
            "format_version": None,
            "target": {"display_path": "target", "root_token": "kb:operation-failed"},
            "summary": {"status": "failed", "message": "operation failed safely"},
            "warnings": [],
            "conflicts": [],
            "findings": [{"code": "GW_DOCTOR_FAILED", "level": "invalid", "severity": "error", "path": "", "message": "operation failed safely"}],
            "artifacts": {},
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        exit_code = 1
    raise SystemExit(exit_code)
