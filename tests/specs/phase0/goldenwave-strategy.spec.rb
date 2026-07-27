#!/usr/bin/env ruby
# frozen_string_literal: true

require "minitest/autorun"
require "open3"
require "pathname"
require "tempfile"
require "tmpdir"
require "yaml"

class GoldenwaveStrategyScorecardValidatorTest < Minitest::Test
  ROOT = Pathname.new(__dir__).join("..", "..", "..").expand_path.freeze
  SUITE_PATH = "tests/specs/phase0/real-dogfood-tasks-v0.1.yaml"
  RUNS_PATH = "tests/evidence/phase0/run-manifests/p0-v0.1-run-ids.yaml"
  VALIDATOR_PATH = "tests/specs/phase0/p0-scorecard-metadata-validate.rb"
  TIMESTAMPS = {
    "started_at" => "2026-07-27T14:00:00+08:00",
    "first_response_at" => "2026-07-27T14:00:08+08:00",
    "scored_at" => "2026-07-27T14:00:20+08:00",
    "ended_at" => "2026-07-27T14:00:25+08:00"
  }.freeze
  CORRECTION_COST = {
    "first_response_turns" => 1,
    "reviewer_reframes" => 0,
    "repeated_explanations" => 0
  }.freeze

  def test_accepts_minimal_valid_scorecard_metadata
    stdout, stderr, status = run_validator(write_scorecard(valid_scorecard_entries))

    assert status.success?, failure_message(stdout, stderr)
    assert_match(/"status":"ok"/, stdout)
  end

  def test_rejects_extra_repo_field
    invalid = valid_scorecard_entries
    invalid.first["notes"] = "should not be stored in repo"

    stdout, stderr, status = run_validator(write_scorecard(invalid))

    refute status.success?
    assert_match(/entry\[0\]: keys=/, combined_output(stdout, stderr))
  end

  def test_rejects_private_path_in_evidence_refs
    invalid = valid_scorecard_entries
    invalid.first["evidence_refs"] = [
      ".private/goldenwave/baselines/p0-v0.1/raw-output.md",
      "review_rdt_profile_handoff_update_style"
    ]

    stdout, stderr, status = run_validator(write_scorecard(invalid))

    refute status.success?
    assert_match(/evidence_refs/, combined_output(stdout, stderr))
  end

  private

  def run_validator(scorecard_path)
    Open3.capture3(
      "ruby",
      VALIDATOR_PATH,
      "--suite",
      SUITE_PATH,
      "--runs",
      RUNS_PATH,
      "--scorecard",
      scorecard_path,
      chdir: ROOT.to_s
    )
  end

  def write_scorecard(entries)
    file = Tempfile.new(["p0-scorecard", ".yaml"], ROOT.join("tests/evidence/phase0/run-manifests"))
    file.write(YAML.dump(entries))
    file.flush
    Pathname.new(file.path).relative_path_from(ROOT).to_s
  ensure
    file.close
  end

  def valid_scorecard_entries
    suite = YAML.safe_load(File.read(ROOT.join(SUITE_PATH)), permitted_classes: [], permitted_symbols: [], aliases: false)
    run_ids = YAML.safe_load(File.read(ROOT.join(RUNS_PATH)), permitted_classes: [], permitted_symbols: [], aliases: false).fetch("run_ids")
    tasks = suite.fetch("tasks")
    dimensions_by_task = tasks.to_h do |task|
      [task.fetch("id"), task.fetch("assertion_dimensions").map { |assertion| assertion.fetch("dimension") }]
    end
    suite_id = suite.dig("suite", "id")

    tasks.map.with_index do |task, index|
      task_id = task.fetch("id")
      {
        "suite_id" => suite_id,
        "task_id" => task_id,
        "run_id" => run_ids.fetch(index),
        "agent" => "codex-cli",
        "timestamps" => Marshal.load(Marshal.dump(TIMESTAMPS)),
        "assertion_results" => dimensions_by_task.fetch(task_id).map do |dimension|
          {"dimension" => dimension, "result" => "pass"}
        end,
        "error_class" => "none",
        "correction_cost" => Marshal.load(Marshal.dump(CORRECTION_COST)),
        "evidence_refs" => [
          "capture_#{task_id}",
          "response_#{task_id}",
          "review_#{task_id}"
        ]
      }
    end
  end

  def failure_message(stdout, stderr)
    "validator failed\nSTDOUT:\n#{stdout}\nSTDERR:\n#{stderr}"
  end

  def combined_output(stdout, stderr)
    [stdout, stderr].join("\n")
  end
end
