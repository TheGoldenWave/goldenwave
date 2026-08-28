"""CLI for deterministic Candidate validation and governed decisions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import decision
from .constants import RESULT_VERSION
from .schema import CANDIDATE_ID_PATTERN, CONTRACT
from .validator import (
    RFC3339_PATTERN,
    DuplicateKeyError,
    parse_candidate,
    validate_candidate,
)

AVAILABLE_COMMANDS = (
    "validate", "review", "accept", "reject",
    "inject-review", "inject-apply", "inject-recover", "inject-backup", "inject-restore",
)
COMMANDS = frozenset(AVAILABLE_COMMANDS)
HELP_FLAGS = frozenset({"-h", "--help"})


class CandidateArgumentError(ValueError):
    """Raised instead of allowing argparse to emit attacker-controlled diagnostics."""


class CandidateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CandidateArgumentError from None


def _parser() -> argparse.ArgumentParser:
    parser = CandidateArgumentParser(prog="goldenwave-candidate")
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=CandidateArgumentParser
    )

    validate = subparsers.add_parser("validate")
    validate.add_argument("candidate")
    validate.add_argument("--now", required=True)

    review = subparsers.add_parser("review")
    review.add_argument("candidate")
    review.add_argument("--include-source-ref", action="store_true")

    accept = subparsers.add_parser("accept")
    accept.add_argument("candidate")
    accept.add_argument("--target", required=True)
    accept.add_argument("--confirm", required=True)
    accept.add_argument("--review-digest", required=True)
    accept.add_argument("--authorization-basis")
    accept.add_argument("--retention-until")
    accept.add_argument("--attest-no-consent-required-data", action="store_true")
    accept.add_argument("--ack-git-history", action="store_true")

    reject = subparsers.add_parser("reject")
    reject.add_argument("candidate")
    reject.add_argument("--target", required=True)
    reject.add_argument("--confirm", required=True)
    reject.add_argument("--review-digest", required=True)
    reject.add_argument("--reason", required=True)

    inject_review = subparsers.add_parser("inject-review")
    inject_review.add_argument("candidate")
    inject_review.add_argument("--target", required=True)
    inject_review.add_argument("--authorization-basis")
    inject_review.add_argument("--retention-until")
    inject_review.add_argument("--attest-no-consent-required-data", action="store_true")
    inject_review.add_argument("--ack-git-history", action="store_true")

    inject_apply = subparsers.add_parser("inject-apply")
    inject_apply.add_argument("candidate")
    inject_apply.add_argument("--target", required=True)
    inject_apply.add_argument("--expected-base", required=True)
    inject_apply.add_argument("--idempotency-key", required=True)
    inject_apply.add_argument("--confirm")
    inject_apply.add_argument("--review-digest")
    inject_apply.add_argument("--authorization-basis")
    inject_apply.add_argument("--retention-until")
    inject_apply.add_argument("--attest-no-consent-required-data", action="store_true")
    inject_apply.add_argument("--ack-git-history", action="store_true")

    inject_recover = subparsers.add_parser("inject-recover")
    inject_recover.add_argument("--target", required=True)

    inject_backup = subparsers.add_parser("inject-backup")
    inject_backup.add_argument("--target", required=True)
    inject_backup.add_argument("--destination", required=True)

    inject_restore = subparsers.add_parser("inject-restore")
    inject_restore.add_argument("--source", required=True)
    inject_restore.add_argument("--destination", required=True)
    return parser


def _parse_now(value: str) -> datetime:
    if not RFC3339_PATTERN.fullmatch(value):
        raise ValueError("now must be RFC 3339")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("now must include a timezone")
    return parsed


def _validation_payload(
    errors: list[dict[str, str]], candidate_id: str | None = None
) -> dict[str, Any]:
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


def _candidate_id(candidate: dict[str, Any]) -> str | None:
    value = candidate.get("candidate_id")
    if isinstance(value, str) and re.fullmatch(CANDIDATE_ID_PATTERN, value):
        return value
    return None


def _invalid_payload(command: str, errors: list[dict[str, str]]) -> dict[str, Any]:
    if command == "validate":
        return _validation_payload(errors)
    return decision.result(command, "failed", errors)


def _argument_command(argv: list[str]) -> str:
    return argv[0] if argv and argv[0] in COMMANDS else "invalid"


def _is_help_request(argv: list[str]) -> bool:
    if not argv:
        return False
    return argv[0] in HELP_FLAGS or (
        argv[0] in COMMANDS and any(value in HELP_FLAGS for value in argv[1:])
    )


def _help_payload() -> dict[str, Any]:
    payload = decision.result("help", "help")
    payload["available_commands"] = list(AVAILABLE_COMMANDS)
    return payload


def _write_payload(payload: dict[str, Any]) -> None:
    encoded = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")
    sys.stdout.buffer.write(encoded)


def _dispatch(
    args: argparse.Namespace,
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    decision_time: datetime | None,
) -> dict[str, Any]:
    # Keep platform-specific writer checks out of CLI module import so unsupported
    # systems can still load the entrypoint and report capability failures safely.
    from . import workflow

    if args.command == "validate":
        return _validation_payload([], _candidate_id(candidate))
    if args.command == "review":
        return workflow.review_candidate(
            candidate,
            candidate_bytes,
            include_source_ref=args.include_source_ref,
        )
    if args.command == "accept":
        assert decision_time is not None
        if args.authorization_basis is None or args.retention_until is None:
            return decision.failed_result(
                "accept", "GW_CANDIDATE_AUTHORIZATION_REQUIRED", "authorization"
            )
        return workflow.accept_candidate(
            candidate,
            candidate_bytes,
            Path(args.target),
            now=decision_time.isoformat().replace("+00:00", "Z"),
            confirm=args.confirm,
            review_digest=args.review_digest,
            authorization_basis=args.authorization_basis,
            retention_until=args.retention_until,
            attest_no_consent_required_data=args.attest_no_consent_required_data,
            acknowledge_git_history=args.ack_git_history,
        )
    assert decision_time is not None
    return workflow.reject_candidate(
        candidate,
        candidate_bytes,
        Path(args.target),
        now=decision_time.isoformat().replace("+00:00", "Z"),
        confirm=args.confirm,
        review_digest=args.review_digest,
        reason=args.reason,
    )


def main(argv: list[str]) -> int:
    if _is_help_request(argv):
        _write_payload(_help_payload())
        return 0
    try:
        args = _parser().parse_args(argv)
    except CandidateArgumentError:
        payload = decision.failed_result(
            _argument_command(argv),
            "GW_CANDIDATE_ARGUMENT_INVALID",
            "arguments",
        )
        _write_payload(payload)
        return 2
    if args.command in {"inject-recover", "inject-backup", "inject-restore"}:
        from . import reliable
        try:
            if args.command == "inject-recover":
                payload = reliable.recover(Path(args.target))
            elif args.command == "inject-backup":
                payload = reliable.backup(Path(args.target), Path(args.destination))
            else:
                payload = reliable.restore(Path(args.source), Path(args.destination))
            payload = {"ok": True, "command": args.command, **payload}
        except (OSError, ValueError, reliable.ReliableError) as error:
            code = error.code if isinstance(error, reliable.ReliableError) else "GW_CANDIDATE_WRITE_FAILED"
            payload = decision.failed_result(args.command, code, "target")
        _write_payload(payload)
        return 0 if payload["ok"] else 1

    decision_time = (
        None if args.command == "validate" else datetime.now(timezone.utc)
    )
    try:
        candidate_bytes = Path(args.candidate).read_bytes()
        candidate = parse_candidate(candidate_bytes.decode("utf-8"))
        validation_time = (
            _parse_now(args.now) if decision_time is None else decision_time
        )
        errors = validate_candidate(candidate, validation_time)
    except DuplicateKeyError:
        errors = [{"code": "GW_CANDIDATE_DUPLICATE_KEY", "field": "document"}]
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError, ValueError):
        errors = [{"code": "GW_CANDIDATE_DOCUMENT_INVALID", "field": "document"}]

    if errors:
        payload = _invalid_payload(args.command, errors)
    elif args.command in {"inject-review", "inject-apply"}:
        from . import reliable
        try:
            reliable.assert_initialized(Path(args.target))
            if args.command == "inject-review":
                values = reliable.review(
                    Path(args.target),
                    candidate,
                    candidate_bytes,
                    authorization_basis=args.authorization_basis,
                    retention_until=args.retention_until,
                    attest_no_consent_required_data=args.attest_no_consent_required_data,
                    acknowledge_git_history=args.ack_git_history,
                )
                payload = {"ok": True, "command": args.command, "summary": {"status": "reviewable"}, **values}
            else:
                if any(
                    value is None
                    for value in (
                        args.confirm,
                        args.review_digest,
                        args.authorization_basis,
                        args.retention_until,
                    )
                ):
                    payload = decision.failed_result(
                        args.command,
                        "GW_CANDIDATE_AUTHORIZATION_REQUIRED",
                        "authorization",
                    )
                    _write_payload(payload)
                    return 1
                values = reliable.apply(
                    Path(args.target), candidate, candidate_bytes,
                    expected_base=args.expected_base,
                    idempotency_key=args.idempotency_key,
                    confirm=args.confirm,
                    review_digest=args.review_digest,
                    authorization_basis=args.authorization_basis,
                    retention_until=args.retention_until,
                    attest_no_consent_required_data=args.attest_no_consent_required_data,
                    acknowledge_git_history=args.ack_git_history,
                    now=decision_time.isoformat().replace("+00:00", "Z"),
                )
                if values["status"] == "failed":
                    payload = decision.failed_result(
                        args.command,
                        values["error"],
                        "authorization" if "AUTHORIZATION" in values["error"] else "target",
                    )
                else:
                    payload = {"ok": values["status"] == "applied", "command": args.command, "summary": {"status": values["status"]}, **values}
        except (OSError, ValueError, reliable.ReliableError) as error:
            code = error.code if isinstance(error, reliable.ReliableError) else "GW_CANDIDATE_WRITE_FAILED"
            payload = decision.failed_result(args.command, code, "target")
    else:
        payload = _dispatch(args, candidate, candidate_bytes, decision_time)
    _write_payload(payload)
    return 0 if payload["ok"] else 1
