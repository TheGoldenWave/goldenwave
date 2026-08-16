"""Descriptor-relative exclusive writes for Candidate decision artifacts."""

from __future__ import annotations

import errno
import os
import stat
import unicodedata
from pathlib import Path
from typing import Callable


CONFLICT = "GW_CANDIDATE_CONFLICT"
KB_UNSAFE = "GW_CANDIDATE_KB_UNSAFE"
PLATFORM_UNSUPPORTED = "GW_CANDIDATE_PLATFORM_UNSUPPORTED"
TARGET_UNSAFE = "GW_CANDIDATE_TARGET_UNSAFE"
WRITE_FAILED = "GW_CANDIDATE_WRITE_FAILED"

BIDI_CONTROL_CODEPOINTS = frozenset(
    {0x061C, 0x200E, 0x200F}
    | set(range(0x202A, 0x202F))
    | set(range(0x2066, 0x206A))
)

PATH_STRUCTURE_ERRNOS = frozenset(
    {
        errno.ENOENT,
        errno.ENOTDIR,
        errno.ELOOP,
        errno.ENAMETOOLONG,
    }
)

FILE_MODE = 0o600
PLATFORM_SUPPORTED = all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_EXCL"))
DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW if PLATFORM_SUPPORTED else None
)
FILE_FLAGS = (
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW if PLATFORM_SUPPORTED else None
)
if PLATFORM_SUPPORTED and hasattr(os, "O_CLOEXEC"):
    assert DIRECTORY_FLAGS is not None
    assert FILE_FLAGS is not None
    DIRECTORY_FLAGS |= os.O_CLOEXEC
    FILE_FLAGS |= os.O_CLOEXEC


class SafeWriteError(Exception):
    """A controlled write failure that does not disclose filesystem paths."""

    def __init__(
        self,
        code: str,
        *,
        artifact_created: bool = False,
        cleanup_confirmed: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.artifact_created = artifact_created
        self.cleanup_confirmed = cleanup_confirmed


def _components(relative_path: str) -> tuple[str, ...]:
    if not isinstance(relative_path, str) or not relative_path:
        raise SafeWriteError(TARGET_UNSAFE)
    if unicodedata.normalize("NFC", relative_path) != relative_path:
        raise SafeWriteError(TARGET_UNSAFE)
    if any(ord(character) in BIDI_CONTROL_CODEPOINTS for character in relative_path):
        raise SafeWriteError(TARGET_UNSAFE)
    if relative_path.startswith("/") or "\\" in relative_path:
        raise SafeWriteError(TARGET_UNSAFE)
    if any(ord(character) < 32 or ord(character) == 127 for character in relative_path):
        raise SafeWriteError(TARGET_UNSAFE)

    components = tuple(relative_path.split("/"))
    if len(components) < 2 or any(component in {"", ".", ".."} for component in components):
        raise SafeWriteError(TARGET_UNSAFE)
    return components


def _error_for_oserror(error: OSError) -> SafeWriteError:
    code = TARGET_UNSAFE if error.errno in PATH_STRUCTURE_ERRNOS else WRITE_FAILED
    return SafeWriteError(code)


def _root_error_for_oserror(error: OSError) -> SafeWriteError:
    code = KB_UNSAFE if error.errno in PATH_STRUCTURE_ERRNOS else WRITE_FAILED
    return SafeWriteError(code)


def _safe_close(descriptor: int) -> bool:
    try:
        os.close(descriptor)
    except OSError:
        return False
    return True


def _open_parent(
    root: Path,
    components: tuple[str, ...],
    expected_root_identity: tuple[int, int] | None,
    expected_component_identities: dict[str, tuple[int, int]] | None,
) -> tuple[int, int]:
    assert DIRECTORY_FLAGS is not None
    try:
        root_fd = os.open(root, DIRECTORY_FLAGS)
    except OSError as error:
        raise _root_error_for_oserror(error) from error
    except (TypeError, ValueError) as error:
        raise SafeWriteError(KB_UNSAFE) from error

    descriptor = root_fd
    try:
        if expected_root_identity is not None and _identity(root_fd) != expected_root_identity:
            raise SafeWriteError(KB_UNSAFE)
        traversed: list[str] = []
        for component in components[:-1]:
            next_descriptor = os.open(component, DIRECTORY_FLAGS, dir_fd=descriptor)
            if descriptor != root_fd and not _safe_close(descriptor):
                _safe_close(next_descriptor)
                raise SafeWriteError(WRITE_FAILED)
            descriptor = next_descriptor
            traversed.append(component)
            expected_identity = (expected_component_identities or {}).get("/".join(traversed))
            if expected_identity is not None and _identity(descriptor) != expected_identity:
                raise SafeWriteError(KB_UNSAFE)
        return root_fd, descriptor
    except OSError as error:
        if descriptor != root_fd:
            _safe_close(descriptor)
        _safe_close(root_fd)
        raise _error_for_oserror(error) from error
    except (TypeError, ValueError) as error:
        if descriptor != root_fd:
            _safe_close(descriptor)
        _safe_close(root_fd)
        raise SafeWriteError(TARGET_UNSAFE) from error
    except SafeWriteError:
        if descriptor != root_fd:
            _safe_close(descriptor)
        _safe_close(root_fd)
        raise


def _identity(descriptor: int) -> tuple[int, int]:
    metadata = os.fstat(descriptor)
    return metadata.st_dev, metadata.st_ino


def _ancestry_reaches_root(parent_fd: int, root_identity: tuple[int, int]) -> bool:
    assert DIRECTORY_FLAGS is not None
    current_fd = os.open(".", DIRECTORY_FLAGS, dir_fd=parent_fd)
    try:
        while True:
            current_identity = _identity(current_fd)
            if current_identity == root_identity:
                return True
            ancestor_fd = os.open("..", DIRECTORY_FLAGS, dir_fd=current_fd)
            ancestor_transferred = False
            try:
                ancestor_identity = _identity(ancestor_fd)
                if not _safe_close(current_fd):
                    raise SafeWriteError(WRITE_FAILED)
                current_fd = ancestor_fd
                ancestor_transferred = True
            finally:
                if not ancestor_transferred:
                    _safe_close(ancestor_fd)
            if ancestor_identity == current_identity:
                return False
    finally:
        _safe_close(current_fd)


def _reopened_parent_matches(
    root: Path,
    components: tuple[str, ...],
    root_identity: tuple[int, int],
    parent_identity: tuple[int, int],
    expected_component_identities: dict[str, tuple[int, int]] | None,
) -> bool:
    assert DIRECTORY_FLAGS is not None
    verification_root_fd: int | None = None
    descriptor: int | None = None
    try:
        try:
            verification_root_fd = os.open(root, DIRECTORY_FLAGS)
        except OSError as error:
            raise _root_error_for_oserror(error) from error
        descriptor = verification_root_fd
        if _identity(verification_root_fd) != root_identity:
            return False
        traversed: list[str] = []
        for component in components[:-1]:
            try:
                next_descriptor = os.open(component, DIRECTORY_FLAGS, dir_fd=descriptor)
            except OSError as error:
                raise _error_for_oserror(error) from error
            if descriptor != verification_root_fd and not _safe_close(descriptor):
                _safe_close(next_descriptor)
                raise SafeWriteError(WRITE_FAILED)
            descriptor = next_descriptor
            traversed.append(component)
            expected_identity = (expected_component_identities or {}).get("/".join(traversed))
            if expected_identity is not None and _identity(descriptor) != expected_identity:
                raise SafeWriteError(KB_UNSAFE)
        return _identity(descriptor) == parent_identity
    finally:
        if descriptor is not None and descriptor != verification_root_fd:
            _safe_close(descriptor)
        if verification_root_fd is not None:
            _safe_close(verification_root_fd)


def _path_still_names_parent(
    root: Path,
    components: tuple[str, ...],
    root_identity: tuple[int, int],
    parent_identity: tuple[int, int],
    expected_component_identities: dict[str, tuple[int, int]] | None,
) -> bool:
    return _reopened_parent_matches(
        root,
        components,
        root_identity,
        parent_identity,
        expected_component_identities,
    )


def _remove_unconfirmed(parent_fd: int, filename: str) -> bool:
    try:
        os.unlink(filename, dir_fd=parent_fd)
    except OSError:
        return False
    try:
        os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        cleanup_confirmed = True
    except OSError:
        cleanup_confirmed = False
    else:
        cleanup_confirmed = False
    try:
        os.fsync(parent_fd)
    except OSError:
        return False
    return cleanup_confirmed


def _write_all(descriptor: int, content: bytes) -> None:
    remaining = memoryview(content)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError(errno.EIO, "write made no progress")
        remaining = remaining[written:]


def write_exclusive(
    root: Path,
    relative_path: str,
    content: bytes,
    *,
    role: str,
    expected_root_identity: tuple[int, int] | None = None,
    expected_component_identities: dict[str, tuple[int, int]] | None = None,
    boundary_hook: Callable[[str], None] | None = None,
) -> None:
    """Create one file beneath ``root`` without following or replacing links."""

    if not PLATFORM_SUPPORTED:
        raise SafeWriteError(PLATFORM_UNSUPPORTED)
    assert FILE_FLAGS is not None
    components = _components(relative_path)
    filename = components[-1]
    root_fd, parent_fd = _open_parent(
        root,
        components,
        expected_root_identity,
        expected_component_identities,
    )
    file_fd: int | None = None
    file_created = False
    file_fsync_confirmed = False
    failure: SafeWriteError | None = None

    try:
        try:
            file_fd = os.open(filename, FILE_FLAGS, FILE_MODE, dir_fd=parent_fd)
            file_created = True
        except FileExistsError as error:
            raise SafeWriteError(CONFLICT) from error
        except OSError as error:
            raise _error_for_oserror(error) from error

        try:
            metadata = os.fstat(file_fd)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise SafeWriteError(TARGET_UNSAFE)
            root_identity = _identity(root_fd)
            parent_identity = _identity(parent_fd)
            ancestry_is_safe = _ancestry_reaches_root(parent_fd, root_identity)
            path_is_safe = _path_still_names_parent(
                root,
                components,
                root_identity,
                parent_identity,
                expected_component_identities,
            )
            if not ancestry_is_safe or not path_is_safe:
                raise SafeWriteError(TARGET_UNSAFE)
            _write_all(file_fd, content)
            os.fsync(file_fd)
            file_fsync_confirmed = True
            if boundary_hook is not None:
                boundary_hook(f"{role}:file_fsync")
        except SafeWriteError:
            raise
        except OSError as error:
            raise _error_for_oserror(error) from error
        except (TypeError, ValueError) as error:
            raise SafeWriteError(WRITE_FAILED) from error
        finally:
            if file_fd is not None:
                if not _safe_close(file_fd):
                    failure = SafeWriteError(WRITE_FAILED)
                file_fd = None

        if failure is not None:
            raise failure

        os.fsync(parent_fd)
        if boundary_hook is not None:
            boundary_hook(f"{role}:parent_fsync")
    except SafeWriteError as error:
        if failure is None:
            failure = error
        if file_fd is not None:
            if not _safe_close(file_fd):
                failure = SafeWriteError(WRITE_FAILED)
            file_fd = None
        cleanup_confirmed = False
        if file_created and not file_fsync_confirmed:
            cleanup_confirmed = _remove_unconfirmed(parent_fd, filename)
        failure.artifact_created = file_created
        failure.cleanup_confirmed = cleanup_confirmed
        raise failure
    except (OSError, TypeError, ValueError) as error:
        cleanup_confirmed = False
        if file_created and not file_fsync_confirmed:
            cleanup_confirmed = _remove_unconfirmed(parent_fd, filename)
        raise SafeWriteError(
            WRITE_FAILED,
            artifact_created=file_created,
            cleanup_confirmed=cleanup_confirmed,
        ) from error
    finally:
        _safe_close(parent_fd)
        _safe_close(root_fd)
