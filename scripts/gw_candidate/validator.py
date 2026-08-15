"""Fail-closed validation for context-candidate/v0.1."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

from .constants import (
    CANDIDATE_ID_PATTERN,
    CONTENT_FIELDS,
    CONTRACT,
    CONTRACT_STATUS,
    MEDIA_TYPES,
    PROVENANCE_FIELDS,
    ROOT_FIELDS,
    SOURCE_TYPES,
    STORAGE_CLASSES,
    TARGET_FIELDS,
    TARGET_ROOTS,
)


class DuplicateKeyError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def parse_candidate(raw: str) -> dict[str, Any]:
    value = json.loads(raw, object_pairs_hook=_strict_object)
    if not isinstance(value, dict):
        raise ValueError("candidate must be an object")
    return value


def _error(code: str, field: str) -> dict[str, str]:
    return {"code": code, "field": field}


def _unknown_fields(value: Any, allowed: set[str], field: str) -> list[dict[str, str]]:
    if not isinstance(value, dict):
        return []
    return [
        _error("GW_CANDIDATE_UNKNOWN_FIELD", f"{field}.{name}".strip("."))
        for name in sorted(set(value) - allowed)
    ]


def _required_fields(value: Any, required: set[str], field: str) -> list[dict[str, str]]:
    if not isinstance(value, dict):
        return [_error("GW_CANDIDATE_TYPE", field)]
    return [
        _error("GW_CANDIDATE_REQUIRED", f"{field}.{name}".strip("."))
        for name in sorted(required - set(value))
    ]


def _timestamp(value: Any, field: str) -> tuple[datetime | None, list[dict[str, str]]]:
    if not isinstance(value, str):
        return None, [_error("GW_CANDIDATE_TIMESTAMP_INVALID", field)]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None, [_error("GW_CANDIDATE_TIMESTAMP_INVALID", field)]
    if parsed.tzinfo is None:
        return None, [_error("GW_CANDIDATE_TIMESTAMP_INVALID", field)]
    return parsed, []


def _target_errors(target: Any) -> list[dict[str, str]]:
    errors = _required_fields(target, TARGET_FIELDS, "target")
    errors.extend(_unknown_fields(target, TARGET_FIELDS, "target"))
    if not isinstance(target, dict):
        return errors
    kind = target.get("kind")
    path = target.get("path")
    if kind not in TARGET_ROOTS:
        errors.append(_error("GW_CANDIDATE_ENUM", "target.kind"))
    if not isinstance(path, str) or not path:
        errors.append(_error("GW_CANDIDATE_TARGET_UNSAFE", "target.path"))
        return errors
    pure_path = PurePosixPath(path)
    allowed_roots = TARGET_ROOTS.get(kind, ())
    unsafe = (
        pure_path.is_absolute()
        or ".." in pure_path.parts
        or "\\" in path
        or not path.endswith(".md")
        or not path.startswith(allowed_roots)
    )
    if unsafe:
        errors.append(_error("GW_CANDIDATE_TARGET_UNSAFE", "target.path"))
    return errors


def validate_candidate(candidate: dict[str, Any], now: datetime) -> list[dict[str, str]]:
    errors = _required_fields(candidate, ROOT_FIELDS, "")
    errors.extend(_unknown_fields(candidate, ROOT_FIELDS, ""))

    if candidate.get("contract") != CONTRACT:
        errors.append(_error("GW_CANDIDATE_CONTRACT_UNSUPPORTED", "contract"))
    if candidate.get("contract_status") != CONTRACT_STATUS:
        errors.append(_error("GW_CANDIDATE_STATUS_INVALID", "contract_status"))
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not re.fullmatch(CANDIDATE_ID_PATTERN, candidate_id):
        errors.append(_error("GW_CANDIDATE_ID_INVALID", "candidate_id"))
    if candidate.get("storage_class") not in STORAGE_CLASSES:
        errors.append(_error("GW_CANDIDATE_ENUM", "storage_class"))

    created_at, timestamp_errors = _timestamp(candidate.get("created_at"), "created_at")
    errors.extend(timestamp_errors)
    expires_value = candidate.get("expires_at")
    expires_at = None
    if expires_value is not None:
        expires_at, timestamp_errors = _timestamp(expires_value, "expires_at")
        errors.extend(timestamp_errors)
    if created_at and created_at > now:
        errors.append(_error("GW_CANDIDATE_FUTURE", "created_at"))
    if expires_at and expires_at <= now:
        errors.append(_error("GW_CANDIDATE_STALE", "expires_at"))
    if created_at and expires_at and expires_at <= created_at:
        errors.append(_error("GW_CANDIDATE_TIME_ORDER", "expires_at"))

    errors.extend(_target_errors(candidate.get("target")))
    errors.extend(_provenance_errors(candidate.get("provenance"), created_at))
    errors.extend(_content_errors(candidate.get("content")))
    return sorted(errors, key=lambda item: (item["field"], item["code"]))


def _provenance_errors(provenance: Any, created_at: datetime | None) -> list[dict[str, str]]:
    errors = _required_fields(provenance, PROVENANCE_FIELDS, "provenance")
    errors.extend(_unknown_fields(provenance, PROVENANCE_FIELDS, "provenance"))
    if not isinstance(provenance, dict):
        return errors
    if provenance.get("source_type") not in SOURCE_TYPES:
        errors.append(_error("GW_CANDIDATE_ENUM", "provenance.source_type"))
    source_ref = provenance.get("source_ref")
    if not isinstance(source_ref, str) or not source_ref.strip():
        errors.append(_error("GW_CANDIDATE_SOURCE_INVALID", "provenance.source_ref"))
    observed_at, timestamp_errors = _timestamp(provenance.get("observed_at"), "provenance.observed_at")
    errors.extend(timestamp_errors)
    if created_at and observed_at and observed_at > created_at:
        errors.append(_error("GW_CANDIDATE_TIME_ORDER", "provenance.observed_at"))
    return errors


def _content_errors(content: Any) -> list[dict[str, str]]:
    errors = _required_fields(content, CONTENT_FIELDS, "content")
    errors.extend(_unknown_fields(content, CONTENT_FIELDS, "content"))
    if not isinstance(content, dict):
        return errors
    if content.get("media_type") not in MEDIA_TYPES:
        errors.append(_error("GW_CANDIDATE_ENUM", "content.media_type"))
    if content.get("treat_as") != "data":
        errors.append(_error("GW_CANDIDATE_CONTENT_NOT_DATA", "content.treat_as"))
    text = content.get("text")
    if not isinstance(text, str) or not text.strip():
        errors.append(_error("GW_CANDIDATE_CONTENT_INVALID", "content.text"))
    return errors
