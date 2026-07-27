"""Result envelope helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .constants import INITIALIZER_VERSION, RESULT_VERSION


def stable_token(path: Path) -> str:
    digest = hashlib.sha256(path.as_posix().encode("utf-8")).hexdigest()[:12]
    return "kb:" + digest


def display_path(path: Path, home: Path) -> str:
    try:
        relative = path.relative_to(home)
    except ValueError:
        return "target:" + stable_token(path).removeprefix("kb:")
    if not relative.parts:
        return "~"
    return "~/" + relative.parts[-1]


def target_descriptor(path: Path, home: Path) -> dict[str, str]:
    return {
        "display_path": display_path(path, home),
        "root_token": stable_token(path),
    }


def issue(
    code: str,
    level: str,
    severity: str,
    path: str,
    message: str,
) -> dict[str, str]:
    return {
        "code": code,
        "level": level,
        "severity": severity,
        "path": path,
        "message": message,
    }


def envelope(
    *,
    ok: bool,
    command: str,
    target: dict[str, str],
    format_version,
    status: str,
    message: str,
    warnings=None,
    conflicts=None,
    findings=None,
    artifacts=None,
) -> dict[str, object]:
    return {
        "ok": ok,
        "command": command,
        "result_version": RESULT_VERSION,
        "initializer_version": INITIALIZER_VERSION,
        "format_version": format_version,
        "target": target,
        "summary": {
            "status": status,
            "message": message,
        },
        "warnings": list(warnings or []),
        "conflicts": list(conflicts or []),
        "findings": list(findings or []),
        "artifacts": dict(artifacts or {}),
    }


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False))
