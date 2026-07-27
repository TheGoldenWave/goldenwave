"""Target analysis and plan/apply orchestration."""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .constants import FORMAT_VERSION, GIT_MODE_INIT, MANAGED_FILES, REPO_ROOT
from .doctor import inspect_target
from .renderer import render_template
from .result import issue


@dataclass(frozen=True)
class TargetAnalysis:
    requested: Path
    canonical: Path
    exists: bool
    empty_dir: bool
    unsafe_reason: str | None
    parent_anchor: Path
    target_exists_and_is_dir: bool


def _absolute_input(target: str) -> Path:
    expanded = Path(target).expanduser()
    if expanded.is_absolute():
        return Path(os.path.abspath(str(expanded)))
    return Path(os.path.abspath(str(Path.cwd() / expanded)))


def analyze_target(target: str) -> TargetAnalysis:
    requested = _absolute_input(target)
    home = Path.home()
    if requested == Path("/"):
        return TargetAnalysis(requested, requested, requested.exists(), False, "root", requested.parent, False)
    if requested == home:
        return TargetAnalysis(requested, requested, requested.exists(), False, "home", requested.parent, False)
    if requested == REPO_ROOT:
        return TargetAnalysis(requested, requested, requested.exists(), False, "repo", requested.parent, False)
    if not requested.parent.exists():
        return TargetAnalysis(requested, requested, requested.exists(), False, "parent_missing", requested.parent, False)
    if not os.access(requested.parent, os.W_OK):
        return TargetAnalysis(requested, requested, requested.exists(), False, "parent_not_writable", requested.parent, False)

    anchor = requested
    while not anchor.exists():
        anchor = anchor.parent
    resolved_anchor = anchor.resolve(strict=True)
    if anchor.is_symlink():
        return TargetAnalysis(requested, requested, requested.exists(), False, "symlink", anchor.parent, False)

    relative_parts = requested.relative_to(anchor).parts if anchor != requested else ()
    current = resolved_anchor
    for part in relative_parts:
        candidate = current / part
        if candidate.exists() and candidate.is_symlink():
            return TargetAnalysis(requested, requested, requested.exists(), False, "symlink", resolved_anchor, False)
        current = candidate

    exists = requested.exists()
    target_is_dir = requested.is_dir()
    empty_dir = exists and target_is_dir and not any(requested.iterdir())
    return TargetAnalysis(requested, requested, exists, empty_dir, None, resolved_anchor, target_is_dir)


def detect_existing_state(target: Path) -> str:
    if not target.exists():
        return "absent"
    if not target.is_dir():
        return "unsafe"
    if not any(target.iterdir()):
        return "empty"

    manifest_path = target / ".kb" / "goldenwave.json"
    if not manifest_path.is_file():
        return "not_empty"

    result = inspect_target(target, read_only_mode="doctor")
    if result["findings"]:
        managed_conflicts = [
            item for item in result["findings"]
            if item["code"] in {"GW_MANIFEST_INVALID", "GW_DOCTOR_FAILED", "GW_PRIVATE_NOT_IGNORED", "GW_EPHEMERAL_NOT_IGNORED", "GW_PRIVATE_TRACKED", "GW_EPHEMERAL_FORMAL_PATH"}
        ]
        if managed_conflicts:
            return "changed"

    if result["warnings"]:
        return "changed"

    managed_set = set(MANAGED_FILES)
    manifest = manifest_path.read_text(encoding="utf-8")
    if all(path in manifest for path in managed_set):
        return "managed"
    return "changed"


def _prepare_staging(target: Path) -> tuple[Path, Path]:
    anchor = target.parent if target.parent.exists() else target.parent
    while not anchor.exists():
        anchor = anchor.parent
    temp_root = Path(tempfile.mkdtemp(prefix=".gw-init-", dir=anchor))
    payload = temp_root / target.name
    return temp_root, payload


def apply_new(target: Path, git_mode: str) -> dict[str, object]:
    if git_mode == GIT_MODE_INIT and shutil.which("git") is None:
        return {
            "ok": False,
            "status": "blocked",
            "message": "git was requested but is unavailable",
            "warnings": [],
            "conflicts": [issue("GW_GIT_UNAVAILABLE", "invalid", "error", "", "git was requested but is unavailable")],
            "findings": [],
            "artifacts": {},
        }

    state = detect_existing_state(target)
    if state == "managed":
        if git_mode == GIT_MODE_INIT and not (target / ".git").exists():
            git_result = subprocess.run(["git", "init"], cwd=target, capture_output=True, text=True, check=False)
            if git_result.returncode != 0:
                return _git_failure()
        return {
            "ok": True,
            "status": "ok",
            "message": "target already matches the managed template",
            "warnings": [],
            "conflicts": [],
            "findings": [],
            "artifacts": {
                "git_mode": git_mode,
                "managed_template_count": len(MANAGED_FILES),
                "noop": True,
            },
        }

    if state == "unsafe":
        return {
            "ok": False,
            "status": "blocked",
            "message": "target is unsafe",
            "warnings": [],
            "conflicts": [issue("GW_TARGET_UNSAFE", "unsafe", "error", "", "target is not a directory")],
            "findings": [],
            "artifacts": {},
        }
    if state == "not_empty":
        return {
            "ok": False,
            "status": "blocked",
            "message": "target must be empty for new mode",
            "warnings": [],
            "conflicts": [issue("GW_TARGET_NOT_EMPTY", "repairable", "error", "", "new mode does not accept non-empty targets")],
            "findings": [],
            "artifacts": {},
        }
    if state == "changed":
        return {
            "ok": False,
            "status": "blocked",
            "message": "target contains a changed managed GoldenWave layout",
            "warnings": [],
            "conflicts": [issue("GW_TARGET_CHANGED", "repairable", "error", "", "managed target differs from its manifest baseline")],
            "findings": [],
            "artifacts": {},
        }

    temp_root, payload = _prepare_staging(target)
    try:
        try:
            render_template(payload)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            return {
                "ok": False,
                "status": "failed",
                "message": "bundled template is invalid",
                "warnings": [],
                "conflicts": [],
                "findings": [
                    issue("GW_TEMPLATE_INVALID", "invalid", "error", "", "bundled template is invalid"),
                    issue("GW_APPLY_INCOMPLETE", "invalid", "error", "", "apply aborted before install"),
                ],
                "artifacts": {"error_class": type(error).__name__},
            }
        preflight = inspect_target(payload, read_only_mode="doctor")
        if preflight["findings"]:
            return {
                "ok": False,
                "status": "failed",
                "message": "rendered template did not pass preflight",
                "warnings": preflight["warnings"],
                "conflicts": [],
                "findings": preflight["findings"] + [issue("GW_APPLY_INCOMPLETE", "invalid", "error", "", "apply aborted before install")],
                "artifacts": {},
            }

        try:
            if target.exists():
                target.rmdir()
            payload.rename(target)
        except OSError:
            return {
                "ok": False,
                "status": "blocked",
                "message": "target changed before atomic placement",
                "warnings": [],
                "conflicts": [issue("GW_TARGET_CHANGED", "repairable", "error", "", "target changed before atomic placement")],
                "findings": [],
                "artifacts": {},
            }
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)

    doctor_result = inspect_target(target, read_only_mode="doctor")
    if doctor_result["findings"]:
        return {
            "ok": False,
            "status": "failed",
            "message": "doctor failed after apply",
            "warnings": doctor_result["warnings"],
            "conflicts": [],
            "findings": doctor_result["findings"],
            "artifacts": {
                "git_mode": git_mode,
                "managed_template_count": len(MANAGED_FILES),
            },
        }

    if git_mode == GIT_MODE_INIT:
        git_result = subprocess.run(["git", "init"], cwd=target, capture_output=True, text=True, check=False)
        if git_result.returncode != 0:
            return _git_failure()
        doctor_result = inspect_target(target, read_only_mode="doctor")
        if doctor_result["findings"]:
            return {
                "ok": False,
                "status": "failed",
                "message": "doctor failed after git init",
                "warnings": doctor_result["warnings"],
                "conflicts": [],
                "findings": doctor_result["findings"],
                "artifacts": {
                    "git_mode": git_mode,
                    "managed_template_count": len(MANAGED_FILES),
                },
            }

    return {
        "ok": True,
        "status": "ok",
        "message": "target initialized",
        "warnings": doctor_result["warnings"],
        "conflicts": [],
        "findings": [],
        "artifacts": {
            "git_mode": git_mode,
            "managed_template_count": len(MANAGED_FILES),
            "format_version": FORMAT_VERSION,
        },
    }


def _git_failure() -> dict[str, object]:
    return {
        "ok": False,
        "status": "failed",
        "message": "git init failed",
        "warnings": [],
        "conflicts": [],
        "findings": [issue("GW_GIT_UNAVAILABLE", "invalid", "error", "", "git init failed")],
        "artifacts": {},
    }
