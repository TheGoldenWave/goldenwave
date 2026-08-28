---
feature_id: goldenwave-strategy
document: technical-design
scope: P1B-02
status: approved-for-implementation
approved: 2026-08-16
---

# P1B-02 Candidate Decision Design

## Goal

Add the smallest auditable `review / accept / reject` workflow for one validated Candidate. A formal write may occur only after an explicit `accept` confirmation bound to the Candidate ID and reviewed byte digest.

## Considered approaches

1. **Stateless commands**: return review and decision results without storing decisions. This is smallest, but rejected because a formal write would not have durable authorization evidence.
2. **Minimal decision journal (selected)**: keep review read-only, write redacted decision receipts under `.kb/candidate-decisions/`, and allow one exclusive target creation after an authorization receipt exists.
3. **Transactional state machine**: add locks, CAS, recovery and multi-file transactions. This is deferred to Phase 1C because it exceeds P1B-02.

## Command contract

```text
goldenwave-candidate review <candidate> [--include-source-ref]
goldenwave-candidate accept <candidate> --target <KB_ROOT> --confirm <CANDIDATE_ID> --review-digest <SHA256> --authorization-basis <BASIS> --retention-until <RFC3339|none> --attest-no-consent-required-data --ack-git-history
goldenwave-candidate reject <candidate> --target <KB_ROOT> --confirm <CANDIDATE_ID> --review-digest <SHA256> --reason <CODE>
```

All commands emit deterministic JSON and use stable error codes. They never run Git commands, contact a network service, or execute Candidate content.

Decision commands use the local system UTC clock for freshness, retention checks and `decided_at`. Only domain-level tests may inject a clock; the production decision CLI has no caller-controlled time option. The `validate` command retains explicit `--now` for deterministic Contract validation.

## Review

- Validates the Candidate with the P1B-01 Validator.
- Performs no filesystem writes.
- Returns the Candidate ID, storage class, target, provenance source type and observation time, content media type, content text and a SHA-256 digest of the exact Candidate bytes for local human review.
- `source_ref` is omitted by default and represented by `source_ref_sha256`. It is disclosed only when the user explicitly supplies `--include-source-ref`; it is never copied into a decision receipt.
- Review output intentionally includes Candidate content because the command is the explicit local disclosure boundary. Validation error output remains redacted.

## Accept

- Requires an existing, non-symlink Knowledge Base root containing `.kb/goldenwave.json`.
- Requires `--confirm` to exactly match the validated Candidate ID and `--review-digest` to match the SHA-256 digest returned by review. Any byte change requires a new review.
- P1B-02 accepts only `storage_class: git_tracked`. `local_private` and `ephemeral` fail closed because v0.1 does not yet define a safe private target mapping.
- Requires a fresh human `store` authorization tuple: fixed `scope: store`, `--authorization-basis self_context|public_source`, `--retention-until <RFC3339|none>`, `revoked_at: null`, `--attest-no-consent-required-data`, and `--ack-git-history`.
- The attestation explicitly states that the reviewed bytes contain no third-party sensitive data, personality inference, or policy-tag category that requires data-subject consent. Because v0.1 cannot independently derive this classification, the CLI treats the attestation as the human B1 decision gate and records it; absent attestation fails closed. Candidates that cannot truthfully satisfy it must be rejected or remain pending for a future Contract with enforceable sensitivity/policy/consent evidence.
- Opens the Knowledge Base root, `.kb`, receipt directory and every existing target parent descriptor-relatively with `O_DIRECTORY|O_NOFOLLOW`. It creates receipt and target files with `O_CREAT|O_EXCL|O_NOFOLLOW`, verifies the opened file is regular with link count one, and never relies on a path-string pre-check for mutation.
- Immediately before the first content write, it verifies that the opened parent reaches the opened KB root and that the requested relative parent path still names the same inode. Swaps completed before this verification fail closed without writing content. The pinned descriptor prevents pathname replacement from redirecting mutation to a different directory object.
- Requires `.kb/candidate-decisions/` and the target parent to exist. Init creates the decision directory; adopt users must add it explicitly before using accept/reject.
- Before any decision-specific receipt, accept and reject compete to exclusively create `<candidate_id>.decision.json`. This shared claim contains only Candidate ID, exact digest, chosen decision and decision time, so sequential and concurrent contradictory decisions conflict. P1B-02 does not reconcile an interrupted claim.
- Every receipt and target file is written completely, flushed with `fsync`, closed, and followed by `fsync` on its opened parent directory before the process advances to the next state. A crash before a persistence boundary may leave a missing or partial file and is treated as indeterminate on the next observed conflict. A failure after the target persistence boundary returns `indeterminate`, never a clean failure claim. Phase 1C owns cross-file reconciliation and transaction recovery.

## Reject

- Requires explicit Candidate ID and reviewed digest confirmation.
- Never writes the formal target.
- Stores one redacted rejection receipt with a controlled reason code: `duplicate`, `incorrect`, `not_relevant`, `privacy`, or `other`.
- Free-form rejection text is out of scope to prevent sensitive content entering audit metadata.

## Decision receipts

Receipts live under `.kb/candidate-decisions/` and never contain Candidate content or `source_ref`.

```json
{
  "record_version": "gw-candidate-decision/v0.1",
  "candidate_id": "cand_...",
  "decision": "authorized|applied|rejected",
  "decided_at": "2026-08-16T10:00:00+08:00",
  "candidate_sha256": "...",
  "target_sha256": "...",
  "authorization_basis": "self_context",
  "authorization_scope": "store",
  "retention_until": null,
  "revoked_at": null,
  "no_consent_required_data_attested": true,
  "git_history_acknowledged": true,
  "reason": "privacy"
}
```

`target_sha256`, the complete store authorization tuple and the Git-history acknowledgement are present only for accepted `git_tracked` Candidates. `reason` is present only for rejection. Receipt filenames use only the validated Candidate ID and controlled decision suffix. Receipts never contain Candidate content, `source_ref`, or clear target paths.

Target paths must be NFC-normalized and must not contain Unicode bidirectional embedding, override, isolate or pop-direction controls. Ordinary international filenames, including Chinese, remain valid.

## Confirmed write outcome matrix

| Last fsync-confirmed state in the current process | CLI outcome | Meaning |
|---|---|---|
| no claim | failed | no decision claim and no target write |
| decision claim only | failed | decision claimed; decision-specific receipt or target not completed |
| authorized receipt only | failed | authorization recorded; target not created |
| authorized receipt + target | indeterminate | formal target exists; applied receipt missing |
| authorized + target + applied | applied | write completed |

Retries never overwrite a target or receipt. An existing malformed/partial artifact is a conflict with an indeterminate prior outcome, not evidence of a confirmed state. P1B-02 reports the last persistence boundary observed by the current process but does not reconcile prior crashes.

## Failure behavior

- Invalid Candidate: reuse P1B-01 errors, no writes.
- Confirmation mismatch: `GW_CANDIDATE_CONFIRMATION_MISMATCH`, no writes.
- Reviewed digest mismatch: `GW_CANDIDATE_REVIEW_MISMATCH`, no writes.
- Missing/unsupported authorization tuple, consent-required-data attestation or Git warning acknowledgement: `GW_CANDIDATE_AUTHORIZATION_REQUIRED`, no writes.
- Unsupported storage class: `GW_CANDIDATE_STORAGE_UNSUPPORTED`, no writes.
- Unsafe Knowledge Base or target path: `GW_CANDIDATE_KB_UNSAFE` or `GW_CANDIDATE_TARGET_UNSAFE`, no formal write.
- Existing target or decision receipt: `GW_CANDIDATE_CONFLICT`, no overwrite.
- Filesystem failure before target creation: `GW_CANDIDATE_WRITE_FAILED`.
- Failure after target creation but before the applied receipt: `GW_CANDIDATE_APPLY_INDETERMINATE`; output status is `indeterminate` and contains no clear path.

## Test boundary

Acceptance tests must prove:

- review is deterministic and read-only;
- accept/reject bind the exact reviewed Candidate digest and reject changed bytes;
- invalid review output remains redacted;
- accept requires exact confirmation, a valid `git_tracked` storage class, the complete store authorization tuple, the consent-required-data attestation and explicit Git-history acknowledgement;
- local-private and ephemeral accept fail closed;
- target traversal, symlink parents, parent swaps completed before the final ancestry/inode verification, missing KB marker, hardlink conflicts and existing targets fail closed;
- accepted content is written exactly once and receipts contain no content/source reference;
- reject writes only a controlled receipt and never the target;
- injected failure after each file/directory fsync boundary returns the corresponding honest failed/indeterminate result and never overwrites on retry;
- all prior Candidate, Phase 1A and Phase 0 tests remain green.

## Deferred to Phase 1C

CAS, concurrent writers, retry/idempotency, atomic multi-file commit, crash reconciliation, backup/restore and migration are explicitly out of scope. A non-cooperating same-UID process can rename or reparent an already-open directory after the final verification; POSIX/macOS provide no portable no-lock primitive that continuously preserves namespace ancestry. That residual risk belongs to the Phase 1C concurrency and OS trust model and is not represented as a P1B-02 guarantee.
