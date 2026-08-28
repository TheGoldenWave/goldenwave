"""Template loading and rendering."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .constants import ASSET_ROOT, FORMAT_VERSION, INITIALIZER_VERSION, MANAGED_FILES, REQUIRED_DIRS, REQUIRED_FILES


class TemplateError(ValueError):
    """Bundled template metadata violates the frozen allowlist."""


def _render_content(content: str) -> str:
    rendered = (
        content.replace("{{FORMAT_VERSION}}", FORMAT_VERSION)
        .replace("{{INITIALIZER_VERSION}}", INITIALIZER_VERSION)
    )
    if "{{" in rendered or "}}" in rendered:
        raise TemplateError("template contains an unsupported variable")
    return rendered


def load_template_manifest() -> dict[str, object]:
    manifest_path = ASSET_ROOT / "template-manifest.json"
    with manifest_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    _validate_template_manifest(payload)
    return payload


def _validate_template_manifest(manifest: dict[str, object]) -> None:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise TemplateError("template entries must be a list")

    seen = set()
    directories = set()
    files = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") not in {"dir", "file"}:
            raise TemplateError("template entry is invalid")
        relative = entry.get("path")
        if not isinstance(relative, str) or not relative:
            raise TemplateError("template path is invalid")
        parsed = PurePosixPath(relative)
        if parsed.is_absolute() or ".." in parsed.parts or relative in seen:
            raise TemplateError("template path is unsafe")
        seen.add(relative)
        if entry["kind"] == "dir":
            directories.add(relative)
        else:
            if not isinstance(entry.get("content"), str):
                raise TemplateError("template file content is invalid")
            files.add(relative)

    created_directories = set(directories)
    for relative in (*directories, *files):
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            created_directories.add(parent.as_posix())
            parent = parent.parent

    expected_files = set(REQUIRED_FILES) - {".kb/goldenwave.json"}
    if files != expected_files or not set(REQUIRED_DIRS).issubset(created_directories):
        raise TemplateError("template layout differs from the frozen contract")


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def render_template(target: Path) -> dict[str, str]:
    manifest = load_template_manifest()
    entries = manifest.get("entries", [])
    directories = [item for item in entries if item.get("kind") == "dir"]
    files = [item for item in entries if item.get("kind") == "file"]

    for entry in sorted(directories, key=lambda item: item["path"]):
        (target / entry["path"]).mkdir(parents=True, exist_ok=True)

    if os.name != "nt":
        for relative in (".private", ".ephemeral"):
            (target / relative).chmod(0o700)

    for entry in files:
        path = target / entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render_content(entry["content"]), encoding="utf-8")

    managed_templates = {
        relative: _digest(target / relative)
        for relative in MANAGED_FILES
    }
    payload = {
        "format_version": FORMAT_VERSION,
        "initializer_version": INITIALIZER_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "managed_templates": managed_templates,
    }
    manifest_path = target / ".kb" / "goldenwave.json"
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return managed_templates
