"""Pure decision-domain helpers for the Candidate governance workflow."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any

from .schema import CONTRACT


DECISION_RESULT_VERSION = "gw-candidate-decision/v0.1"
DECISION_RECORD_VERSION = "gw-candidate-decision/v0.1"

ACCEPTED_STORAGE_CLASS = "git_tracked"
AUTHORIZATION_BASES = frozenset({"public_source", "self_context"})
REJECTION_REASONS = frozenset(
    {"duplicate", "incorrect", "not_relevant", "other", "privacy"}
)
RFC3339_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def error(code: str, field: str) -> dict[str, str]:
    return {"code": code, "field": field}


def result(command: str, status: str, errors: list[dict[str, str]] | None = None) -> dict[str, Any]:
    controlled_errors = list(errors or [])
    return {
        "ok": not controlled_errors,
        "command": command,
        "result_version": DECISION_RESULT_VERSION,
        "contract": CONTRACT,
        "summary": {
            "status": status,
            "error_count": len(controlled_errors),
        },
        "errors": controlled_errors,
    }


def failed_result(command: str, code: str, field: str) -> dict[str, Any]:
    return result(command, "failed", [error(code, field)])


def build_review_payload(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    include_source_ref: bool = False,
) -> dict[str, Any]:
    provenance = candidate["provenance"]
    source_ref = provenance["source_ref"]
    review_provenance = {
        "source_type": provenance["source_type"],
        "observed_at": provenance["observed_at"],
        "source_ref_sha256": sha256_text(source_ref),
    }
    if include_source_ref:
        review_provenance["source_ref"] = source_ref

    payload = result("review", "reviewable")
    payload.update(
        {
            "candidate_id": candidate["candidate_id"],
            "candidate_sha256": sha256_bytes(candidate_bytes),
            "storage_class": candidate["storage_class"],
            "target": {
                "kind": candidate["target"]["kind"],
                "path": candidate["target"]["path"],
            },
            "provenance": review_provenance,
            "content": {
                "media_type": candidate["content"]["media_type"],
                "text": candidate["content"]["text"],
            },
        }
    )
    return payload


def validate_review_binding(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    confirm: str,
    review_digest: str,
) -> list[dict[str, str]]:
    if confirm != candidate.get("candidate_id"):
        return [error("GW_CANDIDATE_CONFIRMATION_MISMATCH", "confirm")]
    if review_digest != sha256_bytes(candidate_bytes):
        return [error("GW_CANDIDATE_REVIEW_MISMATCH", "review_digest")]
    return []


def validate_accept_request(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    now: str,
    confirm: str,
    review_digest: str,
    authorization_basis: str | None,
    retention_until: str | None,
    attest_no_consent_required_data: bool,
    acknowledge_git_history: bool,
) -> tuple[list[dict[str, str]], str | None]:
    errors = validate_review_binding(
        candidate,
        candidate_bytes,
        confirm=confirm,
        review_digest=review_digest,
    )
    if errors:
        return errors, retention_until
    if candidate.get("storage_class") != ACCEPTED_STORAGE_CLASS:
        return [error("GW_CANDIDATE_STORAGE_UNSUPPORTED", "storage_class")], retention_until

    normalized_retention = None if retention_until == "none" else retention_until
    decision_time = _parse_rfc3339(now)
    retention_time = (
        None if normalized_retention is None else _parse_rfc3339(normalized_retention)
    )
    authorization_valid = (
        decision_time is not None
        and authorization_basis in AUTHORIZATION_BASES
        and (
            normalized_retention is None
            or (retention_time is not None and retention_time > decision_time)
        )
        and attest_no_consent_required_data is True
        and acknowledge_git_history is True
    )
    if not authorization_valid:
        return [error("GW_CANDIDATE_AUTHORIZATION_REQUIRED", "authorization")], normalized_retention
    return [], normalized_retention


def validate_reject_request(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    now: str,
    confirm: str,
    review_digest: str,
    reason: str,
) -> list[dict[str, str]]:
    errors = validate_review_binding(
        candidate,
        candidate_bytes,
        confirm=confirm,
        review_digest=review_digest,
    )
    if errors:
        return errors
    if reason not in REJECTION_REASONS:
        return [error("GW_CANDIDATE_REASON_INVALID", "reason")]
    if not _is_rfc3339(now):
        return [error("GW_CANDIDATE_AUTHORIZATION_REQUIRED", "authorization")]
    return []


def build_accept_receipt(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    decision: str,
    decided_at: str,
    authorization_basis: str,
    retention_until: str | None,
) -> dict[str, Any]:
    return {
        "record_version": DECISION_RECORD_VERSION,
        "candidate_id": candidate["candidate_id"],
        "decision": decision,
        "decided_at": decided_at,
        "candidate_sha256": sha256_bytes(candidate_bytes),
        "target_sha256": sha256_text(candidate["content"]["text"]),
        "authorization_basis": authorization_basis,
        "authorization_scope": "store",
        "retention_until": retention_until,
        "revoked_at": None,
        "no_consent_required_data_attested": True,
        "git_history_acknowledged": True,
    }


def build_decision_claim(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    decision: str,
    decided_at: str,
) -> dict[str, Any]:
    return {
        "record_version": DECISION_RECORD_VERSION,
        "candidate_id": candidate["candidate_id"],
        "decision": decision,
        "decided_at": decided_at,
        "candidate_sha256": sha256_bytes(candidate_bytes),
    }


def build_reject_receipt(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    decided_at: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "record_version": DECISION_RECORD_VERSION,
        "candidate_id": candidate["candidate_id"],
        "decision": "rejected",
        "decided_at": decided_at,
        "candidate_sha256": sha256_bytes(candidate_bytes),
        "reason": reason,
    }


def serialize_receipt(receipt: dict[str, Any]) -> bytes:
    return (json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _is_rfc3339(value: Any) -> bool:
    return _parse_rfc3339(value) is not None


def _parse_rfc3339(value: Any) -> datetime | None:
    if not isinstance(value, str) or not RFC3339_PATTERN.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None
