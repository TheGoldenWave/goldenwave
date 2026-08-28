#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "test_helper"

class GoldenwaveInitContractTest < Minitest::Test
  include GoldenwaveInitTestHelper

  def test_given_empty_target_fixture_when_plan_then_it_returns_read_only_json_envelope
    with_workspace("gw-init-empty-target") do |workspace|
      target = workspace / "Knowledge Base"

      stdout, stderr, status = run_init("plan", "--target", target, "--mode", "new", "--format", "json")

      assert status.success?, "plan should pass for empty target\nSTDOUT:\n#{stdout}\nSTDERR:\n#{stderr}"
      payload = parse_json!(stdout, stderr)
      assert_equal true, payload.fetch("ok")
      assert_equal "plan", payload.fetch("command")
      assert_equal RESULT_VERSION, payload.fetch("result_version")
      assert_equal FORMAT_VERSION, payload.fetch("format_version")
      assert_match(/^plan:[0-9a-f]{16}$/, payload.dig("artifacts", "plan_id"))
      assert_equal %w[render_template write_manifest doctor], payload.dig("artifacts", "actions")
      refute target.exist?, "plan must not create the target directory"
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_existing_conflict_fixture_when_plan_new_then_it_blocks_with_zero_writes
    with_workspace("gw-init-existing-conflict") do |workspace|
      target = workspace / "existing-conflict"
      target.mkpath
      sentinel = target / "keep.txt"
      File.write(sentinel, "do not touch\n")
      before = snapshot_tree(target)

      stdout, stderr, status = run_init("plan", "--target", target, "--mode", "new", "--format", "json")

      refute status.success?, "plan should block non-empty targets"
      payload = parse_json!(stdout, stderr)
      assert_equal false, payload.fetch("ok")
      assert_equal "blocked", payload.dig("summary", "status")
      assert_equal "GW_TARGET_NOT_EMPTY", payload.fetch("conflicts").first.fetch("code")
      assert_equal before, snapshot_tree(target), "new mode must not write into a non-empty target"
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_space_and_chinese_target_fixture_when_apply_then_it_creates_the_mvp_layout
    with_workspace("gw-init-space-zh") do |workspace|
      target = workspace / "知识库 Space"

      stdout, stderr, status = run_init("apply", "--target", target, "--mode", "new", "--git", "off", "--format", "json")

      assert status.success?, "apply should initialize a new KB\nSTDOUT:\n#{stdout}\nSTDERR:\n#{stderr}"
      payload = parse_json!(stdout, stderr)
      assert_equal true, payload.fetch("ok")
      assert_equal FORMAT_VERSION, JSON.parse((target / ".kb" / "goldenwave.json").read).fetch("format_version")
      assert (target / ".kb" / "candidate-decisions").directory?
      assert (target / ".private" / "social").directory?
      assert (target / ".ephemeral").directory?
      GoldenwaveInitTestHelper::WIKI_TYPES.each_key do |type|
        assert (target / "wiki" / type / "index.md").file?, "missing wiki type index for #{type}"
      end
      GoldenwaveInitTestHelper::PROFILE_DOMAINS.each do |domain|
        assert (target / "profile" / domain).directory?, "missing profile domain #{domain}"
      end
      assert (target / "profile" / "console" / "me.md").file?
      refute (target / ".git").exist?, "--git off must not initialize git"
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_repeated_apply_fixture_when_apply_runs_twice_then_second_run_is_deterministic
    with_workspace("gw-init-repeat-apply") do |workspace|
      target = workspace / "kb"

      first_stdout, first_stderr, first_status = run_init("apply", "--target", target, "--mode", "new", "--git", "off", "--format", "json")
      assert first_status.success?, "first apply should succeed\nSTDOUT:\n#{first_stdout}\nSTDERR:\n#{first_stderr}"
      first_snapshot = snapshot_tree(target)

      second_stdout, second_stderr, second_status = run_init("apply", "--target", target, "--mode", "new", "--git", "off", "--format", "json")
      assert second_status.success?, "second apply should also succeed deterministically\nSTDOUT:\n#{second_stdout}\nSTDERR:\n#{second_stderr}"
      assert_equal first_snapshot, snapshot_tree(target), "repeat apply must not introduce diff"
    end
  end

  def test_doctor_reports_missing_candidate_decision_directory_after_init
    with_workspace("gw-init-missing-candidate-decisions") do |workspace|
      target = workspace / "kb"
      apply_stdout, apply_stderr, apply_status = run_init(
        "apply", "--target", target, "--mode", "new", "--git", "off", "--format", "json"
      )
      assert apply_status.success?, "init failed\nSTDOUT:\n#{apply_stdout}\nSTDERR:\n#{apply_stderr}"
      (target / ".kb/candidate-decisions").rmdir

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")
      payload = parse_json!(stdout, stderr)

      refute status.success?
      assert_equal "", stderr
      finding = payload.fetch("findings").find do |item|
        item.fetch("code") == "GW_DOCTOR_FAILED" && item.fetch("path") == ".kb/candidate-decisions"
      end
      refute_nil finding
      assert_equal "invalid", finding.fetch("level")
      assert_equal "error", finding.fetch("severity")
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_private_not_ignored_fixture_when_doctor_then_it_fails_closed
    with_workspace("gw-init-private-not-ignored") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      File.write(target / ".gitignore", ".ephemeral/\n")

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?, "doctor must fail when .private/ is not ignored"
      payload = parse_json!(stdout, stderr)
      finding = payload.fetch("findings").find { |item| item["code"] == "GW_PRIVATE_NOT_IGNORED" }
      refute_nil finding
      assert_equal "unsafe", finding.fetch("level")
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_private_already_tracked_fixture_when_doctor_then_it_reports_gw_private_tracked
    with_workspace("gw-init-private-tracked") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      private_file = target / ".private" / "social" / "example.md"
      write_markdown(private_file, "title" => "secret")
      run_git(target, "init")
      run_git(target, "add", "-f", private_file.relative_path_from(target).to_s)

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?, "doctor must fail when local_private is already tracked"
      payload = parse_json!(stdout, stderr)
      finding = payload.fetch("findings").find { |item| item["code"] == "GW_PRIVATE_TRACKED" }
      refute_nil finding
      assert_equal ".private/social/example.md", finding.fetch("path")
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_ephemeral_not_ignored_fixture_when_doctor_then_it_reports_gw_ephemeral_not_ignored
    with_workspace("gw-init-ephemeral-not-ignored") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      File.write(target / ".gitignore", ".private/\n")

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?, "doctor must fail when .ephemeral/ is not ignored"
      payload = parse_json!(stdout, stderr)
      finding = payload.fetch("findings").find { |item| item["code"] == "GW_EPHEMERAL_NOT_IGNORED" }
      refute_nil finding
      assert_equal "unsafe", finding.fetch("level")
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_ephemeral_in_formal_path_fixture_when_doctor_then_it_reports_gw_ephemeral_formal_path
    with_workspace("gw-init-ephemeral-formal") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      leaked = target / "wiki" / "concepts" / "raw-chat.md"
      write_markdown(leaked, "storage_class" => "ephemeral", "type" => "concept")

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?, "doctor must fail when ephemeral content lands in a formal path"
      payload = parse_json!(stdout, stderr)
      finding = payload.fetch("findings").find { |item| item["code"] == "GW_EPHEMERAL_FORMAL_PATH" }
      refute_nil finding
      assert_equal "wiki/concepts/raw-chat.md", finding.fetch("path")
      assert_relative_path_payload!(payload)
    end
  end

  def test_given_manifest_unknown_version_and_managed_drift_fixtures_when_doctor_and_adopt_inventory_run_then_contracts_hold
    with_workspace("gw-init-manifest-and-drift") do |workspace|
      invalid_target = workspace / "manifest-unknown-version"
      build_valid_kb(invalid_target, format_version: "gwkb/v9.9")
      invalid_stdout, invalid_stderr, invalid_status = run_init("doctor", "--target", invalid_target, "--format", "json")
      refute invalid_status.success?, "doctor must fail closed on unknown manifest versions"
      invalid_payload = parse_json!(invalid_stdout, invalid_stderr)
      invalid_finding = invalid_payload.fetch("findings").find { |item| item["code"] == "GW_MANIFEST_INVALID" }
      refute_nil invalid_finding

      drift_target = workspace / "managed-template-drift"
      build_valid_kb(drift_target)
      File.write(drift_target / "AGENTS.md", "---\nstatus: edited\n---\n\nuser changed\n")
      before = snapshot_tree(drift_target)
      drift_stdout, drift_stderr, drift_status = run_init("adopt", "inventory", "--target", drift_target, "--format", "json")
      assert drift_status.success?, "adopt inventory should stay read-only for drift inspection\nSTDOUT:\n#{drift_stdout}\nSTDERR:\n#{drift_stderr}"
      drift_payload = parse_json!(drift_stdout, drift_stderr)
      drift_finding = drift_payload.fetch("findings").find { |item| item.fetch("path") == "AGENTS.md" }
      refute_nil drift_finding
      assert_includes %w[repairable advisory], drift_finding.fetch("level")
      assert_equal before, snapshot_tree(drift_target), "adopt inventory must not write files"
      assert_relative_path_payload!(invalid_payload)
      assert_relative_path_payload!(drift_payload)
    end
  end

  def test_given_path_traversal_and_explicit_git_init_fixtures_when_apply_then_it_fails_closed_or_only_git_inits
    with_workspace("gw-init-path-traversal") do |workspace|
      outside = workspace.parent.expand_path
      symlink_target = workspace / "nested" / "kb-link"
      symlink_target.parent.mkpath
      File.symlink(outside.to_s, symlink_target.to_s)

      unsafe_stdout, unsafe_stderr, unsafe_status = run_init("apply", "--target", symlink_target, "--mode", "new", "--git", "off", "--format", "json")
      refute unsafe_status.success?, "apply must fail closed on symlink traversal"
      unsafe_payload = parse_json!(unsafe_stdout, unsafe_stderr)
      conflict = unsafe_payload.fetch("conflicts").first
      assert_equal "GW_TARGET_UNSAFE", conflict.fetch("code")
      assert_relative_path_payload!(unsafe_payload)

      safe_target = workspace / "git-init-only"
      git_stdout, git_stderr, git_status = run_init("apply", "--target", safe_target, "--mode", "new", "--git", "init", "--format", "json")
      assert git_status.success?, "apply with --git init should still succeed\nSTDOUT:\n#{git_stdout}\nSTDERR:\n#{git_stderr}"
      assert (safe_target / ".git").directory?
      _, _, head_status = run_git(safe_target, "rev-parse", "--verify", "HEAD")
      refute head_status.success?, "git init mode must not create a commit"
      remotes_stdout, = run_git(safe_target, "remote")
      assert_equal "", remotes_stdout.strip
    end
  end
end
