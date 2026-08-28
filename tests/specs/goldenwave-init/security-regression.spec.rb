#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "test_helper"

class GoldenwaveInitSecurityRegressionTest < Minitest::Test
  include GoldenwaveInitTestHelper

  def test_manifest_paths_are_allowlisted_before_doctor_reads_them
    with_workspace("gw-init-manifest-boundary") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      manifest_path = target / ".kb" / "goldenwave.json"
      manifest = JSON.parse(manifest_path.read)
      manifest.fetch("managed_templates")["../../outside.md"] = "sha256:#{"0" * 64}"
      write_json(manifest_path, manifest)

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?
      payload = parse_json!(stdout, stderr)
      assert payload.fetch("findings").any? { |item| item["code"] == "GW_MANIFEST_INVALID" }
      assert_relative_path_payload!(payload)
    end
  end

  def test_doctor_rejects_symlinks_inside_managed_target_without_exposing_destination
    with_workspace("gw-init-internal-symlink") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      File.symlink(workspace.parent.to_s, (target / "projects" / "outside-link").to_s)

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?
      payload = parse_json!(stdout, stderr)
      finding = payload.fetch("findings").find { |item| item["code"] == "GW_TARGET_UNSAFE" }
      assert_equal "projects/outside-link", finding.fetch("path")
      assert_relative_path_payload!(payload)
    end
  end

  def test_doctor_fails_closed_when_ephemeral_file_is_already_tracked
    with_workspace("gw-init-ephemeral-tracked") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      raw_file = target / ".ephemeral" / "raw.md"
      File.write(raw_file, "temporary\n")
      run_git(target, "init")
      run_git(target, "add", "-f", raw_file.relative_path_from(target).to_s)

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?
      payload = parse_json!(stdout, stderr)
      finding = payload.fetch("findings").find { |item| item["path"] == ".ephemeral/raw.md" }
      assert_equal "GW_EPHEMERAL_FORMAL_PATH", finding.fetch("code")
    end
  end

  def test_adopt_inventory_reports_tracked_l3_and_dirty_worktree_as_read_only_metadata
    with_workspace("gw-init-legacy-metadata") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      tracked_l3 = target / "profile" / "01-body-health" / "index.md"
      write_markdown(tracked_l3, "sensitivity" => "L3")
      run_git(target, "init")
      run_git(target, "add", tracked_l3.relative_path_from(target).to_s)
      before = snapshot_tree(target)

      stdout, stderr, status = run_init("adopt", "inventory", "--target", target, "--format", "json")

      assert status.success?, "repairable/advisory findings should not block inventory\n#{stdout}\n#{stderr}"
      payload = parse_json!(stdout, stderr)
      tracked = payload.fetch("findings").find { |item| item["path"] == "profile/01-body-health/index.md" }
      assert_equal "repairable", tracked.fetch("level")
      assert payload.fetch("findings").any? { |item| item["level"] == "advisory" && item["message"].include?("dirty worktree") }
      assert_equal before, snapshot_tree(target)
    end
  end

  def test_explicit_git_init_fails_before_writing_when_git_is_unavailable
    with_workspace("gw-init-no-git") do |workspace|
      target = workspace / "kb"
      python_path, python_status = Open3.capture2("which", GoldenwaveInitTestHelper::PYTHON_BIN)
      assert python_status.success?
      stdout, stderr, status = Open3.capture3(
        {"PATH" => ""},
        python_path.strip,
        GoldenwaveInitTestHelper::SCRIPT_PATH.to_s,
        "apply", "--target", target.to_s, "--mode", "new", "--git", "init", "--format", "json"
      )

      refute status.success?
      payload = parse_json!(stdout, stderr)
      assert_equal "GW_GIT_UNAVAILABLE", payload.fetch("conflicts").first.fetch("code")
      refute target.exist?
    end
  end

  def test_standalone_skill_copy_uses_only_bundled_resources
    with_workspace("gw-init-standalone") do |workspace|
      skill_copy = workspace / "goldenwave-init"
      FileUtils.cp_r(ROOT / "skills" / "goldenwave-init", skill_copy)
      target = workspace / "standalone-kb"
      entry = skill_copy / "scripts" / "goldenwave_init.py"

      apply_stdout, apply_stderr, apply_status = Open3.capture3(
        PYTHON_BIN, entry.to_s, "apply", "--target", target.to_s, "--mode", "new", "--git", "off", "--format", "json"
      )
      assert apply_status.success?, "standalone apply failed\n#{apply_stdout}\n#{apply_stderr}"

      doctor_stdout, doctor_stderr, doctor_status = Open3.capture3(
        PYTHON_BIN, entry.to_s, "doctor", "--target", target.to_s, "--format", "json"
      )
      assert doctor_status.success?, "standalone doctor failed\n#{doctor_stdout}\n#{doctor_stderr}"
      assert_equal true, parse_json!(doctor_stdout, doctor_stderr).fetch("ok")
    end
  end

  def test_tampered_template_path_fails_without_writing_outside_target
    with_workspace("gw-init-template-boundary") do |workspace|
      skill_copy = workspace / "goldenwave-init"
      FileUtils.cp_r(ROOT / "skills" / "goldenwave-init", skill_copy)
      template_path = skill_copy / "assets" / "kb-template" / "template-manifest.json"
      template = JSON.parse(template_path.read)
      template.fetch("entries") << {"kind" => "file", "path" => "../../escaped.md", "content" => "blocked"}
      write_json(template_path, template)
      target = workspace / "kb"
      entry = skill_copy / "scripts" / "goldenwave_init.py"

      stdout, stderr, status = Open3.capture3(
        PYTHON_BIN, entry.to_s, "apply", "--target", target.to_s, "--mode", "new", "--git", "off", "--format", "json"
      )

      refute status.success?
      payload = parse_json!(stdout, stderr)
      assert payload.fetch("findings").any? { |item| item["code"] == "GW_TEMPLATE_INVALID" }
      refute (workspace / "escaped.md").exist?
      refute target.exist?
    end
  end

  def test_doctor_rejects_missing_frontmatter_and_broad_private_permissions
    with_workspace("gw-init-frontmatter-permissions") do |workspace|
      target = workspace / "kb"
      build_valid_kb(target)
      File.write(target / "profile" / "console" / "me.md", "missing frontmatter\n")
      (target / ".private").chmod(0o755)

      stdout, stderr, status = run_init("doctor", "--target", target, "--format", "json")

      refute status.success?
      payload = parse_json!(stdout, stderr)
      assert payload.fetch("findings").any? { |item| item["path"] == "profile/console/me.md" && item["level"] == "invalid" }
      assert payload.fetch("findings").any? { |item| item["path"] == ".private" && item["level"] == "unsafe" }
    end
  end

  def test_plan_rejects_target_when_immediate_parent_does_not_exist
    with_workspace("gw-init-parent-missing") do |workspace|
      target = workspace / "missing-parent" / "kb"

      stdout, stderr, status = run_init("plan", "--target", target, "--mode", "new", "--format", "json")

      refute status.success?
      payload = parse_json!(stdout, stderr)
      assert_equal "GW_TARGET_UNSAFE", payload.fetch("conflicts").first.fetch("code")
      refute target.parent.exist?
    end
  end
end
