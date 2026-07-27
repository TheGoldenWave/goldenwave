# Phase 0 Real Dogfood Candidate Suite

This file defines the `P0-05b` candidate corpus frozen on July 25, 2026: `20` anonymized work-intent tasks, `20` embedded oracle manifests, and `120` concrete assertions. The suite remains `pending_representativeness_confirmation` until one owner confirmation binds the complete immutable manifest.

The suite is the candidate denominator for the PRD real-task baseline. Phase 0 may execute manual human-proxy observations after confirmation. Phase 2 is the first phase that may claim the full `20 tasks x 2 agents = 40 runs` cross-agent result. `golden-tasks-v0.1.yaml` remains a contract-security suite and is not this denominator.

## Immutable Suite Manifest

`suite.immutable_manifest.content_sha256` is SHA-256 over canonical UTF-8 JSON with recursively sorted object keys. Its payload contains the complete stable suite contract:

- suite version
- every task field, including ordered prompts, protocols, assertions, and expected references
- all source paths, content digests, dates, and dynamic-status flags
- all oracle content digests
- confirmation protocol, oracle schema, counts, fixture policy, and evidence policy

Only runtime confirmation-binding fields are normalized out to prevent a confirmation-digest cycle and post-confirmation digest churn:

- `input_manifest.confirmation_ref`
- `input_manifest.confirmation_digest`
- `oracle.owner_value_bindings.confirmation_ref`
- `oracle.owner_value_bindings.confirmation_digest`
- `oracle.permission.confirmation_ref`

The prompt-only digest remains separately available as `task_prompt_manifest_sha256`, using ordered `task_id + NUL + frozen_prompt` records joined with LF. Any stable contract change changes the immutable manifest digest. After owner confirmation, such a change requires a new suite version and a new confirmation.

Dynamic roadmap, process, and board inputs are frozen as immutable repository snapshots under `tests/specs/phase0/snapshots/`. The original live files may continue changing after July 25, 2026 without invalidating this suite. Only snapshot changes or stable contract changes require a new suite version. The strict validator verifies snapshot frontmatter plus the embedded body digest and never re-checks the current live file digest.

## Oracle Contract

Every task names a real embedded oracle ID and digest. Oracles are canonicalized as recursively sorted UTF-8 JSON and hashed with SHA-256. The digest excludes `content_sha256`, `owner_value_bindings.confirmation_ref`, `owner_value_bindings.confirmation_digest`, and `permission.confirmation_ref`; owner tokens and the fixed `binding_target=suite.representativeness_evidence` remain covered. Runtime binding fields are separately required to equal suite evidence, avoiding a cyclic digest while preserving binding integrity.

The 16 repository-only oracles contain explicit expected facts, forbidden facts, required sources, freshness, and permissions. The four owner-value oracles may contain only `<OWNER_VALUE:update_style_label>` and/or `<OWNER_VALUE:timezone>`, bound to the same suite confirmation reference and confirmation digest used by suite evidence and task input. Pending suites keep explicit placeholders and do not execute confirmation-bound runs; after confirmation the runtime binding fields are resolved without changing oracle digests or the suite immutable digest. Raw owner values never enter Git.

## Confirmation Payload V1

The owner reviews all 20 ordered task IDs and frozen prompts once. `owner-confirmation/v1` is canonical UTF-8 JSON with recursively sorted object keys and these exact fields:

- `schema_version`
- `fixture_ref`
- `local_fixture_content_sha256`
- `confirmed_at`
- `retention`
- `scope`
- `storage_class`

The local fixture is exact `owner-values/v1` canonical JSON with keys `schema_version`, `update_style_label`, and `timezone`. `update_style_label` is a frozen enum:

- `current_next_prose`: one compact paragraph only, containing exactly one `Current:` clause followed by exactly one `Next:` clause, with no bullets.
- `current_next_bullets`: exactly two flat bullets only; the first begins `Current:` and the second begins `Next:`, with no extra prose or bullets.

`timezone` must be a valid IANA timezone identifier. Confirmation-time validation resolves it against a local zoneinfo database rooted at `/usr/share/zoneinfo` or `/var/db/timezone/zoneinfo/zoneinfo`, and the resolved target must be a regular file whose first 4 bytes are exactly `TZif`; helper text files such as `zone.tab`, `iso3166.tab`, `tzdata.zi`, and `leapseconds` are invalid. Compatibility or local-machine special entries are also invalid owner timezones: basename or full ID `posixrules`, `localtime`, `Factory`, and any `SystemV/*` identifier must be rejected even if present on the host. Pending preregistration checks only the schema and placeholder protocol. Its content hash input is exactly `ASCII lowercase_hex(random_32_bytes) + NUL + canonical_json_utf8`. The 32-byte nonce, canonical value bytes, raw values, and storage location stay `local_private` or `ephemeral`; none enters Git. Only the salted content hash is included in the repository confirmation payload.

The preregistration placeholder reference is exactly `<OWNER_CONFIRMATION_REF:owner_suite_confirmation_v1>`. After confirmation, the fixture reference becomes an opaque identifier matching `ownerconf_[0-9a-f]{16,64}`. A resolved fixture reference contains no path, URI, backend name, or placeholder.

`scope` must exactly contain suite ID, suite version, the full immutable manifest digest, prompt digest, all 20 ordered task IDs, and approved fields `[update_style_label, timezone]`. `confirmed_at` must be RFC 3339. Retention mode is `until_baseline_complete` or `expires_at`; both require a later RFC 3339 `expires_at` hard deadline. The first mode deletes at baseline completion or the hard deadline, whichever comes first. Storage class is `local_private` or `ephemeral`.

While pending, the four owner tokens and prescribed confirmation placeholders are allowed, but every oracle and suite immutable digest must already be concrete. Pending suites do not execute confirmation-bound tasks because their runtime binding fields are unresolved placeholders. `preregistered` requires resolved evidence metadata and an independently recomputed confirmation digest. Suite evidence, all four task inputs, and all four oracle bindings must carry the same reference and digest.

## Single-Response Freshness Task

The stale-profile task embeds its sanitized `verified_at`, `refresh_days`, and `evaluation_at` values in the frozen prompt. Its one response must declare the field stale and unusable and state that a separate future confirmation is required. The run must not ask the owner now, wait for a second answer, or collect a replacement value.

## Evidence Storage

Raw agent output never enters Git. It may exist only as `local_private` or `ephemeral`. A redacted derivative is a separate artifact with a strict field allowlist. Repository scorecards use the same metadata allowlist:

`suite_id`, `task_id`, `run_id`, `agent`, `timestamps`, `assertion_results`, `error_class`, `correction_cost`, `evidence_refs`.

Pre-confirmation baseline artifacts generated on July 25, 2026 were quarantined under `tests/evidence/phase0/quarantine/preconfirmation-2026-07-25/` and marked `.invalid`. They are historical context only and must not be used for Gate, metrics, or replay claims.

## Baseline Preflight

No Phase 0 baseline scorecard may be generated or accepted until `tests/specs/phase0/p0-baseline-preflight.rb` passes. The preflight fails closed unless the suite is `preregistered`, evidence is `confirmed`, all source digests match the current frozen files, all owner-bound bindings resolve to the same non-placeholder confirmation metadata, and a run manifest is supplied with non-empty unique `run_id` values.

Run from the repository root:

```bash
ruby tests/specs/phase0/p0-baseline-preflight.rb \
  --suite tests/specs/phase0/real-dogfood-tasks-v0.1.yaml \
  --runs tests/evidence/phase0/run-manifests/example-run-manifest.yaml
```

Accepted run-manifest shapes are:

- a top-level YAML array of scorecard-like entries containing `run_id`
- a top-level YAML mapping with `runs: [...]`
- a top-level YAML mapping with `run_ids: [...]`

`--runs` must point to a regular file under `tests/evidence/phase0/run-manifests/`. Paths outside that directory, any `quarantine` path, and any `.invalid` artifact are rejected before suite-state evaluation. This directory may contain only non-sensitive run metadata such as `run_id`; it must not contain raw outputs, owner values, local-private payloads, or L3/private body text.

Current pending suites must reject with `P0_BASELINE_PREFLIGHT_PENDING_CONFIRMATION` and a non-zero exit status after a safe run-manifest path is validated. Confirmed suites still fail closed if `--runs` is omitted.

## Strict Structure Check

Run from the repository root:

```bash
ruby <<'RUBY'
require "yaml"
require "json"
require "digest"
require "pathname"
require "time"

PATH = "tests/specs/phase0/real-dogfood-tasks-v0.1.yaml"
CORE = %w[fact_value provenance freshness permission].freeze
ORIGIN_KINDS = %w[observed_workflow approved_project_need].freeze
CONFIRMATION_TASKS = %w[
  rdt_profile_handoff_update_style
  rdt_profile_handoff_timezone
  rdt_profile_minimal_self_context_pack
  rdt_project_cross_agent_handoff_packet
].freeze
OWNER_TOKENS = %w[<OWNER_VALUE:update_style_label> <OWNER_VALUE:timezone>].freeze
LOW_SENSITIVITY_FIELDS = %w[update_style_label timezone].freeze
RAW_STORAGE_CLASSES = %w[local_private ephemeral].freeze
REDACTED_FIELDS = %w[suite_id task_id run_id agent timestamps assertion_results error_class correction_cost evidence_refs].freeze
CIRCULAR = /oracle marks|oracle independently|criterion as satisfied|reviewer-local oracle/i
RFC3339 = /\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\z/
PENDING_FIXTURE_REF = "<OWNER_CONFIRMATION_REF:owner_suite_confirmation_v1>"
PENDING_CONFIRMATION_DIGEST = "<OWNER_CONFIRMATION_DIGEST:owner_suite_confirmation_v1>"
PENDING_FIXTURE_HASH = "<LOCAL_FIXTURE_CONTENT_SHA256:nonce_plus_canonical_owner_fixture>"
UPDATE_STYLE_LABELS = %w[current_next_prose current_next_bullets].freeze
UPDATE_STYLE_RULES = {
  "current_next_prose" => [
    "One compact paragraph only.",
    "Paragraph contains exactly one `Current:` clause followed by exactly one `Next:` clause.",
    "No bullets are used."
  ],
  "current_next_bullets" => [
    "Exactly two flat bullets only.",
    "The first bullet begins `Current:` and the second bullet begins `Next:`.",
    "No extra prose paragraph or extra bullet is allowed."
  ]
}.freeze
ZONEINFO_ROOTS = ["/usr/share/zoneinfo", "/var/db/timezone/zoneinfo/zoneinfo"].freeze
DENIED_TIMEZONE_IDS = %w[posixrules localtime Factory].freeze

TOP_LEVEL_KEYS = %w[suite confirmation_protocol tasks oracle_schema oracle_manifests].freeze
SUITE_KEYS = %w[id version status feature_id scope classification measurement_scope rubric_ref predecessor_suite fixture_policy snapshot_ref counts source_manifest representativeness_evidence task_prompt_manifest_sha256 evidence_policy immutable_manifest].freeze
SOURCE_KEYS = %w[path content_sha256 as_of dynamic_status].freeze
TASK_KEYS = %w[id categories real_task_origin user_intent required_context_classes forbidden_context_classes sanitized_snapshot_plan expected_outcome assertion_dimensions baseline_run_protocol frozen_prompt input_manifest expected_manifest].freeze
ORACLE_KEYS = %w[id task_id expected_facts forbidden_facts required_source_ids freshness permission content_sha256].freeze
CONFIRMATION_KEYS = %w[fixture_schema_id owner_values_fixture collection covers canonical_payload allowed_storage_classes per_run_rule repo_record post_confirmation_change_rule].freeze
FIXTURE_REF = /\Aownerconf_[0-9a-f]{16,64}\z/
EXPECTED_IMMUTABLE_CANONICALIZATION = "UTF-8 canonical JSON with recursively lexicographically sorted object keys"
EXPECTED_IMMUTABLE_COVERS = %w[stable_suite_contract source_manifest confirmation_protocol oracle_schema ordered_tasks_except_runtime_confirmation_binding oracle_digests].freeze
EXPECTED_ORACLE_FIELDS = %w[id task_id expected_facts forbidden_facts required_source_ids freshness permission content_sha256].freeze
EXPECTED_ORACLE_CANONICALIZATION = "UTF-8 canonical JSON with recursively lexicographically sorted object keys; content_sha256, owner_value_bindings.confirmation_ref, owner_value_bindings.confirmation_digest, and permission.confirmation_ref excluded"
EXPECTED_DYNAMIC_SNAPSHOTS = {
  "src_roadmap" => {
    "snapshot_path" => "tests/specs/phase0/snapshots/src_roadmap.snapshot.md",
    "original_path" => "ROADMAP.md"
  },
  "src_strategy_process" => {
    "snapshot_path" => "tests/specs/phase0/snapshots/src_strategy_process.snapshot.md",
    "original_path" => "docs/prd/goldenwave-strategy/.artifacts/process.md"
  },
  "src_execution_board" => {
    "snapshot_path" => "tests/specs/phase0/snapshots/src_execution_board.snapshot.md",
    "original_path" => "docs/prd/goldenwave-strategy/.artifacts/execution-board.md"
  },
  "src_social_process" => {
    "snapshot_path" => "tests/specs/phase0/snapshots/src_social_process.snapshot.md",
    "original_path" => "docs/prd/social-memory/.artifacts/process.md"
  }
}.freeze
SNAPSHOT_FRONTMATTER_KEYS = %w[snapshot_schema source_id original_path original_content_sha256 observed_at sanitization].freeze
SNAPSHOT_SCHEMA_VERSION = "source-snapshot/v1"
SNAPSHOT_DIR_PREFIX = "tests/specs/phase0/snapshots/"
EXPECTED_OWNER_VALUES_FIXTURE = {
  "schema_version" => "owner-values/v1",
  "canonicalization" => "UTF-8 canonical JSON with recursively lexicographically sorted object keys and no insignificant whitespace",
  "exact_fields" => %w[schema_version update_style_label timezone],
  "field_rules" => {
    "schema_version" => {"type" => "string", "const" => "owner-values/v1"},
    "update_style_label" => {"type" => "string", "enum" => UPDATE_STYLE_LABELS, "reviewer_observable_contracts" => UPDATE_STYLE_RULES},
    "timezone" => {"type" => "string", "format" => "iana_tz_identifier", "whitespace_only" => "forbidden", "confirmation_time_validation" => "Resolve inside system zoneinfo roots /usr/share/zoneinfo or /var/db/timezone/zoneinfo/zoneinfo to a regular file whose first 4 bytes are TZif; reject helper text files such as zone.tab, iso3166.tab, tzdata.zi, and leapseconds; explicitly reject compatibility or local special IDs posixrules, localtime, Factory, and any SystemV/* identifier even if present; preregistration validates descriptor only."}
  },
  "nonce" => {"random_bytes" => 32, "encoding" => "lowercase_hex", "encoded_length" => 64},
  "content_digest" => {"algorithm" => "sha256", "input_bytes" => "ASCII nonce_hex + NUL byte + canonical_json_utf8"},
  "repository_rule" => "Store only local_fixture_content_sha256; raw values, nonce_hex, and storage location are forbidden."
}.freeze

def canonical_json(value)
  case value
  when Hash
    "{" + value.keys.sort.map { |key| JSON.generate(key) + ":" + canonical_json(value.fetch(key)) }.join(",") + "}"
  when Array
    "[" + value.map { |item| canonical_json(item) }.join(",") + "]"
  else
    JSON.generate(value)
  end
end

def exact_keys!(hash, expected, label)
  actual = hash.keys.sort
  wanted = expected.sort
  raise "#{label}: keys=#{actual.inspect}, expected=#{wanted.inspect}" unless actual == wanted
end

def nonempty_string?(value)
  value.is_a?(String) && !value.strip.empty?
end

def valid_fixture_ref?(value)
  value.is_a?(String) && value.match?(FIXTURE_REF)
end

def valid_pending_fixture_ref?(value)
  value == PENDING_FIXTURE_REF
end

def owner_values_descriptor_valid?(value)
  value == EXPECTED_OWNER_VALUES_FIXTURE
end

def zoneinfo_roots
  ZONEINFO_ROOTS.select { |root| File.directory?(root) }
end

def valid_iana_timezone_identifier?(value)
  return false unless nonempty_string?(value)
  return false if value.start_with?("/") || value.include?("\0")
  relative = Pathname.new(value)
  parts = relative.each_filename.to_a
  return false if parts.empty?
  return false if parts.any? { |part| part.empty? || part == "." || part == ".." || !part.match?(/\A[A-Za-z0-9._+-]+\z/) }
  return false if %w[posix right].include?(parts.first)
  return false if DENIED_TIMEZONE_IDS.include?(value)
  return false if parts.first == "SystemV"
  zoneinfo_roots.any? do |root|
    candidate = File.join(root, value)
    next false unless File.exist?(candidate)
    real_root = File.realpath(root)
    begin
      real_candidate = File.realpath(candidate)
    rescue StandardError
      next false
    end
    next false unless real_candidate.start_with?(real_root + File::SEPARATOR)
    next false unless File.file?(real_candidate)
    File.binread(real_candidate, 4) == "TZif"
  end
end

def owner_values_payload_valid?(value)
  return false unless value.is_a?(Hash) && value.keys.sort == %w[schema_version timezone update_style_label]
  value.fetch("schema_version") == "owner-values/v1" && UPDATE_STYLE_LABELS.include?(value.fetch("update_style_label")) && valid_iana_timezone_identifier?(value.fetch("timezone"))
end

def valid_nonce_hex?(value)
  value.is_a?(String) && value.match?(/\A[0-9a-f]{64}\z/)
end

def parse_snapshot_markdown!(path, label)
  text = File.read(path)
  match = text.match(/\A---\n(?<frontmatter>.*?)\n---\n(?<body>.*)\z/m)
  raise "#{label}: snapshot frontmatter missing" unless match
  reject_duplicate_mapping_keys!(Psych.parse_stream(match[:frontmatter]))
  metadata = YAML.safe_load(match[:frontmatter], permitted_classes: [], permitted_symbols: [], aliases: false)
  raise "#{label}: snapshot metadata" unless metadata.is_a?(Hash)
  [metadata, match[:body]]
end

def reject_duplicate_mapping_keys!(node, path = "$")
  case node
  when Psych::Nodes::Mapping
    seen = {}
    node.children.each_slice(2) do |key_node, value_node|
      raise "#{path}: non-scalar mapping key" unless key_node.is_a?(Psych::Nodes::Scalar)
      key = key_node.value
      raise "#{path}: duplicate key #{key}" if seen.key?(key)
      seen[key] = true
      reject_duplicate_mapping_keys!(value_node, "#{path}.#{key}")
    end
  when Psych::Nodes::Sequence, Psych::Nodes::Document, Psych::Nodes::Stream
    node.children.each_with_index { |child, index| reject_duplicate_mapping_keys!(child, "#{path}[#{index}]") }
  end
end

def immutable_payload(data)
  suite = data.fetch("suite")
  stable_suite_keys = %w[id version feature_id scope classification measurement_scope rubric_ref predecessor_suite fixture_policy snapshot_ref counts evidence_policy]
  normalized_tasks = Marshal.load(Marshal.dump(data.fetch("tasks")))
  normalized_tasks.each do |task|
    task.fetch("input_manifest").delete("confirmation_ref")
    task.fetch("input_manifest").delete("confirmation_digest")
  end
  {
    "suite_contract" => stable_suite_keys.each_with_object({}) { |key, result| result[key] = suite.fetch(key) },
    "source_manifest" => suite.fetch("source_manifest"),
    "confirmation_protocol" => data.fetch("confirmation_protocol"),
    "oracle_schema" => data.fetch("oracle_schema"),
    "ordered_tasks" => normalized_tasks,
    "oracle_digests" => data.fetch("oracle_manifests").keys.sort.each_with_object({}) do |oracle_id, result|
      result[oracle_id] = data.fetch("oracle_manifests").fetch(oracle_id).fetch("content_sha256")
    end
  }
end

def oracle_digest_payload(oracle)
  payload = Marshal.load(Marshal.dump(oracle))
  payload.delete("content_sha256")
  if payload.key?("owner_value_bindings")
    payload.fetch("owner_value_bindings").delete("confirmation_ref")
    payload.fetch("owner_value_bindings").delete("confirmation_digest")
  end
  payload.fetch("permission").delete("confirmation_ref")
  payload
end

yaml_text = File.read(PATH)
reject_duplicate_mapping_keys!(Psych.parse_stream(yaml_text))
data = YAML.safe_load(yaml_text, permitted_classes: [], permitted_symbols: [], aliases: false)
exact_keys!(data, TOP_LEVEL_KEYS, "top-level")

suite = data.fetch("suite")
exact_keys!(suite, SUITE_KEYS, "suite")
status = suite.fetch("status")
raise "suite status" unless %w[pending_representativeness_confirmation preregistered].include?(status)
raise "suite id" unless suite.fetch("id") == "phase0-real-dogfood-preregistration"
raise "suite version" unless suite.fetch("version") == "v0.1"
raise "suite classification" unless suite.fetch("classification") == "real-dogfood-preregistration"

root = File.realpath(".")
sources = suite.fetch("source_manifest")
sources.each do |source_id, source|
  exact_keys!(source, SOURCE_KEYS, "#{source_id}: source")
  path = source.fetch("path")
  expected_dynamic = EXPECTED_DYNAMIC_SNAPSHOTS[source_id]
  relative = Pathname.new(path)
  raise "#{source_id}: absolute path" if relative.absolute?
  raise "#{source_id}: unclean path" unless relative.cleanpath.to_s == path && !relative.each_filename.to_a.include?("..")
  if source.fetch("dynamic_status")
    raise "#{source_id}: expected dynamic snapshot mapping" unless expected_dynamic
    raise "#{source_id}: snapshot path" unless path == expected_dynamic.fetch("snapshot_path")
    raise "#{source_id}: snapshot directory" unless path.start_with?(SNAPSHOT_DIR_PREFIX)
  else
    raise "#{source_id}: unexpected snapshot mapping" if expected_dynamic
  end
  current = Pathname.new(root)
  relative.each_filename do |part|
    current = current.join(part)
    raise "#{source_id}: symlink component #{current}" if File.symlink?(current.to_s)
  end
  raise "#{source_id}: not a file" unless File.file?(current.to_s)
  real = File.realpath(current.to_s)
  raise "#{source_id}: path escape" unless real.start_with?(root + File::SEPARATOR)
  raise "#{source_id}: digest mismatch" unless Digest::SHA256.file(real).hexdigest == source.fetch("content_sha256")
  raise "#{source_id}: digest format" unless source.fetch("content_sha256").match?(/\A[0-9a-f]{64}\z/)
  raise "#{source_id}: as_of" unless source.fetch("as_of").match?(/\A\d{4}-\d{2}-\d{2}\z/)
  raise "#{source_id}: dynamic_status" unless [true, false].include?(source.fetch("dynamic_status"))
  next unless source.fetch("dynamic_status")

  raise "#{source_id}: snapshot symlink" if File.symlink?(real)
  metadata, body = parse_snapshot_markdown!(real, source_id)
  exact_keys!(metadata, SNAPSHOT_FRONTMATTER_KEYS, "#{source_id}: snapshot frontmatter")
  raise "#{source_id}: snapshot schema" unless metadata.fetch("snapshot_schema") == SNAPSHOT_SCHEMA_VERSION
  raise "#{source_id}: snapshot source_id" unless metadata.fetch("source_id") == source_id
  raise "#{source_id}: snapshot original_path" unless metadata.fetch("original_path") == expected_dynamic.fetch("original_path")
  raise "#{source_id}: snapshot original digest format" unless metadata.fetch("original_content_sha256").match?(/\A[0-9a-f]{64}\z/)
  raise "#{source_id}: snapshot observed_at" unless metadata.fetch("observed_at") == source.fetch("as_of")
  raise "#{source_id}: snapshot sanitization" unless nonempty_string?(metadata.fetch("sanitization"))
  raise "#{source_id}: snapshot body digest" unless Digest::SHA256.hexdigest(body) == metadata.fetch("original_content_sha256")
end

tasks = data.fetch("tasks")
raise "task count" unless tasks.length == 20
ids = tasks.map { |task| task.fetch("id") }
raise "duplicate task IDs" unless ids.uniq.length == 20
prompt_bytes = tasks.map { |task| "#{task.fetch("id")}\0#{task.fetch("frozen_prompt")}" }.join("\n")
prompt_digest = Digest::SHA256.hexdigest(prompt_bytes)
raise "prompt digest" unless suite.fetch("task_prompt_manifest_sha256") == prompt_digest

immutable = suite.fetch("immutable_manifest")
exact_keys!(immutable, %w[schema_version canonicalization covers content_sha256], "immutable manifest")
raise "immutable version" unless immutable.fetch("schema_version") == "suite-immutable-manifest/v1"
raise "immutable canonicalization" unless immutable.fetch("canonicalization") == EXPECTED_IMMUTABLE_CANONICALIZATION
raise "immutable covers" unless immutable.fetch("covers") == EXPECTED_IMMUTABLE_COVERS
immutable_digest = Digest::SHA256.hexdigest(canonical_json(immutable_payload(data)))
raise "immutable digest" unless immutable.fetch("content_sha256") == immutable_digest

evidence = suite.fetch("representativeness_evidence")
exact_keys!(evidence, %w[status confirmation_ref confirmation_digest local_fixture_content_sha256 confirmed_at retention storage_class confirmation_scope task_ids], "suite evidence")
raise "representativeness table" unless evidence.fetch("task_ids") == ids
retention = evidence.fetch("retention")
exact_keys!(retention, %w[mode expires_at], "retention")
scope = evidence.fetch("confirmation_scope")
exact_keys!(scope, %w[suite_id suite_version suite_immutable_manifest_sha256 task_prompt_manifest_sha256 ordered_task_ids approved_low_sensitivity_fields], "confirmation scope")
raise "scope suite" unless scope.fetch("suite_id") == suite.fetch("id") && scope.fetch("suite_version") == suite.fetch("version")
raise "scope IDs" unless scope.fetch("ordered_task_ids") == ids
raise "scope prompt digest" unless scope.fetch("task_prompt_manifest_sha256") == prompt_digest
raise "scope immutable digest" unless scope.fetch("suite_immutable_manifest_sha256") == immutable_digest
raise "scope fields" unless scope.fetch("approved_low_sensitivity_fields") == LOW_SENSITIVITY_FIELDS

confirmation = data.fetch("confirmation_protocol")
exact_keys!(confirmation, CONFIRMATION_KEYS, "confirmation protocol")
raise "fixture schema ID" unless confirmation.fetch("fixture_schema_id") == "owner-values/v1"
raise "owner values fixture schema" unless owner_values_descriptor_valid?(confirmation.fetch("owner_values_fixture"))
raise "confirmation once" unless confirmation.fetch("collection") == "suite_level_once"
expected_covers = ["representativeness_of_all_20_tasks"] + LOW_SENSITIVITY_FIELDS.map { |field| "owner_value.#{field}" }
raise "confirmation covers" unless confirmation.fetch("covers") == expected_covers
raise "confirmation storage" unless confirmation.fetch("allowed_storage_classes") == RAW_STORAGE_CLASSES
payload_schema = confirmation.fetch("canonical_payload")
exact_keys!(payload_schema, %w[schema_version canonicalization required_fields retention_modes retention_rule fixture_ref_format local_fixture_content_hash_rule confirmation_digest_rule storage_reference_rule], "confirmation payload schema")
raise "confirmation payload version" unless payload_schema.fetch("schema_version") == "owner-confirmation/v1"
raise "confirmation canonicalization" unless payload_schema.fetch("canonicalization") == EXPECTED_IMMUTABLE_CANONICALIZATION
raise "confirmation payload fields" unless payload_schema.fetch("required_fields") == %w[schema_version fixture_ref local_fixture_content_sha256 confirmed_at retention scope storage_class]
raise "retention modes" unless payload_schema.fetch("retention_modes") == %w[until_baseline_complete expires_at]
raise "fixture ref format" unless payload_schema.fetch("fixture_ref_format") == "ownerconf_[0-9a-f]{16,64}"
raise "fixture hash rule" unless payload_schema.fetch("local_fixture_content_hash_rule") == "SHA-256 over exactly 32 random bytes encoded as lowercase hex64 ASCII, then one NUL byte, then owner-values/v1 canonical JSON UTF-8 bytes."
raise "confirmation digest rule" unless payload_schema.fetch("confirmation_digest_rule") == "SHA-256 of the canonical payload containing metadata plus local_fixture_content_sha256; raw owner values and nonce are excluded."
raise "retention rule" unless payload_schema.fetch("retention_rule") == "Both modes require expires_at later than confirmed_at; until_baseline_complete deletes at baseline completion or the hard expiry, whichever comes first."
raise "storage reference rule" unless payload_schema.fetch("storage_reference_rule") == "Resolved fixture_ref is opaque and must not contain a path, URI, storage backend, or placeholder; pending preregistration uses the explicit placeholder <OWNER_CONFIRMATION_REF:owner_suite_confirmation_v1>."
raise "per-run rule" unless confirmation.fetch("per_run_rule") == "Pending suites do not execute confirmation-bound tasks. After confirmation, runs consume the frozen reference and confirmation digest only; they never ask the owner to repeat values."
raise "post-confirmation rule" unless confirmation.fetch("post_confirmation_change_rule") == "Any immutable suite manifest change after confirmation requires a new suite version and a new owner confirmation over the new manifest digest."
repo_record = confirmation.fetch("repo_record")
exact_keys!(repo_record, %w[allowed raw_owner_values local_fixture_nonce], "confirmation repo record")
expected_repo_fields = %w[schema_version fixture_ref confirmation_digest local_fixture_content_sha256 confirmed_at retention scope storage_class]
raise "confirmation repo allowlist" unless repo_record.fetch("allowed") == expected_repo_fields
raise "confirmation raw values" unless repo_record.fetch("raw_owner_values") == "forbidden" && repo_record.fetch("local_fixture_nonce") == "forbidden"

if status == "pending_representativeness_confirmation"
  raise "pending evidence" unless evidence.fetch("status") == "pending"
  raise "pending ref" unless valid_pending_fixture_ref?(evidence.fetch("confirmation_ref"))
  raise "pending digest" unless evidence.fetch("confirmation_digest") == PENDING_CONFIRMATION_DIGEST
  raise "pending fixture hash" unless evidence.fetch("local_fixture_content_sha256") == PENDING_FIXTURE_HASH
  raise "pending confirmed_at" unless evidence.fetch("confirmed_at") == "<CONFIRMED_AT:RFC3339>"
  raise "pending retention" unless retention == {"mode" => "<RETENTION_MODE:until_baseline_complete_or_expires_at>", "expires_at" => "<RETENTION_EXPIRES_AT:RFC3339_OR_NULL>"}
  raise "pending storage" unless evidence.fetch("storage_class") == "<STORAGE_CLASS:local_private_or_ephemeral>"
else
  raise "confirmed evidence" unless evidence.fetch("status") == "confirmed"
  raise "confirmation ref format" unless valid_fixture_ref?(evidence.fetch("confirmation_ref"))
  raise "confirmation digest format" unless evidence.fetch("confirmation_digest").match?(/\A[0-9a-f]{64}\z/)
  raise "fixture hash format" unless evidence.fetch("local_fixture_content_sha256").match?(/\A[0-9a-f]{64}\z/)
  raise "confirmed_at format" unless evidence.fetch("confirmed_at").match?(RFC3339)
  confirmed_at = Time.iso8601(evidence.fetch("confirmed_at"))
  mode = retention.fetch("mode")
  raise "retention mode" unless %w[until_baseline_complete expires_at].include?(mode)
  raise "retention expires_at format" unless retention.fetch("expires_at").match?(RFC3339)
  expires_at = Time.iso8601(retention.fetch("expires_at"))
  raise "retention expiry" unless expires_at > confirmed_at
  raise "confirmed storage" unless RAW_STORAGE_CLASSES.include?(evidence.fetch("storage_class"))
  payload = {
    "schema_version" => "owner-confirmation/v1",
    "fixture_ref" => evidence.fetch("confirmation_ref"),
    "local_fixture_content_sha256" => evidence.fetch("local_fixture_content_sha256"),
    "confirmed_at" => evidence.fetch("confirmed_at"),
    "retention" => retention,
    "scope" => scope,
    "storage_class" => evidence.fetch("storage_class")
  }
  raise "confirmation digest mismatch" unless Digest::SHA256.hexdigest(canonical_json(payload)) == evidence.fetch("confirmation_digest")
end

evidence_policy = suite.fetch("evidence_policy")
exact_keys!(evidence_policy, %w[raw_output redacted_derivative repo_scorecard], "evidence policy")
raw_policy = evidence_policy.fetch("raw_output")
exact_keys!(raw_policy, %w[allowed_storage_classes repo_storage], "raw policy")
raise "raw policy" unless raw_policy.fetch("allowed_storage_classes") == RAW_STORAGE_CLASSES && raw_policy.fetch("repo_storage") == "forbidden"
redacted_policy = evidence_policy.fetch("redacted_derivative")
exact_keys!(redacted_policy, %w[artifact_kind independent_artifact repo_storage field_allowlist], "redacted policy")
raise "redacted policy" unless redacted_policy.fetch("artifact_kind") == "redacted_evidence" && redacted_policy.fetch("independent_artifact") == true && redacted_policy.fetch("repo_storage") == "allowed" && redacted_policy.fetch("field_allowlist") == REDACTED_FIELDS
scorecard_policy = evidence_policy.fetch("repo_scorecard")
exact_keys!(scorecard_policy, %w[artifact_kind field_allowlist], "scorecard policy")
raise "scorecard allowlist" unless scorecard_policy.fetch("artifact_kind") == "scorecard_metadata" && scorecard_policy.fetch("field_allowlist") == REDACTED_FIELDS

oracle_schema = data.fetch("oracle_schema")
exact_keys!(oracle_schema, %w[version digest_algorithm canonicalization required_fields digest_excluded_fields], "oracle schema")
raise "oracle schema version" unless oracle_schema.fetch("version") == "oracle-manifest/v1"
raise "oracle digest algorithm" unless oracle_schema.fetch("digest_algorithm") == "sha256"
raise "oracle canonicalization" unless oracle_schema.fetch("canonicalization") == EXPECTED_ORACLE_CANONICALIZATION
raise "oracle required fields" unless oracle_schema.fetch("required_fields") == EXPECTED_ORACLE_FIELDS
raise "oracle digest exclusions" unless oracle_schema.fetch("digest_excluded_fields") == ["content_sha256", "owner_value_bindings.confirmation_ref", "owner_value_bindings.confirmation_digest", "permission.confirmation_ref"]
oracles = data.fetch("oracle_manifests")
raise "oracle count" unless oracles.length == 20
oracles.each do |oracle_id, oracle|
  expected_keys = ORACLE_KEYS + (oracle.key?("owner_value_bindings") ? ["owner_value_bindings"] : [])
  exact_keys!(oracle, expected_keys, "#{oracle_id}: oracle")
  raise "#{oracle_id}: key/id" unless oracle.fetch("id") == oracle_id
  actual = Digest::SHA256.hexdigest(canonical_json(oracle_digest_payload(oracle)))
  raise "#{oracle_id}: digest" unless actual == oracle.fetch("content_sha256")
  raise "#{oracle_id}: digest format" unless oracle.fetch("content_sha256").match?(/\A[0-9a-f]{64}\z/)
  raise "#{oracle_id}: facts" unless [oracle.fetch("expected_facts"), oracle.fetch("forbidden_facts")].all? { |facts| !facts.empty? && facts.all? { |fact| nonempty_string?(fact) } }
  raise "#{oracle_id}: sources" unless oracle.fetch("required_source_ids").all? { |source_id| sources.key?(source_id) }
  freshness = oracle.fetch("freshness")
  exact_keys!(freshness, %w[as_of dynamic_source_ids digest_mismatch_result], "#{oracle_id}: freshness")
  raise "#{oracle_id}: freshness values" unless freshness.fetch("as_of") == "2026-07-25" && freshness.fetch("digest_mismatch_result") == "invalid_suite_version"
  raise "#{oracle_id}: dynamic sources" unless freshness.fetch("dynamic_source_ids").all? { |source_id| oracle.fetch("required_source_ids").include?(source_id) && sources.fetch(source_id).fetch("dynamic_status") }
  permission = oracle.fetch("permission")
  exact_keys!(permission, %w[allowed_source_ids confirmation_ref forbidden_context_classes owner_reprompt], "#{oracle_id}: permission")
  raise "#{oracle_id}: owner reprompt" unless permission.fetch("owner_reprompt") == "forbidden"
  raise "#{oracle_id}: forbidden classes" unless permission.fetch("forbidden_context_classes").all? { |value| nonempty_string?(value) }
  raise "#{oracle_id}: source permission" unless oracle.dig("permission", "allowed_source_ids") == oracle.fetch("required_source_ids")
end

coverage = Hash.new(0)
assertion_count = 0
confirmation_count = 0
tasks.each do |task|
  id = task.fetch("id")
  exact_keys!(task, TASK_KEYS, "#{id}: task")
  raise "#{id}: frozen prompt" unless nonempty_string?(task.fetch("frozen_prompt"))
  raise "#{id}: user intent" unless nonempty_string?(task.fetch("user_intent"))
  raise "#{id}: required context" unless !task.fetch("required_context_classes").empty? && task.fetch("required_context_classes").all? { |value| nonempty_string?(value) }
  raise "#{id}: forbidden context" unless !task.fetch("forbidden_context_classes").empty? && task.fetch("forbidden_context_classes").all? { |value| nonempty_string?(value) }
  categories = task.fetch("categories")
  raise "#{id}: categories" unless !categories.empty? && categories.uniq.length == categories.length && categories.all? { |category| %w[Profile Knowledge Project].include?(category) }
  categories.each { |category| coverage[category] += 1 }
  origin = task.fetch("real_task_origin")
  exact_keys!(origin, %w[workflow_type project_docs evidence_kind], "#{id}: origin")
  raise "#{id}: origin values" unless nonempty_string?(origin.fetch("workflow_type")) && ORIGIN_KINDS.include?(origin.fetch("evidence_kind")) && !origin.fetch("project_docs").empty? && origin.fetch("project_docs").all? { |value| nonempty_string?(value) }
  snapshot = task.fetch("sanitized_snapshot_plan")
  exact_keys!(snapshot, %w[extraction_rule], "#{id}: snapshot plan")
  raise "#{id}: extraction rule" unless nonempty_string?(snapshot.fetch("extraction_rule"))
  input = task.fetch("input_manifest")
  exact_keys!(input, %w[source_ids confirmation_ref confirmation_digest], "#{id}: input")
  raise "#{id}: input sources" unless !input.fetch("source_ids").empty? && input.fetch("source_ids").uniq.length == input.fetch("source_ids").length && input.fetch("source_ids").all? { |source_id| sources.key?(source_id) }
  expected = task.fetch("expected_manifest")
  exact_keys!(expected, %w[oracle_id oracle_sha256], "#{id}: expected")
  raise "#{id}: expected digest format" unless expected.fetch("oracle_sha256").match?(/\A[0-9a-f]{64}\z/)
  outcome = task.fetch("expected_outcome")
  if CONFIRMATION_TASKS.include?(id)
    exact_keys!(outcome, %w[once_confirmed confirmation_ref_required if_confirmation_ref_missing], "#{id}: expected outcome")
    exact_keys!(outcome.fetch("once_confirmed"), %w[expected_behavior], "#{id}: once confirmed")
    raise "#{id}: confirmation outcome" unless outcome.fetch("confirmation_ref_required") == true && nonempty_string?(outcome.fetch("if_confirmation_ref_missing")) && nonempty_string?(outcome.dig("once_confirmed", "expected_behavior"))
  else
    exact_keys!(outcome, %w[reference_expected confirmation_ref_required], "#{id}: expected outcome")
    exact_keys!(outcome.fetch("reference_expected"), %w[expected_behavior expected_refs], "#{id}: reference expected")
    raise "#{id}: reference outcome" unless outcome.fetch("confirmation_ref_required") == false && nonempty_string?(outcome.dig("reference_expected", "expected_behavior")) && !outcome.dig("reference_expected", "expected_refs").empty? && outcome.dig("reference_expected", "expected_refs").all? { |value| nonempty_string?(value) }
  end
  oracle = oracles.fetch(expected.fetch("oracle_id"))
  raise "#{id}: oracle task" unless oracle.fetch("task_id") == id
  raise "#{id}: oracle ref" unless oracle.fetch("content_sha256") == expected.fetch("oracle_sha256")
  raise "#{id}: oracle sources" unless oracle.fetch("required_source_ids") == input.fetch("source_ids")

  serialized_oracle = canonical_json(oracle)
  owner_tokens = OWNER_TOKENS.select { |token| serialized_oracle.include?(token) }
  if CONFIRMATION_TASKS.include?(id)
    confirmation_count += 1
    binding = oracle.fetch("owner_value_bindings")
    exact_keys!(binding, %w[tokens confirmation_ref confirmation_digest binding_target], "#{id}: owner binding")
    raise "#{id}: binding target" unless binding.fetch("binding_target") == "suite.representativeness_evidence"
    raise "#{id}: owner tokens" unless binding.fetch("tokens").sort == owner_tokens.sort && !owner_tokens.empty?
    raise "#{id}: ref mismatch" unless input.fetch("confirmation_ref") == evidence.fetch("confirmation_ref") && binding.fetch("confirmation_ref") == evidence.fetch("confirmation_ref")
    raise "#{id}: digest mismatch" unless input.fetch("confirmation_digest") == evidence.fetch("confirmation_digest") && binding.fetch("confirmation_digest") == evidence.fetch("confirmation_digest")
    raise "#{id}: permission ref" unless oracle.dig("permission", "confirmation_ref") == evidence.fetch("confirmation_ref")
    if status == "pending_representativeness_confirmation"
      raise "#{id}: pending confirmation ref" unless valid_pending_fixture_ref?(input.fetch("confirmation_ref"))
      raise "#{id}: pending confirmation digest" unless input.fetch("confirmation_digest") == PENDING_CONFIRMATION_DIGEST
    else
      raise "#{id}: fixture ref format" unless valid_fixture_ref?(input.fetch("confirmation_ref"))
      raise "#{id}: confirmation digest format" unless input.fetch("confirmation_digest").match?(/\A[0-9a-f]{64}\z/)
    end
  else
    raise "#{id}: owner token" unless owner_tokens.empty?
    raise "#{id}: owner binding" if oracle.key?("owner_value_bindings")
    raise "#{id}: confirmation" unless input.fetch("confirmation_ref").nil? && input.fetch("confirmation_digest").nil?
    raise "#{id}: permission confirmation" unless oracle.dig("permission", "confirmation_ref").nil?
  end

  assertions = task.fetch("assertion_dimensions")
  raise "#{id}: assertion count" unless assertions.length == 6
  assertion_count += assertions.length
  assertions.each do |assertion|
    exact_keys!(assertion, %w[dimension must must_not], "#{id}: assertion")
    raise "#{id}: assertion empty" unless assertion.values.all? { |value| value.is_a?(String) && !value.empty? }
    raise "#{id}: circular assertion" if assertion.fetch("must").match?(CIRCULAR) || assertion.fetch("must_not").match?(CIRCULAR)
  end
  dimensions = assertions.map { |assertion| assertion.fetch("dimension") }
  raise "#{id}: dimensions" unless dimensions.uniq.length == 6 && (CORE - dimensions).empty?

  baseline = task.fetch("baseline_run_protocol")
  exact_keys!(baseline, %w[mode run_order evidence_capture], "#{id}: baseline")
  raise "#{id}: baseline values" unless baseline.fetch("mode") == "phase0-human-proxy" && nonempty_string?(baseline.fetch("run_order"))
  capture = baseline.fetch("evidence_capture")
  exact_keys!(capture, %w[raw_output redacted_derivative repo_artifact scorecard_fields], "#{id}: evidence capture")
  raise "#{id}: raw capture" unless capture.fetch("raw_output") == raw_policy
  raise "#{id}: redacted capture" unless capture.fetch("redacted_derivative") == redacted_policy
  raise "#{id}: repo artifact" unless capture.fetch("repo_artifact") == "scorecard_metadata_only"
  raise "#{id}: scorecard fields" unless capture.fetch("scorecard_fields") == REDACTED_FIELDS
end

stale = tasks.find { |task| task.fetch("id") == "rdt_profile_contact_window_stale_reconfirm" }
raise "stale prompt reprompt" unless stale.fetch("frozen_prompt").include?("不要向 owner 追问")
raise "stale run order" unless stale.dig("baseline_run_protocol", "run_order").include?("no owner follow-up or second answer")
raise "stale permission" unless oracles.fetch(stale.dig("expected_manifest", "oracle_id")).dig("permission", "owner_reprompt") == "forbidden"

counts = suite.fetch("counts")
exact_keys!(counts, %w[tasks category_coverage confirmation_ref_tasks], "suite counts")
raise "counts tasks" unless counts.fetch("tasks") == tasks.length
raise "counts confirmation" unless counts.fetch("confirmation_ref_tasks") == confirmation_count && confirmation_count == 4
raise "counts coverage" unless counts.fetch("category_coverage") == coverage
raise "assertions" unless assertion_count == 120
raise "coverage" unless coverage == {"Profile" => 8, "Project" => 13, "Knowledge" => 12}

negative_checks = {
  empty_prompt_rejected: !nonempty_string?("   "),
  bad_fixture_ref_rejected: !valid_fixture_ref?("../private/owner-values.yaml") && !valid_fixture_ref?(PENDING_FIXTURE_REF),
  changed_owner_schema_rejected: begin
    changed = Marshal.load(Marshal.dump(EXPECTED_OWNER_VALUES_FIXTURE))
    changed["schema_version"] = "owner-values/v2"
    !owner_values_descriptor_valid?(changed)
  end,
  unknown_style_label_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "freeform_status", "timezone" => "UTC"}),
  bad_timezone_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "../../etc/passwd"}),
  zone_tab_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "zone.tab"}),
  iso3166_tab_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "iso3166.tab"}),
  tzdata_zi_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "tzdata.zi"}),
  posixrules_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "posixrules"}),
  localtime_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "localtime"}),
  factory_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "Factory"}),
  systemv_rejected: !owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "SystemV/EST5"}),
  bad_nonce_rejected: !valid_nonce_hex?("ABC123")
}
raise "negative checks #{negative_checks.inspect}" unless negative_checks.values.all?

positive_checks = {
  utc_timezone_accepted: owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_prose", "timezone" => "UTC"}),
  asia_shanghai_timezone_accepted: owner_values_payload_valid?({"schema_version" => "owner-values/v1", "update_style_label" => "current_next_bullets", "timezone" => "Asia/Shanghai"})
}
raise "positive checks #{positive_checks.inspect}" unless positive_checks.values.all?

puts({yaml_parse: "safe-no-duplicates", tasks: tasks.length, oracles: oracles.length, assertions: assertion_count, prompt_digest: prompt_digest, immutable_digest: immutable_digest, negative_checks: negative_checks, positive_checks: positive_checks, coverage: coverage}.inspect)
RUBY
```

This specification does not implement a runner, authorize private-body reads, or permit Phase 0 to claim Phase 2 cross-agent success.
