# Phase 1C Reliable Inject Implementation Plan

> **For agentic workers:** REQUIRED: Use subagent-driven development (if subagents are available) or executing-plans to implement this plan. Steps use checkbox syntax for tracking.

**Goal:** Deliver crash-recoverable, idempotent Candidate inject with active-base CAS, verified sandbox backup/restore and controlled adopt repair.

**Architecture:** Store immutable content and generation manifests under `.kb/reliable-inject`, serialize writers with a verified lock, and make `active.json` the single commit point. Treat direct target files as recoverable materialized views and preserve the P1B Contract and authorization boundary.

**Tech Stack:** Python 3.11 standard library, POSIX descriptor-relative I/O and `fcntl`, Ruby Minitest black-box acceptance tests, Python unittest fault/concurrency tests.

---

## Chunk 1: P1C-01 Transaction Core

### Task 1: Freeze identity, review binding and CAS RED

**Files:**
- Create: `tests/specs/reliable-inject/test_reliable.py`
- Create: `tests/specs/reliable-inject/run.rb`

- [x] Add sandbox KB fixtures with empty and populated active generations.
- [x] Test deterministic operation ID/idempotency key, exact review binding, matching replay and mismatched-key rejection.
- [x] Test same-base competing operations where exactly one commits and the loser returns base conflict.
- [x] Run the focused suite and preserve the missing-module/command RED output.

### Task 2: Implement immutable records and active-base CAS

**Files:**
- Create: `scripts/gw_candidate/reliable.py`
- Modify: `scripts/gw_candidate/decision.py`

- [x] Implement canonical JSON/hash helpers and stable operation/key derivation.
- [x] Implement empty-base and immutable generation manifest validation.
- [x] Implement target-aware review fields without changing Candidate Contract v0.1.
- [x] Run identity and manifest tests to GREEN.

### Task 3: Implement serialized transaction commit

**Files:**
- Modify: `scripts/gw_candidate/reliable.py`
- Modify: `scripts/gw_candidate/cli.py`

- [x] Add verified lock acquisition and fail-closed platform behavior.
- [x] Persist objects, prepared journal and manifest before active-pointer replacement.
- [x] Add required review/accept base and idempotency arguments.
- [x] Make exact replay return the existing receipt and conflicts never overwrite.
- [x] Run focused RED/GREEN tests, P1B regression and Python compile.

### Task 4: Review P1C-01

- [x] Run branch coverage and `git diff --check`.
- [x] Complete independent spec review, then code/security review; fix Critical/Major findings test-first.
- [x] Record E-P1C-01 only after both reviews approve.

## Chunk 2: P1C-02 Recovery, Backup and Repair

### Task 5: Freeze crash/concurrency recovery RED

**Files:**
- Modify: `tests/specs/reliable-inject/test_reliable.py`

- [x] Inject failure at every journal/object/manifest/pointer/materialization persistence boundary.
- [x] Add multiprocess identical replay and competing-base tests.
- [x] Add corrupt/tampered journal, object, manifest and pointer tests.
- [x] Preserve expected RED output before implementation.

### Task 6: Implement reconciliation and materialized-view repair

**Files:**
- Modify: `scripts/gw_candidate/reliable.py`
- Modify: `scripts/gw_candidate/cli.py`

- [x] Reconcile prepared, committed and completed journals under the same lock.
- [x] Complete or abort only when hashes and active-base relationships prove the action.
- [x] Rebuild missing exact-content materialized views and refuse divergent files.
- [x] Run recovery and concurrency tests to GREEN.

### Task 7: Implement verified sandbox backup/restore

**Files:**
- Modify: `scripts/gw_candidate/reliable.py`
- Modify: `tests/specs/reliable-inject/test_reliable.py`
- Modify: `scripts/gw_candidate/cli.py`

- [x] Write RED tests for active hash inventory, corruption, partial restore, existing-target refusal and private-backup rejection.
- [x] Implement git-tracked-only backup manifest and empty-sandbox restore.
- [x] Verify restored active root, objects, receipts and materialized views.
- [x] Run backup tests to GREEN.

### Task 8: Implement controlled adopt repair

**Files:**
- Create: `skills/goldenwave-init/scripts/gw_init/repair.py`
- Modify: `skills/goldenwave-init/scripts/gw_init/cli.py`
- Modify: `skills/goldenwave-init/scripts/gw_init/constants.py`
- Modify: `skills/goldenwave-init/assets/kb-template/template-manifest.json`
- Test: `tests/specs/goldenwave-init/goldenwave-init.spec.rb`

- [x] Write RED tests for plan digest, confirmation, dirty/unsafe refusal and no user-file overwrite.
- [x] Implement plan-repair and apply-repair for Phase 1C managed scaffolding only.
- [x] Run init and prior regressions to GREEN.

### Task 9: Review P1C-02

- [x] Run fault, concurrency, backup, restore, repair and full regression suites with zero skips.
- [x] Complete independent spec and code/security reviews; fix Critical/Major findings test-first.
- [x] Record E-P1C-02 only after approval.

## Chunk 3: P1C-03 Gate

### Task 10: Execute sandbox recovery drill and real-KB read-only gate

**Files:**
- Create: `tests/specs/reliable-inject/recovery_drill.py`
- Create: `docs/prd/goldenwave-strategy/.artifacts/p1c03-gate.md`

- [x] Generate the documented sandbox profile, inject, interrupt, recover, back up and restore.
- [x] Verify root/content hashes and record measured elapsed time/RPO evidence.
- [x] Run real `/Users/goldenwave/KnowledgeBase` doctor/inventory with before/after metadata fingerprints and prove unchanged state.
- [x] Do not perform real-KB accept, repair or restore.

### Task 11: Close Phase 1 evidence

**Files:**
- Modify: `tests/evidence/phase1b/coverage-summary.txt` or create Phase 1C equivalent.
- Modify: `docs/prd/goldenwave-strategy/.artifacts/evidence-manifest.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/execution-board.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/process.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/notes.md`

- [x] Run all Phase 1C, P1B, P1A and Phase 0 suites, compile and diff checks from a clean command invocation.
- [x] Complete final independent architecture/security and QA reviews.
- [x] Mark P1C-03 and Phase 1 done only with zero failure/error/skip and complete E-P1C evidence.
