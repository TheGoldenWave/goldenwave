"""Digest-bound, additive-only Phase 1C adopt repair."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .git_policy import worktree_is_dirty


RELIABLE_DIRS = (
    ".kb/reliable-inject",
    ".kb/reliable-inject/objects",
    ".kb/reliable-inject/manifests",
    ".kb/reliable-inject/transactions",
    ".kb/reliable-inject/receipts",
)


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
    material = json.dumps(actions, sort_keys=True, separators=(",", ":"))
    digest = "repair:" + hashlib.sha256(material.encode("utf-8")).hexdigest()
    return {"actions": actions, "plan_digest": digest}


def apply(target: Path, *, plan_digest: str, confirm: str) -> dict[str, object]:
    current = plan(target)
    expected = current["plan_digest"]
    if plan_digest != expected or confirm != expected:
        return {"ok": False, "code": "GW_REPAIR_CONFIRMATION_MISMATCH", **current}
    if worktree_is_dirty(target):
        return {"ok": False, "code": "GW_REPAIR_DIRTY_WORKTREE", **current}
    for action in current["actions"]:
        path = target / action["path"]
        path.mkdir(mode=0o700, parents=True, exist_ok=False)
    return {"ok": True, **current}
