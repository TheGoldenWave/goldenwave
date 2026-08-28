#!/usr/bin/env python3
"""Reproducible Phase 1C sandbox crash and restore drill."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from gw_candidate import reliable  # noqa: E402


def main() -> int:
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="gw-p1c-drill-") as temporary:
        workspace = Path(temporary)
        root = workspace / "kb"
        (root / ".kb").mkdir(parents=True)
        (root / ".kb/goldenwave.json").write_text(
            '{"format_version":"gwkb/v0.1"}\n', encoding="utf-8"
        )
        (root / "wiki/methods").mkdir(parents=True)
        reliable.initialize(root)

        candidate = {
            "candidate_id": "cand_01JAZ6Y5M4N6KD3V8T2WQ9R7HD",
            "storage_class": "git_tracked",
            "target": {"path": "wiki/methods/recovery-drill.md"},
            "content": {"text": "# Recovery drill\n"},
        }
        raw = json.dumps(candidate, sort_keys=True).encode("utf-8")
        authorization = {
            "authorization_basis": "self_context",
            "retention_until": "none",
            "attest_no_consent_required_data": True,
            "acknowledge_git_history": True,
        }
        review = reliable.review(root, candidate, raw, **authorization)

        def interrupt_after_commit(event: str) -> None:
            if event == "active":
                raise OSError("simulated crash after active commit")

        interrupted = reliable.apply(
            root,
            candidate,
            raw,
            expected_base=review["active_base"],
            idempotency_key=review["idempotency_key"],
            confirm=candidate["candidate_id"],
            review_digest=hashlib.sha256(raw).hexdigest(),
            now="2026-08-16T12:00:00Z",
            boundary_hook=interrupt_after_commit,
            **authorization,
        )
        if interrupted["status"] != "indeterminate":
            raise RuntimeError("fault injection did not reach indeterminate state")

        recovered = reliable.recover(root)
        backup = workspace / "backup"
        reliable.backup(root, backup)
        restored = workspace / "restored"
        reliable.restore(backup, restored)

        source = root / candidate["target"]["path"]
        replica = restored / candidate["target"]["path"]
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        replica_hash = hashlib.sha256(replica.read_bytes()).hexdigest()
        result = {
            "status": "pass",
            "interrupted_status": interrupted["status"],
            "recovery_status": recovered["status"],
            "active_base_match": reliable.active_base(root) == reliable.active_base(restored),
            "content_hash_match": source_hash == replica_hash,
            "content_sha256": source_hash,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "measured_rpo_seconds": 0,
            "real_kb_mutated": False,
        }
        if not result["active_base_match"] or not result["content_hash_match"]:
            raise RuntimeError("restore verification failed")
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
