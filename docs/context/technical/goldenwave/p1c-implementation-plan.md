# Phase 1C Reliable Inject Implementation Plan

> **For agentic workers:** REQUIRED: Use subagent-driven development (if subagents are available) or executing-plans to implement this plan. Steps use checkbox syntax for tracking.

**Goal:** Deliver crash-recoverable, idempotent Candidate inject with active-base CAS, verified sandbox backup/restore and controlled adopt repair.

**Architecture:** Store immutable content and generation manifests under `.kb/reliable-inject`, serialize writers with a verified lock, and make `active.json` the single commit point. Treat direct target files as recoverable materialized views and preserve the P1B Contract and authorization boundary.

**Tech Stack:** Python 3.11 standard library, POSIX descriptor-relative I/O and `fcntl`, Ruby Minitest black-box acceptance tests, Python unittest fault/concurrency tests.

---

## Chunk 1: P1C-01 Transaction Core

### Task 1: Freeze identity, review binding and CAS RED

**Files:**
- Create: `tests/specs/reliable-inject/reliable-inject.spec.rb`
- Create: `tests/specs/reliable-inject/test_transaction.py`
- Create: `tests/specs/reliable-inject/run.rb`

- [ ] Add sandbox KB fixtures with empty and populated active generations.
- [ ] Test deterministic operation ID/idempotency key, exact review binding, matching replay and mismatched-key rejection.
- [ ] Test same-base competing operations where exactly one commits and the loser returns base conflict.
- [ ] Run the focused suite and preserve the missing-module/command RED output.

### Task 2: Implement immutable records and active-base CAS

**Files:**
- Create: `scripts/gw_candidate/transaction.py`
- Create: `scripts/gw_candidate/manifest.py`
- Modify: `scripts/gw_candidate/decision.py`

- [ ] Implement canonical JSON/hash helpers and stable operation/key derivation.
- [ ] Implement empty-base and immutable generation manifest validation.
- [ ] Implement target-aware review fields without changing Candidate Contract v0.1.
- [ ] Run identity and manifest tests to GREEN.

### Task 3: Implement serialized transaction commit

**Files:**
- Create: `scripts/gw_candidate/transaction_store.py`
- Modify: `scripts/gw_candidate/workflow.py`
- Modify: `scripts/gw_candidate/cli.py`

- [ ] Add verified lock acquisition and fail-closed platform behavior.
- [ ] Persist objects, prepared journal and manifest before active-pointer replacement.
- [ ] Add required review/accept base and idempotency arguments.
- [ ] Make exact replay return the existing receipt and conflicts never overwrite.
- [ ] Run focused RED/GREEN tests, P1B regression and Python compile.

### Task 4: Review P1C-01

- [ ] Run branch coverage and `git diff --check`.
- [ ] Complete independent spec review, then code/security review; fix Critical/Major findings test-first.
- [ ] Record E-P1C-01 only after both reviews approve.

## Chunk 2: P1C-02 Recovery, Backup and Repair

### Task 5: Freeze crash/concurrency recovery RED

**Files:**
- Create: `tests/specs/reliable-inject/test_recovery.py`
- Create: `tests/specs/reliable-inject/test_concurrency.py`

- [ ] Inject failure at every journal/object/manifest/pointer/materialization persistence boundary.
- [ ] Add multiprocess identical replay and competing-base tests.
- [ ] Add corrupt/tampered journal, object, manifest and pointer tests.
- [ ] Preserve expected RED output before implementation.

### Task 6: Implement reconciliation and materialized-view repair

**Files:**
- Create: `scripts/gw_candidate/recovery.py`
- Modify: `scripts/gw_candidate/transaction_store.py`
- Modify: `scripts/gw_candidate/cli.py`

- [ ] Reconcile prepared, committed and completed journals under the same lock.
- [ ] Complete or abort only when hashes and active-base relationships prove the action.
- [ ] Rebuild missing exact-content materialized views and refuse divergent files.
- [ ] Run recovery and concurrency tests to GREEN.

### Task 7: Implement verified sandbox backup/restore

**Files:**
- Create: `scripts/gw_candidate/backup.py`
- Create: `tests/specs/reliable-inject/test_backup.py`
- Modify: `scripts/gw_candidate/cli.py`

- [ ] Write RED tests for active hash inventory, corruption, partial restore, existing-target refusal and private-backup rejection.
- [ ] Implement git-tracked-only backup manifest and empty-sandbox restore.
- [ ] Verify restored active root, objects, receipts and materialized views.
- [ ] Run backup tests to GREEN.

### Task 8: Implement controlled adopt repair

**Files:**
- Create: `skills/goldenwave-init/scripts/gw_init/repair.py`
- Modify: `skills/goldenwave-init/scripts/gw_init/cli.py`
- Modify: `skills/goldenwave-init/scripts/gw_init/constants.py`
- Modify: `skills/goldenwave-init/assets/kb-template/template-manifest.json`
- Test: `tests/specs/goldenwave-init/goldenwave-init.spec.rb`

- [ ] Write RED tests for plan digest, confirmation, dirty/unsafe refusal and no user-file overwrite.
- [ ] Implement plan-repair and apply-repair for Phase 1C managed scaffolding only.
- [ ] Run init and prior regressions to GREEN.

### Task 9: Review P1C-02

- [ ] Run fault, concurrency, backup, restore, repair and full regression suites with zero skips.
- [ ] Complete independent spec and code/security reviews; fix Critical/Major findings test-first.
- [ ] Record E-P1C-02 only after approval.

## Chunk 3: P1C-03 Gate

### Task 10: Execute sandbox recovery drill and real-KB read-only gate

**Files:**
- Create: `tests/specs/reliable-inject/recovery_drill.py`
- Create: `docs/prd/goldenwave-strategy/.artifacts/p1c03-gate.md`

- [ ] Generate the documented sandbox profile, inject, interrupt, recover, back up and restore.
- [ ] Verify root/content hashes and record measured elapsed time/RPO evidence.
- [ ] Run real `/Users/goldenwave/KnowledgeBase` doctor/inventory with before/after metadata fingerprints and prove unchanged state.
- [ ] Do not perform real-KB accept, repair or restore.

### Task 11: Close Phase 1 evidence

**Files:**
- Modify: `tests/evidence/phase1b/coverage-summary.txt` or create Phase 1C equivalent.
- Modify: `docs/prd/goldenwave-strategy/.artifacts/evidence-manifest.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/execution-board.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/process.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/notes.md`

- [ ] Run all Phase 1C, P1B, P1A and Phase 0 suites, compile and diff checks from a clean command invocation.
- [ ] Complete final independent architecture/security and QA reviews.
- [ ] Mark P1C-03 and Phase 1 done only with zero failure/error/skip and complete E-P1C evidence.
