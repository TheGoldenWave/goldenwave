require "digest"
require "fileutils"
require "find"
require "json"
require "minitest/autorun"
require "open3"
require "pathname"
require "time"
require "tmpdir"

class CandidateDecisionSpec < Minitest::Test
  ROOT = Pathname(__dir__).join("../../..").expand_path
  CLI = ROOT.join("scripts/goldenwave_candidate.py")
  CONTRACT_FIXTURES = ROOT.join("tests/specs/candidate-contract/fixtures")
  FIXTURES = Pathname(__dir__).join("fixtures")
  PYTHON_BIN = ENV.fetch("GW_CANDIDATE_PYTHON", "python3").freeze
  NOW = "2026-07-27T12:00:00Z"
  CANDIDATE_ID = "cand_01JAZ6Y5M4N6KD3V8T2WQ9R7HD"
  TARGET = "wiki/methods/candidate-validation.md"
  SOURCE_REF = "docs/prd/goldenwave-strategy/PRD.md"
  CONTENT = "Validators reject unknown fields and unsafe targets."
  DECISION_RESULT_VERSION = "gw-candidate-decision/v0.1"

  def setup
    assert CLI.file?, "candidate CLI entrypoint is missing"
  end

  def fixture(name = "git-tracked.json")
    CONTRACT_FIXTURES.join("valid", name)
  end

  def command(*args, env: {})
    @last_command = args.first
    @last_candidate_sensitive_values = if %w[review accept reject].include?(@last_command)
      candidate_sensitive_values(args.fetch(1))
    else
      []
    end
    @last_sensitive_values = args.each_with_object([]) do |value, sensitive_values|
      text = value.to_s
      sensitive_values << text if Pathname(text).absolute?
    rescue ArgumentError
      next
    end
    stdout, stderr, status = Open3.capture3(
      env, PYTHON_BIN, CLI.to_s, *args.map(&:to_s), chdir: ROOT.to_s
    )
    @last_stdout = stdout
    @last_stderr = stderr
    payload = JSON.parse(stdout)
    [payload, stdout, stderr, status]
  rescue JSON::ParserError
    flunk "P1B-02 CLI command is not implemented or emitted non-JSON output\nSTDOUT:\n#{stdout}\nSTDERR:\n#{stderr}"
  end

  def candidate_sensitive_values(candidate_path)
    path = Pathname(candidate_path.to_s)
    path = ROOT.join(path) unless path.absolute?
    document = JSON.parse(path.read)
    [
      document.fetch("content").fetch("text"),
      document.fetch("provenance").fetch("source_ref"),
      document.fetch("target").fetch("path")
    ]
  end

  def review(path = fixture, *extra)
    command("review", path, *extra)
  end

  def raw_cli(*args, env: {}, entry: CLI, chdir: ROOT)
    Open3.capture3(env, PYTHON_BIN, entry.to_s, *args.map(&:to_s), chdir: chdir.to_s)
  end

  def assert_argument_invalid(
    args,
    expected_command,
    expected_code: "GW_CANDIDATE_ARGUMENT_INVALID",
    expected_field: "arguments",
    extra_forbidden: []
  )
    first_stdout, first_stderr, first_status = raw_cli(*args)
    second_stdout, second_stderr, second_status = raw_cli(*args)
    payload = JSON.parse(first_stdout)

    refute first_status.success?
    refute second_status.success?
    assert_equal first_stdout.b, second_stdout.b
    assert_equal "", first_stderr
    assert_equal "", second_stderr
    assert_equal %w[command contract errors ok result_version summary], payload.keys.sort
    assert_equal false, payload.fetch("ok")
    assert_equal expected_command, payload.fetch("command")
    assert_equal DECISION_RESULT_VERSION, payload.fetch("result_version")
    assert_equal "context-candidate/v0.1", payload.fetch("contract")
    assert_equal({"status" => "failed", "error_count" => 1}, payload.fetch("summary"))
    assert_equal(
      [{"code" => expected_code, "field" => expected_field}],
      payload.fetch("errors")
    )
    ([CONTENT, SOURCE_REF, TARGET] + extra_forbidden + args.map(&:to_s).select { |arg| Pathname(arg).absolute? }).uniq.each do |value|
      refute_includes first_stdout, value
    end
    refute_includes first_stdout.downcase, "usage:"
  rescue JSON::ParserError => error
    flunk "argument error must be deterministic JSON: #{error.message}\nSTDOUT:\n#{first_stdout}\nSTDERR:\n#{first_stderr}"
  end

  def copy_tree_without_bytecode(source, destination)
    Find.find(source.to_s) do |entry|
      path = Pathname(entry)
      relative = path.relative_path_from(source)
      if path.directory? && path.basename.to_s == "__pycache__"
        Find.prune
        next
      end
      next if path.extname == ".pyc"

      target = destination.join(relative)
      path.directory? ? target.mkpath : FileUtils.cp(path, target.tap { |item| item.parent.mkpath })
    end
  end

  def review_digest(path = fixture)
    Digest::SHA256.file(path).hexdigest
  end

  def accept_args(path, kb, overrides = {})
    values = {
      confirm: CANDIDATE_ID,
      digest: review_digest(path),
      basis: "self_context",
      retention: "none"
    }.merge(overrides)
    [
      "accept", path, "--target", kb,
      "--confirm", values.fetch(:confirm),
      "--review-digest", values.fetch(:digest),
      "--authorization-basis", values.fetch(:basis),
      "--retention-until", values.fetch(:retention),
      "--attest-no-consent-required-data", "--ack-git-history"
    ]
  end

  def reject_args(path, kb, reason: "privacy", digest: review_digest(path), confirm: CANDIDATE_ID)
    [
      "reject", path, "--target", kb,
      "--confirm", confirm, "--review-digest", digest,
      "--reason", reason
    ]
  end

  def initialize_kb(root)
    root.join(".kb/candidate-decisions").mkpath
    root.join("wiki/methods").mkpath
    root.join(".kb/goldenwave.json").write(
      JSON.generate({"format_version" => "gwkb/v0.1", "version" => "0.1.0"})
    )
  end

  def symlink_or_skip(link, target)
    link.make_symlink(target)
  rescue NotImplementedError, SystemCallError => error
    skip "symlink operations unavailable: #{error.message}"
  end

  def hardlink_or_skip(source, target)
    File.link(source, target)
  rescue NotImplementedError, SystemCallError => error
    skip "hardlink operations unavailable: #{error.message}"
  end

  def with_kb
    Dir.mktmpdir("gw-candidate-kb-") do |directory|
      root = Pathname(directory)
      initialize_kb(root)
      yield root
    end
  end

  def with_isolated_candidate
    Dir.mktmpdir("gw-candidate-review-") do |directory|
      sandbox = Pathname(directory)
      root = sandbox.join("input")
      path = root.join("candidate.json")
      root.mkpath
      path.binwrite(fixture.binread)
      yield root, path
    end
  end

  def tree_snapshot(root)
    descendants = root.glob("**/*", File::FNM_DOTMATCH).reject do |path|
      [".", ".."].include?(path.basename.to_s)
    end
    ([root] + descendants.sort).map do |path|
      stat = path.lstat
      [
        path == root ? "." : path.relative_path_from(root).to_s,
        stat.ftype,
        stat.mode,
        stat.uid,
        stat.gid,
        stat.size,
        stat.mtime.to_f,
        stat.nlink,
        stat.file? ? Digest::SHA256.file(path).hexdigest : nil,
        stat.symlink? ? path.readlink.to_s : nil
      ]
    end
  end

  def assert_failed(payload, status, code, sensitive_values: [])
    refute status.success?
    assert_equal %w[command contract errors ok result_version summary], payload.keys.sort
    assert_equal false, payload.fetch("ok")
    assert_equal @last_command, payload.fetch("command")
    assert_equal "context-candidate/v0.1", payload.fetch("contract")
    assert_equal DECISION_RESULT_VERSION, payload.fetch("result_version")
    assert_equal({"status" => "failed", "error_count" => 1}, payload.fetch("summary"))
    assert_equal 1, payload.fetch("errors").length
    assert_equal %w[code field], payload.fetch("errors").first.keys.sort
    assert_equal code, payload.fetch("errors").first.fetch("code")
    assert_equal "", @last_stderr
    assert_equal payload, JSON.parse(@last_stdout)
    derived = @last_candidate_sensitive_values
    assert_equal 3, derived.length
    assert derived.all? { |value| value.is_a?(String) && !value.empty? }
    (derived + sensitive_values + @last_sensitive_values).uniq.each do |sensitive|
      refute_includes @last_stdout, sensitive
    end
  end

  def repo_fingerprint
    %w[status diff].map do |operation|
      args = operation == "status" ? ["status", "--porcelain=v1"] : ["diff", "--binary"]
      stdout, stderr, status = Open3.capture3("git", *args, chdir: ROOT.to_s)
      assert status.success?, stderr
      stdout.b
    end
  end

  def receipt(root, suffix)
    root.join(".kb/candidate-decisions/#{CANDIDATE_ID}.#{suffix}.json")
  end

  def decision_claim(root)
    root.join(".kb/candidate-decisions/#{CANDIDATE_ID}.decision.json")
  end

  def assert_rfc3339(value)
    parsed = Time.iso8601(value)
    refute_nil parsed.utc_offset
  rescue ArgumentError
    flunk "expected RFC3339 timestamp, got #{value.inspect}"
  end

  def assert_redacted_receipt(path)
    raw = path.read
    refute_includes raw, CONTENT
    refute_includes raw, SOURCE_REF
    refute_includes raw, TARGET
    JSON.parse(raw)
  end


  def assert_exact_receipt(receipt_payload, expected)
    assert_equal expected.keys.sort, receipt_payload.keys.sort
    expected.each do |key, value|
      value.nil? ? assert_nil(receipt_payload.fetch(key), key) : assert_equal(value, receipt_payload.fetch(key), key)
    end
    %w[content source_ref target path].each { |key| refute receipt_payload.key?(key), key }
  end

  def test_review_is_deterministic_read_only_and_redacts_source_ref_by_default
    with_isolated_candidate do |candidate_root, candidate_path|
      home = candidate_root.parent.join("home")
      temporary = candidate_root.parent.join("tmp")
      home.mkpath
      temporary.mkpath
      isolated_env = {
        "HOME" => home.to_s,
        "TMPDIR" => temporary.to_s,
        "PYTHONDONTWRITEBYTECODE" => "1"
      }
      before = tree_snapshot(candidate_root)
      home_before = tree_snapshot(home)
      temporary_before = tree_snapshot(temporary)
      repo_before = repo_fingerprint
      first, first_stdout, first_stderr, first_status = command(
        "review", candidate_path, env: isolated_env
      )
      second, second_stdout, second_stderr, second_status = command(
        "review", candidate_path, env: isolated_env
      )

      assert first_status.success?
      assert second_status.success?
      assert_equal first, second
      assert_equal first_stdout.b, second_stdout.b
      assert_equal before, tree_snapshot(candidate_root)
      assert_equal home_before, tree_snapshot(home)
      assert_equal temporary_before, tree_snapshot(temporary)
      assert_equal repo_before, repo_fingerprint
      assert_equal %w[
        candidate_id candidate_sha256 command content contract errors ok provenance
        result_version storage_class summary target
      ].sort, first.keys.sort
      assert_equal %w[error_count status], first.fetch("summary").keys.sort
      assert_equal %w[kind path], first.fetch("target").keys.sort
      assert_equal %w[observed_at source_ref_sha256 source_type], first.fetch("provenance").keys.sort
      assert_equal %w[media_type text], first.fetch("content").keys.sort
      assert_equal "reviewable", first.dig("summary", "status")
      assert_equal CANDIDATE_ID, first.fetch("candidate_id")
      assert_equal review_digest(candidate_path), first.fetch("candidate_sha256")
      assert_equal "git_tracked", first.fetch("storage_class")
      assert_equal({"kind" => "experience", "path" => TARGET}, first.fetch("target"))
      assert_equal "repository_document", first.dig("provenance", "source_type")
      assert_equal "2026-07-27T09:55:00+08:00", first.dig("provenance", "observed_at")
      assert_equal Digest::SHA256.hexdigest(SOURCE_REF), first.dig("provenance", "source_ref_sha256")
      refute first.fetch("provenance").key?("source_ref")
      assert_equal "text/markdown", first.dig("content", "media_type")
      assert_equal CONTENT, first.dig("content", "text")
      assert_equal "", first_stderr
      assert_equal "", second_stderr
    end
  end

  def test_review_discloses_source_ref_only_when_explicitly_requested
    payload, _stdout, stderr, status = review(fixture, "--include-source-ref")

    assert status.success?
    assert_equal %w[
      candidate_id candidate_sha256 command content contract errors ok provenance
      result_version storage_class summary target
    ].sort, payload.keys.sort
    assert_equal %w[observed_at source_ref source_ref_sha256 source_type], payload.fetch("provenance").keys.sort
    assert_equal SOURCE_REF, payload.dig("provenance", "source_ref")
    assert_equal "", stderr
  end

  def test_invalid_review_remains_redacted
    path = CONTRACT_FIXTURES.join("invalid/content-as-instructions.json")
    payload, _stdout, _stderr, status = review(path)

    assert_failed payload, status, "GW_CANDIDATE_CONTENT_NOT_DATA"
  end

  def test_accept_rejects_confirmation_and_review_digest_mismatch_without_writes
    with_kb do |kb|
      before = tree_snapshot(kb)
      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb, confirm: "cand_wrong"))
      assert_failed payload, status, "GW_CANDIDATE_CONFIRMATION_MISMATCH"
      assert_equal before, tree_snapshot(kb)

      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb, digest: "0" * 64))
      assert_failed payload, status, "GW_CANDIDATE_REVIEW_MISMATCH"
      assert_equal before, tree_snapshot(kb)
    end
  end

  def test_accept_binds_exact_candidate_bytes
    Dir.mktmpdir("gw-candidate-mutated-") do |directory|
      changed = Pathname(directory).join("candidate.json")
      changed.write(fixture.read.sub(CONTENT, "Changed after review."))
      with_kb do |kb|
        payload, _stdout, _stderr, status = command(
          *accept_args(changed, kb, digest: review_digest(fixture))
        )
        assert_failed payload, status, "GW_CANDIDATE_REVIEW_MISMATCH"
        refute kb.join(TARGET).exist?
      end
    end
  end

  def test_accept_requires_complete_authorization_tuple
    with_kb do |kb|
      base = accept_args(fixture, kb)
      required = {
        "--authorization-basis" => "GW_CANDIDATE_AUTHORIZATION_REQUIRED",
        "--retention-until" => "GW_CANDIDATE_AUTHORIZATION_REQUIRED",
        "--attest-no-consent-required-data" => "GW_CANDIDATE_AUTHORIZATION_REQUIRED",
        "--ack-git-history" => "GW_CANDIDATE_AUTHORIZATION_REQUIRED"
      }
      required.each do |flag, code|
        args = base.dup
        index = args.index(flag)
        args.slice!(index, flag.start_with?("--attest", "--ack") ? 1 : 2)
        before = tree_snapshot(kb)
        payload, _stdout, _stderr, status = command(*args)
        assert_failed payload, status, code
        assert_equal before, tree_snapshot(kb)
      end
    end
  end

  def test_accept_rejects_non_git_storage_classes
    Dir.mktmpdir("gw-storage-classes-") do |directory|
      local_private = Pathname(directory).join("local-private.json")
      local_document = JSON.parse(fixture("local-private.json").read)
      local_document["expires_at"] = nil
      local_private.write(JSON.generate(local_document))
      [local_private, FIXTURES.join("ephemeral.json")].each do |path|
        with_kb do |kb|
          candidate_id = JSON.parse(path.read).fetch("candidate_id")
          args = accept_args(path, kb, confirm: candidate_id)
          before = tree_snapshot(kb)
          payload, _stdout, _stderr, status = command(*args)
          assert_failed payload, status, "GW_CANDIDATE_STORAGE_UNSUPPORTED"
          assert_equal before, tree_snapshot(kb)
        end
      end
    end
  end

  def test_accept_writes_exact_content_and_redacted_receipts_once
    with_kb do |kb|
      payload, _stdout, stderr, status = command(*accept_args(fixture, kb))

      assert status.success?
      assert_equal "applied", payload.dig("summary", "status")
      assert_equal CONTENT, kb.join(TARGET).binread
      claim = assert_redacted_receipt(decision_claim(kb))
      authorized = assert_redacted_receipt(receipt(kb, "authorized"))
      applied = assert_redacted_receipt(receipt(kb, "applied"))
      decided_at = claim.fetch("decided_at")
      assert_rfc3339(decided_at)
      assert_exact_receipt claim, {
        "record_version" => "gw-candidate-decision/v0.1",
        "candidate_id" => CANDIDATE_ID,
        "decision" => "accept",
        "decided_at" => decided_at,
        "candidate_sha256" => review_digest(fixture)
      }
      accepted_values = {
        "record_version" => "gw-candidate-decision/v0.1",
        "candidate_id" => CANDIDATE_ID,
        "decided_at" => decided_at,
        "candidate_sha256" => review_digest(fixture),
        "target_sha256" => Digest::SHA256.hexdigest(CONTENT),
        "authorization_basis" => "self_context",
        "authorization_scope" => "store",
        "retention_until" => nil,
        "revoked_at" => nil,
        "no_consent_required_data_attested" => true,
        "git_history_acknowledged" => true
      }
      assert_exact_receipt authorized, accepted_values.merge("decision" => "authorized")
      assert_exact_receipt applied, accepted_values.merge("decision" => "applied")
      assert_equal "", stderr

      retry_payload, _stdout, _stderr, retry_status = command(*accept_args(fixture, kb))
      assert_failed retry_payload, retry_status, "GW_CANDIDATE_CONFLICT"
      assert_equal CONTENT, kb.join(TARGET).binread
    end
  end

  def test_reject_writes_only_each_controlled_redacted_reason_receipt
    %w[duplicate incorrect not_relevant privacy other].each do |reason|
      with_kb do |kb|
        payload, _stdout, stderr, status = command(*reject_args(fixture, kb, reason: reason))

        assert status.success?
        assert_equal "rejected", payload.dig("summary", "status")
        refute kb.join(TARGET).exist?
        claim = assert_redacted_receipt(decision_claim(kb))
        rejected = assert_redacted_receipt(receipt(kb, "rejected"))
        decided_at = claim.fetch("decided_at")
        assert_rfc3339(decided_at)
        assert_exact_receipt claim, {
          "record_version" => "gw-candidate-decision/v0.1",
          "candidate_id" => CANDIDATE_ID,
          "decision" => "reject",
          "decided_at" => decided_at,
          "candidate_sha256" => review_digest(fixture)
        }
        assert_exact_receipt rejected, {
          "record_version" => "gw-candidate-decision/v0.1",
          "candidate_id" => CANDIDATE_ID,
          "decision" => "rejected",
          "decided_at" => decided_at,
          "candidate_sha256" => review_digest(fixture),
          "reason" => reason
        }
        assert_equal "", stderr
      end
    end
  end

  def test_reject_rejects_free_form_reason_and_digest_mismatch
    with_kb do |kb|
      payload, _stdout, _stderr, status = command(*reject_args(fixture, kb, reason: "private details"))
      assert_failed(
        payload,
        status,
        "GW_CANDIDATE_REASON_INVALID",
        sensitive_values: ["private details"]
      )
      payload, _stdout, _stderr, status = command(*reject_args(fixture, kb, digest: "f" * 64))
      assert_failed payload, status, "GW_CANDIDATE_REVIEW_MISMATCH"
      refute receipt(kb, "rejected").exist?
    end
  end

  def test_authorization_basis_and_retention_are_validated
    with_kb do |kb|
      payload, _stdout, _stderr, status = command(
        *accept_args(fixture, kb, basis: "third_party_consent")
      )
      assert_failed payload, status, "GW_CANDIDATE_AUTHORIZATION_REQUIRED"
      payload, _stdout, _stderr, status = command(
        *accept_args(fixture, kb, retention: "2026-07-28")
      )
      assert_failed payload, status, "GW_CANDIDATE_AUTHORIZATION_REQUIRED"
      refute kb.join(TARGET).exist?
    end
  end

  def test_public_source_authorization_is_accepted_and_recorded
    with_kb do |kb|
      payload, _stdout, _stderr, status = command(
        *accept_args(fixture, kb, basis: "public_source", retention: "2027-07-27T12:05:00Z")
      )

      assert status.success?
      assert_equal "applied", payload.dig("summary", "status")
      authorized = assert_redacted_receipt(receipt(kb, "authorized"))
      assert_equal "public_source", authorized.fetch("authorization_basis")
      assert_equal "2027-07-27T12:05:00Z", authorized.fetch("retention_until")
    end
  end

  def test_reject_binds_candidate_id_and_exact_reviewed_bytes
    with_kb do |kb|
      payload, _stdout, _stderr, status = command(
        *reject_args(fixture, kb, confirm: "cand_wrong")
      )
      assert_failed payload, status, "GW_CANDIDATE_CONFIRMATION_MISMATCH"
      refute receipt(kb, "rejected").exist?
    end

    Dir.mktmpdir("gw-reject-mutated-") do |directory|
      changed = Pathname(directory).join("candidate.json")
      changed.write(fixture.read.sub(CONTENT, "Changed after review."))
      with_kb do |kb|
        payload, _stdout, _stderr, status = command(
          *reject_args(changed, kb, digest: review_digest(fixture))
        )
        assert_failed payload, status, "GW_CANDIDATE_REVIEW_MISMATCH"
        refute receipt(kb, "rejected").exist?
      end
    end
  end

  def test_symlinked_kb_components_fail_closed_for_accept_and_reject
    %i[root kb decisions].each do |component|
      %i[accept reject].each do |decision|
        Dir.mktmpdir("gw-symlink-kb-") do |directory|
          base = Pathname(directory)
          external = base.join("external")
          external.mkpath
          case component
          when :root
            external_root = external.join("kb")
            initialize_kb(external_root)
            kb = base.join("kb-link")
            symlink_or_skip(kb, external_root)
          when :kb
            kb = base.join("kb")
            kb.join("wiki/methods").mkpath
            external_kb = external.join(".kb")
            external_kb.join("candidate-decisions").mkpath
            external_kb.join("goldenwave.json").write(
              JSON.generate({"format_version" => "gwkb/v0.1", "version" => "0.1.0"})
            )
            symlink_or_skip(kb.join(".kb"), external_kb)
          when :decisions
            kb = base.join("kb")
            initialize_kb(kb)
            kb.join(".kb/candidate-decisions").rmdir
            external_decisions = external.join("candidate-decisions")
            external_decisions.mkpath
            symlink_or_skip(kb.join(".kb/candidate-decisions"), external_decisions)
          end
          external_before = tree_snapshot(external)
          args = decision == :accept ? accept_args(fixture, kb) : reject_args(fixture, kb)
          payload, _stdout, _stderr, status = command(*args)

          assert_failed payload, status, "GW_CANDIDATE_KB_UNSAFE"
          assert_equal external_before, tree_snapshot(external)
          refute kb.join(TARGET).exist? unless component == :root
        end
      end
    end
  end

  def test_unsafe_kb_marker_and_symlink_parent_fail_closed
    with_kb do |kb|
      kb.join(".kb/goldenwave.json").write("not-json")
      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb))
      assert_failed payload, status, "GW_CANDIDATE_KB_UNSAFE"
    end

    with_kb do |kb|
      outside = Pathname(Dir.mktmpdir("gw-outside-"))
      kb.join("wiki/methods").rmdir
      symlink_or_skip(kb.join("wiki/methods"), outside)
      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb))
      assert_failed payload, status, "GW_CANDIDATE_TARGET_UNSAFE"
      refute outside.join("candidate-validation.md").exist?
    ensure
      outside&.rmtree if outside&.exist?
    end
  end

  def test_missing_kb_marker_fails_closed_for_accept_and_reject
    %i[accept reject].each do |decision|
      with_kb do |kb|
        kb.join(".kb/goldenwave.json").delete
        before = tree_snapshot(kb)
        args = decision == :accept ? accept_args(fixture, kb) : reject_args(fixture, kb)
        payload, _stdout, _stderr, status = command(*args)

        assert_failed payload, status, "GW_CANDIDATE_KB_UNSAFE"
        assert_equal before, tree_snapshot(kb)
        refute kb.join(TARGET).exist?
        assert_empty kb.join(".kb/candidate-decisions").children
      end
    end
  end

  def test_target_traversal_and_missing_decision_directory_fail_closed
    Dir.mktmpdir("gw-candidate-traversal-") do |directory|
      unsafe = Pathname(directory).join("candidate.json")
      unsafe.write(fixture.read.sub(TARGET, "wiki/methods/../../escaped.md"))
      with_kb do |kb|
        candidate_digest = Digest::SHA256.file(unsafe).hexdigest
        payload, _stdout, _stderr, status = command(
          *accept_args(unsafe, kb, digest: candidate_digest)
        )
        assert_failed payload, status, "GW_CANDIDATE_TARGET_UNSAFE"
        refute kb.parent.join("escaped.md").exist?
      end
    end

    with_kb do |kb|
      kb.join(".kb/candidate-decisions").rmdir
      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb))
      assert_failed payload, status, "GW_CANDIDATE_KB_UNSAFE"
      refute kb.join(TARGET).exist?
    end
  end

  def test_existing_target_receipt_and_hardlink_are_never_overwritten
    with_kb do |kb|
      target = kb.join(TARGET)
      target.write("existing")
      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb))
      assert_failed payload, status, "GW_CANDIDATE_CONFLICT"
      assert_equal "existing", target.read
    end

    with_kb do |kb|
      source = kb.join("existing-receipt")
      source.write("linked")
      hardlink_or_skip(source, receipt(kb, "authorized"))
      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb))
      assert_failed payload, status, "GW_CANDIDATE_CONFLICT"
      assert_equal "linked", source.read
    end


    with_kb do |kb|
      receipt(kb, "authorized").write("{partial")
      payload, _stdout, _stderr, status = command(*accept_args(fixture, kb))
      assert_failed payload, status, "GW_CANDIDATE_CONFLICT"
      assert_equal "{partial", receipt(kb, "authorized").read
    end
  end

  def test_cli_missing_required_flags_returns_argument_invalid_json
    assert_argument_invalid(["accept", fixture], "accept")
  end

  def test_cli_invalid_authorization_basis_returns_argument_invalid_json
    with_kb do |kb|
      invalid_basis = accept_args(fixture, kb)
      invalid_basis[invalid_basis.index("self_context")] = "third_party_secret_basis"
      assert_argument_invalid(
        invalid_basis,
        "accept",
        expected_code: "GW_CANDIDATE_AUTHORIZATION_REQUIRED",
        expected_field: "authorization",
        extra_forbidden: ["third_party_secret_basis"]
      )
    end
  end

  def test_cli_invalid_retention_returns_argument_invalid_json
    with_kb do |kb|
      invalid_retention = accept_args(fixture, kb)
      invalid_retention[invalid_retention.index("none")] = "not-a-retention-time"
      assert_argument_invalid(
        invalid_retention,
        "accept",
        expected_code: "GW_CANDIDATE_AUTHORIZATION_REQUIRED",
        expected_field: "authorization",
        extra_forbidden: ["not-a-retention-time"]
      )
    end
  end

  def test_cli_invalid_reject_reason_returns_argument_invalid_json
    with_kb do |kb|
      assert_argument_invalid(
        reject_args(fixture, kb, reason: "private free form reason"),
        "reject",
        expected_code: "GW_CANDIDATE_REASON_INVALID",
        expected_field: "reason",
        extra_forbidden: ["private free form reason"]
      )
    end
  end

  def test_cli_unknown_command_returns_argument_invalid_json
    assert_argument_invalid(
      ["unknown-secret-command", fixture],
      "invalid",
      extra_forbidden: ["unknown-secret-command"]
    )
  end

  def test_cli_unknown_option_returns_argument_invalid_json
    assert_argument_invalid(
      ["review", fixture, "--secret-option", "/Users/private/value"],
      "review",
      extra_forbidden: ["--secret-option", "/Users/private/value"]
    )
  end

  def test_review_rejects_removed_now_option
    assert_argument_invalid(
      ["review", fixture, "--now", NOW],
      "review",
      extra_forbidden: [NOW]
    )
  end

  def test_accept_rejects_backdated_now_bypass_option
    with_kb do |kb|
      args = accept_args(fixture, kb) + ["--now", "2000-01-01T00:00:00Z"]
      assert_argument_invalid(
        args,
        "accept",
        extra_forbidden: ["2000-01-01T00:00:00Z"]
      )
    end
  end

  def test_reject_rejects_removed_now_option
    with_kb do |kb|
      args = reject_args(fixture, kb) + ["--now", NOW]
      assert_argument_invalid(args, "reject", extra_forbidden: [NOW])
    end
  end

  def test_help_is_structured_deterministic_json
    first_stdout, first_stderr, first_status = raw_cli("--help")
    second_stdout, second_stderr, second_status = raw_cli("--help")
    payload = JSON.parse(first_stdout)

    assert first_status.success?
    assert second_status.success?
    assert_equal first_stdout.b, second_stdout.b
    assert_equal "", first_stderr
    assert_equal "", second_stderr
    assert_equal true, payload.fetch("ok")
    assert_equal "help", payload.fetch("command")
    assert_equal DECISION_RESULT_VERSION, payload.fetch("result_version")
    assert_equal "context-candidate/v0.1", payload.fetch("contract")
    assert_equal({"status" => "help", "error_count" => 0}, payload.fetch("summary"))
    assert_equal [], payload.fetch("errors")
    assert_equal %w[
      validate review accept reject inject-review inject-apply inject-recover
      inject-backup inject-restore
    ], payload.fetch("available_commands")
    assert_equal %w[available_commands command contract errors ok result_version summary], payload.keys.sort
  rescue JSON::ParserError => error
    flunk "help must be structured JSON: #{error.message}\nSTDOUT:\n#{first_stdout}\nSTDERR:\n#{first_stderr}"
  end

  def test_target_paths_reject_bidi_controls_and_non_nfc_but_allow_nfc_chinese
    Dir.mktmpdir("gw-target-unicode-") do |directory|
      root = Pathname(directory)
      bidi_codepoints = [0x061C, 0x200E, 0x200F, *0x202A..0x202E, *0x2066..0x2069]
      invalid_paths = bidi_codepoints.map do |codepoint|
        "wiki/methods/bidi-#{[codepoint].pack('U')}-target.md"
      end
      invalid_paths << "wiki/methods/cafe\u0301.md"
      results = invalid_paths.each_with_index.map do |target_path, index|
        path = root.join("invalid-#{index}.json")
        document = JSON.parse(fixture.read)
        document.fetch("target")["path"] = target_path
        path.write(JSON.generate(document))
        payload, _stdout, stderr, status = command("review", path)
        [target_path, payload, stderr, status]
      end

      results.each do |target_path, payload, stderr, status|
        refute status.success?, target_path.inspect
        assert_equal "", stderr
        assert_equal "failed", payload.dig("summary", "status")
        assert_includes payload.fetch("errors").map { |item| item.fetch("code") }, "GW_CANDIDATE_TARGET_UNSAFE"
      end

      valid_path = root.join("valid-chinese.json")
      valid_document = JSON.parse(fixture.read)
      valid_document.fetch("target")["path"] = "wiki/methods/候选验证.md"
      valid_path.write(JSON.generate(valid_document))
      payload, _stdout, stderr, status = command("review", valid_path)
      assert status.success?
      assert_equal "", stderr
      assert_equal "wiki/methods/候选验证.md", payload.dig("target", "path")
    end
  end

  def test_review_emits_utf8_json_when_stdio_encoding_is_ascii
    Dir.mktmpdir("gw-candidate-chinese-") do |directory|
      path = Pathname(directory).join("candidate.json")
      document = JSON.parse(fixture.read)
      document.fetch("content")["text"] = "候选内容必须保持 UTF-8。"
      path.binwrite(JSON.generate(document))

      stdout, stderr, status = raw_cli(
        "review", path,
        env: {"PYTHONIOENCODING" => "ascii"}
      )
      payload = JSON.parse(stdout.dup.force_encoding("UTF-8"))

      assert status.success?
      assert_equal "", stderr
      assert_equal "候选内容必须保持 UTF-8。", payload.dig("content", "text")
      assert stdout.dup.force_encoding("UTF-8").valid_encoding?
    end
  rescue JSON::ParserError => error
    flunk "review must emit UTF-8 JSON under ASCII stdio: #{error.message}"
  end

  def test_lone_surrogate_fails_closed_for_review_and_accept_without_traceback
    Dir.mktmpdir("gw-candidate-surrogate-") do |directory|
      path = Pathname(directory).join("candidate.json")
      path.binwrite(fixture.read.sub(CONTENT, "\\uD800"))

      review_stdout, review_stderr, review_status = raw_cli("review", path)
      review_payload = JSON.parse(review_stdout)
      refute review_status.success?
      assert_equal "", review_stderr
      assert_equal "failed", review_payload.dig("summary", "status")
      assert_equal ["GW_CANDIDATE_DOCUMENT_INVALID"], review_payload.fetch("errors").map { |item| item.fetch("code") }
      refute_includes review_stdout, path.to_s
      refute_includes review_stderr, "Traceback"

      with_kb do |kb|
        accept_stdout, accept_stderr, accept_status = raw_cli(*accept_args(path, kb))
        accept_payload = JSON.parse(accept_stdout)
        refute accept_status.success?
        assert_equal "", accept_stderr
        assert_equal "failed", accept_payload.dig("summary", "status")
        assert_equal ["GW_CANDIDATE_DOCUMENT_INVALID"], accept_payload.fetch("errors").map { |item| item.fetch("code") }
        refute_includes accept_stdout, path.to_s
        refute_includes accept_stderr, "Traceback"
        refute kb.join(TARGET).exist?
      end
    end
  rescue JSON::ParserError => error
    flunk "lone surrogate failures must remain structured JSON: #{error.message}"
  end

  def test_clean_copied_cli_review_creates_no_python_bytecode
    Dir.mktmpdir("gw-candidate-clean-copy-") do |directory|
      clean = Pathname(directory)
      copy_tree_without_bytecode(ROOT.join("scripts"), clean.join("scripts"))
      copy_tree_without_bytecode(ROOT.join("contracts"), clean.join("contracts"))
      candidate = clean.join("candidate.json")
      candidate.binwrite(fixture.binread)
      entry = clean.join("scripts/goldenwave_candidate.py")

      stdout, stderr, status = raw_cli(
        "review", candidate,
        env: {"PYTHONDONTWRITEBYTECODE" => nil, "PYTHONPATH" => nil},
        entry: entry,
        chdir: clean
      )

      assert status.success?, "clean copied review failed\nSTDOUT:\n#{stdout}\nSTDERR:\n#{stderr}"
      assert_equal "", stderr
      JSON.parse(stdout)
      assert_equal [], clean.glob("**/__pycache__")
      assert_equal [], clean.glob("**/*.pyc")
    end
  end
end
