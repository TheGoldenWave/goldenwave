"""Digest-bound, additive-only Phase 1C adopt repair."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Callable

from .git_policy import (
    tracked_files,
    tracked_markdown_files,
    tracked_private_files,
    worktree_is_dirty,
)


RELIABLE_DIRS = (
    ".kb/reliable-inject",
    ".kb/reliable-inject/objects",
    ".kb/reliable-inject/manifests",
    ".kb/reliable-inject/transactions",
    ".kb/reliable-inject/receipts",
)
RELIABLE_FILES = {
    ".kb/reliable-inject/active.json": '{"active_base":"base_0000000000000000000000000000000000000000000000000000000000000000","manifest":null,"version":"gw-reliable-inject/v0.1"}\n',
    ".kb/reliable-inject/lock": "",
}
BoundaryHook = Callable[[str, Path], None]


def _tracked_l3_exists(target: Path) -> bool:
    for relative in tracked_markdown_files(target, "profile"):
        try:
            lines = (target / relative).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            return True
        if not lines or lines[0] != "---":
            continue
        for line in lines[1:]:
            if line == "---":
                break
            if line.strip() == "sensitivity: L3":
                return True
    return False


def plan(target: Path) -> dict[str, object]:
    if not target.is_dir() or target.is_symlink():
        raise ValueError("unsafe repair root")
    marker = target / ".kb/goldenwave.json"
    if marker.is_symlink() or not marker.is_file():
        raise ValueError("invalid GoldenWave marker")
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("invalid GoldenWave marker") from None
    if payload.get("format_version") != "gwkb/v0.1":
        raise ValueError("unsupported GoldenWave marker")
    if (
        tracked_private_files(target)
        or tracked_files(target, ".ephemeral")
        or _tracked_l3_exists(target)
    ):
        raise ValueError("storage boundary must be repaired before adopt repair")
    actions = []
    for relative in RELIABLE_DIRS:
        path = target / relative
        cursor = target
        for component in Path(relative).parts:
            cursor = cursor / component
            if cursor.is_symlink():
                raise ValueError("unsafe managed repair path")
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError("unsafe managed repair path")
        if not path.exists():
            actions.append({"action": "create_directory", "path": relative})
    for relative in RELIABLE_FILES:
        path = target / relative
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError("unsafe managed repair path")
        if not path.exists():
            actions.append({"action": "create_file", "path": relative})
    root_metadata = target.stat()
    material = json.dumps(
        {
            "actions": actions,
            "root_device": root_metadata.st_dev,
            "root_inode": root_metadata.st_ino,
            "marker_sha256": hashlib.sha256(marker.read_bytes()).hexdigest(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = "repair:" + hashlib.sha256(material.encode("utf-8")).hexdigest()
    return {"actions": actions, "plan_digest": digest}


def _open_parent(target: Path, relative: str) -> tuple[int, str]:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags)
    try:
        for component in Path(relative).parts[:-1]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor, Path(relative).parts[-1]
    except BaseException:
        os.close(descriptor)
        raise


def _create_directory(target: Path, relative: str) -> None:
    parent_fd, name = _open_parent(target, relative)
    try:
        os.mkdir(name, mode=0o700, dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def _create_file(target: Path, relative: str, content: str) -> None:
    parent_fd, name = _open_parent(target, relative)
    descriptor: int | None = None
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_fd,
        )
        remaining = memoryview(content.encode("utf-8"))
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("short write")
            remaining = remaining[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.fsync(parent_fd)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)


def apply(
    target: Path,
    *,
    plan_digest: str,
    confirm: str,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, object]:
    current = plan(target)
    expected = current["plan_digest"]
    if plan_digest != expected or confirm != expected:
        return {"ok": False, "code": "GW_REPAIR_CONFIRMATION_MISMATCH", **current}
    if worktree_is_dirty(target):
        return {"ok": False, "code": "GW_REPAIR_DIRTY_WORKTREE", **current}
    try:
        for action in current["actions"]:
            path = target / action["path"]
            if action["action"] == "create_directory":
                if boundary_hook is not None:
                    boundary_hook("before_create_directory", path)
                _create_directory(target, action["path"])
            else:
                if boundary_hook is not None:
                    boundary_hook("before_create_file", path)
                _create_file(target, action["path"], RELIABLE_FILES[action["path"]])
    except OSError:
        return {"ok": False, "code": "GW_REPAIR_TARGET_CHANGED", **current}
    return {"ok": True, **current}
