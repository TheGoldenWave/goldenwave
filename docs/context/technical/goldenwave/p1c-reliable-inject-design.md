---
feature_id: goldenwave-strategy
task_ids: [P1C-01, P1C-02, P1C-03]
status: approved-by-existing-prd-boundary
updated: 2026-08-16
decision_level: D1
---

# Phase 1C Reliable Inject Design

## Goal and Boundaries

Phase 1C adds stable operation identity, idempotent replay, active-base CAS, serialized transaction commit, crash reconciliation, verified backup/restore evidence and explicitly bounded adopt repair. It does not change `context-candidate/v0.1`, enable `local_private` accept, create Git commits/remotes, or write a real personal Knowledge Base without a fresh operation-specific authorization.

## Considered Approaches

1. **In-place multi-file journal.** Smallest change, but readers can observe a target before receipts and recovery must reason about overwritten live paths.
2. **Whole Knowledge Base generation directories.** Clean atomic pointer switch, but copies unrelated user content and scales poorly.
3. **Immutable objects plus generation manifests.** Stage content-addressed objects, commit one immutable manifest, then CAS-switch one active pointer. This is selected because retries converge on stable hashes and GoldenWave readers only observe complete generations.

## Storage Layout

```text
.kb/reliable-inject/
  active.json
  lock
  objects/<sha256>
  manifests/<generation-id>.json
  transactions/<operation-id>.json
  receipts/<operation-id>.json
  backups/<backup-id>.json
```

All JSON uses sorted keys, UTF-8 and a trailing newline. IDs are lowercase SHA-256 tokens with a type prefix. Records never contain Candidate body, `source_ref`, absolute KB paths or clear target paths; target paths are represented by a salted-in-record hash and are present only inside the active manifest required to materialize the governed view.

## Identity and Review Binding

- `operation_id` is derived from the exact Candidate digest, Candidate ID, governed target path, action and authorization tuple.
- The idempotency key is `sha256(operation_id + expected_active_base)` and is produced by a target-aware review.
- Target-aware review remains read-only and returns the current active-base token, operation ID and idempotency key.
- Accept requires exact Candidate confirmation, reviewed digest, active-base token and idempotency key. A matching completed operation returns the recorded result without writing. A key reused for different material fails closed.

## Transaction Protocol

1. Validate Candidate and authorization before opening transaction storage.
2. Open and verify the KB root, `.kb` path and reliable-inject directories with descriptor-relative no-follow operations.
3. Acquire an advisory exclusive `flock` on the pre-created lock file; unsupported platforms fail closed.
4. Re-read `active.json` under the lock. If its token differs from `expected_active_base`, return `GW_CANDIDATE_BASE_CONFLICT` with no formal mutation.
5. Persist content-addressed Candidate content and redacted receipt objects using exclusive writes and fsync.
6. Persist a `prepared` transaction journal containing hashes only.
7. Persist the immutable next-generation manifest and verify its root hash.
8. Atomically replace `active.json` with a same-directory temporary file, then fsync the directory. This is the only commit point.
9. Materialize the governed target with a no-overwrite or exact-content check, persist the completed receipt, and mark the journal `completed`. Materialization is recoverable derived state; the active manifest is authoritative.

GoldenWave readers resolve content through the active manifest. A legacy direct-file reader is outside the atomic-read guarantee; doctor reports materialized-view drift instead of silently treating it as authoritative.

## Crash and Concurrency Recovery

Recovery always holds the same lock and is idempotent:

- journal exists, manifest absent: remove unreferenced staged objects only when link/reference checks prove safety, then mark aborted;
- manifest exists, active pointer still names the old base: verify artifacts, then either complete the recorded CAS or abort if another generation won;
- active pointer names the transaction generation: rematerialize missing exact-content views and complete the receipt;
- active pointer, manifest or object hash mismatch: stop with `GW_CANDIDATE_RECOVERY_REQUIRED`; never guess or overwrite.

Concurrent requests serialize on the lock. Same operation and key converge to one receipt; different operations created from the same base produce one winner and deterministic base conflicts for losers.

## Backup and Restore Evidence

Phase 1C backup covers only the active manifest, referenced `git_tracked` objects, redacted transaction/receipt records and the KB format marker. It writes a content-hash inventory into a caller-selected temporary/sandbox destination. `local_private` backup remains unsupported until an encrypted mechanism is selected and must return an honest unsupported result.

Restore verifies every hash into a new or empty sandbox KB, rebuilds materialized views, runs doctor and compares the active root hash. It never overwrites an existing real KB. The Gate records measured RPO/RTO for the test profile without claiming production-scale guarantees.

## Controlled Adopt Repair

`adopt plan-repair` remains read-only and emits a digest-bound repair plan limited to missing Phase 1C managed directories/files and exact managed-template drift. `adopt apply-repair` requires the plan digest and confirmation, refuses dirty Git state, symlinks, tracked private/ephemeral content, L3 storage ambiguity and user-authored file replacement. It never stages, commits, pushes or changes storage class.

## Error Model

New stable errors include base conflict, idempotency mismatch, lock/platform unsupported, transaction corrupt, recovery required, backup unsupported and repair confirmation mismatch. All outputs keep the current structured envelope and redact absolute paths and content.

## Verification

- RED/GREEN tests for identity, target-aware review, replay and CAS.
- Deterministic fault injection before and after every object, journal, manifest, active-pointer and materialization fsync boundary.
- Multiprocess same-key and same-base/different-key races.
- Tampered journal/object/manifest and interrupted recovery fixtures.
- Backup corruption, incomplete restore and unsupported private backup fixtures.
- Repair-plan binding, dirty-worktree refusal and no-user-file-overwrite fixtures.
- Full P1B, P1A and Phase 0 regression, branch coverage >=80%, security/strategy fixture coverage, no skips.

## Gate Interpretation

P1C-03 uses a temporary sandbox that mirrors the real Knowledge Base format plus a fresh read-only doctor/inventory run against the real KB. It does not mutate `/Users/goldenwave/KnowledgeBase`; a real write drill requires a separate explicit authorization.
