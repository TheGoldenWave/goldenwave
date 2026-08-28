# P1B-02 Candidate Decision Implementation Plan

> **For agentic workers:** REQUIRED: use subagent-driven development. Steps use checkbox syntax for tracking.

**Goal:** Implement the approved single-Candidate `review / accept / reject` workflow with digest-bound authorization, redacted receipts and descriptor-relative safe writes.

**Architecture:** Keep parsing and validation in the existing P1B-01 modules. Add a focused decision module for review payloads, authorization validation and receipt construction, plus a filesystem module that performs descriptor-relative no-follow exclusive writes and fsync boundaries. CLI only parses arguments and maps domain results to deterministic JSON.

**Tech Stack:** Python 3.11 standard library, Ruby Minitest acceptance harness, JSON Schema SSOT.

---

## Chunk 1: Freeze P1B-02 acceptance behavior

### Task 1: QA RED suite

**Files:**
- Create: `tests/specs/candidate-decision/candidate-decision.spec.rb`
- Create: `tests/specs/candidate-decision/test_safe_write.py`
- Create: `tests/specs/candidate-decision/test_workflow.py`
- Create: `tests/specs/candidate-decision/run.rb`
- Create: `tests/specs/candidate-decision/fixtures/`

- [ ] Add a temp Knowledge Base helper with `.kb/goldenwave.json`, `.kb/candidate-decisions/` and governed target parents.
- [ ] Add read-only deterministic review tests, including default `source_ref` hashing and explicit local disclosure.
- [ ] Add digest-change, ID-confirmation, storage-class and full authorization-tuple rejection tests.
- [ ] Add successful git-tracked accept assertions for exact target bytes and redacted authorized/applied receipts.
- [ ] Add reject assertions proving no target write and a controlled redacted receipt.
- [ ] Add traversal, symlink parent, parent-swap, hardlink conflict, existing target/receipt, malformed/partial artifact, retry non-overwrite and malformed KB tests.
- [ ] Run `ruby tests/specs/candidate-decision/run.rb` and preserve the expected missing-command RED result.

## Chunk 2: Implement the minimal decision workflow

### Task 2: Decision domain logic

**Files:**
- Create: `scripts/gw_candidate/decision.py`
- Modify: `scripts/gw_candidate/constants.py`

- [ ] Add stable decision result/error constants and controlled reason/basis enums.
- [ ] Implement exact-byte SHA-256 review digests and source/target hashing.
- [ ] Implement review payload allowlisting.
- [ ] Implement ID/digest/storage/authorization validation and redacted receipt builders.
- [ ] Run the focused suite and verify domain failures progress toward GREEN.

### Task 3: Descriptor-relative filesystem writer

**Files:**
- Create: `scripts/gw_candidate/safe_write.py`

- [ ] Open KB root and every existing directory component with `O_DIRECTORY|O_NOFOLLOW`.
- [ ] Create files with `O_CREAT|O_EXCL|O_NOFOLLOW`, verify regular file/link count, write all bytes, fsync file and parent.
- [ ] Return controlled conflict/unsafe/write/indeterminate outcomes without clear paths.
- [ ] Expose an in-process persistence-boundary callback for tests without a production fault environment variable.
- [ ] Use `test_safe_write.py` to inject failure after every file fsync and parent-directory fsync and verify file/link invariants.
- [ ] Run parent-swap, hardlink, malformed/partial artifact, conflict and retry non-overwrite tests to GREEN.

### Task 4: Decision workflow coordinator

**Files:**
- Create: `scripts/gw_candidate/workflow.py`
- Test: `tests/specs/candidate-decision/test_workflow.py`

- [ ] Own the ordered state machine: validate authorization -> authorized receipt -> target -> applied receipt.
- [ ] Convert the last confirmed persistence boundary into `failed`, `indeterminate` or `applied` without path/content leakage.
- [ ] Inject the single-file writer as a dependency so tests can fail each boundary deterministically.
- [ ] Prove authorized-only, target-without-applied, fully-applied and retry-conflict outcomes in direct module tests.
- [ ] Run direct Python tests to GREEN before CLI integration.

### Task 5: CLI commands

**Files:**
- Modify: `scripts/gw_candidate/cli.py`
- Modify: `contracts/context-candidate/v0.1/README.md`

- [ ] Add `review`, `accept` and `reject` parsers exactly matching the approved design.
- [ ] Reuse P1B-01 parsing/validation and keep invalid diagnostics redacted.
- [ ] Emit deterministic JSON statuses: `reviewable`, `applied`, `rejected`, `failed`, `indeterminate`.
- [ ] Run the complete P1B-02 suite to GREEN.

## Chunk 3: Integrate, review and close evidence

### Task 6: Knowledge Base scaffold and regression

**Files:**
- Modify: `skills/goldenwave-init/assets/kb-template/template-manifest.json`
- Modify tests under `tests/specs/goldenwave-init/` only if the frozen template expectations require alignment.

- [ ] Add `.kb/candidate-decisions/` to new Knowledge Base scaffolding.
- [ ] Run Candidate Decision, Candidate Contract, Phase 1A and Phase 0 suites.
- [ ] Run Python compile, coverage and `git diff --check`.

### Task 7: Independent reviews and project evidence

**Files:**
- Modify: `docs/prd/goldenwave-strategy/.artifacts/evidence-manifest.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/execution-board.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/process.md`
- Modify: `docs/prd/goldenwave-strategy/.artifacts/notes.md`

- [ ] Request non-author spec review against the approved design and QA fixtures.
- [ ] Request non-author code/security review; fix all Critical/Major findings test-first and re-review.
- [ ] After the final review fix and approval, rerun Candidate Decision, Candidate Contract, Phase 1A and Phase 0 suites, direct Python module tests, Python compile, branch coverage and `git diff --check`.
- [ ] Record commands, RED/GREEN evidence, reviewer and coverage in existing evidence sources.
- [ ] Mark P1B-02 done only after reviewer approval and no skipped Gate tests.
