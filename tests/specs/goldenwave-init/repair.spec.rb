#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "test_helper"

class GoldenwaveRepairContractTest < Minitest::Test
  include GoldenwaveInitTestHelper

  def test_repair_plan_is_bound_and_apply_only_creates_missing_phase1c_directories
    with_workspace("repair") do |target|
      build_valid_kb(target)
      File.write(target / "user.md", "user")
      user_digest = Digest::SHA256.hexdigest("user")
      missing = target / ".kb/reliable-inject/objects"
      missing.rmtree if missing.exist?
      stdout, stderr, status = run_init("adopt", "plan-repair", "--target", target, "--format", "json")
      assert status.success?, "plan should succeed\n#{stdout}\n#{stderr}"
      plan = parse_json!(stdout, stderr)
      digest = plan.fetch("artifacts").fetch("plan_digest")
      refute missing.exist?

      stdout, stderr, status = run_init(
        "adopt", "apply-repair", "--target", target, "--format", "json",
        "--plan-digest", digest, "--confirm", digest
      )
      assert status.success?, "apply should succeed\n#{stdout}\n#{stderr}"
      assert_equal "repaired", parse_json!(stdout, stderr).fetch("summary").fetch("status")
      assert missing.directory?
      assert_equal "file:#{user_digest}", snapshot_tree(target)["user.md"]
    end
  end

  def test_repair_refuses_dirty_git_and_wrong_confirmation
    with_workspace("repair-dirty") do |target|
      build_valid_kb(target)
      run_git(target, "init", "-q")
      File.write(target / "user.md", "dirty")
      stdout, stderr, status = run_init(
        "adopt", "apply-repair", "--target", target, "--format", "json",
        "--plan-digest", "bad", "--confirm", "bad"
      )
      refute status.success?
      payload = parse_json!(stdout, stderr)
      assert_equal "GW_REPAIR_CONFIRMATION_MISMATCH", payload.fetch("findings").first.fetch("code")
      refute (target / ".kb/reliable-inject").exist?
    end
  end
end
