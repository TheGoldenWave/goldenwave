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
from typing import Any, Iterator

from . import safe_write


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


class ReliableError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _load(path: Path) -> dict[str, Any]:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    value = json.loads(path.read_text(encoding="utf-8"))
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


def _operation(candidate: dict[str, Any], raw: bytes) -> str:
    material = b"\0".join((b"accept", raw, _target(candidate).encode("utf-8")))
    return "op_" + _sha(material)


def _idempotency(operation_id: str, base: str) -> str:
    return "idem_" + _sha((operation_id + "\0" + base).encode("ascii"))


def initialize(root: Path) -> None:
    marker = root / ".kb/goldenwave.json"
    if not marker.is_file() or marker.is_symlink():
        raise ReliableError("GW_CANDIDATE_KB_UNSAFE")
    for relative in (ROOT, *DIRECTORIES):
        path = root / relative
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.is_symlink():
            raise ReliableError("GW_CANDIDATE_KB_UNSAFE")
    lock = root / LOCK
    lock.touch(mode=0o600, exist_ok=True)
    active = root / ACTIVE
    if not active.exists():
        _atomic(active, _json({"version": VERSION, "active_base": EMPTY_BASE, "manifest": None}))


def active_base(root: Path) -> str:
    payload = _load(root / ACTIVE)
    value = payload.get("active_base")
    if not isinstance(value, str) or not value.startswith("base_"):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    return value


def review(
    root: Path,
    candidate: dict[str, Any],
    raw: bytes,
    *,
    active_base: str | None = None,
) -> dict[str, str]:
    base = active_base if active_base is not None else globals()["active_base"](root)
    operation_id = _operation(candidate, raw)
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
        if path.read_bytes() != content:
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
) -> dict[str, Any]:
    identity = review(root, candidate, raw, active_base=expected_base)
    if idempotency_key != identity["idempotency_key"]:
        return _result("failed", error="GW_CANDIDATE_IDEMPOTENCY_MISMATCH")
    operation_id = identity["operation_id"]
    receipt_path = root / RECEIPTS / f"{operation_id}.json"
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
        _exclusive(root / OBJECTS / object_hash, content)
        target = _target(candidate)
        entries = _active_entries(root)
        if target in entries and entries[target] != object_hash:
            return _result("failed", error="GW_CANDIDATE_CONFLICT")
        entries[target] = object_hash
        manifest = {"version": VERSION, "parent": current, "operation_id": operation_id, "entries": entries}
        manifest_bytes = _json(manifest)
        manifest_hash = _sha(manifest_bytes)
        next_base = "base_" + manifest_hash
        journal = {
            "version": VERSION,
            "state": "prepared",
            "operation_id": operation_id,
            "idempotency_key": idempotency_key,
            "expected_base": expected_base,
            "active_base": next_base,
            "manifest": manifest_hash,
        }
        _exclusive(root / TRANSACTIONS / f"{operation_id}.json", _json(journal))
        _exclusive(root / MANIFESTS / f"{manifest_hash}.json", manifest_bytes)
        _atomic(root / ACTIVE, _json({"version": VERSION, "active_base": next_base, "manifest": manifest_hash}))
        try:
            _materialize(root, target, object_hash)
        except (OSError, ReliableError):
            return _result("indeterminate", error="GW_CANDIDATE_APPLY_INDETERMINATE", operation_id=operation_id, active_base=next_base)
        receipt = {**journal, "state": "completed"}
        _exclusive(receipt_path, _json(receipt))
        return _result("applied", replayed=False, operation_id=operation_id, active_base=next_base)


def _active_entries(root: Path) -> dict[str, str]:
    active = _load(root / ACTIVE)
    manifest_hash = active.get("manifest")
    if manifest_hash is None:
        return {}
    manifest = _load(root / MANIFESTS / f"{manifest_hash}.json")
    entries = manifest.get("entries")
    if not isinstance(entries, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in entries.items()):
        raise ReliableError("GW_CANDIDATE_TRANSACTION_CORRUPT")
    return dict(entries)


def _materialize(root: Path, target: str, object_hash: str) -> None:
    content = (root / OBJECTS / object_hash).read_bytes()
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


def recover(root: Path) -> dict[str, Any]:
    with _locked(root):
        entries = _active_entries(root)
        for target, object_hash in entries.items():
            _materialize(root, target, object_hash)
        active = _load(root / ACTIVE)
        manifest_hash = active.get("manifest")
        for journal_path in sorted((root / TRANSACTIONS).glob("op_*.json")):
            journal = _load(journal_path)
            if journal.get("active_base") != active.get("active_base"):
                continue
            receipt_path = root / RECEIPTS / f"{journal['operation_id']}.json"
            if not receipt_path.exists():
                _exclusive(receipt_path, _json({**journal, "state": "completed", "manifest": manifest_hash}))
        return _result("recovered", repaired=len(entries))


def backup(root: Path, destination: Path) -> dict[str, Any]:
    if destination.exists():
        raise ReliableError("GW_CANDIDATE_BACKUP_CONFLICT")
    destination.mkdir(parents=True)
    with _locked(root):
        for path in (root / ROOT, root / ".kb/goldenwave.json", *(root / ROOT).rglob("*")):
            if path.is_symlink():
                raise ReliableError("GW_CANDIDATE_KB_UNSAFE")
        shutil.copytree(root / ROOT, destination / ROOT)
        shutil.copy2(root / ".kb/goldenwave.json", destination / ".kb/goldenwave.json")
        inventory = {}
        for path in sorted(p for p in destination.rglob("*") if p.is_file()):
            inventory[path.relative_to(destination).as_posix()] = _sha(path.read_bytes())
        (destination / "backup-manifest.json").write_bytes(_json({"version": VERSION, "files": inventory}))
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
