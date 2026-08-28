#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "optparse"
require "pathname"
require "psych"
require "set"
require "time"
require "yaml"

RUN_MANIFEST_DIR = "tests/evidence/phase0/run-manifests/".freeze
ALLOWED_ENTRY_KEYS = %w[
  suite_id
  task_id
  run_id
  agent
  timestamps
  assertion_results
  error_class
  correction_cost
  evidence_refs
].freeze
TIMESTAMP_KEYS = %w[started_at first_response_at scored_at ended_at].freeze
ASSERTION_RESULT_KEYS = %w[dimension result].freeze
ALLOWED_ASSERTION_RESULTS = %w[pass fail invalid].freeze
CORRECTION_COST_KEYS = %w[first_response_turns reviewer_reframes repeated_explanations].freeze
OPAQUE_REF = /\A[a-z0-9]+(?:_[a-z0-9]+)*\z/
SLUG = /\A[a-z0-9]+(?:[._-][a-z0-9]+)*\z/
RFC3339 = /\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\z/
REQUIRED_EVIDENCE_PREFIXES = %w[capture_ response_ review_].freeze
OPTIONAL_EVIDENCE_PREFIX = "transcript_"
SUITE_DEFAULT = "tests/specs/phase0/real-dogfood-tasks-v0.1.yaml"
RUNS_DEFAULT = "tests/evidence/phase0/run-manifests/p0-v0.1-run-ids.yaml"

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

def resolve_repo_regular_file!(root, path, label)
  relative = Pathname.new(path)
  raise "#{label}: absolute path" if relative.absolute?
  raise "#{label}: unclean path" unless relative.cleanpath.to_s == path && !relative.each_filename.to_a.include?("..")

  current = Pathname.new(root)
  relative.each_filename do |part|
    current = current.join(part)
    raise "#{label}: symlink component #{current}" if File.symlink?(current.to_s)
  end
  raise "#{label}: missing file" unless File.file?(current.to_s)

  real = File.realpath(current.to_s)
  raise "#{label}: path escape" unless real.start_with?(root + File::SEPARATOR)

  real
end

def validate_repo_metadata_path!(root, path, label)
  relative = Pathname.new(path)
  raise "#{label}: absolute path" if relative.absolute?
  raise "#{label}: unclean path" unless relative.cleanpath.to_s == path && !relative.each_filename.to_a.include?("..")

  parts = relative.each_filename.to_a
  raise "#{label}: quarantine path forbidden" if parts.include?("quarantine")
  raise "#{label}: .invalid forbidden" if path.end_with?(".invalid")
  raise "#{label}: outside allowed directory" unless path.start_with?(RUN_MANIFEST_DIR)

  real = resolve_repo_regular_file!(root, path, label)
  allowed_real = File.realpath(File.join(root, RUN_MANIFEST_DIR))
  raise "#{label}: outside allowed directory" unless real.start_with?(allowed_real + File::SEPARATOR)

  real
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

def validate_timestamps!(value, label)
  raise "#{label}: not a hash" unless value.is_a?(Hash)

  exact_keys!(value, TIMESTAMP_KEYS, label)
  parsed = TIMESTAMP_KEYS.map do |key|
    raw = value.fetch(key)
    raise "#{label}: #{key} format" unless raw.match?(RFC3339)

    Time.iso8601(raw)
  end
  raise "#{label}: non-monotonic" unless parsed == parsed.sort
end

def validate_assertion_results!(task, results, label)
  raise "#{label}: not an array" unless results.is_a?(Array)

  expected_dimensions = task.fetch("assertion_dimensions").map { |assertion| assertion.fetch("dimension") }
  raise "#{label}: count" unless results.length == expected_dimensions.length

  actual_dimensions = results.map do |result|
    raise "#{label}: item hash" unless result.is_a?(Hash)

    exact_keys!(result, ASSERTION_RESULT_KEYS, label)
    raise "#{label}: dimension" unless nonempty_string?(result.fetch("dimension"))
    raise "#{label}: result" unless ALLOWED_ASSERTION_RESULTS.include?(result.fetch("result"))

    result.fetch("dimension")
  end
  raise "#{label}: dimensions" unless actual_dimensions == expected_dimensions
end

def validate_correction_cost!(value, label)
  raise "#{label}: not a hash" unless value.is_a?(Hash)

  exact_keys!(value, CORRECTION_COST_KEYS, label)
  CORRECTION_COST_KEYS.each do |key|
    count = value.fetch(key)
    raise "#{label}: #{key}" unless count.is_a?(Integer) && count >= 0
  end
  raise "#{label}: first_response_turns must be 1" unless value.fetch("first_response_turns") == 1
  raise "#{label}: reviewer_reframes must be 0" unless value.fetch("reviewer_reframes").zero?
end

def validate_evidence_refs!(value, label)
  raise "#{label}: not an array" unless value.is_a?(Array)
  raise "#{label}: count" unless value.length.between?(3, 4)
  raise "#{label}: duplicate refs" unless value.uniq.length == value.length

  value.each do |ref|
    raise "#{label}: blank ref" unless nonempty_string?(ref)
    raise "#{label}: opaque ref required" unless ref.match?(OPAQUE_REF)
    raise "#{label}: private path leak" if ref.include?("/") || ref.include?("\\") || ref.start_with?(".")
  end

  REQUIRED_EVIDENCE_PREFIXES.each do |prefix|
    raise "#{label}: missing #{prefix}" unless value.any? { |ref| ref.start_with?(prefix) }
  end

  extra = value.reject do |ref|
    REQUIRED_EVIDENCE_PREFIXES.any? { |prefix| ref.start_with?(prefix) } || ref.start_with?(OPTIONAL_EVIDENCE_PREFIX)
  end
  raise "#{label}: unexpected ref prefix #{extra.inspect}" unless extra.empty?
end

def validate_scorecard_entries!(scorecard, suite, expected_run_ids)
  raise "scorecard: top-level array required" unless scorecard.is_a?(Array)

  tasks = suite.fetch("tasks")
  suite_id = suite.dig("suite", "id")
  expected_task_ids = tasks.map { |task| task.fetch("id") }
  expected_by_task = tasks.to_h { |task| [task.fetch("id"), task] }
  expected_runs = expected_run_ids.to_set

  raise "scorecard: entry count" unless scorecard.length == expected_task_ids.length

  seen_task_ids = []
  seen_run_ids = []
  scorecard.each_with_index do |entry, index|
    label = "entry[#{index}]"
    raise "#{label}: not a hash" unless entry.is_a?(Hash)

    exact_keys!(entry, ALLOWED_ENTRY_KEYS, label)
    raise "#{label}: suite_id" unless entry.fetch("suite_id") == suite_id

    task_id = entry.fetch("task_id")
    raise "#{label}: task_id" unless expected_by_task.key?(task_id)
    seen_task_ids << task_id

    run_id = entry.fetch("run_id")
    raise "#{label}: run_id format" unless nonempty_string?(run_id) && run_id.match?(SLUG)
    raise "#{label}: run_id not preregistered" unless expected_runs.include?(run_id)
    raise "#{label}: run/task mismatch" unless run_id.end_with?(task_id)
    seen_run_ids << run_id

    agent = entry.fetch("agent")
    raise "#{label}: agent" unless nonempty_string?(agent) && agent.match?(SLUG)

    error_class = entry.fetch("error_class")
    raise "#{label}: error_class" unless nonempty_string?(error_class) && error_class.match?(SLUG)

    validate_timestamps!(entry.fetch("timestamps"), "#{label}: timestamps")
    validate_assertion_results!(expected_by_task.fetch(task_id), entry.fetch("assertion_results"), "#{label}: assertion_results")
    validate_correction_cost!(entry.fetch("correction_cost"), "#{label}: correction_cost")
    validate_evidence_refs!(entry.fetch("evidence_refs"), "#{label}: evidence_refs")

    results = entry.fetch("assertion_results").map { |item| item.fetch("result") }
    raise "#{label}: passing run must use error_class none" if results.all?("pass") && error_class != "none"
    raise "#{label}: failing run must not use error_class none" if results.any? { |result| result != "pass" } && error_class == "none"
  end

  raise "scorecard: duplicate task_id" unless seen_task_ids.uniq.length == seen_task_ids.length
  raise "scorecard: duplicate run_id" unless seen_run_ids.uniq.length == seen_run_ids.length
  raise "scorecard: task coverage" unless seen_task_ids.sort == expected_task_ids.sort
  raise "scorecard: run coverage" unless seen_run_ids.sort == expected_run_ids.sort
end

options = {
  suite: SUITE_DEFAULT,
  runs: RUNS_DEFAULT
}

OptionParser.new do |parser|
  parser.banner = "Usage: ruby tests/specs/phase0/p0-scorecard-metadata-validate.rb --scorecard PATH [--suite PATH] [--runs PATH]"
  parser.on("--suite PATH", "Path to the frozen suite YAML") { |value| options[:suite] = value }
  parser.on("--runs PATH", "Path to the preregistered run manifest") { |value| options[:runs] = value }
  parser.on("--scorecard PATH", "Path to repository scorecard metadata YAML") { |value| options[:scorecard] = value }
end.parse!(ARGV)

fail_closed!("P0_SCORECARD_VALIDATE_MISSING_SCORECARD", "scorecard is required") unless options[:scorecard]

root = Dir.pwd
suite_real = resolve_repo_regular_file!(root, options[:suite], "suite")
runs_real = validate_repo_metadata_path!(root, options[:runs], "run manifest")
scorecard_real = validate_repo_metadata_path!(root, options[:scorecard], "scorecard")
suite = parse_yaml_file!(suite_real)
run_ids = parse_runs_file!(runs_real)
scorecard = parse_yaml_file!(scorecard_real)
validate_scorecard_entries!(scorecard, suite, run_ids)

puts(JSON.generate({
  status: "ok",
  suite_id: suite.dig("suite", "id"),
  scorecard_entries: scorecard.length,
  run_ids: run_ids.length
}))
