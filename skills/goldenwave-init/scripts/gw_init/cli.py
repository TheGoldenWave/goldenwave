"""CLI surface for GoldenWave init."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from .constants import (
    COMMAND_ADOPT_INVENTORY,
    COMMAND_APPLY,
    COMMAND_DOCTOR,
    COMMAND_PLAN,
    FORMAT_VERSION,
    GIT_MODE_INIT,
    GIT_MODE_OFF,
)
from .doctor import inspect_target
from .planner import analyze_target, apply_new, detect_existing_state
from .result import emit, envelope, issue, target_descriptor


def _common_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="goldenwave_init.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in (COMMAND_PLAN, COMMAND_APPLY, COMMAND_DOCTOR):
        command = subparsers.add_parser(name)
        command.add_argument("--target", required=True)
        if name != COMMAND_DOCTOR:
            command.add_argument("--mode", required=(name != COMMAND_DOCTOR), choices=["new"])
        if name == COMMAND_APPLY:
            command.add_argument("--git", choices=[GIT_MODE_OFF, GIT_MODE_INIT], default=GIT_MODE_OFF)
        command.add_argument("--format", choices=["json"], required=True)

    adopt = subparsers.add_parser("adopt")
    adopt_subparsers = adopt.add_subparsers(dest="adopt_command", required=True)
    inventory = adopt_subparsers.add_parser("inventory")
    inventory.add_argument("--target", required=True)
    inventory.add_argument("--format", choices=["json"], required=True)
    return parser


def _unsafe_response(command: str, target: Path, reason: str) -> dict[str, object]:
    return envelope(
        ok=False,
        command=command,
        target=target_descriptor(target, Path.home()),
        format_version=FORMAT_VERSION if command in {COMMAND_PLAN, COMMAND_APPLY} else None,
        status="blocked",
        message="target is unsafe",
        conflicts=[issue("GW_TARGET_UNSAFE", "unsafe", "error", "", "target is unsafe: " + reason)],
    )


def _plan(target_text: str) -> dict[str, object]:
    analysis = analyze_target(target_text)
    target = target_descriptor(analysis.canonical, Path.home())
    if analysis.unsafe_reason:
        return _unsafe_response(COMMAND_PLAN, analysis.canonical, analysis.unsafe_reason)

    state = detect_existing_state(analysis.canonical)
    if state == "not_empty":
        return envelope(
            ok=False,
            command=COMMAND_PLAN,
            target=target,
            format_version=FORMAT_VERSION,
            status="blocked",
            message="target must be empty for new mode",
            conflicts=[issue("GW_TARGET_NOT_EMPTY", "repairable", "error", "", "new mode does not accept non-empty targets")],
        )
    if state == "unsafe":
        return _unsafe_response(COMMAND_PLAN, analysis.canonical, "target is not a directory")
    if state == "changed":
        return envelope(
            ok=False,
            command=COMMAND_PLAN,
            target=target,
            format_version=FORMAT_VERSION,
            status="blocked",
            message="target contains a changed managed GoldenWave layout",
            conflicts=[issue("GW_TARGET_CHANGED", "repairable", "error", "", "managed target differs from its manifest baseline")],
        )

    message = "ready to apply" if state in {"absent", "empty"} else "target already matches the managed template"
    plan_material = "|".join((analysis.canonical.as_posix(), state, FORMAT_VERSION))
    plan_id = "plan:" + hashlib.sha256(plan_material.encode("utf-8")).hexdigest()[:16]
    return envelope(
        ok=True,
        command=COMMAND_PLAN,
        target=target,
        format_version=FORMAT_VERSION,
        status="ok",
        message=message,
        artifacts={
            "actions": ["render_template", "write_manifest", "doctor"],
            "git_mode": GIT_MODE_OFF,
            "mode": "new",
            "plan_id": plan_id,
        },
    )


def _apply(target_text: str, git_mode: str) -> dict[str, object]:
    analysis = analyze_target(target_text)
    if analysis.unsafe_reason:
        return _unsafe_response(COMMAND_APPLY, analysis.canonical, analysis.unsafe_reason)
    result = apply_new(analysis.canonical, git_mode)
    return envelope(
        ok=result["ok"],
        command=COMMAND_APPLY,
        target=target_descriptor(analysis.canonical, Path.home()),
        format_version=FORMAT_VERSION,
        status=result["status"],
        message=result["message"],
        warnings=result["warnings"],
        conflicts=result["conflicts"],
        findings=result["findings"],
        artifacts=result["artifacts"],
    )


def _doctor(target_text: str) -> dict[str, object]:
    analysis = analyze_target(target_text)
    target = target_descriptor(analysis.canonical, Path.home())
    if analysis.unsafe_reason:
        return _unsafe_response(COMMAND_DOCTOR, analysis.canonical, analysis.unsafe_reason)
    result = inspect_target(analysis.canonical, read_only_mode="doctor")
    return envelope(
        ok=result["ok"],
        command=COMMAND_DOCTOR,
        target=target,
        format_version=result["format_version"],
        status="ok" if result["ok"] else "failed",
        message="doctor passed" if result["ok"] else "doctor found blocking issues",
        warnings=result["warnings"],
        conflicts=result["conflicts"],
        findings=result["findings"],
        artifacts={"mode": "read-only"},
    )


def _adopt_inventory(target_text: str) -> dict[str, object]:
    analysis = analyze_target(target_text)
    target = target_descriptor(analysis.canonical, Path.home())
    if analysis.unsafe_reason:
        return _unsafe_response(COMMAND_ADOPT_INVENTORY, analysis.canonical, analysis.unsafe_reason)
    result = inspect_target(analysis.canonical, read_only_mode="adopt")
    ok = not any(item["level"] in {"unsafe", "invalid"} for item in result["findings"])
    return envelope(
        ok=ok,
        command=COMMAND_ADOPT_INVENTORY,
        target=target,
        format_version=result["format_version"],
        status="ok" if ok else "failed",
        message="inventory completed" if ok else "inventory found blocking issues",
        warnings=result["warnings"],
        conflicts=result["conflicts"],
        findings=result["findings"],
        artifacts={"mode": "read-only"},
    )


def main(argv: list[str]) -> int:
    parser = _common_parser()
    args = parser.parse_args(argv)

    if args.command == COMMAND_PLAN:
        payload = _plan(args.target)
    elif args.command == COMMAND_APPLY:
        payload = _apply(args.target, args.git)
    elif args.command == COMMAND_DOCTOR:
        payload = _doctor(args.target)
    else:
        payload = _adopt_inventory(args.target)

    emit(payload)
    return 0 if payload["ok"] else 1
