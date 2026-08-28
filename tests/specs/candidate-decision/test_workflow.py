from __future__ import annotations

import hashlib
import importlib
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


try:
    safe_write = importlib.import_module("gw_candidate.safe_write")
    workflow = importlib.import_module("gw_candidate.workflow")
    IMPORT_ERROR = None
except ModuleNotFoundError as error:
    safe_write = None
    workflow = None
    IMPORT_ERROR = error


CANDIDATE = {
    "candidate_id": "cand_01JAZ6Y5M4N6KD3V8T2WQ9R7HD",
    "storage_class": "git_tracked",
    "target": {"kind": "experience", "path": "wiki/methods/candidate-validation.md"},
    "provenance": {"source_ref": "private/source/ref"},
    "content": {"media_type": "text/markdown", "text": "exact candidate content"},
}
CANDIDATE_BYTES = json.dumps(CANDIDATE, sort_keys=True).encode("utf-8")
DIGEST = hashlib.sha256(CANDIDATE_BYTES).hexdigest()
NOW = "2026-07-27T12:05:00Z"


class RecordingWriter:
    def __init__(self, fail_at: str | None = None) -> None:
        self.fail_at = fail_at
        self.writes: list[tuple[str, str, bytes]] = []
        self.expected_root_identities: list[tuple[int, int] | None] = []
        self.expected_component_identities: list[dict[str, tuple[int, int]] | None] = []

    def __call__(
        self,
        root,
        relative_path,
        content,
        *,
        role,
        boundary_hook=None,
        expected_root_identity=None,
        expected_component_identities=None,
    ):
        self.writes.append((role, relative_path, content))
        self.expected_root_identities.append(expected_root_identity)
        self.expected_component_identities.append(expected_component_identities)
        for event in (f"{role}:file_fsync", f"{role}:parent_fsync"):
            if boundary_hook is not None:
                boundary_hook(event)
            if event == self.fail_at:
                raise OSError("injected persistence failure")


class WorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNone(
            IMPORT_ERROR,
            "P1B-02 safe_write/workflow modules are missing; this is the expected RED until implementation",
        )
        self.directory = tempfile.TemporaryDirectory(prefix="gw-workflow-")
        self.root = Path(self.directory.name)
        self.initialize_kb(self.root)

    def tearDown(self) -> None:
        if hasattr(self, "directory"):
            self.directory.cleanup()

    def initialize_kb(self, root: Path) -> None:
        (root / ".kb/candidate-decisions").mkdir(parents=True)
        (root / "wiki/methods").mkdir(parents=True)
        (root / ".kb/goldenwave.json").write_text(
            json.dumps({"format_version": "gwkb/v0.1", "version": "0.1.0"}),
            encoding="utf-8",
        )

    def artifact_bytes(self, root: Path) -> dict[str, bytes]:
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def accept(self, writer=None, hook=None, root=None, retention_until=None):
        return workflow.accept_candidate(
            CANDIDATE,
            CANDIDATE_BYTES,
            root or self.root,
            now=NOW,
            confirm=CANDIDATE["candidate_id"],
            review_digest=DIGEST,
            authorization_basis="self_context",
            retention_until=retention_until,
            attest_no_consent_required_data=True,
            acknowledge_git_history=True,
            writer=writer or safe_write.write_exclusive,
            boundary_hook=hook,
        )

    def test_accept_orders_authorized_target_and_applied_writes(self) -> None:
        writer = RecordingWriter()
        result = self.accept(writer)

        self.assertEqual("applied", result["summary"]["status"])
        self.assertEqual(
            ["decision", "authorized", "target", "applied"],
            [item[0] for item in writer.writes],
        )
        root_metadata = self.root.stat()
        expected_identity = (root_metadata.st_dev, root_metadata.st_ino)
        self.assertEqual([expected_identity] * 4, writer.expected_root_identities)
        kb_metadata = (self.root / ".kb").stat()
        decisions_metadata = (self.root / ".kb/candidate-decisions").stat()
        expected_components = {
            ".kb": (kb_metadata.st_dev, kb_metadata.st_ino),
            ".kb/candidate-decisions": (decisions_metadata.st_dev, decisions_metadata.st_ino),
        }
        self.assertEqual(expected_components, writer.expected_component_identities[0])
        self.assertEqual(expected_components, writer.expected_component_identities[1])
        self.assertEqual(expected_components, writer.expected_component_identities[3])
        claim = json.loads(writer.writes[0][2])
        self.assertEqual(
            {
                "record_version": "gw-candidate-decision/v0.1",
                "candidate_id": CANDIDATE["candidate_id"],
                "decision": "accept",
                "decided_at": NOW,
                "candidate_sha256": DIGEST,
            },
            claim,
        )
        self.assertEqual(CANDIDATE["content"]["text"].encode("utf-8"), writer.writes[2][2])
        for role, _path, raw in (writer.writes[1], writer.writes[3]):
            receipt = json.loads(raw)
            self.assertEqual(role, receipt["decision"])
            self.assertNotIn("exact candidate content", raw.decode("utf-8"))
            self.assertNotIn("private/source/ref", raw.decode("utf-8"))

    def test_each_persistence_boundary_maps_to_an_honest_status(self) -> None:
        expected = {
            "decision:file_fsync": ("failed", "GW_CANDIDATE_WRITE_FAILED"),
            "decision:parent_fsync": ("failed", "GW_CANDIDATE_WRITE_FAILED"),
            "authorized:file_fsync": ("failed", "GW_CANDIDATE_WRITE_FAILED"),
            "authorized:parent_fsync": ("failed", "GW_CANDIDATE_WRITE_FAILED"),
            "target:file_fsync": ("indeterminate", "GW_CANDIDATE_APPLY_INDETERMINATE"),
            "target:parent_fsync": ("indeterminate", "GW_CANDIDATE_APPLY_INDETERMINATE"),
            "applied:file_fsync": ("indeterminate", "GW_CANDIDATE_APPLY_INDETERMINATE"),
            "applied:parent_fsync": ("applied", None),
        }
        for event, (status, code) in expected.items():
            with self.subTest(event=event):
                with tempfile.TemporaryDirectory(prefix="gw-workflow-boundary-") as directory:
                    root = Path(directory)
                    self.initialize_kb(root)

                    def fail_at(observed: str) -> None:
                        if observed == event:
                            raise OSError("injected persistence failure")

                    result = self.accept(hook=fail_at, root=root)
                    self.assertEqual(status, result["summary"]["status"])
                    codes = [error["code"] for error in result.get("errors", [])]
                    if code is None:
                        self.assertEqual([], codes)
                    else:
                        self.assertEqual([code], codes)

                    decision_root = root / ".kb/candidate-decisions"
                    claim = decision_root / f"{CANDIDATE['candidate_id']}.decision.json"
                    authorized = decision_root / f"{CANDIDATE['candidate_id']}.authorized.json"
                    target = root / CANDIDATE["target"]["path"]
                    applied = decision_root / f"{CANDIDATE['candidate_id']}.applied.json"
                    rejected = decision_root / f"{CANDIDATE['candidate_id']}.rejected.json"
                    self.assertTrue(claim.is_file())
                    self.assertEqual(not event.startswith("decision:"), authorized.is_file())
                    self.assertEqual(event.startswith(("target:", "applied:")), target.is_file())
                    self.assertEqual(event.startswith("applied:"), applied.is_file())
                    self.assertFalse(rejected.exists())
                    if target.is_file():
                        self.assertEqual(CANDIDATE["content"]["text"].encode(), target.read_bytes())

                    before_retry = self.artifact_bytes(root)
                    retry = self.accept(root=root)
                    self.assertEqual("failed", retry["summary"]["status"])
                    self.assertEqual(
                        ["GW_CANDIDATE_CONFLICT"],
                        [error["code"] for error in retry.get("errors", [])],
                    )
                    self.assertEqual(before_retry, self.artifact_bytes(root))

                    serialized = json.dumps(result, sort_keys=True)
                    self.assertNotIn(str(root), serialized)
                    self.assertNotIn("exact candidate content", serialized)
                    self.assertNotIn("wiki/methods/candidate-validation.md", serialized)
                    self.assertNotIn("private/source/ref", serialized)

    def test_boundary_hook_observes_controlled_role_events(self) -> None:
        events: list[str] = []
        result = self.accept(RecordingWriter(), events.append)

        self.assertEqual("applied", result["summary"]["status"])
        self.assertEqual(
            [
                "decision:file_fsync",
                "decision:parent_fsync",
                "authorized:file_fsync",
                "authorized:parent_fsync",
                "target:file_fsync",
                "target:parent_fsync",
                "applied:file_fsync",
                "applied:parent_fsync",
            ],
            events,
        )

    def test_accept_after_reject_conflicts_without_contradictory_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gw-reject-then-accept-") as directory:
            root = Path(directory)
            self.initialize_kb(root)
            rejected = workflow.reject_candidate(
                CANDIDATE,
                CANDIDATE_BYTES,
                root,
                now=NOW,
                confirm=CANDIDATE["candidate_id"],
                review_digest=DIGEST,
                reason="privacy",
            )
            self.assertEqual("rejected", rejected["summary"]["status"])
            accept_after_reject = self.accept(root=root)
            self.assertEqual("failed", accept_after_reject["summary"]["status"])
            self.assertEqual(
                ["GW_CANDIDATE_CONFLICT"],
                [error["code"] for error in accept_after_reject["errors"]],
            )
            decision_root = root / ".kb/candidate-decisions"
            self.assertEqual(
                [
                    f"{CANDIDATE['candidate_id']}.decision.json",
                    f"{CANDIDATE['candidate_id']}.rejected.json",
                ],
                sorted(path.name for path in decision_root.glob("*.json")),
            )
            self.assertFalse((root / CANDIDATE["target"]["path"]).exists())

    def test_reject_after_accept_conflicts_without_contradictory_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gw-accept-then-reject-") as directory:
            root = Path(directory)
            self.initialize_kb(root)
            accepted = self.accept(root=root)
            self.assertEqual("applied", accepted["summary"]["status"])
            before = self.artifact_bytes(root)
            reject_after_accept = workflow.reject_candidate(
                CANDIDATE,
                CANDIDATE_BYTES,
                root,
                now=NOW,
                confirm=CANDIDATE["candidate_id"],
                review_digest=DIGEST,
                reason="privacy",
            )
            self.assertEqual("failed", reject_after_accept["summary"]["status"])
            self.assertEqual(
                ["GW_CANDIDATE_CONFLICT"],
                [error["code"] for error in reject_after_accept["errors"]],
            )
            self.assertEqual(before, self.artifact_bytes(root))
            decision_root = root / ".kb/candidate-decisions"
            self.assertFalse(
                (decision_root / f"{CANDIDATE['candidate_id']}.rejected.json").exists()
            )

    def test_concurrent_accept_and_reject_have_exactly_one_claim_winner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gw-decision-race-") as directory:
            root = Path(directory)
            self.initialize_kb(root)
            barrier = threading.Barrier(2)
            results = {}

            def barrier_writer(
                writer_root,
                relative_path,
                content,
                *,
                role,
                boundary_hook=None,
                expected_root_identity=None,
                expected_component_identities=None,
            ):
                if relative_path.endswith(".decision.json"):
                    barrier.wait(timeout=5)
                return safe_write.write_exclusive(
                    writer_root,
                    relative_path,
                    content,
                    role=role,
                    boundary_hook=boundary_hook,
                    expected_root_identity=expected_root_identity,
                    expected_component_identities=expected_component_identities,
                )

            def run_accept():
                results["accept"] = self.accept(barrier_writer, root=root)

            def run_reject():
                results["reject"] = workflow.reject_candidate(
                    CANDIDATE,
                    CANDIDATE_BYTES,
                    root,
                    now=NOW,
                    confirm=CANDIDATE["candidate_id"],
                    review_digest=DIGEST,
                    reason="privacy",
                    writer=barrier_writer,
                )

            threads = [threading.Thread(target=run_accept), threading.Thread(target=run_reject)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
                self.assertFalse(thread.is_alive(), "decision race thread did not finish")

            statuses = {name: result["summary"]["status"] for name, result in results.items()}
            winners = [name for name, status in statuses.items() if status in {"applied", "rejected"}]
            losers = [name for name, status in statuses.items() if status == "failed"]
            self.assertEqual(1, len(winners))
            self.assertEqual(1, len(losers))
            self.assertEqual(
                ["GW_CANDIDATE_CONFLICT"],
                [error["code"] for error in results[losers[0]]["errors"]],
            )

            decision_root = root / ".kb/candidate-decisions"
            claim_path = decision_root / f"{CANDIDATE['candidate_id']}.decision.json"
            self.assertTrue(claim_path.is_file())
            claim = json.loads(claim_path.read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "record_version",
                    "candidate_id",
                    "decision",
                    "decided_at",
                    "candidate_sha256",
                },
                set(claim),
            )
            self.assertEqual(winners[0], claim["decision"])
            target = root / CANDIDATE["target"]["path"]
            if winners[0] == "accept":
                self.assertTrue(target.is_file())
                self.assertTrue(
                    (decision_root / f"{CANDIDATE['candidate_id']}.authorized.json").is_file()
                )
                self.assertTrue(
                    (decision_root / f"{CANDIDATE['candidate_id']}.applied.json").is_file()
                )
                self.assertFalse(
                    (decision_root / f"{CANDIDATE['candidate_id']}.rejected.json").exists()
                )
            else:
                self.assertFalse(target.exists())
                self.assertTrue(
                    (decision_root / f"{CANDIDATE['candidate_id']}.rejected.json").is_file()
                )
                self.assertFalse(
                    (decision_root / f"{CANDIDATE['candidate_id']}.authorized.json").exists()
                )
                self.assertFalse(
                    (decision_root / f"{CANDIDATE['candidate_id']}.applied.json").exists()
                )

    def test_component_identity_swap_after_validation_fails_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gw-component-swap-") as directory:
            base = Path(directory)
            root = base / "kb"
            moved_kb = base / "validated-kb"
            replacement_kb = base / "replacement-kb"
            self.initialize_kb(root)
            (replacement_kb / "candidate-decisions").mkdir(parents=True)
            swapped = False

            def swapping_writer(
                writer_root,
                relative_path,
                content,
                *,
                role,
                boundary_hook=None,
                expected_root_identity=None,
                expected_component_identities=None,
            ):
                nonlocal swapped
                if not swapped:
                    (root / ".kb").rename(moved_kb)
                    replacement_kb.rename(root / ".kb")
                    swapped = True
                kwargs = {
                    "role": role,
                    "boundary_hook": boundary_hook,
                    "expected_root_identity": expected_root_identity,
                }
                if expected_component_identities is not None:
                    kwargs["expected_component_identities"] = expected_component_identities
                return safe_write.write_exclusive(
                    writer_root,
                    relative_path,
                    content,
                    **kwargs,
                )

            result = self.accept(swapping_writer, root=root)

            self.assertTrue(swapped)
            self.assertEqual("failed", result["summary"]["status"])
            self.assertEqual(
                ["GW_CANDIDATE_KB_UNSAFE"],
                [error["code"] for error in result["errors"]],
            )
            self.assertFalse((root / CANDIDATE["target"]["path"]).exists())
            self.assertEqual([], list((moved_kb / "candidate-decisions").glob("*.json")))
            self.assertEqual([], list((root / ".kb/candidate-decisions").glob("*.json")))

    def test_target_cleanup_uncertainty_controls_failed_vs_indeterminate_outcome(self) -> None:
        original_unlink = os.unlink
        original_fsync = os.fsync
        for cleanup_mode in ("confirmed", "raise", "noop", "fsync_raise"):
            with self.subTest(cleanup_mode=cleanup_mode):
                with tempfile.TemporaryDirectory(prefix="gw-cleanup-outcome-") as directory:
                    root = Path(directory)
                    self.initialize_kb(root)

                    def writer(
                        writer_root,
                        relative_path,
                        content,
                        *,
                        role,
                        boundary_hook=None,
                        expected_root_identity=None,
                        expected_component_identities=None,
                    ):
                        kwargs = {
                            "role": role,
                            "boundary_hook": boundary_hook,
                            "expected_root_identity": expected_root_identity,
                        }
                        if expected_component_identities is not None:
                            kwargs["expected_component_identities"] = expected_component_identities
                        if role != "target":
                            return safe_write.write_exclusive(
                                writer_root, relative_path, content, **kwargs
                            )

                        def fail_write(_descriptor, _remaining):
                            raise OSError("injected target write failure")

                        def controlled_unlink(path, *, dir_fd=None):
                            if cleanup_mode == "raise":
                                raise OSError("injected cleanup unlink failure")
                            if cleanup_mode == "noop":
                                return None
                            return original_unlink(path, dir_fd=dir_fd)

                        def controlled_fsync(descriptor):
                            if cleanup_mode == "fsync_raise":
                                raise OSError("injected cleanup parent fsync failure")
                            return original_fsync(descriptor)

                        with mock.patch.object(safe_write.os, "write", side_effect=fail_write):
                            with mock.patch.object(
                                safe_write.os, "unlink", side_effect=controlled_unlink
                            ):
                                with mock.patch.object(
                                    safe_write.os, "fsync", side_effect=controlled_fsync
                                ):
                                    return safe_write.write_exclusive(
                                        writer_root, relative_path, content, **kwargs
                                    )

                    result = self.accept(writer, root=root)
                    expected_status = "failed" if cleanup_mode == "confirmed" else "indeterminate"
                    expected_code = (
                        "GW_CANDIDATE_WRITE_FAILED"
                        if cleanup_mode == "confirmed"
                        else "GW_CANDIDATE_APPLY_INDETERMINATE"
                    )
                    self.assertEqual(expected_status, result["summary"]["status"])
                    self.assertEqual(
                        [expected_code], [error["code"] for error in result["errors"]]
                    )
                    target = root / CANDIDATE["target"]["path"]
                    self.assertEqual(cleanup_mode in {"raise", "noop"}, target.exists())
                    decision_root = root / ".kb/candidate-decisions"
                    self.assertTrue(
                        (decision_root / f"{CANDIDATE['candidate_id']}.decision.json").exists()
                    )
                    self.assertTrue(
                        (decision_root / f"{CANDIDATE['candidate_id']}.authorized.json").exists()
                    )
                    self.assertFalse(
                        (decision_root / f"{CANDIDATE['candidate_id']}.applied.json").exists()
                    )

    def test_retention_must_be_none_or_strictly_later_than_decision_time(self) -> None:
        invalid = ("2026-07-27T12:04:59Z", NOW)
        for retention in invalid:
            with self.subTest(retention=retention):
                writer = RecordingWriter()
                result = self.accept(writer, retention_until=retention)
                self.assertEqual("failed", result["summary"]["status"])
                self.assertEqual(
                    ["GW_CANDIDATE_AUTHORIZATION_REQUIRED"],
                    [error["code"] for error in result["errors"]],
                )
                self.assertEqual([], writer.writes)

        for retention in (None, "2026-07-27T12:05:01Z"):
            with self.subTest(retention=retention):
                writer = RecordingWriter()
                result = self.accept(writer, retention_until=retention)
                self.assertEqual("applied", result["summary"]["status"])
                self.assertEqual(
                    ["decision", "authorized", "target", "applied"],
                    [x[0] for x in writer.writes],
                )

    def test_kb_marker_validation_is_descriptor_relative_and_no_follow(self) -> None:
        original_open = os.open
        opened = []

        def tracked_open(path, flags, mode=0o777, *, dir_fd=None):
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            opened.append((str(path), flags, dir_fd, descriptor))
            return descriptor

        writer = RecordingWriter()
        with mock.patch.object(workflow.os, "open", side_effect=tracked_open):
            result = self.accept(writer)

        self.assertEqual("applied", result["summary"]["status"])
        marker_calls = [
            item
            for item in opened
            if Path(item[0]) == self.root or item[0] in {".kb", "goldenwave.json"}
        ]
        self.assertEqual(
            [str(self.root), ".kb", "goldenwave.json"],
            [item[0] for item in marker_calls],
        )
        root_call, kb_call, marker_call = marker_calls
        self.assertTrue(root_call[1] & os.O_DIRECTORY)
        self.assertTrue(root_call[1] & os.O_NOFOLLOW)
        self.assertIsNone(root_call[2])
        self.assertTrue(kb_call[1] & os.O_DIRECTORY)
        self.assertTrue(kb_call[1] & os.O_NOFOLLOW)
        self.assertEqual(root_call[3], kb_call[2])
        self.assertTrue(marker_call[1] & os.O_NOFOLLOW)
        self.assertEqual(kb_call[3], marker_call[2])

    def test_kb_marker_cannot_be_borrowed_through_intermediate_symlink_swap(self) -> None:
        for command in ("accept", "reject"):
            with self.subTest(command=command):
                with tempfile.TemporaryDirectory(prefix="gw-marker-swap-") as directory:
                    base = Path(directory)
                    root = base / "invalid-kb"
                    external = base / "external-kb"
                    moved_kb = base / "moved-invalid-kb"
                    self.initialize_kb(root)
                    self.initialize_kb(external)
                    (root / ".kb/goldenwave.json").write_text(
                        json.dumps({"format_version": "invalid"}), encoding="utf-8"
                    )
                    sentinel = external / ".kb/sentinel"
                    sentinel.write_bytes(b"unchanged")
                    external_before = self.artifact_bytes(external)
                    original_open = os.open
                    swapped = False

                    def swap_before_marker_open(path, flags, mode=0o777, *, dir_fd=None):
                        nonlocal swapped
                        if Path(path).name == "goldenwave.json" and not swapped:
                            (root / ".kb").rename(moved_kb)
                            try:
                                (root / ".kb").symlink_to(external / ".kb", target_is_directory=True)
                            except (NotImplementedError, OSError) as error:
                                self.skipTest(f"symlink operations unavailable: {error}")
                            swapped = True
                        return original_open(path, flags, mode, dir_fd=dir_fd)

                    writer = RecordingWriter()
                    with mock.patch.object(workflow.os, "open", side_effect=swap_before_marker_open):
                        if command == "accept":
                            result = self.accept(writer, root=root)
                        else:
                            result = workflow.reject_candidate(
                                CANDIDATE,
                                CANDIDATE_BYTES,
                                root,
                                now=NOW,
                                confirm=CANDIDATE["candidate_id"],
                                review_digest=DIGEST,
                                reason="privacy",
                                writer=writer,
                            )

                    self.assertTrue(swapped)
                    self.assertEqual("failed", result["summary"]["status"])
                    self.assertEqual(
                        ["GW_CANDIDATE_KB_UNSAFE"],
                        [error["code"] for error in result["errors"]],
                    )
                    self.assertEqual([], writer.writes)
                    self.assertEqual(external_before, self.artifact_bytes(external))
                    self.assertEqual([], list((moved_kb / "candidate-decisions").glob("*.json")))
                    self.assertFalse((root / CANDIDATE["target"]["path"]).exists())

    def test_reject_writes_only_a_redacted_controlled_receipt(self) -> None:
        writer = RecordingWriter()
        result = workflow.reject_candidate(
            CANDIDATE,
            CANDIDATE_BYTES,
            self.root,
            now=NOW,
            confirm=CANDIDATE["candidate_id"],
            review_digest=DIGEST,
            reason="privacy",
            writer=writer,
        )

        self.assertEqual("rejected", result["summary"]["status"])
        self.assertEqual(["decision", "rejected"], [item[0] for item in writer.writes])
        root_metadata = self.root.stat()
        self.assertEqual(
            [(root_metadata.st_dev, root_metadata.st_ino)] * 2,
            writer.expected_root_identities,
        )
        kb_metadata = (self.root / ".kb").stat()
        decisions_metadata = (self.root / ".kb/candidate-decisions").stat()
        self.assertEqual(
            {
                ".kb": (kb_metadata.st_dev, kb_metadata.st_ino),
                ".kb/candidate-decisions": (
                    decisions_metadata.st_dev,
                    decisions_metadata.st_ino,
                ),
            },
            writer.expected_component_identities[0],
        )
        self.assertEqual(
            writer.expected_component_identities[0],
            writer.expected_component_identities[1],
        )
        claim = json.loads(writer.writes[0][2])
        self.assertEqual("reject", claim["decision"])
        self.assertEqual(
            {"record_version", "candidate_id", "decision", "decided_at", "candidate_sha256"},
            set(claim),
        )
        receipt = json.loads(writer.writes[1][2])
        self.assertEqual("privacy", receipt["reason"])
        self.assertNotIn("content", receipt)
        self.assertNotIn("source_ref", receipt)


if __name__ == "__main__":
    unittest.main()
