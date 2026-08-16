from __future__ import annotations

import json
import hashlib
import subprocess
import threading
from unittest import mock
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from gw_candidate import reliable  # noqa: E402


class ReliableInjectTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "kb"
        (self.root / ".kb").mkdir(parents=True)
        (self.root / ".kb/goldenwave.json").write_text(
            '{"format_version":"gwkb/v0.1"}\n', encoding="utf-8"
        )
        (self.root / "wiki/methods").mkdir(parents=True)
        reliable.initialize(self.root)
        self.candidate = {
            "candidate_id": "cand_01j9z6n0r4k2m8q7v5x3c1b2a9",
            "storage_class": "git_tracked",
            "target": {"path": "wiki/methods/test.md"},
            "content": {"text": "# Test\n"},
        }
        self.raw = json.dumps(self.candidate, sort_keys=True).encode()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def review_candidate(self, root: Path, candidate: dict, raw: bytes, **kwargs: object) -> dict:
        return reliable.review(
            root,
            candidate,
            raw,
            authorization_basis="self_context",
            retention_until="none",
            attest_no_consent_required_data=True,
            acknowledge_git_history=True,
            **kwargs,
        )

    def apply_candidate(self, root: Path, candidate: dict, raw: bytes, **kwargs: object) -> dict:
        expected_base = kwargs.pop("expected_base")
        idempotency_key = kwargs.pop("idempotency_key")
        boundary_hook = kwargs.pop("boundary_hook", None)
        optional = {} if boundary_hook is None else {"boundary_hook": boundary_hook}
        return reliable.apply(
            root,
            candidate,
            raw,
            expected_base=expected_base,
            idempotency_key=idempotency_key,
            confirm=candidate["candidate_id"],
            review_digest=hashlib.sha256(raw).hexdigest(),
            authorization_basis="self_context",
            retention_until="none",
            attest_no_consent_required_data=True,
            acknowledge_git_history=True,
            now="2026-08-16T12:00:00Z",
            **optional,
        )

    def new_reliable_root(self, name: str) -> Path:
        root = Path(self.temp.name) / name
        (root / ".kb").mkdir(parents=True)
        (root / ".kb/goldenwave.json").write_text(
            '{"format_version":"gwkb/v0.1"}\n', encoding="utf-8"
        )
        (root / "wiki/methods").mkdir(parents=True)
        reliable.initialize(root)
        return root

    def test_review_identity_is_stable_and_bound_to_base(self) -> None:
        first = self.review_candidate(self.root, self.candidate, self.raw)
        second = self.review_candidate(self.root, self.candidate, self.raw)
        self.assertEqual(first, second)
        self.assertRegex(first["operation_id"], r"^op_[0-9a-f]{64}$")
        self.assertRegex(first["idempotency_key"], r"^idem_[0-9a-f]{64}$")
        self.assertEqual(reliable.EMPTY_BASE, first["active_base"])

    def test_apply_replays_same_operation_and_rejects_stale_base(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)
        first = self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        replay = self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        self.assertEqual("applied", first["status"])
        self.assertEqual("applied", replay["status"])
        self.assertTrue(replay["replayed"])
        self.assertEqual("# Test\n", (self.root / "wiki/methods/test.md").read_text())
        receipt_path = next((self.root / ".kb/reliable-inject/receipts").iterdir())
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), receipt["candidate_sha256"])

        other = dict(self.candidate)
        other["candidate_id"] = "cand_01j9z6n0r4k2m8q7v5x3c1b2b0"
        other["target"] = {"path": "wiki/methods/other.md"}
        raw = json.dumps(other, sort_keys=True).encode()
        stale = self.review_candidate(self.root, other, raw, active_base=reliable.EMPTY_BASE)
        result = self.apply_candidate(
            self.root,
            other,
            raw,
            expected_base=stale["active_base"],
            idempotency_key=stale["idempotency_key"],
        )
        self.assertEqual("failed", result["status"])
        self.assertEqual("GW_CANDIDATE_BASE_CONFLICT", result["error"])
        self.assertFalse((self.root / "wiki/methods/other.md").exists())

    def test_recovery_repairs_missing_materialized_view(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)
        self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        (self.root / "wiki/methods/test.md").unlink()
        result = reliable.recover(self.root)
        self.assertEqual("recovered", result["status"])
        self.assertEqual("# Test\n", (self.root / "wiki/methods/test.md").read_text())

    def test_post_commit_materialization_failure_is_indeterminate_and_recoverable(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)
        with mock.patch.object(reliable, "_materialize", side_effect=OSError("fault")):
            result = self.apply_candidate(
                self.root, self.candidate, self.raw,
                expected_base=review["active_base"], idempotency_key=review["idempotency_key"],
            )
        self.assertEqual("indeterminate", result["status"])
        recovered = reliable.recover(self.root)
        self.assertEqual("recovered", recovered["status"])
        replay = self.apply_candidate(
            self.root, self.candidate, self.raw,
            expected_base=review["active_base"], idempotency_key=review["idempotency_key"],
        )
        self.assertTrue(replay["replayed"])

    def test_fault_matrix_reports_honest_status_and_recovery_converges(self) -> None:
        expected = {
            "object": ("failed", False),
            "authorized": ("failed", False),
            "journal": ("failed", False),
            "manifest": ("failed", True),
            "active": ("indeterminate", True),
            "materialized": ("indeterminate", True),
            "receipt": ("applied", True),
        }
        for boundary, (status, converges) in expected.items():
            with self.subTest(boundary=boundary):
                root = self.new_reliable_root(f"fault-{boundary}")
                review = self.review_candidate(root, self.candidate, self.raw)

                def fail(event: str) -> None:
                    if event == boundary:
                        raise OSError("fault")

                result = self.apply_candidate(
                    root,
                    self.candidate,
                    self.raw,
                    expected_base=review["active_base"],
                    idempotency_key=review["idempotency_key"],
                    boundary_hook=fail,
                )
                self.assertEqual(status, result["status"])
                recovered = reliable.recover(root)
                self.assertEqual("recovered", recovered["status"])
                self.assertEqual(converges, (root / "wiki/methods/test.md").exists())
                if converges:
                    self.assertEqual("# Test\n", (root / "wiki/methods/test.md").read_text())
                if boundary == "journal":
                    journal = json.loads(next((root / ".kb/reliable-inject/transactions").iterdir()).read_text(encoding="utf-8"))
                    self.assertEqual("aborted", journal["state"])
                    self.assertEqual([], list((root / ".kb/reliable-inject/objects").iterdir()))

    def test_recovery_rejects_tampered_authorization_in_journal(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)

        def interrupt(event: str) -> None:
            if event == "active":
                raise OSError("fault")

        result = self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
            boundary_hook=interrupt,
        )
        self.assertEqual("indeterminate", result["status"])
        journal_path = next((self.root / ".kb/reliable-inject/transactions").iterdir())
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        journal["authorization_basis"] = "forged"
        journal_path.write_text(json.dumps(journal), encoding="utf-8")
        with self.assertRaisesRegex(reliable.ReliableError, "GW_CANDIDATE_TRANSACTION_CORRUPT"):
            reliable.recover(self.root)

    def test_recovery_rejects_active_base_that_does_not_match_manifest(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)
        self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        active_path = self.root / ".kb/reliable-inject/active.json"
        active = json.loads(active_path.read_text(encoding="utf-8"))
        active["active_base"] = "base_" + ("f" * 64)
        active_path.write_text(json.dumps(active), encoding="utf-8")
        with self.assertRaisesRegex(reliable.ReliableError, "GW_CANDIDATE_TRANSACTION_CORRUPT"):
            reliable.recover(self.root)

    def test_concurrent_same_base_has_one_winner(self) -> None:
        candidates = []
        for suffix in ("B0", "B1"):
            candidate = {
                **self.candidate,
                "candidate_id": f"cand_01JAZ6Y5M4N6KD3V8T2WQ9R7{suffix}",
                "target": {"path": f"wiki/methods/{suffix}.md"},
            }
            raw = json.dumps(candidate, sort_keys=True).encode()
            candidates.append((candidate, raw, self.review_candidate(self.root, candidate, raw)))
        results = []

        def run(item: tuple[dict, bytes, dict]) -> None:
            candidate, raw, review = item
            results.append(self.apply_candidate(
                self.root, candidate, raw,
                expected_base=review["active_base"], idempotency_key=review["idempotency_key"],
            ))

        threads = [threading.Thread(target=run, args=(item,)) for item in candidates]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(["applied", "failed"], sorted(result["status"] for result in results))
        self.assertEqual(1, sum(result.get("error") == "GW_CANDIDATE_BASE_CONFLICT" for result in results))

    def test_multiprocess_cli_same_base_has_one_winner(self) -> None:
        entry = REPO / "scripts/goldenwave_candidate.py"
        base_candidate = {
            "contract": "context-candidate/v0.1",
            "contract_status": "experimental",
            "created_at": "2026-07-27T10:00:00+08:00",
            "expires_at": None,
            "storage_class": "git_tracked",
            "provenance": {"source_type": "repository_document", "source_ref": "docs/source.md", "observed_at": "2026-07-27T09:55:00+08:00"},
            "content": {"media_type": "text/markdown", "treat_as": "data", "text": "process race"},
        }
        commands = []
        for suffix, filename in (("HD", "process-a.md"), ("HE", "process-b.md")):
            candidate = {
                **base_candidate,
                "candidate_id": f"cand_01JAZ6Y5M4N6KD3V8T2WQ9R7{suffix}",
                "target": {"kind": "experience", "path": f"wiki/methods/{filename}"},
            }
            candidate_path = Path(self.temp.name) / f"{suffix}.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            review_command = [sys.executable, str(entry), "inject-review", str(candidate_path), "--target", str(self.root), "--authorization-basis", "self_context", "--retention-until", "none", "--attest-no-consent-required-data", "--ack-git-history"]
            reviewed = subprocess.run(review_command, check=True, capture_output=True, text=True)
            values = json.loads(reviewed.stdout)
            commands.append([
                sys.executable, str(entry), "inject-apply", str(candidate_path), "--target", str(self.root),
                "--expected-base", values["active_base"], "--idempotency-key", values["idempotency_key"],
                "--confirm", candidate["candidate_id"], "--review-digest", hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
                "--authorization-basis", "self_context", "--retention-until", "none", "--attest-no-consent-required-data", "--ack-git-history",
            ])
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for command in commands]
        outputs = [process.communicate() for process in processes]
        payloads = [json.loads(stdout) for stdout, _ in outputs]
        self.assertEqual([0, 1], sorted(process.returncode for process in processes))
        self.assertEqual(1, sum(payload.get("status") == "applied" for payload in payloads))
        self.assertEqual(1, sum(payload.get("errors", [{}])[0].get("code") == "GW_CANDIDATE_BASE_CONFLICT" for payload in payloads))

    def test_backup_restore_verifies_active_generation(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)
        self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        backup = Path(self.temp.name) / "backup"
        reliable.backup(self.root, backup)
        restored = Path(self.temp.name) / "restored"
        result = reliable.restore(backup, restored)
        self.assertEqual("restored", result["status"])
        self.assertEqual("# Test\n", (restored / "wiki/methods/test.md").read_text())
        self.assertEqual(reliable.active_base(self.root), reliable.active_base(restored))

    def test_backup_rejects_symlink_inside_managed_state(self) -> None:
        outside = Path(self.temp.name) / "outside"
        outside.write_text("secret", encoding="utf-8")
        link = self.root / ".kb/reliable-inject/objects/link"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        with self.assertRaisesRegex(reliable.ReliableError, "GW_CANDIDATE_KB_UNSAFE"):
            reliable.backup(self.root, Path(self.temp.name) / "unsafe-backup")

    def test_backup_rejects_a_corrupted_referenced_object(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)
        self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        object_path = next((self.root / ".kb/reliable-inject/objects").iterdir())
        object_path.write_text("corrupt", encoding="utf-8")
        with self.assertRaisesRegex(reliable.ReliableError, "GW_CANDIDATE_RECOVERY_REQUIRED"):
            reliable.backup(self.root, Path(self.temp.name) / "corrupt-backup")

    def test_backup_excludes_unreferenced_objects(self) -> None:
        review = self.review_candidate(self.root, self.candidate, self.raw)
        self.apply_candidate(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        extra = b"unreferenced"
        extra_hash = hashlib.sha256(extra).hexdigest()
        (self.root / ".kb/reliable-inject/objects" / extra_hash).write_bytes(extra)
        backup = Path(self.temp.name) / "allowlisted-backup"
        reliable.backup(self.root, backup)
        self.assertFalse((backup / ".kb/reliable-inject/objects" / extra_hash).exists())

    def test_apply_rejects_symlinked_existing_object_even_when_bytes_match(self) -> None:
        content = self.candidate["content"]["text"].encode()
        outside = Path(self.temp.name) / "object-outside"
        outside.write_bytes(content)
        object_path = self.root / ".kb/reliable-inject/objects" / hashlib.sha256(content).hexdigest()
        try:
            object_path.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        review = self.review_candidate(self.root, self.candidate, self.raw)
        with self.assertRaisesRegex(reliable.ReliableError, "GW_CANDIDATE_TARGET_UNSAFE"):
            self.apply_candidate(
                self.root,
                self.candidate,
                self.raw,
                expected_base=review["active_base"],
                idempotency_key=review["idempotency_key"],
            )

    def test_cli_review_and_apply_golden_path(self) -> None:
        candidate_path = Path(self.temp.name) / "candidate.json"
        full_candidate = {
            "contract": "context-candidate/v0.1",
            "contract_status": "experimental",
            "candidate_id": "cand_01JAZ6Y5M4N6KD3V8T2WQ9R7HD",
            "created_at": "2026-07-27T10:00:00+08:00",
            "expires_at": None,
            "storage_class": "git_tracked",
            "provenance": {"source_type": "repository_document", "source_ref": "docs/source.md", "observed_at": "2026-07-27T09:55:00+08:00"},
            "target": {"kind": "experience", "path": "wiki/methods/cli-test.md"},
            "content": {"media_type": "text/markdown", "treat_as": "data", "text": "# Test\n"},
        }
        candidate_path.write_text(json.dumps(full_candidate), encoding="utf-8")
        entry = REPO / "scripts/goldenwave_candidate.py"
        reviewed = subprocess.run(
            [sys.executable, str(entry), "inject-review", str(candidate_path), "--target", str(self.root), "--authorization-basis", "self_context", "--retention-until", "none", "--attest-no-consent-required-data", "--ack-git-history"],
            check=True, capture_output=True, text=True,
        )
        review_payload = json.loads(reviewed.stdout)
        applied = subprocess.run(
            [
                sys.executable, str(entry), "inject-apply", str(candidate_path), "--target", str(self.root),
                "--expected-base", review_payload["active_base"], "--idempotency-key", review_payload["idempotency_key"],
                "--confirm", full_candidate["candidate_id"], "--review-digest", hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
                "--authorization-basis", "self_context", "--retention-until", "none", "--attest-no-consent-required-data", "--ack-git-history",
            ],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual("applied", json.loads(applied.stdout)["status"])

    def test_cli_target_review_is_read_only_when_reliable_state_is_missing(self) -> None:
        state = self.root / ".kb/reliable-inject"
        shutil = __import__("shutil")
        shutil.rmtree(state)
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        candidate_path = Path(self.temp.name) / "candidate-read-only.json"
        candidate_path.write_text(json.dumps({
            "contract": "context-candidate/v0.1", "contract_status": "experimental",
            "candidate_id": "cand_01JAZ6Y5M4N6KD3V8T2WQ9R7HD",
            "created_at": "2026-07-27T10:00:00+08:00", "expires_at": None,
            "storage_class": "git_tracked",
            "provenance": {"source_type": "repository_document", "source_ref": "docs/source.md", "observed_at": "2026-07-27T09:55:00+08:00"},
            "target": {"kind": "experience", "path": "wiki/methods/cli-test.md"},
            "content": {"media_type": "text/markdown", "treat_as": "data", "text": "# Test\n"},
        }), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts/goldenwave_candidate.py"), "inject-review", str(candidate_path), "--target", str(self.root)],
            capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*")))

    def test_reliable_state_rejects_a_symlinked_kb_parent(self) -> None:
        shutil = __import__("shutil")
        original = self.root / ".kb"
        outside = Path(self.temp.name) / "outside-kb"
        shutil.move(original, outside)
        original.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(reliable.ReliableError, "GW_CANDIDATE_KB_UNSAFE"):
            reliable.review(self.root, self.candidate, self.raw)

    def test_cli_inject_apply_requires_the_p1b_authorization_tuple(self) -> None:
        candidate_path = Path(self.temp.name) / "candidate-auth.json"
        candidate_path.write_text(json.dumps({
            "contract": "context-candidate/v0.1", "contract_status": "experimental",
            "candidate_id": "cand_01JAZ6Y5M4N6KD3V8T2WQ9R7HD",
            "created_at": "2026-07-27T10:00:00+08:00", "expires_at": None,
            "storage_class": "git_tracked",
            "provenance": {"source_type": "repository_document", "source_ref": "docs/source.md", "observed_at": "2026-07-27T09:55:00+08:00"},
            "target": {"kind": "experience", "path": "wiki/methods/cli-test.md"},
            "content": {"media_type": "text/markdown", "treat_as": "data", "text": "# Test\n"},
        }), encoding="utf-8")
        review = subprocess.run(
            [sys.executable, str(REPO / "scripts/goldenwave_candidate.py"), "inject-review", str(candidate_path), "--target", str(self.root)],
            check=True, capture_output=True, text=True,
        )
        values = json.loads(review.stdout)
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts/goldenwave_candidate.py"), "inject-apply", str(candidate_path), "--target", str(self.root), "--expected-base", values["active_base"], "--idempotency-key", values["idempotency_key"]],
            capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("GW_CANDIDATE_AUTHORIZATION_REQUIRED", json.loads(result.stdout)["errors"][0]["code"])

    def test_cli_inject_apply_rejects_local_private_storage(self) -> None:
        candidate_path = Path(self.temp.name) / "local-private.json"
        private_candidate = json.loads(
            (REPO / "tests/specs/candidate-contract/fixtures/valid/local-private.json").read_text(encoding="utf-8")
        )
        private_candidate["expires_at"] = None
        candidate_path.write_text(json.dumps(private_candidate), encoding="utf-8")
        reviewed = subprocess.run(
            [sys.executable, str(REPO / "scripts/goldenwave_candidate.py"), "inject-review", str(candidate_path), "--target", str(self.root), "--authorization-basis", "self_context", "--retention-until", "none", "--attest-no-consent-required-data", "--ack-git-history"],
            check=True, capture_output=True, text=True,
        )
        values = json.loads(reviewed.stdout)
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts/goldenwave_candidate.py"), "inject-apply", str(candidate_path), "--target", str(self.root), "--expected-base", values["active_base"], "--idempotency-key", values["idempotency_key"], "--confirm", candidate["candidate_id"], "--review-digest", hashlib.sha256(candidate_path.read_bytes()).hexdigest(), "--authorization-basis", "self_context", "--retention-until", "none", "--attest-no-consent-required-data", "--ack-git-history"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("GW_CANDIDATE_STORAGE_UNSUPPORTED", json.loads(result.stdout)["errors"][0]["code"])


if __name__ == "__main__":
    unittest.main()
