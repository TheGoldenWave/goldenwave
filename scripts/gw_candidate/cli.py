"""CLI for deterministic Candidate validation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .constants import CONTRACT, RESULT_VERSION
from .validator import DuplicateKeyError, parse_candidate, validate_candidate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="goldenwave-candidate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("candidate")
    validate.add_argument("--now", required=True)
    return parser


def _parse_now(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("now must include a timezone")
    return parsed


def _payload(errors: list[dict[str, str]], candidate_id: str | None = None) -> dict[str, Any]:
    valid = not errors
    payload: dict[str, Any] = {
        "ok": valid,
        "command": "validate",
        "result_version": RESULT_VERSION,
        "contract": CONTRACT,
        "summary": {
            "status": "valid" if valid else "invalid",
            "error_count": len(errors),
        },
        "errors": errors,
    }
    if candidate_id:
        payload["candidate_id"] = candidate_id
    return payload


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        candidate = parse_candidate(Path(args.candidate).read_text(encoding="utf-8"))
        errors = validate_candidate(candidate, _parse_now(args.now))
        candidate_id = candidate.get("candidate_id") if isinstance(candidate.get("candidate_id"), str) else None
    except DuplicateKeyError:
        errors = [{"code": "GW_CANDIDATE_DUPLICATE_KEY", "field": "document"}]
        candidate_id = None
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors = [{"code": "GW_CANDIDATE_DOCUMENT_INVALID", "field": "document"}]
        candidate_id = None
    sys.stdout.write(json.dumps(_payload(errors, candidate_id), ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if not errors else 1
