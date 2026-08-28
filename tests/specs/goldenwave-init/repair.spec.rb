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
      assert (target / ".kb/reliable-inject/active.json").file?
      assert (target / ".kb/reliable-inject/lock").file?
      assert_equal "file:#{user_digest}", snapshot_tree(target)["user.md"]
    end
  end

  def test_new_kb_contains_complete_reliable_inject_state
    with_workspace("repair-new") do |workspace|
      target = workspace / "kb"
      stdout, stderr, status = run_init(
        "apply", "--target", target, "--mode", "new", "--git", "off", "--format", "json"
      )
      assert status.success?, "new apply should succeed\n#{stdout}\n#{stderr}"
      assert (target / ".kb/reliable-inject/active.json").file?
      assert (target / ".kb/reliable-inject/lock").file?
    end
  end

  def test_repair_refuses_dirty_git_and_wrong_confirmation
    with_workspace("repair-dirty") do |target|
      build_valid_kb(target)
      (target / ".kb/reliable-inject").rmtree
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

  def test_repair_plan_digest_cannot_be_reused_for_another_kb
    with_workspace("repair-binding") do |workspace|
      first = workspace / "first"
      second = workspace / "second"
      [first, second].each do |target|
        build_valid_kb(target)
        (target / ".kb/reliable-inject").rmtree
      end
      stdout, stderr, status = run_init("adopt", "plan-repair", "--target", first, "--format", "json")
      assert status.success?, "plan should succeed\n#{stdout}\n#{stderr}"
      digest = parse_json!(stdout, stderr).fetch("artifacts").fetch("plan_digest")
      stdout, stderr, status = run_init(
        "adopt", "apply-repair", "--target", second, "--format", "json",
        "--plan-digest", digest, "--confirm", digest
      )
      refute status.success?
      assert_equal "GW_REPAIR_CONFIRMATION_MISMATCH", parse_json!(stdout, stderr).fetch("findings").first.fetch("code")
      refute (second / ".kb/reliable-inject").exist?
    end
  end

  def test_repair_refuses_a_clean_repo_with_tracked_private_content
    with_workspace("repair-private") do |target|
      build_valid_kb(target)
      (target / ".kb/reliable-inject").rmtree
      File.write(target / ".private/secret.md", "private")
      run_git(target, "init", "-q")
      run_git(target, "add", ".")
      run_git(target, "add", "-f", ".private/secret.md")
      run_git(target, "commit", "-qm", "fixture")
      stdout, stderr, status = run_init(
        "adopt", "plan-repair", "--target", target, "--format", "json"
      )
      refute status.success?
      assert_equal "GW_DOCTOR_FAILED", parse_json!(stdout, stderr).fetch("findings").first.fetch("code")
      refute (target / ".kb/reliable-inject").exist?
    end
  end
end
