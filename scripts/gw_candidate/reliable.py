"""Reliable, manifest-backed Candidate inject for Phase 1C."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator

from . import decision, safe_write


VERSION = "gw-reliable-inject/v0.1"
EMPTY_BASE = "base_" + ("0" * 64)
ROOT = Path(".kb/reliable-inject")
ACTIVE = ROOT / "active.json"
LOCK = ROOT / "lock"
OBJECTS = ROOT / "objects"
MANIFESTS = ROOT / "manifests"
TRANSACTIONS = ROOT / "transactions"
RECEIPTS = ROOT / "receipts"
DIRECTORIES = (OBJECTS, MANIFESTS, TRANSACTIONS, RECEIPTS)
BoundaryHook = Callable[[str], None]


class ReliableError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _assert_no_symlink_ancestors(root: Path, relative: Path) -> None:
    cursor = root
    for component in relative.parts:
        cursor = cursor / component
        if cursor.is_symlink():
            raise ReliableError("GW_CANDIDATE_KB_UNSAFE")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _load(path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT") from None
    if not isinstance(value, dict):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    return value


def _target(candidate: dict[str, Any]) -> str:
    value = candidate.get("target", {}).get("path")
    if not isinstance(value, str) or not value or "\\" in value:
        raise ReliableError("GW_CANDIDATE_TARGET_UNSAFE")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ReliableError("GW_CANDIDATE_TARGET_UNSAFE")
    if not value.startswith(("wiki/", "profile/", "projects/")):
        raise ReliableError("GW_CANDIDATE_TARGET_UNSAFE")
    return value


def _content(candidate: dict[str, Any]) -> bytes:
    value = candidate.get("content", {}).get("text")
    if not isinstance(value, str):
        raise ReliableError("GW_CANDIDATE_DOCUMENT_INVALID")
    return value.encode("utf-8")


def _operation(
    candidate: dict[str, Any],
    raw: bytes,
    *,
    authorization_basis: str | None,
    retention_until: str | None,
    attest_no_consent_required_data: bool,
    acknowledge_git_history: bool,
) -> str:
    authorization = json.dumps(
        {
            "authorization_basis": authorization_basis,
            "retention_until": retention_until,
            "attest_no_consent_required_data": attest_no_consent_required_data,
            "acknowledge_git_history": acknowledge_git_history,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    material = b"\0".join(
        (b"accept", raw, _target(candidate).encode("utf-8"), authorization)
    )
    return "op_" + _sha(material)


def _idempotency(operation_id: str, base: str) -> str:
    return "idem_" + _sha((operation_id + "\0" + base).encode("ascii"))


def initialize(root: Path) -> None:
    marker = root / ".kb/goldenwave.json"
    if not marker.is_file() or marker.is_symlink():
        raise ReliableError("GW_CANDIDATE_KB_UNSAFE")
    for relative in (ROOT, *DIRECTORIES):
        _assert_no_symlink_ancestors(root, relative)
        path = root / relative
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.is_symlink():
            raise ReliableError("GW_CANDIDATE_KB_UNSAFE")
    lock = root / LOCK
    lock.touch(mode=0o600, exist_ok=True)
    active = root / ACTIVE
    if not active.exists():
        _atomic(active, _json({"version": VERSION, "active_base": EMPTY_BASE, "manifest": None}))


def assert_initialized(root: Path) -> None:
    marker = root / ".kb/goldenwave.json"
    if marker.is_symlink() or not marker.is_file():
        raise ReliableError("GW_CANDIDATE_KB_UNSAFE")
    for relative in (ROOT, *DIRECTORIES):
        _assert_no_symlink_ancestors(root, relative)
        path = root / relative
        if path.is_symlink() or not path.is_dir():
            raise ReliableError("GW_CANDIDATE_TRANSACTION_UNINITIALIZED")
    for relative in (ACTIVE, LOCK):
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ReliableError("GW_CANDIDATE_TRANSACTION_UNINITIALIZED")
    active_base(root)


def active_base(root: Path) -> str:
    payload, _ = _active_state(root)
    return payload["active_base"]


def review(
    root: Path,
    candidate: dict[str, Any],
    raw: bytes,
    *,
    active_base: str | None = None,
    authorization_basis: str | None = None,
    retention_until: str | None = None,
    attest_no_consent_required_data: bool = False,
    acknowledge_git_history: bool = False,
) -> dict[str, str]:
    assert_initialized(root)
    base = active_base if active_base is not None else globals()["active_base"](root)
    operation_id = _operation(
        candidate,
        raw,
        authorization_basis=authorization_basis,
        retention_until=retention_until,
        attest_no_consent_required_data=attest_no_consent_required_data,
        acknowledge_git_history=acknowledge_git_history,
    )
    return {
        "operation_id": operation_id,
        "idempotency_key": _idempotency(operation_id, base),
        "active_base": base,
        "candidate_sha256": _sha(raw),
    }


@contextmanager
def _locked(root: Path) -> Iterator[None]:
    descriptor = os.open(root / LOCK, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _exclusive(path: Path, content: bytes) -> None:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except FileExistsError:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ReliableError("GW_CANDIDATE_TARGET_UNSAFE")
        read_descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(read_descriptor, 64 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(read_descriptor)
        if b"".join(chunks) != content:
            raise ReliableError("GW_CANDIDATE_IDEMPOTENCY_MISMATCH")
        return
    try:
        view = memoryview(content)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise OSError("short write")
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_dir(path.parent)


def _notify(hook: BoundaryHook | None, event: str) -> None:
    if hook is not None:
        hook(event)


def _regular_bytes(path: Path, error_code: str) -> bytes:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ReliableError(error_code)
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except (OSError, ValueError):
        raise ReliableError(error_code) from None
    try:
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 64 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _atomic(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".gw-", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        view = memoryview(content)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise OSError("short write")
            view = view[count:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        _fsync_dir(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _result(status: str, **extra: Any) -> dict[str, Any]:
    return {"version": VERSION, "status": status, **extra}


def apply(
    root: Path,
    candidate: dict[str, Any],
    raw: bytes,
    *,
    expected_base: str,
    idempotency_key: str,
    confirm: str | None,
    review_digest: str | None,
    authorization_basis: str | None,
    retention_until: str | None,
    attest_no_consent_required_data: bool,
    acknowledge_git_history: bool,
    now: str,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, Any]:
    errors, _ = decision.validate_accept_request(
        candidate,
        raw,
        now=now,
        confirm=confirm,
        review_digest=review_digest,
        authorization_basis=authorization_basis,
        retention_until=retention_until,
        attest_no_consent_required_data=attest_no_consent_required_data,
        acknowledge_git_history=acknowledge_git_history,
    )
    if errors:
        return _result("failed", error=errors[0]["code"])
    identity = review(
        root,
        candidate,
        raw,
        active_base=expected_base,
        authorization_basis=authorization_basis,
        retention_until=retention_until,
        attest_no_consent_required_data=attest_no_consent_required_data,
        acknowledge_git_history=acknowledge_git_history,
    )
    if idempotency_key != identity["idempotency_key"]:
        return _result("failed", error="GW_CANDIDATE_IDEMPOTENCY_MISMATCH")
    operation_id = identity["operation_id"]
    receipt_path = root / RECEIPTS / f"{operation_id}.json"
    committed = False
    with _locked(root):
        if receipt_path.exists():
            receipt = _load(receipt_path)
            if receipt.get("idempotency_key") != idempotency_key:
                return _result("failed", error="GW_CANDIDATE_IDEMPOTENCY_MISMATCH")
            return _result("applied", replayed=True, operation_id=operation_id, active_base=receipt["active_base"])
        current = active_base(root)
        if current != expected_base:
            return _result("failed", error="GW_CANDIDATE_BASE_CONFLICT")

        content = _content(candidate)
        object_hash = _sha(content)
        try:
            _exclusive(root / OBJECTS / object_hash, content)
            _notify(boundary_hook, "object")
        except OSError:
            return _result("failed", error="GW_CANDIDATE_WRITE_FAILED")
        target = _target(candidate)
        entries = _active_entries(root)
        if target in entries and entries[target] != object_hash:
            return _result("failed", error="GW_CANDIDATE_CONFLICT")
        entries[target] = object_hash
        manifest = {"version": VERSION, "parent": current, "operation_id": operation_id, "entries": entries}
        manifest_bytes = _json(manifest)
        manifest_hash = _sha(manifest_bytes)
        next_base = "base_" + manifest_hash
        authorized = {
            "version": VERSION,
            "state": "authorized",
            "operation_id": operation_id,
            "idempotency_key": idempotency_key,
            "expected_base": expected_base,
            "candidate_sha256": _sha(raw),
            "authorization_basis": authorization_basis,
            "retention_until": None if retention_until == "none" else retention_until,
            "no_consent_required_data_attested": attest_no_consent_required_data,
            "git_history_acknowledged": acknowledge_git_history,
        }
        authorized_bytes = _json(authorized)
        authorization_hash = _sha(authorized_bytes)
        journal = {
            "version": VERSION,
            "state": "prepared",
            "operation_id": operation_id,
            "idempotency_key": idempotency_key,
            "expected_base": expected_base,
            "active_base": next_base,
            "manifest": manifest_hash,
            "candidate_sha256": _sha(raw),
            "authorization_sha256": authorization_hash,
            "object_sha256": object_hash,
        }
        try:
            _exclusive(
                root / RECEIPTS / f"{operation_id}.authorized.json",
                authorized_bytes,
            )
            _notify(boundary_hook, "authorized")
            _exclusive(root / TRANSACTIONS / f"{operation_id}.json", _json(journal))
            _notify(boundary_hook, "journal")
            _exclusive(root / MANIFESTS / f"{manifest_hash}.json", manifest_bytes)
            _notify(boundary_hook, "manifest")
            _atomic(root / ACTIVE, _json({"version": VERSION, "active_base": next_base, "manifest": manifest_hash}))
            committed = True
            _notify(boundary_hook, "active")
        except OSError:
            return _result(
                "indeterminate" if committed else "failed",
                error="GW_CANDIDATE_APPLY_INDETERMINATE" if committed else "GW_CANDIDATE_WRITE_FAILED",
                operation_id=operation_id,
                active_base=next_base,
            )
        try:
            _materialize(root, target, object_hash)
            _notify(boundary_hook, "materialized")
        except (OSError, ReliableError):
            return _result("indeterminate", error="GW_CANDIDATE_APPLY_INDETERMINATE", operation_id=operation_id, active_base=next_base)
        receipt = {
            **authorized,
            "state": "completed",
            "active_base": next_base,
            "manifest": manifest_hash,
        }
        receipt_written = False
        try:
            _exclusive(receipt_path, _json(receipt))
            receipt_written = True
            _notify(boundary_hook, "receipt")
        except OSError:
            if not receipt_written:
                return _result("indeterminate", error="GW_CANDIDATE_APPLY_INDETERMINATE", operation_id=operation_id, active_base=next_base)
        return _result("applied", replayed=False, operation_id=operation_id, active_base=next_base)


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _manifest_entries(root: Path, manifest_hash: str) -> dict[str, str]:
    if not _valid_sha256(manifest_hash):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    manifest_path = root / MANIFESTS / f"{manifest_hash}.json"
    manifest_bytes = _regular_bytes(manifest_path, "GW_CANDIDATE_TRANSACTION_CORRUPT")
    if _sha(manifest_bytes) != manifest_hash:
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    manifest = _load(manifest_path)
    if manifest.get("version") != VERSION:
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    entries = manifest.get("entries")
    if not isinstance(entries, dict):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    controlled: dict[str, str] = {}
    for target, object_hash in entries.items():
        if not isinstance(target, str) or not _valid_sha256(object_hash):
            raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
        _target({"target": {"path": target}})
        content = _regular_bytes(
            root / OBJECTS / object_hash,
            "GW_CANDIDATE_RECOVERY_REQUIRED",
        )
        if _sha(content) != object_hash:
            raise ReliableError("GW_CANDIDATE_RECOVERY_REQUIRED")
        controlled[target] = object_hash
    return controlled


def _active_state(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    active = _load(root / ACTIVE)
    if active.get("version") != VERSION:
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    manifest_hash = active.get("manifest")
    if manifest_hash is None:
        if active.get("active_base") != EMPTY_BASE:
            raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
        return active, {}
    if active.get("active_base") != "base_" + str(manifest_hash):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    return active, _manifest_entries(root, manifest_hash)


def _active_entries(root: Path) -> dict[str, str]:
    _, entries = _active_state(root)
    return entries


def _materialize(root: Path, target: str, object_hash: str) -> None:
    content = _regular_bytes(
        root / OBJECTS / object_hash,
        "GW_CANDIDATE_RECOVERY_REQUIRED",
    )
    if _sha(content) != object_hash:
        raise ReliableError("GW_CANDIDATE_RECOVERY_REQUIRED")
    path = root / target
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
            raise ReliableError("GW_CANDIDATE_RECOVERY_REQUIRED")
        return
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    cursor = parent
    while cursor != root:
        if cursor.is_symlink() or not cursor.is_dir():
            raise ReliableError("GW_CANDIDATE_TARGET_UNSAFE")
        cursor = cursor.parent
    safe_write.write_exclusive(root, target, content, role="materialized")


JOURNAL_KEYS = frozenset(
    {
        "version",
        "state",
        "operation_id",
        "idempotency_key",
        "expected_base",
        "active_base",
        "manifest",
        "candidate_sha256",
        "authorization_sha256",
        "object_sha256",
    }
)
AUTHORIZED_KEYS = frozenset(
    {
        "version",
        "state",
        "operation_id",
        "idempotency_key",
        "expected_base",
        "candidate_sha256",
        "authorization_basis",
        "retention_until",
        "no_consent_required_data_attested",
        "git_history_acknowledged",
    }
)


def _validated_journal(root: Path, journal_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    journal = _load(journal_path)
    operation_id = journal.get("operation_id")
    if (
        set(journal) != JOURNAL_KEYS
        or journal.get("version") != VERSION
        or journal.get("state") not in {"prepared", "aborted"}
        or not isinstance(operation_id, str)
        or journal_path.name != f"{operation_id}.json"
        or not _valid_sha256(journal.get("manifest"))
        or not _valid_sha256(journal.get("candidate_sha256"))
        or not _valid_sha256(journal.get("authorization_sha256"))
        or not _valid_sha256(journal.get("object_sha256"))
        or journal.get("active_base") != "base_" + str(journal.get("manifest"))
    ):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    authorized_path = root / RECEIPTS / f"{operation_id}.authorized.json"
    authorized_bytes = _regular_bytes(
        authorized_path,
        "GW_CANDIDATE_TRANSACTION_CORRUPT",
    )
    if _sha(authorized_bytes) != journal["authorization_sha256"]:
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    authorized = _load(authorized_path)
    if (
        set(authorized) != AUTHORIZED_KEYS
        or authorized.get("version") != VERSION
        or authorized.get("state") != "authorized"
        or authorized.get("operation_id") != operation_id
        or authorized.get("idempotency_key") != journal.get("idempotency_key")
        or authorized.get("expected_base") != journal.get("expected_base")
        or authorized.get("candidate_sha256") != journal.get("candidate_sha256")
    ):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    return journal, authorized


def _object_is_referenced(root: Path, object_hash: str) -> bool:
    for manifest_path in sorted((root / MANIFESTS).glob("*.json")):
        manifest_hash = manifest_path.stem
        if object_hash in _manifest_entries(root, manifest_hash).values():
            return True
    return False


def _abort_prepared(root: Path, journal_path: Path, journal: dict[str, Any]) -> None:
    object_hash = journal["object_sha256"]
    object_path = root / OBJECTS / object_hash
    if object_path.exists() or object_path.is_symlink():
        _regular_bytes(object_path, "GW_CANDIDATE_RECOVERY_REQUIRED")
        if _object_is_referenced(root, object_hash):
            raise ReliableError("GW_CANDIDATE_RECOVERY_REQUIRED")
        os.unlink(object_path)
        _fsync_dir(object_path.parent)
    _atomic(journal_path, _json({**journal, "state": "aborted"}))


def recover(root: Path) -> dict[str, Any]:
    with _locked(root):
        active, entries = _active_state(root)
        for journal_path in sorted((root / TRANSACTIONS).glob("op_*.json")):
            journal, authorized = _validated_journal(root, journal_path)
            if journal["state"] == "aborted":
                continue
            operation_id = journal["operation_id"]
            manifest_hash = journal.get("manifest")
            manifest_path = root / MANIFESTS / f"{manifest_hash}.json"
            if not manifest_path.exists():
                _abort_prepared(root, journal_path, journal)
                continue
            journal_entries = _manifest_entries(root, manifest_hash)
            if journal.get("expected_base") == active.get("active_base"):
                _atomic(
                    root / ACTIVE,
                    _json(
                        {
                            "version": VERSION,
                            "active_base": journal["active_base"],
                            "manifest": manifest_hash,
                        }
                    ),
                )
                active = {
                    "version": VERSION,
                    "active_base": journal["active_base"],
                    "manifest": manifest_hash,
                }
                entries = journal_entries
            if journal.get("active_base") != active.get("active_base"):
                continue
            entries = journal_entries
            for target, object_hash in entries.items():
                _materialize(root, target, object_hash)
            receipt_path = root / RECEIPTS / f"{operation_id}.json"
            if not receipt_path.exists():
                _exclusive(
                    receipt_path,
                    _json(
                        {
                            **authorized,
                            "state": "completed",
                            "active_base": journal["active_base"],
                            "manifest": manifest_hash,
                        }
                    ),
                )
            break
        for target, object_hash in entries.items():
            _materialize(root, target, object_hash)
        return _result("recovered", repaired=len(entries))


def backup(root: Path, destination: Path) -> dict[str, Any]:
    if destination.exists():
        raise ReliableError("GW_CANDIDATE_BACKUP_CONFLICT")
    destination.mkdir(parents=True)
    with _locked(root):
        active, entries = _active_state(root)
        for path in (root / ROOT, root / ".kb/goldenwave.json", *(root / ROOT).rglob("*")):
            if path.is_symlink():
                raise ReliableError("GW_CANDIDATE_KB_UNSAFE")
        for relative in (ROOT, *DIRECTORIES):
            (destination / relative).mkdir(mode=0o700, parents=True, exist_ok=True)
        _exclusive(
            destination / ".kb/goldenwave.json",
            _regular_bytes(root / ".kb/goldenwave.json", "GW_CANDIDATE_KB_UNSAFE"),
        )
        _exclusive(destination / ACTIVE, _regular_bytes(root / ACTIVE, "GW_CANDIDATE_KB_UNSAFE"))
        _exclusive(destination / LOCK, b"")
        manifest_hash = active.get("manifest")
        active_operation: str | None = None
        if manifest_hash is not None:
            manifest_path = root / MANIFESTS / f"{manifest_hash}.json"
            manifest = _load(manifest_path)
            active_operation = manifest.get("operation_id")
            if not isinstance(active_operation, str):
                raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
            _exclusive(
                destination / MANIFESTS / f"{manifest_hash}.json",
                _regular_bytes(manifest_path, "GW_CANDIDATE_TRANSACTION_CORRUPT"),
            )
        for object_hash in sorted(set(entries.values())):
            _exclusive(
                destination / OBJECTS / object_hash,
                _regular_bytes(root / OBJECTS / object_hash, "GW_CANDIDATE_RECOVERY_REQUIRED"),
            )
        if active_operation is not None:
            transaction_path = root / TRANSACTIONS / f"{active_operation}.json"
            if transaction_path.exists():
                _exclusive(
                    destination / TRANSACTIONS / transaction_path.name,
                    _regular_bytes(transaction_path, "GW_CANDIDATE_TRANSACTION_CORRUPT"),
                )
            for suffix in ("authorized.json", "json"):
                receipt_path = root / RECEIPTS / f"{active_operation}.{suffix}"
                if receipt_path.exists():
                    _exclusive(
                        destination / RECEIPTS / receipt_path.name,
                        _regular_bytes(receipt_path, "GW_CANDIDATE_TRANSACTION_CORRUPT"),
                    )
        inventory = {}
        for path in sorted(p for p in destination.rglob("*") if p.is_file()):
            inventory[path.relative_to(destination).as_posix()] = _sha(path.read_bytes())
        _exclusive(
            destination / "backup-manifest.json",
            _json({"version": VERSION, "files": inventory}),
        )
    return _result("backed_up", files=len(inventory))


def restore(source: Path, destination: Path) -> dict[str, Any]:
    if destination.exists():
        raise ReliableError("GW_CANDIDATE_BACKUP_CONFLICT")
    manifest = _load(source / "backup-manifest.json")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ReliableError("GW_CANDIDATE_BACKUP_INVALID")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ReliableError("GW_CANDIDATE_BACKUP_INVALID")
    for relative, digest in files.items():
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or any(part in {"", ".", ".."} for part in relative_path.parts):
            raise ReliableError("GW_CANDIDATE_BACKUP_INVALID")
        path = source / relative
        if not path.is_file() or _sha(path.read_bytes()) != digest:
            raise ReliableError("GW_CANDIDATE_BACKUP_INVALID")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("backup-manifest.json"))
    recover(destination)
    return _result("restored", active_base=active_base(destination))
