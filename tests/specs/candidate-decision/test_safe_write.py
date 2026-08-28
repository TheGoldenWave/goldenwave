from __future__ import annotations

import errno
import importlib
import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


try:
    safe_write = importlib.import_module("gw_candidate.safe_write")
    IMPORT_ERROR = None
except ModuleNotFoundError as error:
    safe_write = None
    IMPORT_ERROR = error


class SafeWriteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNone(
            IMPORT_ERROR,
            "P1B-02 safe_write module is missing; this is the expected RED until implementation",
        )
        if not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_EXCL")):
            self.skipTest("descriptor-relative no-follow file operations are unavailable")
        self.directory = tempfile.TemporaryDirectory(prefix="gw-safe-write-")
        self.root = Path(self.directory.name)
        (self.root / "wiki" / "methods").mkdir(parents=True)

    def tearDown(self) -> None:
        if hasattr(self, "directory"):
            self.directory.cleanup()

    def write(self, relative: str, content: bytes = b"exact bytes", hook=None):
        return safe_write.write_exclusive(
            self.root,
            relative,
            content,
            role="target",
            boundary_hook=hook,
        )

    def assert_code(self, expected: str, callable_) -> None:
        with self.assertRaises(safe_write.SafeWriteError) as caught:
            callable_()
        self.assertEqual(expected, caught.exception.code)

    def symlink_or_skip(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"symlink operations unavailable: {error}")

    def hardlink_or_skip(self, source: Path, target: Path) -> None:
        try:
            os.link(source, target)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"hardlink operations unavailable: {error}")

    def test_writes_exact_bytes_and_reports_both_persistence_boundaries(self) -> None:
        events: list[str] = []
        self.write("wiki/methods/result.md", b"\x00exact\n", events.append)

        self.assertEqual(b"\x00exact\n", (self.root / "wiki/methods/result.md").read_bytes())
        self.assertEqual(["target:file_fsync", "target:parent_fsync"], events)

    def test_retries_bounded_short_writes_until_all_bytes_are_persisted(self) -> None:
        original_write = os.write
        payload = b"short writes must preserve every byte"
        written_chunks = []

        def bounded_write(descriptor, remaining):
            prefix = remaining[:3]
            written_chunks.append(bytes(prefix))
            return original_write(descriptor, prefix)

        with mock.patch.object(safe_write.os, "write", side_effect=bounded_write):
            self.write("wiki/methods/short-write.md", payload)

        self.assertGreater(len(written_chunks), 1)
        self.assertEqual(payload, b"".join(written_chunks))
        self.assertEqual(payload, (self.root / "wiki/methods/short-write.md").read_bytes())

    def test_zero_byte_write_fails_closed_without_retry_loop(self) -> None:
        calls = 0
        target = self.root / "wiki/methods/zero-write.md"

        def zero_write(_descriptor, _remaining):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise AssertionError("zero-byte write was retried")
            return 0

        with mock.patch.object(safe_write.os, "write", side_effect=zero_write):
            self.assert_code(
                "GW_CANDIDATE_WRITE_FAILED",
                lambda: self.write("wiki/methods/zero-write.md", b"must not survive"),
            )

        self.assertEqual(1, calls)
        self.assertFalse(target.exists())

    def test_uses_descriptor_relative_no_follow_exclusive_open_and_real_fsync(self) -> None:
        original_open = os.open
        original_fstat = os.fstat
        original_write = os.write
        original_fsync = os.fsync
        open_results = []
        events = []
        fsync_descriptors = []

        def tracked_open(path, flags, mode=0o777, *, dir_fd=None):
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            open_results.append((str(path), flags, dir_fd, descriptor))
            events.append(("open", descriptor, str(path)))
            return descriptor

        def tracked_fstat(descriptor):
            events.append(("fstat", descriptor, None))
            return original_fstat(descriptor)

        def tracked_write(descriptor, content):
            events.append(("write", descriptor, None))
            return original_write(descriptor, content)

        def tracked_fsync(descriptor):
            events.append(("fsync", descriptor, None))
            fsync_descriptors.append(descriptor)
            return original_fsync(descriptor)

        with mock.patch.object(safe_write.os, "open", side_effect=tracked_open):
            with mock.patch.object(safe_write.os, "fstat", side_effect=tracked_fstat) as fstat_spy:
                with mock.patch.object(safe_write.os, "write", side_effect=tracked_write):
                    with mock.patch.object(safe_write.os, "fsync", side_effect=tracked_fsync):
                        self.write("wiki/methods/result.md", b"durable")

        directory_calls = [item for item in open_results if item[0] in {"wiki", "methods"}]
        file_calls = [item for item in open_results if item[0] == "result.md"]

        file_open_index = open_results.index(file_calls[0])
        initial_directory_calls = [
            item for item in open_results[:file_open_index] if item[0] in {"wiki", "methods"}
        ]
        final_directory_calls = [
            item for item in open_results[file_open_index + 1 :] if item[0] in {"wiki", "methods"}
        ]
        self.assertEqual(
            ["wiki", "methods", "wiki", "methods"],
            [str(item[0]) for item in directory_calls],
        )
        self.assertEqual(["wiki", "methods"], [item[0] for item in initial_directory_calls])
        self.assertEqual(["wiki", "methods"], [item[0] for item in final_directory_calls])
        for _path, flags, directory_fd, _opened_fd in directory_calls:
            self.assertIsInstance(directory_fd, int)
            self.assertTrue(flags & os.O_DIRECTORY)
            self.assertTrue(flags & os.O_NOFOLLOW)
        self.assertEqual(1, len(file_calls))
        _path, flags, directory_fd, file_fd = file_calls[0]
        parent_fd = initial_directory_calls[-1][3]
        self.assertIsInstance(directory_fd, int)
        self.assertEqual(parent_fd, directory_fd)
        self.assertNotEqual(file_fd, parent_fd)
        self.assertTrue(flags & os.O_CREAT)
        self.assertTrue(flags & os.O_EXCL)
        self.assertTrue(flags & os.O_NOFOLLOW)
        fstat_descriptors = [call.args[0] for call in fstat_spy.call_args_list]
        self.assertIn(file_fd, fstat_descriptors)
        open_index = events.index(("open", file_fd, "result.md"))
        fstat_index = events.index(("fstat", file_fd, None))
        write_index = events.index(("write", file_fd, None))
        self.assertLess(open_index, fstat_index)
        self.assertLess(fstat_index, write_index)
        self.assertIn(file_fd, fsync_descriptors)
        self.assertIn(parent_fd, fsync_descriptors)
        self.assertLess(
            events.index(("fsync", file_fd, None)),
            events.index(("fsync", parent_fd, None)),
        )

    def test_rejects_non_regular_or_multiply_linked_created_file_before_writing(self) -> None:
        original_open = os.open
        original_fstat = os.fstat
        cases = (
            ("non-regular.md", stat.S_IFDIR | 0o700, 1),
            ("multiply-linked.md", stat.S_IFREG | 0o600, 2),
        )
        for filename, injected_mode, injected_nlink in cases:
            with self.subTest(filename=filename):
                created_fd = None
                fstat_descriptors = []

                def tracked_open(path, flags, mode=0o777, *, dir_fd=None):
                    nonlocal created_fd
                    descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
                    if str(path) == filename:
                        created_fd = descriptor
                    return descriptor

                def injected_fstat(descriptor):
                    fstat_descriptors.append(descriptor)
                    actual = original_fstat(descriptor)
                    if descriptor == created_fd:
                        return SimpleNamespace(st_mode=injected_mode, st_nlink=injected_nlink)
                    return actual

                with mock.patch.object(safe_write.os, "open", side_effect=tracked_open):
                    with mock.patch.object(safe_write.os, "fstat", side_effect=injected_fstat):
                        with mock.patch.object(safe_write.os, "write", wraps=os.write) as write_spy:
                            with self.assertRaises(safe_write.SafeWriteError):
                                self.write(f"wiki/methods/{filename}", b"must not survive")

                self.assertIsNotNone(created_fd)
                self.assertIn(created_fd, fstat_descriptors)
                write_spy.assert_not_called()
                self.assertFalse((self.root / "wiki/methods" / filename).exists())

    def test_existing_file_is_a_conflict_and_is_not_overwritten(self) -> None:
        target = self.root / "wiki/methods/result.md"
        target.write_bytes(b"original")

        self.assert_code(
            "GW_CANDIDATE_CONFLICT",
            lambda: self.write("wiki/methods/result.md", b"replacement"),
        )
        self.assertEqual(b"original", target.read_bytes())

    def test_symlink_parent_and_traversal_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gw-safe-write-outside-") as directory:
            outside = Path(directory)
            (self.root / "wiki/methods").rmdir()
            self.symlink_or_skip(self.root / "wiki/methods", outside)

            self.assert_code(
                "GW_CANDIDATE_TARGET_UNSAFE",
                lambda: self.write("wiki/methods/result.md"),
            )
            self.assert_code(
                "GW_CANDIDATE_TARGET_UNSAFE",
                lambda: self.write("../escaped.md"),
            )
            self.assertFalse((outside / "result.md").exists())

    def test_existing_hardlink_is_a_conflict_and_preserves_linked_content(self) -> None:
        source = self.root / "source"
        target = self.root / "wiki/methods/result.md"
        source.write_bytes(b"linked")
        self.hardlink_or_skip(source, target)

        self.assert_code(
            "GW_CANDIDATE_CONFLICT",
            lambda: self.write("wiki/methods/result.md", b"replacement"),
        )
        self.assertEqual(b"linked", source.read_bytes())
        self.assertEqual(2, source.stat().st_nlink)

    def test_parent_swap_does_not_redirect_the_open_directory_descriptor(self) -> None:
        parent = self.root / "wiki/methods"
        moved_parent = self.root / "wiki/methods-opened"
        original_open = os.open
        swapped = False

        def open_with_parent_swap(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal swapped
            if str(path) == "result.md" and dir_fd is not None and not swapped:
                parent.rename(moved_parent)
                parent.mkdir()
                swapped = True
            return original_open(path, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(safe_write.os, "open", side_effect=open_with_parent_swap):
            with mock.patch.object(safe_write.os, "write", wraps=os.write) as write_spy:
                with self.assertRaises(safe_write.SafeWriteError) as caught:
                    self.write("wiki/methods/result.md", b"must not escape")

        self.assertTrue(swapped)
        self.assertIn(
            caught.exception.code,
            {"GW_CANDIDATE_TARGET_UNSAFE", "GW_CANDIDATE_KB_UNSAFE"},
        )
        write_spy.assert_not_called()
        self.assertFalse((moved_parent / "result.md").exists())
        self.assertFalse((parent / "result.md").exists())

    def test_intermediate_symlink_introduced_after_file_open_fails_final_identity_check(self) -> None:
        original_open = os.open
        open_calls = []
        swapped = False
        with tempfile.TemporaryDirectory(prefix="gw-ancestor-swap-") as directory:
            external = Path(directory)
            attacker = external / "attacker"
            attacker.mkdir()
            sentinel = attacker / "sentinel"
            sentinel.write_bytes(b"unchanged")
            moved_wiki = external / "moved-wiki"

            def swap_after_created_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                observed = [str(path), flags, dir_fd, None]
                open_calls.append(observed)
                descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
                observed[3] = descriptor
                if str(path) == "result.md" and not swapped:
                    (self.root / "wiki").rename(moved_wiki)
                    self.symlink_or_skip(self.root / "wiki", attacker)
                    swapped = True
                return descriptor

            with mock.patch.object(safe_write.os, "open", side_effect=swap_after_created_open):
                with mock.patch.object(safe_write.os, "write", wraps=os.write) as write_spy:
                    with self.assertRaises(safe_write.SafeWriteError) as caught:
                        self.write("wiki/methods/result.md", b"must not escape")

            self.assertTrue(swapped)
            self.assertIn(
                caught.exception.code,
                {"GW_CANDIDATE_TARGET_UNSAFE", "GW_CANDIDATE_KB_UNSAFE"},
            )
            write_spy.assert_not_called()
            self.assertEqual(b"unchanged", sentinel.read_bytes())
            self.assertEqual(["sentinel"], sorted(path.name for path in attacker.iterdir()))
            self.assertFalse((moved_wiki / "methods/result.md").exists())
            created_index = next(index for index, item in enumerate(open_calls) if item[0] == "result.md")
            final_calls = open_calls[created_index + 1 :]
            self.assertTrue(any(Path(item[0]) == self.root for item in final_calls))
            wiki_reopens = [item for item in final_calls if item[0] == "wiki"]
            self.assertTrue(wiki_reopens)
            self.assertTrue(all(item[1] & os.O_NOFOLLOW for item in wiki_reopens))
            self.assertTrue(all(isinstance(item[2], int) for item in wiki_reopens))

    def test_same_inode_intermediate_symlink_requires_unconditional_descriptor_reopen(self) -> None:
        original_open = os.open
        open_calls = []
        swapped = False
        with tempfile.TemporaryDirectory(prefix="gw-same-inode-swap-") as directory:
            external = Path(directory)
            moved_wiki = external / "moved-wiki"

            def swap_to_symlink_back_to_same_inode(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                observed = [str(path), flags, dir_fd, None]
                open_calls.append(observed)
                descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
                observed[3] = descriptor
                if str(path) == "same-inode.md" and not swapped:
                    (self.root / "wiki").rename(moved_wiki)
                    self.symlink_or_skip(self.root / "wiki", moved_wiki)
                    swapped = True
                return descriptor

            with mock.patch.object(
                safe_write.os,
                "open",
                side_effect=swap_to_symlink_back_to_same_inode,
            ):
                with mock.patch.object(safe_write.os, "write", wraps=os.write) as write_spy:
                    with self.assertRaises(safe_write.SafeWriteError) as caught:
                        self.write("wiki/methods/same-inode.md", b"must not escape")

            self.assertTrue(swapped)
            self.assertIn(
                caught.exception.code,
                {"GW_CANDIDATE_TARGET_UNSAFE", "GW_CANDIDATE_KB_UNSAFE"},
            )
            write_spy.assert_not_called()
            self.assertFalse((moved_wiki / "methods/same-inode.md").exists())
            created_index = next(
                index for index, item in enumerate(open_calls) if item[0] == "same-inode.md"
            )
            final_calls = open_calls[created_index + 1 :]
            self.assertTrue(any(Path(item[0]) == self.root for item in final_calls))
            wiki_reopens = [item for item in final_calls if item[0] == "wiki"]
            self.assertTrue(wiki_reopens)
            self.assertTrue(all(item[1] & os.O_NOFOLLOW for item in wiki_reopens))
            self.assertTrue(all(isinstance(item[2], int) for item in wiki_reopens))

    def test_missing_symlink_or_regular_file_root_is_kb_unsafe(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gw-invalid-root-") as directory:
            base = Path(directory)
            missing = base / "missing"
            regular = base / "regular"
            regular.write_bytes(b"not a directory")
            real_root = base / "real-root"
            (real_root / "wiki/methods").mkdir(parents=True)
            linked = base / "linked-root"
            self.symlink_or_skip(linked, real_root)

            for root in (missing, linked, regular):
                with self.subTest(root=root.name):
                    with self.assertRaises(safe_write.SafeWriteError) as caught:
                        safe_write.write_exclusive(
                            root,
                            "wiki/methods/result.md",
                            b"must not survive",
                            role="target",
                        )
                    self.assertEqual("GW_CANDIDATE_KB_UNSAFE", caught.exception.code)

            self.assertFalse((real_root / "wiki/methods/result.md").exists())

    def test_expected_root_identity_rejects_a_different_resolved_root(self) -> None:
        expected_metadata = self.root.stat()
        expected_identity = (expected_metadata.st_dev, expected_metadata.st_ino)
        with tempfile.TemporaryDirectory(prefix="gw-other-root-") as directory:
            other_root = Path(directory)
            (other_root / "wiki/methods").mkdir(parents=True)
            target = other_root / "wiki/methods/result.md"
            try:
                with self.assertRaises(safe_write.SafeWriteError) as caught:
                    safe_write.write_exclusive(
                        other_root,
                        "wiki/methods/result.md",
                        b"must not survive",
                        role="target",
                        expected_root_identity=expected_identity,
                    )
            except TypeError as error:
                self.fail(f"safe_write expected_root_identity API is missing: {error}")

            self.assertEqual("GW_CANDIDATE_KB_UNSAFE", caught.exception.code)
            self.assertFalse(target.exists())

    def test_expected_component_identities_are_checked_during_descriptor_traversal(self) -> None:
        (self.root / ".kb/candidate-decisions").mkdir(parents=True)
        kb_metadata = (self.root / ".kb").stat()
        decisions_metadata = (self.root / ".kb/candidate-decisions").stat()
        expected = {
            ".kb": (kb_metadata.st_dev, kb_metadata.st_ino),
            ".kb/candidate-decisions": (decisions_metadata.st_dev, decisions_metadata.st_ino),
        }
        try:
            safe_write.write_exclusive(
                self.root,
                ".kb/candidate-decisions/authorized.json",
                b"authorized",
                role="authorized",
                expected_component_identities=expected,
            )
        except TypeError as error:
            self.fail(f"safe_write expected_component_identities API is missing: {error}")
        self.assertEqual(
            b"authorized",
            (self.root / ".kb/candidate-decisions/authorized.json").read_bytes(),
        )

        wrong = dict(expected)
        wrong[".kb/candidate-decisions"] = expected[".kb"]
        with self.assertRaises(safe_write.SafeWriteError) as caught:
            safe_write.write_exclusive(
                self.root,
                ".kb/candidate-decisions/rejected.json",
                b"must not survive",
                role="rejected",
                expected_component_identities=wrong,
            )
        self.assertEqual("GW_CANDIDATE_KB_UNSAFE", caught.exception.code)
        self.assertFalse((self.root / ".kb/candidate-decisions/rejected.json").exists())

    def test_safe_write_error_reports_created_and_cleanup_confirmation(self) -> None:
        original_unlink = os.unlink
        original_fsync = os.fsync
        cases = (
            ("cleanup-confirmed.md", "normal", True, False),
            ("cleanup-raise.md", "raise", False, True),
            ("cleanup-noop.md", "noop", False, True),
            ("cleanup-fsync.md", "fsync_raise", False, False),
        )
        for filename, cleanup_mode, expected_cleanup, expected_exists in cases:
            with self.subTest(cleanup_mode=cleanup_mode):
                target = self.root / "wiki/methods" / filename

                def fail_write(_descriptor, _remaining):
                    raise OSError(errno.EIO, "injected target write failure")

                def controlled_unlink(path, *, dir_fd=None):
                    if str(path) != filename:
                        return original_unlink(path, dir_fd=dir_fd)
                    if cleanup_mode == "raise":
                        raise OSError(errno.EIO, "injected cleanup unlink failure")
                    if cleanup_mode == "noop":
                        return None
                    return original_unlink(path, dir_fd=dir_fd)

                def controlled_fsync(descriptor):
                    if cleanup_mode == "fsync_raise":
                        raise OSError(errno.EIO, "injected cleanup parent fsync failure")
                    return original_fsync(descriptor)

                with mock.patch.object(safe_write.os, "write", side_effect=fail_write):
                    with mock.patch.object(safe_write.os, "unlink", side_effect=controlled_unlink):
                        with mock.patch.object(safe_write.os, "fsync", side_effect=controlled_fsync):
                            with self.assertRaises(safe_write.SafeWriteError) as caught:
                                self.write(f"wiki/methods/{filename}", b"must not survive")

                self.assertEqual("GW_CANDIDATE_WRITE_FAILED", caught.exception.code)
                self.assertTrue(
                    hasattr(caught.exception, "artifact_created"),
                    "SafeWriteError.artifact_created metadata is missing",
                )
                self.assertTrue(
                    hasattr(caught.exception, "cleanup_confirmed"),
                    "SafeWriteError.cleanup_confirmed metadata is missing",
                )
                self.assertIs(True, caught.exception.artifact_created)
                self.assertIs(expected_cleanup, caught.exception.cleanup_confirmed)
                self.assertEqual(expected_exists, target.exists())

    def test_ancestor_fstat_io_error_closes_every_open_descriptor(self) -> None:
        original_open = os.open
        original_close = os.close
        original_fstat = os.fstat
        events = []
        live_fds = set()
        ancestor_fd = None
        injected = False

        def tracked_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal ancestor_fd
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            self.assertNotIn(descriptor, live_fds)
            live_fds.add(descriptor)
            events.append(("open", str(path), descriptor))
            if str(path) == ".." and ancestor_fd is None:
                ancestor_fd = descriptor
            return descriptor

        def fail_ancestor_fstat(descriptor):
            nonlocal injected
            events.append(("fstat", descriptor))
            if descriptor == ancestor_fd and not injected:
                injected = True
                raise OSError(errno.EIO, "injected ancestor fstat failure")
            return original_fstat(descriptor)

        def tracked_close(descriptor):
            events.append(("close", descriptor))
            result = original_close(descriptor)
            live_fds.remove(descriptor)
            return result

        leaked_fds = set()
        try:
            with mock.patch.object(safe_write.os, "open", side_effect=tracked_open):
                with mock.patch.object(safe_write.os, "fstat", side_effect=fail_ancestor_fstat):
                    with mock.patch.object(safe_write.os, "close", side_effect=tracked_close):
                        self.assert_code(
                            "GW_CANDIDATE_WRITE_FAILED",
                            lambda: self.write("wiki/methods/ancestor-eio.md", b"must not survive"),
                        )
            leaked_fds = set(live_fds)
        finally:
            for descriptor in list(live_fds):
                try:
                    original_close(descriptor)
                except OSError:
                    pass
                live_fds.discard(descriptor)

        self.assertIsNotNone(ancestor_fd)
        self.assertTrue(injected)
        ancestor_open_index = events.index(("open", "..", ancestor_fd))
        later_events = events[ancestor_open_index + 1 :]
        self.assertIn(("fstat", ancestor_fd), later_events)
        self.assertIn(("close", ancestor_fd), later_events)
        self.assertEqual(set(), leaked_fds)
        self.assertFalse((self.root / "wiki/methods/ancestor-eio.md").exists())

    def test_missing_platform_open_flags_loads_module_but_fails_call_closed(self) -> None:
        module_path = Path(safe_write.__file__)
        saved_flags = {name: getattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")}
        loaded = None
        try:
            for name in saved_flags:
                delattr(os, name)
            review_cli = importlib.import_module("gw_candidate.cli")
            self.assertTrue(callable(review_cli.main))
            spec = importlib.util.spec_from_file_location("gw_candidate_safe_write_without_flags", module_path)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            loaded = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(loaded)
            except Exception as error:
                self.fail(f"safe_write import failed without platform flags: {error}")

            with self.assertRaises(loaded.SafeWriteError) as caught:
                loaded.write_exclusive(
                    self.root,
                    "wiki/methods/unsupported.md",
                    b"must not survive",
                    role="target",
                )
            self.assertEqual("GW_CANDIDATE_PLATFORM_UNSUPPORTED", caught.exception.code)
        finally:
            for name, value in saved_flags.items():
                setattr(os, name, value)

        self.assertIsNotNone(loaded)
        self.assertFalse((self.root / "wiki/methods/unsupported.md").exists())

    def test_pre_creation_open_io_error_maps_to_write_failed(self) -> None:
        original_open = os.open
        target = self.root / "wiki/methods/open-eio.md"

        def fail_file_open(path, flags, mode=0o777, *, dir_fd=None):
            if str(path) == "open-eio.md" and dir_fd is not None:
                raise OSError(errno.EIO, "injected open failure")
            return original_open(path, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(safe_write.os, "open", side_effect=fail_file_open):
            self.assert_code(
                "GW_CANDIDATE_WRITE_FAILED",
                lambda: self.write("wiki/methods/open-eio.md", b"must not survive"),
            )

        self.assertFalse(target.exists())

    def test_cleanup_close_failure_is_controlled_and_removes_unconfirmed_file(self) -> None:
        original_open = os.open
        original_close = os.close
        original_fstat = os.fstat
        file_fd = None
        close_failed = False
        target = self.root / "wiki/methods/cleanup-close.md"

        def tracked_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal file_fd
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            if str(path) == "cleanup-close.md":
                file_fd = descriptor
            return descriptor

        def unsafe_fstat(descriptor):
            actual = original_fstat(descriptor)
            if descriptor == file_fd:
                return SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_nlink=1)
            return actual

        def fail_file_close_once(descriptor):
            nonlocal close_failed
            if descriptor == file_fd and not close_failed:
                close_failed = True
                raise OSError(errno.EIO, "injected cleanup close failure")
            return original_close(descriptor)

        try:
            with mock.patch.object(safe_write.os, "open", side_effect=tracked_open):
                with mock.patch.object(safe_write.os, "fstat", side_effect=unsafe_fstat):
                    with mock.patch.object(safe_write.os, "close", side_effect=fail_file_close_once):
                        self.assert_code(
                            "GW_CANDIDATE_WRITE_FAILED",
                            lambda: self.write("wiki/methods/cleanup-close.md", b"must not survive"),
                        )
        finally:
            if file_fd is not None:
                try:
                    original_close(file_fd)
                except OSError:
                    pass

        self.assertTrue(close_failed)
        self.assertFalse(target.exists())

    def test_file_close_failure_before_parent_boundary_is_controlled(self) -> None:
        original_open = os.open
        original_close = os.close
        file_fd = None
        close_failed = False
        target = self.root / "wiki/methods/file-close.md"

        def tracked_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal file_fd
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            if str(path) == "file-close.md":
                file_fd = descriptor
            return descriptor

        def fail_file_close_once(descriptor):
            nonlocal close_failed
            if descriptor == file_fd and not close_failed:
                close_failed = True
                raise OSError(errno.EIO, "injected file close failure")
            return original_close(descriptor)

        try:
            with mock.patch.object(safe_write.os, "open", side_effect=tracked_open):
                with mock.patch.object(safe_write.os, "close", side_effect=fail_file_close_once):
                    self.assert_code(
                        "GW_CANDIDATE_WRITE_FAILED",
                        lambda: self.write("wiki/methods/file-close.md", b"persisted bytes"),
                    )
        finally:
            if file_fd is not None:
                try:
                    original_close(file_fd)
                except OSError:
                    pass

        self.assertTrue(close_failed)
        self.assertEqual(b"persisted bytes", target.read_bytes())

    def test_parent_close_failure_after_confirmed_fsync_does_not_escape(self) -> None:
        original_open = os.open
        original_close = os.close
        parent_fd = None
        close_failed = False
        target = self.root / "wiki/methods/parent-close.md"

        def tracked_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal parent_fd
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            if str(path) == "methods":
                parent_fd = descriptor
            return descriptor

        def fail_parent_close_once(descriptor):
            nonlocal close_failed
            if descriptor == parent_fd and not close_failed:
                close_failed = True
                raise OSError(errno.EIO, "injected final close failure")
            return original_close(descriptor)

        try:
            with mock.patch.object(safe_write.os, "open", side_effect=tracked_open):
                with mock.patch.object(safe_write.os, "close", side_effect=fail_parent_close_once):
                    self.write("wiki/methods/parent-close.md", b"fully persisted")
        except OSError as error:
            self.fail(f"raw close error escaped: {error}")
        finally:
            if parent_fd is not None:
                try:
                    original_close(parent_fd)
                except OSError:
                    pass

        self.assertTrue(close_failed)
        self.assertEqual(b"fully persisted", target.read_bytes())

    def test_failure_after_each_fsync_never_allows_retry_overwrite(self) -> None:
        for event in ("target:file_fsync", "target:parent_fsync"):
            with self.subTest(event=event):
                relative = f"wiki/methods/{event.replace(':', '-')}.md"

                def fail_at(observed: str) -> None:
                    if observed == event:
                        raise OSError("injected boundary failure")

                self.assert_code(
                    "GW_CANDIDATE_WRITE_FAILED",
                    lambda: self.write(relative, b"persisted", fail_at),
                )
                self.assertEqual(b"persisted", (self.root / relative).read_bytes())
                self.assert_code(
                    "GW_CANDIDATE_CONFLICT",
                    lambda: self.write(relative, b"overwrite"),
                )
                self.assertEqual(b"persisted", (self.root / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
