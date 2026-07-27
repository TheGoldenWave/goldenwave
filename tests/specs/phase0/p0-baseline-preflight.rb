#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "json"
require "optparse"
require "open3"
require "pathname"
require "psych"
require "time"
require "yaml"

SUITE_DEFAULT = "tests/specs/phase0/real-dogfood-tasks-v0.1.yaml"
README_PATH = "tests/specs/phase0/real-dogfood-README.md"
RUN_MANIFEST_DIR = "tests/evidence/phase0/run-manifests/".freeze
PENDING_FIXTURE_REF = "<OWNER_CONFIRMATION_REF:owner_suite_confirmation_v1>"
PENDING_CONFIRMATION_DIGEST = "<OWNER_CONFIRMATION_DIGEST:owner_suite_confirmation_v1>"
PENDING_FIXTURE_HASH = "<LOCAL_FIXTURE_CONTENT_SHA256:nonce_plus_canonical_owner_fixture>"
CONFIRMATION_TASKS = %w[
  rdt_profile_handoff_update_style
  rdt_profile_handoff_timezone
  rdt_profile_minimal_self_context_pack
  rdt_project_cross_agent_handoff_packet
].freeze
FIXTURE_REF = /\Aownerconf_[0-9a-f]{16,64}\z/
SHA256_HEX = /\A[0-9a-f]{64}\z/
RFC3339 = /\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\z/
RAW_STORAGE_CLASSES = %w[local_private ephemeral].freeze
RETENTION_MODES = %w[until_baseline_complete expires_at].freeze
TOP_LEVEL_KEYS = %w[suite confirmation_protocol tasks oracle_schema oracle_manifests].freeze

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

def fail_closed!(code, detail)
  warn("#{code}: #{detail}")
  exit(1)
end

def exact_keys!(hash, expected, label)
  actual = hash.keys.sort
  wanted = expected.sort
  raise "#{label}: keys=#{actual.inspect}, expected=#{wanted.inspect}" unless actual == wanted
end

def nonempty_string?(value)
  value.is_a?(String) && !value.strip.empty?
end

def parse_yaml_file!(path)
  text = File.read(path)
  reject_duplicate_mapping_keys!(Psych.parse_stream(text))
  YAML.safe_load(text, permitted_classes: [], permitted_symbols: [], aliases: false)
end

def resolve_repo_relative_path!(root, path, label)
  relative = Pathname.new(path)
  raise "#{label}: absolute path" if relative.absolute?
  raise "#{label}: unclean path" unless relative.cleanpath.to_s == path && !relative.each_filename.to_a.include?("..")

  current = Pathname.new(root)
  relative.each_filename do |part|
    current = current.join(part)
    raise "#{label}: symlink component #{current}" if File.symlink?(current.to_s)
  end
  raise "#{label}: missing file" unless File.exist?(current.to_s)

  real = File.realpath(current.to_s)
  raise "#{label}: path escape" unless real.start_with?(root + File::SEPARATOR)

  real
end

def resolve_repo_regular_file!(root, path, label)
  real = resolve_repo_relative_path!(root, path, label)
  raise "#{label}: not a regular file" unless File.file?(real)

  real
end

def validate_run_manifest_path!(root, path)
  relative = Pathname.new(path)
  raise "run manifest: absolute path" if relative.absolute?
  raise "run manifest: unclean path" unless relative.cleanpath.to_s == path && !relative.each_filename.to_a.include?("..")

  parts = relative.each_filename.to_a
  raise "run manifest: quarantine path forbidden" if parts.include?("quarantine")
  raise "run manifest: .invalid forbidden" if path.end_with?(".invalid")
  raise "run manifest: outside allowed directory" unless path.start_with?(RUN_MANIFEST_DIR)

  real = resolve_repo_regular_file!(root, path, "run manifest")
  allowed_real = File.realpath(File.join(root, RUN_MANIFEST_DIR))
  raise "run manifest: outside allowed directory" unless real.start_with?(allowed_real + File::SEPARATOR)

  real
end

def shared_strict_ruby!(root, suite_path)
  readme_real = resolve_repo_regular_file!(root, README_PATH, "readme")
  readme_text = File.read(readme_real)
  fenced = readme_text.match(/```bash\n(?<bash>ruby <<'RUBY'\n.*?\nRUBY)\n```/m)
  raise "shared strict validator block missing" unless fenced

  ruby_block = fenced[:bash]
  ruby_source = ruby_block.match(/\Aruby <<'RUBY'\n(?<ruby>.*)\nRUBY\z/m)
  raise "shared strict validator ruby block missing" unless ruby_source

  path_assignments = ruby_source[:ruby].scan(/^PATH = ".*"$/)
  raise "shared strict validator PATH assignment count" unless path_assignments.length == 1

  ruby_source[:ruby].sub(/^PATH = ".*"$/, %(PATH = #{suite_path.dump}))
end

def run_shared_strict_validator!(root, suite_path)
  suite_real = resolve_repo_regular_file!(root, suite_path, "suite")
  ruby_source = shared_strict_ruby!(root, suite_path)
  stdout, stderr, status = Open3.capture3("ruby", stdin_data: ruby_source)
  return if status.success?

  detail = [suite_real, stdout, stderr].reject(&:empty?).join("\n")
  raise "shared strict validator failed\n#{detail}"
end

def parse_runs_file!(path)
  data = parse_yaml_file!(path)
  runs =
    case data
    when Array
      data
    when Hash
      if data.key?("runs")
        data.fetch("runs")
      elsif data.key?("run_ids")
        data.fetch("run_ids")
      else
        raise "#{path}: expected top-level array, runs, or run_ids"
      end
    else
      raise "#{path}: unsupported run manifest root #{data.class}"
    end

  raise "#{path}: empty run manifest" unless runs.is_a?(Array) && !runs.empty?

  run_ids = runs.map do |entry|
    case entry
    when Hash
      entry.fetch("run_id")
    when String
      entry
    else
      raise "#{path}: unsupported run entry #{entry.class}"
    end
  end
  raise "#{path}: blank run_id" unless run_ids.all? { |value| nonempty_string?(value) }
  raise "#{path}: duplicate run_id" unless run_ids.uniq.length == run_ids.length

  run_ids
end

def validate_source_file!(root, source_id, source)
  path = source.fetch("path")
  relative = Pathname.new(path)
  raise "#{source_id}: absolute path" if relative.absolute?
  raise "#{source_id}: unclean path" unless relative.cleanpath.to_s == path && !relative.each_filename.to_a.include?("..")

  current = Pathname.new(root)
  relative.each_filename do |part|
    current = current.join(part)
    raise "#{source_id}: symlink component #{current}" if File.symlink?(current.to_s)
  end
  raise "#{source_id}: not a file" unless File.file?(current.to_s)

  real = File.realpath(current.to_s)
  raise "#{source_id}: path escape" unless real.start_with?(root + File::SEPARATOR)
  raise "#{source_id}: digest format" unless source.fetch("content_sha256").match?(SHA256_HEX)
  raise "#{source_id}: digest mismatch" unless Digest::SHA256.file(real).hexdigest == source.fetch("content_sha256")
end

def validate_confirmation_state!(suite)
  raise "suite status" unless suite.fetch("status") == "preregistered"

  evidence = suite.fetch("representativeness_evidence")
  raise "evidence status" unless evidence.fetch("status") == "confirmed"
  raise "placeholder confirmation_ref" if evidence.fetch("confirmation_ref") == PENDING_FIXTURE_REF
  raise "placeholder confirmation_digest" if evidence.fetch("confirmation_digest") == PENDING_CONFIRMATION_DIGEST
  raise "placeholder fixture hash" if evidence.fetch("local_fixture_content_sha256") == PENDING_FIXTURE_HASH
  raise "confirmation_ref format" unless evidence.fetch("confirmation_ref").match?(FIXTURE_REF)
  raise "confirmation_digest format" unless evidence.fetch("confirmation_digest").match?(SHA256_HEX)
  raise "fixture hash format" unless evidence.fetch("local_fixture_content_sha256").match?(SHA256_HEX)
  raise "confirmed_at format" unless evidence.fetch("confirmed_at").match?(RFC3339)

  confirmed_at = Time.iso8601(evidence.fetch("confirmed_at"))
  retention = evidence.fetch("retention")
  raise "retention mode" unless RETENTION_MODES.include?(retention.fetch("mode"))
  raise "retention expires_at format" unless retention.fetch("expires_at").match?(RFC3339)
  expires_at = Time.iso8601(retention.fetch("expires_at"))
  raise "retention expiry" unless expires_at > confirmed_at
  raise "storage class" unless RAW_STORAGE_CLASSES.include?(evidence.fetch("storage_class"))

  payload = {
    "schema_version" => "owner-confirmation/v1",
    "fixture_ref" => evidence.fetch("confirmation_ref"),
    "local_fixture_content_sha256" => evidence.fetch("local_fixture_content_sha256"),
    "confirmed_at" => evidence.fetch("confirmed_at"),
    "retention" => retention,
    "scope" => evidence.fetch("confirmation_scope"),
    "storage_class" => evidence.fetch("storage_class")
  }
  raise "confirmation digest mismatch" unless Digest::SHA256.hexdigest(canonical_json(payload)) == evidence.fetch("confirmation_digest")

  evidence
end

def validate_task_and_oracle_bindings!(tasks, oracles, evidence)
  tasks.each do |task|
    input = task.fetch("input_manifest")
    id = task.fetch("id")
    oracle = oracles.fetch(task.dig("expected_manifest", "oracle_id"))
    if CONFIRMATION_TASKS.include?(id)
      raise "#{id}: missing confirmation_ref" unless input.fetch("confirmation_ref") == evidence.fetch("confirmation_ref")
      raise "#{id}: missing confirmation_digest" unless input.fetch("confirmation_digest") == evidence.fetch("confirmation_digest")
      raise "#{id}: placeholder confirmation_ref" if input.fetch("confirmation_ref") == PENDING_FIXTURE_REF
      raise "#{id}: placeholder confirmation_digest" if input.fetch("confirmation_digest") == PENDING_CONFIRMATION_DIGEST

      binding = oracle.fetch("owner_value_bindings")
      raise "#{id}: owner binding ref" unless binding.fetch("confirmation_ref") == evidence.fetch("confirmation_ref")
      raise "#{id}: owner binding digest" unless binding.fetch("confirmation_digest") == evidence.fetch("confirmation_digest")
      raise "#{id}: permission ref" unless oracle.dig("permission", "confirmation_ref") == evidence.fetch("confirmation_ref")
    else
      raise "#{id}: unexpected task confirmation_ref" unless input.fetch("confirmation_ref").nil?
      raise "#{id}: unexpected task confirmation_digest" unless input.fetch("confirmation_digest").nil?
      raise "#{id}: unexpected owner bindings" if oracle.key?("owner_value_bindings")
      raise "#{id}: unexpected permission ref" unless oracle.dig("permission", "confirmation_ref").nil?
    end
  end
end

options = {suite: SUITE_DEFAULT}
OptionParser.new do |parser|
  parser.banner = "Usage: ruby tests/specs/phase0/p0-baseline-preflight.rb --runs RUN_MANIFEST [--suite SUITE]"
  parser.on("--suite PATH", "Path to suite YAML") { |value| options[:suite] = value }
  parser.on("--runs PATH", "Path to scorecard skeleton or run manifest") { |value| options[:runs] = value }
end.parse!

begin
  fail_closed!("P0_BASELINE_PREFLIGHT_MISSING_RUN_MANIFEST", "run manifest is required") unless options[:runs]

  root = File.realpath(".")
  validate_run_manifest_path!(root, options[:runs])
  resolve_repo_regular_file!(root, options[:suite], "suite")
  run_shared_strict_validator!(root, options[:suite])
  suite_data = parse_yaml_file!(options[:suite])
  raise "#{options[:suite]}: expected mapping root" unless suite_data.is_a?(Hash)
  exact_keys!(suite_data, TOP_LEVEL_KEYS, "top-level")
  suite = suite_data.fetch("suite")

  if suite.fetch("status") == "pending_representativeness_confirmation" || suite.fetch("representativeness_evidence").fetch("status") == "pending"
    fail_closed!("P0_BASELINE_PREFLIGHT_PENDING_CONFIRMATION", "suite confirmation is unresolved")
  end

  evidence = validate_confirmation_state!(suite)
  suite.fetch("source_manifest").each { |source_id, source| validate_source_file!(root, source_id, source) }
  validate_task_and_oracle_bindings!(suite_data.fetch("tasks"), suite_data.fetch("oracle_manifests"), evidence)
  run_ids = parse_runs_file!(options[:runs])

  puts({
    status: "ok",
    suite_id: suite.fetch("id"),
    suite_status: suite.fetch("status"),
    evidence_status: evidence.fetch("status"),
    run_ids: run_ids.length
  }.to_json)
rescue OptionParser::ParseError => e
  fail_closed!("P0_BASELINE_PREFLIGHT_USAGE", e.message)
rescue StandardError => e
  fail_closed!("P0_BASELINE_PREFLIGHT_FAIL_CLOSED", e.message)
end
