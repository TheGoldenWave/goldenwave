from __future__ import annotations

import json
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
            "target": {"path": "wiki/methods/test.md"},
            "content": {"text": "# Test\n"},
        }
        self.raw = json.dumps(self.candidate, sort_keys=True).encode()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_review_identity_is_stable_and_bound_to_base(self) -> None:
        first = reliable.review(self.root, self.candidate, self.raw)
        second = reliable.review(self.root, self.candidate, self.raw)
        self.assertEqual(first, second)
        self.assertRegex(first["operation_id"], r"^op_[0-9a-f]{64}$")
        self.assertRegex(first["idempotency_key"], r"^idem_[0-9a-f]{64}$")
        self.assertEqual(reliable.EMPTY_BASE, first["active_base"])

    def test_apply_replays_same_operation_and_rejects_stale_base(self) -> None:
        review = reliable.review(self.root, self.candidate, self.raw)
        first = reliable.apply(
            self.root,
            self.candidate,
            self.raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
        )
        replay = reliable.apply(
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

        other = dict(self.candidate)
        other["candidate_id"] = "cand_01j9z6n0r4k2m8q7v5x3c1b2b0"
        other["target"] = {"path": "wiki/methods/other.md"}
        raw = json.dumps(other, sort_keys=True).encode()
        stale = reliable.review(self.root, other, raw, active_base=reliable.EMPTY_BASE)
        result = reliable.apply(
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
        review = reliable.review(self.root, self.candidate, self.raw)
        reliable.apply(
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
        review = reliable.review(self.root, self.candidate, self.raw)
        with mock.patch.object(reliable, "_materialize", side_effect=OSError("fault")):
            result = reliable.apply(
                self.root, self.candidate, self.raw,
                expected_base=review["active_base"], idempotency_key=review["idempotency_key"],
            )
        self.assertEqual("indeterminate", result["status"])
        recovered = reliable.recover(self.root)
        self.assertEqual("recovered", recovered["status"])
        replay = reliable.apply(
            self.root, self.candidate, self.raw,
            expected_base=review["active_base"], idempotency_key=review["idempotency_key"],
        )
        self.assertTrue(replay["replayed"])

    def test_concurrent_same_base_has_one_winner(self) -> None:
        candidates = []
        for suffix in ("B0", "B1"):
            candidate = {
                **self.candidate,
                "candidate_id": f"cand_01JAZ6Y5M4N6KD3V8T2WQ9R7{suffix}",
                "target": {"path": f"wiki/methods/{suffix}.md"},
            }
            raw = json.dumps(candidate, sort_keys=True).encode()
            candidates.append((candidate, raw, reliable.review(self.root, candidate, raw)))
        results = []

        def run(item: tuple[dict, bytes, dict]) -> None:
            candidate, raw, review = item
            results.append(reliable.apply(
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

    def test_backup_restore_verifies_active_generation(self) -> None:
        review = reliable.review(self.root, self.candidate, self.raw)
        reliable.apply(
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
            [sys.executable, str(entry), "inject-review", str(candidate_path), "--target", str(self.root)],
            check=True, capture_output=True, text=True,
        )
        review_payload = json.loads(reviewed.stdout)
        applied = subprocess.run(
            [
                sys.executable, str(entry), "inject-apply", str(candidate_path), "--target", str(self.root),
                "--expected-base", review_payload["active_base"], "--idempotency-key", review_payload["idempotency_key"],
            ],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual("applied", json.loads(applied.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
