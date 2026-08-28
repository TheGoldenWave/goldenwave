"""Ordered review, accept and reject coordination for one validated Candidate."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, Callable

from . import decision, safe_write


Writer = Callable[..., None]
BoundaryHook = Callable[[str], None]
DECISION_DIRECTORY = ".kb/candidate-decisions"
KB_FORMAT_VERSION = "gwkb/v0.1"
MARKER_READ_SIZE = 64 * 1024
MAX_MARKER_BYTES = 1024 * 1024

DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if safe_write.PLATFORM_SUPPORTED
    else None
)
FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW if safe_write.PLATFORM_SUPPORTED else None
if safe_write.PLATFORM_SUPPORTED and hasattr(os, "O_CLOEXEC"):
    assert DIRECTORY_FLAGS is not None
    assert FILE_FLAGS is not None
    DIRECTORY_FLAGS |= os.O_CLOEXEC
    FILE_FLAGS |= os.O_CLOEXEC


def review_candidate(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    *,
    include_source_ref: bool = False,
) -> dict[str, Any]:
    return decision.build_review_payload(
        candidate,
        candidate_bytes,
        include_source_ref=include_source_ref,
    )


def accept_candidate(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    root: Path,
    *,
    now: str,
    confirm: str,
    review_digest: str,
    authorization_basis: str | None,
    retention_until: str | None,
    attest_no_consent_required_data: bool,
    acknowledge_git_history: bool,
    writer: Writer = safe_write.write_exclusive,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, Any]:
    errors, normalized_retention = decision.validate_accept_request(
        candidate,
        candidate_bytes,
        now=now,
        confirm=confirm,
        review_digest=review_digest,
        authorization_basis=authorization_basis,
        retention_until=retention_until,
        attest_no_consent_required_data=attest_no_consent_required_data,
        acknowledge_git_history=acknowledge_git_history,
    )
    if errors:
        return decision.result("accept", "failed", errors)
    candidate_id = candidate["candidate_id"]
    expected_root_identity, expected_component_identities, kb_error = _validated_kb_root(
        Path(root)
    )
    if kb_error is not None:
        return decision.failed_result("accept", kb_error, "target")
    assert expected_root_identity is not None
    assert expected_component_identities is not None

    claim_path = f"{DECISION_DIRECTORY}/{candidate_id}.decision.json"
    authorized_path = f"{DECISION_DIRECTORY}/{candidate_id}.authorized.json"
    applied_path = f"{DECISION_DIRECTORY}/{candidate_id}.applied.json"
    target_path = candidate["target"]["path"]
    assert authorization_basis is not None
    accepted_fields = {
        "decided_at": now,
        "authorization_basis": authorization_basis,
        "retention_until": normalized_retention,
    }
    claim = decision.serialize_receipt(
        decision.build_decision_claim(
            candidate,
            candidate_bytes,
            decision="accept",
            decided_at=now,
        )
    )
    authorized = decision.serialize_receipt(
        decision.build_accept_receipt(
            candidate,
            candidate_bytes,
            decision="authorized",
            **accepted_fields,
        )
    )
    applied = decision.serialize_receipt(
        decision.build_accept_receipt(
            candidate,
            candidate_bytes,
            decision="applied",
            **accepted_fields,
        )
    )
    target = candidate["content"]["text"].encode("utf-8")
    observed: set[str] = set()

    def observe(event: str) -> None:
        observed.add(event)
        if boundary_hook is not None:
            boundary_hook(event)

    try:
        current_role = "decision"
        writer(
            root,
            claim_path,
            claim,
            role="decision",
            boundary_hook=observe,
            expected_root_identity=expected_root_identity,
            expected_component_identities=expected_component_identities,
        )
        current_role = "authorized"
        writer(
            root,
            authorized_path,
            authorized,
            role="authorized",
            boundary_hook=observe,
            expected_root_identity=expected_root_identity,
            expected_component_identities=expected_component_identities,
        )
        current_role = "target"
        writer(
            root,
            target_path,
            target,
            role="target",
            boundary_hook=observe,
            expected_root_identity=expected_root_identity,
        )
        current_role = "applied"
        writer(
            root,
            applied_path,
            applied,
            role="applied",
            boundary_hook=observe,
            expected_root_identity=expected_root_identity,
            expected_component_identities=expected_component_identities,
        )
    except (safe_write.SafeWriteError, OSError, TypeError, ValueError) as error:
        return _accept_failure(error, observed, current_role)
    return decision.result("accept", "applied")


def reject_candidate(
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    root: Path,
    *,
    now: str,
    confirm: str,
    review_digest: str,
    reason: str,
    writer: Writer = safe_write.write_exclusive,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, Any]:
    errors = decision.validate_reject_request(
        candidate,
        candidate_bytes,
        now=now,
        confirm=confirm,
        review_digest=review_digest,
        reason=reason,
    )
    if errors:
        return decision.result("reject", "failed", errors)
    candidate_id = candidate["candidate_id"]
    expected_root_identity, expected_component_identities, kb_error = _validated_kb_root(
        Path(root)
    )
    if kb_error is not None:
        return decision.failed_result("reject", kb_error, "target")
    assert expected_root_identity is not None
    assert expected_component_identities is not None

    claim_path = f"{DECISION_DIRECTORY}/{candidate_id}.decision.json"
    receipt_path = f"{DECISION_DIRECTORY}/{candidate_id}.rejected.json"
    claim = decision.serialize_receipt(
        decision.build_decision_claim(
            candidate,
            candidate_bytes,
            decision="reject",
            decided_at=now,
        )
    )
    receipt = decision.serialize_receipt(
        decision.build_reject_receipt(
            candidate,
            candidate_bytes,
            decided_at=now,
            reason=reason,
        )
    )
    observed: set[str] = set()

    def observe(event: str) -> None:
        observed.add(event)
        if boundary_hook is not None:
            boundary_hook(event)

    try:
        writer(
            root,
            claim_path,
            claim,
            role="decision",
            boundary_hook=observe,
            expected_root_identity=expected_root_identity,
            expected_component_identities=expected_component_identities,
        )
        writer(
            root,
            receipt_path,
            receipt,
            role="rejected",
            boundary_hook=observe,
            expected_root_identity=expected_root_identity,
            expected_component_identities=expected_component_identities,
        )
    except (safe_write.SafeWriteError, OSError, TypeError, ValueError) as error:
        if "rejected:parent_fsync" in observed:
            return decision.result("reject", "rejected")
        return decision.failed_result("reject", _write_error_code(error), "target")
    return decision.result("reject", "rejected")


def _accept_failure(
    error: BaseException,
    observed: set[str],
    current_role: str,
) -> dict[str, Any]:
    if "applied:parent_fsync" in observed:
        return decision.result("accept", "applied")
    target_persisted = any(
        event in observed
        for event in (
            "target:file_fsync",
            "target:parent_fsync",
            "applied:file_fsync",
            "applied:parent_fsync",
        )
    )
    target_cleanup_uncertain = (
        current_role == "target"
        and isinstance(error, safe_write.SafeWriteError)
        and error.artifact_created
        and not error.cleanup_confirmed
    )
    if target_persisted or target_cleanup_uncertain:
        return decision.result(
            "accept",
            "indeterminate",
            [decision.error("GW_CANDIDATE_APPLY_INDETERMINATE", "target")],
        )
    return decision.failed_result("accept", _write_error_code(error), "target")


def _write_error_code(error: BaseException) -> str:
    if isinstance(error, safe_write.SafeWriteError):
        return error.code
    return "GW_CANDIDATE_WRITE_FAILED"


def _validated_kb_root(
    root: Path,
) -> tuple[
    tuple[int, int] | None,
    dict[str, tuple[int, int]] | None,
    str | None,
]:
    if not safe_write.PLATFORM_SUPPORTED:
        return None, None, safe_write.PLATFORM_UNSUPPORTED
    assert DIRECTORY_FLAGS is not None
    assert FILE_FLAGS is not None
    root_fd: int | None = None
    kb_fd: int | None = None
    decisions_fd: int | None = None
    marker_fd: int | None = None
    root_identity: tuple[int, int] | None = None
    component_identities: dict[str, tuple[int, int]] | None = None
    error_code: str | None = None
    try:
        root_fd = os.open(root, DIRECTORY_FLAGS)
        root_metadata = os.fstat(root_fd)
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError("KB root is not a directory")
        root_identity = (root_metadata.st_dev, root_metadata.st_ino)

        kb_fd = os.open(".kb", DIRECTORY_FLAGS, dir_fd=root_fd)
        kb_metadata = os.fstat(kb_fd)
        if not stat.S_ISDIR(kb_metadata.st_mode):
            raise ValueError("KB metadata root is not a directory")

        decisions_fd = os.open("candidate-decisions", DIRECTORY_FLAGS, dir_fd=kb_fd)
        decisions_metadata = os.fstat(decisions_fd)
        if not stat.S_ISDIR(decisions_metadata.st_mode):
            raise ValueError("decision root is not a directory")
        component_identities = {
            ".kb": (kb_metadata.st_dev, kb_metadata.st_ino),
            DECISION_DIRECTORY: (decisions_metadata.st_dev, decisions_metadata.st_ino),
        }

        marker_fd = os.open("goldenwave.json", FILE_FLAGS, dir_fd=kb_fd)
        marker_metadata = os.fstat(marker_fd)
        if not stat.S_ISREG(marker_metadata.st_mode) or marker_metadata.st_nlink != 1:
            raise ValueError("KB marker is not an exclusive regular file")
        marker = _read_marker(marker_fd)
        if not isinstance(marker, dict) or marker.get("format_version") != KB_FORMAT_VERSION:
            raise ValueError("KB marker format is invalid")
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        error_code = "GW_CANDIDATE_KB_UNSAFE"
    finally:
        for descriptor in (marker_fd, decisions_fd, kb_fd, root_fd):
            if descriptor is not None and not _close_descriptor(descriptor):
                error_code = error_code or "GW_CANDIDATE_WRITE_FAILED"

    if error_code is not None:
        return None, None, error_code
    return root_identity, component_identities, None
def _read_marker(descriptor: int) -> Any:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(descriptor, MARKER_READ_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_MARKER_BYTES:
            raise ValueError("KB marker exceeds the validation limit")
        chunks.append(chunk)
    return json.loads(b"".join(chunks).decode("utf-8"))


def _close_descriptor(descriptor: int) -> bool:
    try:
        os.close(descriptor)
    except OSError:
        return False
    return True
