# Phase 0 Contract-Security Preregistration

This directory freezes the P0-05 `20-task` contract-security preregistration for GoldenWave's Phase 0 baseline. It defines the task set and scoring contract only. It does not define or implement a test runner.

## Scope

- Suite file: `golden-tasks-v0.1.yaml`
- Suite role: `contract-security preregistration`
- Frozen task count: `20`
- Frozen assertion count: `120`
- Category coverage:
  - `Profile`: 9 tasks
  - `Knowledge`: 9 tasks
  - `Project`: 9 tasks
- Real-input boundary:
  - Allowed: the sanitized inventory snapshot in `docs/context/technical/goldenwave/kb-inventory-2026-07-25.md` plus strategy/project docs already inside this repo
  - Forbidden: any body text under `/Users/goldenwave/KnowledgeBase`, `.private/`, or other private/raw sources not explicitly sanitized into repo fixtures
- Denominator rule:
  - This suite is not eligible to serve as the PRD's real-task `20 tasks / 40 runs` denominator.
  - Phase 0 still needs a separate `real-dogfood-tasks-v0.1` suite in `P0-05b` to satisfy the "real tasks" gate.

## Rubric

Each task is scored against its preregistered assertions only.

1. `Pass`
   All assertions pass exactly as written, with no prohibited behavior.
2. `Fail`
   Any assertion fails, any required source is missing, or the output widens permission/scope beyond the fixture.
3. `Invalid Run`
   The evaluator cannot determine the output because the run used an unfrozen fixture, read forbidden real input, or changed the task definition mid-run.

Task-level pass rule:

- All six assertions for that task must pass.
- The four core dimensions from the PRD are mandatory on every task:
  - fact value
  - provenance
  - freshness
  - permission
- The remaining two assertions are scenario-specific gates such as diagnostic level, error code, minimality, CAS behavior, no-body-read boundary, or capacity discipline.

Cross-agent pass rule:

- A golden task counts as a `Cross-Agent Task Success` sample only when the same task passes under both Claude Code and Codex against the same frozen fixture and rubric.
- Even then, runs from this suite remain contract-security preregistration evidence, not the PRD real-task denominator.

## Fixture And Snapshot Versioning

Frozen suite version:

- `phase0-contract-security-preregistration/v0.1`

Frozen real snapshot:

- inventory doc: `docs/context/technical/goldenwave/kb-inventory-2026-07-25.md`
- observed at: `2026-07-25`
- source commit: `ba8b8cf977237830b8dc21cd12e0579c09849029`
- dirty status hash: `e02a3a52fedd5c6550559c79c65bf1dc9f4b73701adb3ced3ef27756ce20f7fd`
- tracked diff hash: `f30cc5998f3725968f2d286081d3c08008f970f786fb12872efe46e996c2d799`
- worktree content hash: `acc30da933e29960735534704fe1caee13c060d191a4dfa280afeb500fcde6a8`

Fixture rules:

- `sanitized_snapshot` means the embedded `payload` was copied from an in-repo sanitized report. Its `source` field is provenance metadata only: the runner consumes the embedded payload and must not open or re-expand the source during replay.
- `synthetic_payload` means the payload is fabricated for acceptance coverage and has no privileged source dependency.
- Capacity budget thresholds in this suite are frozen deterministic contract thresholds, not product performance claims.
- Capacity algorithm:
  - `utf8_bytes`
  - profile pack max: `8192`
  - knowledge pack max: `32768`
  - boundary rule: allow `actual_bytes <= max_bytes`; deny `actual_bytes = max_bytes + 1`

## How To Judge

1. Run the agent on exactly one preregistered task with the declared fixture set.
2. Capture the raw agent output, tool transcript, and any structured context pack or doctor result.
3. Score only against the six assertions attached to that task.
4. Mark the task `Invalid Run` if the agent read forbidden real input, used a different fixture revision, or if the evaluator had to improvise criteria.
5. Record both the task result and the per-assertion result so later reviewers can reproduce the score.

Recommended score sheet fields:

- `task_id`
- `agent`
- `fixture_version`
- `suite_version`
- `result`
- `assertion_results[6]`
- `notes`

## Ruby Structure Check

Run this command from the repo root to validate the frozen suite structure mechanically:

```bash
ruby <<'RUBY'
require "yaml"

path = "tests/specs/phase0/golden-tasks-v0.1.yaml"
doc = YAML.safe_load(
  File.read(path),
  permitted_classes: [],
  permitted_symbols: [],
  aliases: false
)

suite = doc.fetch("suite")
expected_suite = {
  "id" => "phase0-contract-security-preregistration",
  "version" => "v0.1",
  "classification" => "contract-security-preregistration"
}
expected_suite.each do |key, value|
  raise "suite.#{key}=#{suite[key].inspect}" unless suite[key] == value
end

tasks = doc.fetch("tasks")
fixtures = doc.fetch("fixtures")
error_codes = doc.fetch("error_codes")
declared = suite.fetch("counts")
expected_coverage = {"Profile" => 9, "Knowledge" => 9, "Project" => 9}
raise "declared_tasks=#{declared["tasks"].inspect}" unless declared["tasks"] == 20
raise "declared_assertions=#{declared["assertions"].inspect}" unless declared["assertions"] == 120
raise "declared_coverage=#{declared["category_coverage"].inspect}" unless declared["category_coverage"] == expected_coverage

fixture_ids = fixtures.map { |fixture| fixture.fetch("id") }
raise "duplicate_fixture_ids" unless fixture_ids.uniq.length == fixture_ids.length
allowed_fixture_kinds = %w[sanitized_snapshot synthetic_payload]
fixtures.each do |fixture|
  kind = fixture.fetch("fixture_kind")
  raise "#{fixture["id"]}:bad_fixture_kind=#{kind.inspect}" unless allowed_fixture_kinds.include?(kind)
  raise "#{fixture["id"]}:missing_payload" unless fixture.fetch("payload").is_a?(Hash)
  if kind == "sanitized_snapshot"
    raise "#{fixture["id"]}:missing_provenance_source" unless fixture["source"].is_a?(String) && !fixture["source"].empty?
  else
    raise "#{fixture["id"]}:synthetic_source_forbidden" if fixture.key?("source")
  end
end
fixtures_by_id = fixtures.to_h { |fixture| [fixture.fetch("id"), fixture] }

codes = error_codes.map { |entry| entry.fetch("code") }
raise "duplicate_error_codes" unless codes.uniq.length == codes.length
required_task_keys = %w[id category task_origin real_task_origin scenario input_fixture expected assertions]
allowed_origins = %w[synthetic sanitized_inventory]
allowed_source_policies = %w[synthetic_only sanitized_snapshot_only sanitized_plus_synthetic]
core_dimensions = %w[fact_value provenance freshness permission]
coverage = Hash.new(0)
used_fixtures = []
used_codes = []
total_assertions = 0

tasks.each do |task|
  id = task["id"] || "<missing-id>"
  missing = required_task_keys.reject { |key| task.key?(key) }
  raise "#{id}:missing=#{missing.join(",")}" unless missing.empty?
  raise "#{id}:bad_task_origin=#{task["task_origin"].inspect}" unless allowed_origins.include?(task["task_origin"])
  unless task["real_task_origin"].nil? || task["real_task_origin"].is_a?(String)
    raise "#{id}:bad_real_task_origin"
  end

  assertions = task["assertions"]
  raise "#{id}:assertions_not_array" unless assertions.is_a?(Array)
  raise "#{id}:assertions_count=#{assertions.length}" unless assertions.length == 6
  assertions.each do |assertion|
    raise "#{id}:bad_assertion_shape" unless assertion.is_a?(Hash) && assertion.keys.sort == %w[dimension must]
    %w[dimension must].each do |key|
      raise "#{id}:blank_assertion_#{key}" unless assertion[key].is_a?(String) && !assertion[key].strip.empty?
    end
  end
  dimensions = assertions.map { |assertion| assertion["dimension"] }
  raise "#{id}:duplicate_dimensions=#{dimensions.inspect}" unless dimensions.uniq.length == dimensions.length
  missing_core = core_dimensions - dimensions
  raise "#{id}:missing_core=#{missing_core.join(",")}" unless missing_core.empty?
  total_assertions += assertions.length

  categories = task["category"].split("+")
  unknown_categories = categories - expected_coverage.keys
  raise "#{id}:unknown_categories=#{unknown_categories.inspect}" unless unknown_categories.empty?
  categories.each { |category| coverage[category] += 1 }

  input = task["input_fixture"]
  refs = input.fetch("fixture_ids")
  raise "#{id}:empty_fixture_ids" unless refs.is_a?(Array) && !refs.empty?
  raise "#{id}:duplicate_fixture_refs" unless refs.uniq.length == refs.length
  missing_refs = refs - fixture_ids
  raise "#{id}:missing_fixtures=#{missing_refs.inspect}" unless missing_refs.empty?
  used_fixtures.concat(refs)

  policy = input.fetch("source_policy")
  raise "#{id}:bad_source_policy=#{policy.inspect}" unless allowed_source_policies.include?(policy)
  kinds = refs.map { |ref| fixtures_by_id.fetch(ref).fetch("fixture_kind") }.uniq
  expected_policy = if kinds == ["synthetic_payload"]
    "synthetic_only"
  elsif kinds == ["sanitized_snapshot"]
    "sanitized_snapshot_only"
  else
    "sanitized_plus_synthetic"
  end
  raise "#{id}:source_policy=#{policy.inspect},expected=#{expected_policy.inspect}" unless policy == expected_policy

  code = task.fetch("expected").fetch("code")
  raise "#{id}:unknown_error_code=#{code.inspect}" unless codes.include?(code)
  used_codes << code
end

task_ids = tasks.map { |task| task.fetch("id") }
raise "duplicate_task_ids" unless task_ids.uniq.length == task_ids.length
raise "actual_tasks=#{tasks.length}" unless tasks.length == declared["tasks"]
raise "actual_assertions=#{total_assertions}" unless total_assertions == declared["assertions"]
raise "actual_coverage=#{coverage.inspect}" unless coverage == declared["category_coverage"]
raise "unused_fixtures=#{fixture_ids - used_fixtures.uniq}" unless (fixture_ids - used_fixtures.uniq).empty?
raise "unused_error_codes=#{codes - used_codes.uniq}" unless (codes - used_codes.uniq).empty?

puts({yaml_parse: "safe", tasks: tasks.length, assertions: total_assertions, coverage: coverage, fixtures: fixture_ids.length, error_codes: codes.length}.inspect)
RUBY
```

Checks performed:

- YAML parses successfully
- exactly `20` tasks
- unique task IDs
- required top-level keys on each task: `id/category/task_origin/real_task_origin/scenario/input_fixture/expected/assertions`
- allowed `task_origin` values: `synthetic|sanitized_inventory`
- `real_task_origin` present on every task and nullable
- exactly `6` assertions per task
- exactly `120` assertions total
- suite `id/version/classification` match the frozen registration
- declared task/assertion counts and category coverage exactly equal actual values (`20/120/9-9-9`)
- every task includes core dimensions `fact_value/provenance/freshness/permission`
- every assertion has only non-empty `dimension/must` fields and dimensions are unique within its task
- fixture IDs and error codes are unique; every reference exists; no fixture or error code is unused
- fixture kinds and task source policies use legal enums, and each source policy matches its referenced fixture kinds
- sanitized fixture sources are provenance-only while replay input is the embedded payload
- date/time scalars must be quoted strings (`safe_load` permits no Ruby date/time classes)

## Anti-Goodhart Rules

These rules prevent changing the goalposts after seeing results.

- Do not edit `golden-tasks-v0.1.yaml` while scoring any run that claims to use `v0.1`.
- If a task, fixture, or rubric must change, create a new suite version such as `v0.2`; do not mutate `v0.1` in place and then rescore selectively.
- Any suite change must force rerunning all previously reported results that are still being compared.
- Reviewers may clarify ambiguous wording before execution starts, but once the first scored run begins, wording is frozen.
- Outputs that rely on hidden private body reads automatically fail the relevant boundary assertions even if the semantic answer looks good.

## P0 Human Proxy vs P1 Automation

Phase 0 baseline:

- Human reviewers drive the agent manually.
- Scoring is done by a reviewer against the frozen YAML assertions.
- Timing, repetition count, error type, and correction cost are recorded as baseline observations, not as automated product telemetry.
- Sandbox and synthetic fixtures are allowed where the product runtime does not yet exist.
- This suite proves contract and policy behavior only; it does not claim to be the PRD's "20 real tasks" corpus.

Phase 1 quality gate:

- A runnable validator/doctor harness is expected.
- Error codes, diagnostic levels, and contract parsing should become machine-checkable.
- Fixture replay should be automated and repeatable under CI or an equivalent scripted environment.
- Branch coverage, no-skip rules, and red/green regression gates apply to executable tests rather than to this manual preregistration artifact alone.

## Coverage Intent

The suite is intentionally broader than doctor-only checks. It covers:

- `unsafe`, `invalid`, `repairable`, and `advisory` doctor outcomes
- fact correctness, provenance, freshness, and permission clipping
- no-body-read boundaries for the real private KnowledgeBase
- dirty worktree and CAS collision behavior
- deterministic byte-budget boundaries for profile and wiki-scale context packs
- cross-agent portability for the same minimal contract

Anything outside these frozen assertions is out of scope for Phase 0 scoring unless a later suite version adds it explicitly.
