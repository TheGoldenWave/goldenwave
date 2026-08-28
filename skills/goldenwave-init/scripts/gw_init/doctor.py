"""Doctor and adopt inventory checks."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from .constants import (
    EPHEMERAL_SENTINEL,
    FRONTMATTER_FILES,
    FORMAT_VERSION,
    IGNORE_RULES,
    MANAGED_FILES,
    PRIVATE_SENTINEL,
    REQUIRED_DIRS,
    REQUIRED_FILES,
)
from .git_policy import (
    check_ignored,
    is_git_repo,
    tracked_files,
    tracked_markdown_files,
    tracked_private_files,
    worktree_is_dirty,
)
from .result import issue


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_manifest(target: Path) -> tuple[dict[str, object] | None, str | None, list[dict[str, str]]]:
    findings = []
    manifest_path = target / ".kb" / "goldenwave.json"
    if not manifest_path.is_file():
        findings.append(issue("GW_MANIFEST_INVALID", "invalid", "error", ".kb/goldenwave.json", "manifest is missing"))
        return None, None, findings

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        findings.append(issue("GW_MANIFEST_INVALID", "invalid", "error", ".kb/goldenwave.json", "manifest is not valid JSON"))
        return None, None, findings

    format_version = payload.get("format_version")
    managed_templates = payload.get("managed_templates")
    if format_version is None or not isinstance(managed_templates, dict):
        findings.append(issue("GW_MANIFEST_INVALID", "invalid", "error", ".kb/goldenwave.json", "manifest is missing required keys"))
        return payload, format_version, findings

    expected_paths = sorted(MANAGED_FILES)
    actual_paths = sorted(managed_templates.keys())
    managed_list_valid = actual_paths == expected_paths
    if not managed_list_valid:
        findings.append(issue("GW_MANIFEST_INVALID", "invalid", "error", ".kb/goldenwave.json", "manifest managed template list is invalid"))

    # Never resolve manifest-controlled paths until the exact allowlist matches.
    for path, digest in managed_templates.items() if managed_list_valid else ():
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            findings.append(issue("GW_MANIFEST_INVALID", "invalid", "error", path, "managed template digest is invalid"))

    if format_version != FORMAT_VERSION:
        findings.append(issue("GW_MANIFEST_INVALID", "invalid", "error", ".kb/goldenwave.json", "manifest format version is not supported"))
    return payload, format_version, findings


def _read_ignore_lines(target: Path) -> set[str]:
    ignore_path = target / ".gitignore"
    if not ignore_path.is_file():
        return set()
    return {line.strip() for line in ignore_path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _ignore_present(lines: set[str], rule: str) -> bool:
    return rule in lines or rule.rstrip("/") in lines or "/" + rule in lines


def _scan_ephemeral_frontmatter(target: Path) -> list[dict[str, str]]:
    findings = []
    excluded_prefixes = (".private", ".ephemeral")
    for path in target.rglob("*.md"):
        relative = path.relative_to(target).as_posix()
        if relative.startswith(excluded_prefixes):
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                if handle.readline().rstrip("\r\n") != "---":
                    continue
                for line in handle:
                    stripped = line.strip()
                    if stripped == "---":
                        break
                    if stripped == "storage_class: ephemeral":
                        findings.append(
                            issue(
                                "GW_EPHEMERAL_FORMAL_PATH",
                                "unsafe",
                                "error",
                                relative,
                                "ephemeral markdown cannot live in a formal path",
                            )
                        )
                        break
        except (OSError, UnicodeError):
            findings.append(issue("GW_DOCTOR_FAILED", "invalid", "error", relative, "frontmatter cannot be inspected"))
    return findings


def _scan_boundary_symlinks(target: Path) -> list[dict[str, str]]:
    findings = []
    for root, dirnames, filenames in os.walk(target, followlinks=False):
        root_path = Path(root)
        for name in (*dirnames, *filenames):
            candidate = root_path / name
            if candidate.is_symlink():
                relative = candidate.relative_to(target).as_posix()
                findings.append(issue("GW_TARGET_UNSAFE", "unsafe", "error", relative, "symlinks are not allowed inside a managed target"))
    return findings


def _frontmatter_value(path: Path, key: str) -> str | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            if handle.readline().rstrip("\r\n") != "---":
                return None
            prefix = key + ":"
            for line in handle:
                stripped = line.strip()
                if stripped == "---":
                    return None
                if stripped.startswith(prefix):
                    return stripped.removeprefix(prefix).strip().strip("\"'")
    except (OSError, UnicodeError):
        return None
    return None


def _tracked_l3_findings(target: Path) -> list[dict[str, str]]:
    findings = []
    for relative in tracked_markdown_files(target, "profile"):
        if _frontmatter_value(target / relative, "sensitivity") == "L3":
            findings.append(
                issue(
                    "GW_POLICY_DRIFT",
                    "repairable",
                    "warning",
                    relative,
                    "tracked L3 metadata requires storage-class review",
                )
            )
    return findings


def _remote_policy_findings(target: Path) -> list[dict[str, str]]:
    contract = target / "profile" / "console" / "agent-contract.md"
    if contract.is_file() and _frontmatter_value(contract, "remote_model") != "deny":
        return [
            issue(
                "GW_POLICY_DRIFT",
                "repairable",
                "warning",
                "profile/console/agent-contract.md",
                "remote_model is not explicitly denied",
            )
        ]
    return []


def _has_closed_frontmatter(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as handle:
            if handle.readline().rstrip("\r\n") != "---":
                return False
            return any(line.rstrip("\r\n") == "---" for line in handle)
    except (OSError, UnicodeError):
        return False


def _frontmatter_findings(target: Path) -> list[dict[str, str]]:
    return [
        issue("GW_DOCTOR_FAILED", "invalid", "error", relative, "required frontmatter is missing or invalid")
        for relative in FRONTMATTER_FILES
        if (target / relative).is_file() and not _has_closed_frontmatter(target / relative)
    ]


def _permission_findings(target: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    if os.name == "nt":
        warning = issue("GW_DOCTOR_FAILED", "advisory", "warning", ".private", "POSIX private-directory permissions are unavailable on this platform")
        return [], [warning]

    findings = []
    for relative in (".private", ".ephemeral"):
        path = target / relative
        if path.is_dir() and stat.S_IMODE(path.stat().st_mode) & 0o077:
            findings.append(issue("GW_DOCTOR_FAILED", "unsafe", "error", relative, "private directory permissions are too broad"))
    return findings, []


def inspect_target(target: Path, *, read_only_mode: str) -> dict[str, object]:
    findings = []
    warnings = []
    conflicts = []

    if not target.is_dir():
        return {
            "ok": False,
            "format_version": None,
            "warnings": [],
            "conflicts": [],
            "findings": [issue("GW_DOCTOR_FAILED", "invalid", "error", "", "target directory is missing")],
        }

    findings.extend(_scan_boundary_symlinks(target))

    for relative in REQUIRED_DIRS:
        if read_only_mode == "adopt" and (
            relative == ".kb/candidate-decisions"
            or relative.startswith(".kb/reliable-inject")
        ):
            continue
        if not (target / relative).is_dir():
            findings.append(issue("GW_DOCTOR_FAILED", "invalid", "error", relative, "required directory is missing"))

    for relative in REQUIRED_FILES:
        if not (target / relative).is_file():
            findings.append(issue("GW_DOCTOR_FAILED", "invalid", "error", relative, "required file is missing"))

    findings.extend(_frontmatter_findings(target))
    permission_findings, permission_warnings = _permission_findings(target)
    findings.extend(permission_findings)
    warnings.extend(permission_warnings)

    manifest, format_version, manifest_findings = _parse_manifest(target)
    findings.extend(manifest_findings)

    ignore_lines = _read_ignore_lines(target)
    private_rule_present = _ignore_present(ignore_lines, IGNORE_RULES[0])
    ephemeral_rule_present = _ignore_present(ignore_lines, IGNORE_RULES[1])
    if not private_rule_present:
        findings.append(issue("GW_PRIVATE_NOT_IGNORED", "unsafe", "error", ".gitignore", "'.private/' must be ignored"))
    if not ephemeral_rule_present:
        findings.append(issue("GW_EPHEMERAL_NOT_IGNORED", "unsafe", "error", ".gitignore", "'.ephemeral/' must be ignored"))

    if is_git_repo(target):
        if private_rule_present and not check_ignored(target, PRIVATE_SENTINEL):
            findings.append(issue("GW_PRIVATE_NOT_IGNORED", "unsafe", "error", ".gitignore", "'.private/' is not ignored by Git behavior"))
        if ephemeral_rule_present and not check_ignored(target, EPHEMERAL_SENTINEL):
            findings.append(issue("GW_EPHEMERAL_NOT_IGNORED", "unsafe", "error", ".gitignore", "'.ephemeral/' is not ignored by Git behavior"))
        for relative in tracked_private_files(target):
            findings.append(issue("GW_PRIVATE_TRACKED", "unsafe", "error", relative, "local_private file is tracked by Git"))
        for relative in tracked_files(target, ".ephemeral"):
            findings.append(issue("GW_EPHEMERAL_FORMAL_PATH", "unsafe", "error", relative, "ephemeral file is tracked by Git"))
        findings.extend(_tracked_l3_findings(target))
        if worktree_is_dirty(target):
            dirty = issue("GW_POLICY_DRIFT", "advisory", "warning", "", "dirty worktree detected; inspection remained read-only")
            if read_only_mode == "doctor":
                warnings.append(dirty)
            else:
                findings.append(dirty)

    findings.extend(_scan_ephemeral_frontmatter(target))
    findings.extend(_remote_policy_findings(target))

    if manifest and isinstance(manifest.get("managed_templates"), dict) and sorted(manifest["managed_templates"]) == sorted(MANAGED_FILES):
        for relative, expected in manifest["managed_templates"].items():
            file_path = target / relative
            if not file_path.is_file():
                continue
            actual = _digest(file_path)
            if actual != expected:
                drift = issue("GW_POLICY_DRIFT", "advisory", "warning", relative, "managed template differs from manifest baseline")
                if read_only_mode == "doctor":
                    warnings.append(drift)
                else:
                    findings.append(
                        issue("GW_POLICY_DRIFT", "repairable", "warning", relative, "managed template differs from manifest baseline")
                    )

    ok = not findings
    return {
        "ok": ok,
        "format_version": format_version,
        "warnings": warnings,
        "conflicts": conflicts,
        "findings": findings,
    }
