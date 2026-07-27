"""Read-only Git helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repo(target: Path) -> bool:
    result = run_git(target, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return False
    try:
        return Path(result.stdout.strip()).resolve(strict=True) == target.resolve(strict=True)
    except OSError:
        return False


def check_ignored(target: Path, relative_path: str) -> bool:
    if not is_git_repo(target):
        return False
    result = run_git(target, "check-ignore", "-q", "--", relative_path)
    return result.returncode == 0


def tracked_files(target: Path, storage_root: str) -> list[str]:
    if not is_git_repo(target):
        return []
    result = run_git(target, "ls-files", "--cached", "--", storage_root)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def tracked_private_files(target: Path) -> list[str]:
    return tracked_files(target, ".private")


def tracked_markdown_files(target: Path, storage_root: str) -> list[str]:
    return [path for path in tracked_files(target, storage_root) if path.endswith(".md")]


def worktree_is_dirty(target: Path) -> bool:
    if not is_git_repo(target):
        return False
    result = run_git(target, "status", "--porcelain=v1")
    return result.returncode == 0 and bool(result.stdout)
