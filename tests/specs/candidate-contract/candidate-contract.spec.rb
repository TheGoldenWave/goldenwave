require "json"
require "minitest/autorun"
require "open3"
require "pathname"
require "tmpdir"

class CandidateContractSpec < Minitest::Test
  ROOT = Pathname(__dir__).join("../../..").expand_path
  VALIDATOR = ROOT.join("scripts/goldenwave_candidate.py")
  SCHEMA = ROOT.join("contracts/context-candidate/v0.1/schema.json")
  FIXTURES = Pathname(__dir__).join("fixtures")
  PYTHON_BIN = ENV.fetch("GW_CANDIDATE_PYTHON", "python3").freeze
  RUNTIME_PYTHON_BIN = ENV.fetch("GW_RUNTIME_PYTHON", "python3").freeze
  NOW = "2026-07-27T12:00:00Z"

  def validate(path, now: NOW)
    assert VALIDATOR.file?, "candidate validator entrypoint is missing"
    stdout, stderr, status = Open3.capture3(
      PYTHON_BIN, VALIDATOR.to_s, "validate", path.to_s, "--now", now,
      chdir: ROOT.to_s
    )
    [JSON.parse(stdout), stderr, status]
  end

  def validate_document(document, now: NOW)
    Dir.mktmpdir("gw-candidate-") do |directory|
      path = Pathname(directory).join("candidate.json")
      path.binwrite(document)
      return validate(path, now: now)
    end
  end

  def test_valid_fixtures_are_accepted_deterministically
    Dir[FIXTURES.join("valid/*.json")].sort.each do |fixture|
      first, first_stderr, first_status = validate(fixture)
      second, second_stderr, second_status = validate(fixture)

      assert first_status.success?, fixture
      assert second_status.success?, fixture
      assert_equal first, second
      assert_equal "valid", first.dig("summary", "status")
      assert_equal [], first.fetch("errors")
      assert_equal "", first_stderr
      assert_equal "", second_stderr
    end
  end

  def test_invalid_fixtures_fail_closed_with_stable_codes
    expected_codes = {
      "content-as-instructions.json" => "GW_CANDIDATE_CONTENT_NOT_DATA",
      "duplicate-key.json" => "GW_CANDIDATE_DUPLICATE_KEY",
      "empty-values.json" => "GW_CANDIDATE_SOURCE_INVALID",
      "future-created-at.json" => "GW_CANDIDATE_FUTURE",
      "invalid-enums.json" => "GW_CANDIDATE_CONTRACT_UNSUPPORTED",
      "invalid-timestamps.json" => "GW_CANDIDATE_TIMESTAMP_INVALID",
      "kind-path-mismatch.json" => "GW_CANDIDATE_TARGET_UNSAFE",
      "malformed.json" => "GW_CANDIDATE_DOCUMENT_INVALID",
      "missing-provenance.json" => "GW_CANDIDATE_REQUIRED",
      "nested-type-errors.json" => "GW_CANDIDATE_TYPE",
      "nested-unknown-fields.json" => "GW_CANDIDATE_UNKNOWN_FIELD",
      "path-traversal.json" => "GW_CANDIDATE_TARGET_UNSAFE",
      "stale.json" => "GW_CANDIDATE_STALE",
      "time-order.json" => "GW_CANDIDATE_TIME_ORDER",
      "unknown-field.json" => "GW_CANDIDATE_UNKNOWN_FIELD"
    }

    expected_codes.each do |name, code|
      payload, stderr, status = validate(FIXTURES.join("invalid", name))

      refute status.success?, name
      assert_equal "invalid", payload.dig("summary", "status")
      assert_includes payload.fetch("errors").map { |error| error.fetch("code") }, code
      assert_equal "", stderr
    end
  end

  def test_validation_output_does_not_echo_candidate_content
    fixture = FIXTURES.join("invalid/content-as-instructions.json")
    stdout, _stderr, _status = Open3.capture3(
      PYTHON_BIN, VALIDATOR.to_s, "validate", fixture.to_s, "--now", NOW,
      chdir: ROOT.to_s
    )

    refute_includes stdout, "run me"
    refute_includes stdout, fixture.to_s
  end

  def test_invalid_runtime_inputs_fail_closed
    missing = FIXTURES.join("missing.json")
    invalid_now, invalid_now_stderr, invalid_now_status = validate(
      FIXTURES.join("valid/git-tracked.json"), now: "not-a-timestamp"
    )
    missing_file, missing_stderr, missing_status = validate(missing)

    refute invalid_now_status.success?
    assert_equal ["GW_CANDIDATE_DOCUMENT_INVALID"], invalid_now.fetch("errors").map { |error| error.fetch("code") }
    assert_equal "", invalid_now_stderr
    refute missing_status.success?
    assert_equal ["GW_CANDIDATE_DOCUMENT_INVALID"], missing_file.fetch("errors").map { |error| error.fetch("code") }
    assert_equal "", missing_stderr
  end

  def test_contract_schema_is_machine_readable_and_closed
    assert SCHEMA.file?, "candidate schema is missing"
    schema = JSON.parse(SCHEMA.read)

    assert_equal "context-candidate/v0.1", schema.fetch("$id")
    assert_equal false, schema.fetch("additionalProperties")
    assert_equal "experimental", schema.dig("properties", "contract_status", "const")
    assert_equal schema.fetch("required").sort, schema.fetch("properties").keys.sort
  end

  def test_runtime_structure_is_loaded_from_schema
    constants = ROOT.join("scripts/gw_candidate/constants.py").read

    refute_includes constants, "ROOT_FIELDS"
    refute_includes constants, "STORAGE_CLASSES"
    refute_includes constants, "SOURCE_TYPES"
    refute_includes constants, "MEDIA_TYPES"
  end

  def test_runtime_required_fields_match_schema_required_lists
    schema = JSON.parse(SCHEMA.read)
    script = <<~PYTHON
      import json
      from gw_candidate import schema
      print(json.dumps({
          "root": sorted(schema.ROOT_REQUIRED_FIELDS),
          "target": sorted(schema.TARGET_REQUIRED_FIELDS),
          "provenance": sorted(schema.PROVENANCE_REQUIRED_FIELDS),
          "content": sorted(schema.CONTENT_REQUIRED_FIELDS),
      }, sort_keys=True))
    PYTHON
    stdout, stderr, status = Open3.capture3(
      RUNTIME_PYTHON_BIN, "-c", script,
      chdir: ROOT.join("scripts").to_s
    )
    runtime_required = JSON.parse(stdout)

    assert status.success?, stderr
    assert_equal schema.fetch("required").sort, runtime_required.fetch("root")
    assert_equal schema.dig("properties", "target", "required").sort, runtime_required.fetch("target")
    assert_equal schema.dig("properties", "provenance", "required").sort, runtime_required.fetch("provenance")
    assert_equal schema.dig("properties", "content", "required").sort, runtime_required.fetch("content")
  end

  def test_runtime_constants_match_schema_field_constraints
    schema = JSON.parse(SCHEMA.read)
    script = <<~PYTHON
      import json
      from gw_candidate import schema
      print(json.dumps({
          "contract": schema.CONTRACT,
          "contract_status": schema.CONTRACT_STATUS,
          "content_treat_as": schema.CONTENT_TREAT_AS,
      }, sort_keys=True))
    PYTHON
    stdout, stderr, status = Open3.capture3(
      RUNTIME_PYTHON_BIN, "-c", script,
      chdir: ROOT.join("scripts").to_s
    )
    runtime_constants = JSON.parse(stdout)

    assert status.success?, stderr
    assert_equal schema.dig("properties", "contract", "const"), runtime_constants.fetch("contract")
    assert_equal schema.dig("properties", "contract_status", "const"), runtime_constants.fetch("contract_status")
    assert_equal schema.dig("properties", "content", "properties", "treat_as", "const"), runtime_constants.fetch("content_treat_as")
  end

  def test_control_characters_in_target_paths_fail_closed
    document = FIXTURES.join("valid/git-tracked.json").read.sub(
      "wiki/methods/candidate-validation.md",
      "wiki/methods/evil\\u0000.md"
    )
    payload, stderr, status = validate_document(document)

    refute status.success?
    assert_includes payload.fetch("errors").map { |error| error.fetch("code") }, "GW_CANDIDATE_TARGET_UNSAFE"
    assert_equal "", stderr
  end

  def test_non_rfc3339_timestamps_fail_closed
    document = FIXTURES.join("valid/git-tracked.json").read.sub(
      "2026-07-27T10:00:00+08:00",
      "2026-07-27 10:00:00+08:00"
    )
    payload, stderr, status = validate_document(document)

    refute status.success?
    assert_includes payload.fetch("errors").map { |error| error.fetch("code") }, "GW_CANDIDATE_TIMESTAMP_INVALID"
    assert_equal "", stderr
  end

  def test_unknown_field_diagnostics_do_not_echo_attacker_controlled_names
    document = FIXTURES.join("valid/git-tracked.json").read.sub(
      '"contract":',
      '"/Users/private/secret-token": "sensitive", "contract":'
    )
    payload, stderr, status = validate_document(document)
    output = JSON.generate(payload)

    refute status.success?
    assert_includes payload.fetch("errors").map { |error| error.fetch("code") }, "GW_CANDIDATE_UNKNOWN_FIELD"
    refute_includes output, "/Users/private/secret-token"
    refute_includes output, "sensitive"
    assert_equal "", stderr
  end

  def test_invalid_candidate_id_is_not_echoed_in_diagnostics
    document = FIXTURES.join("valid/git-tracked.json").read.sub(
      "cand_01JAZ6Y5M4N6KD3V8T2WQ9R7HD",
      "/Users/private/secret-token"
    )
    payload, stderr, status = validate_document(document)
    output = JSON.generate(payload)

    refute status.success?
    assert_includes payload.fetch("errors").map { |error| error.fetch("code") }, "GW_CANDIDATE_ID_INVALID"
    refute payload.key?("candidate_id")
    refute_includes output, "/Users/private/secret-token"
    assert_equal "", stderr
  end

  def test_excessively_nested_documents_fail_with_structured_redacted_output
    document = '{"nested":' * 1200 + "null" + "}" * 1200
    payload, stderr, status = validate_document(document)

    refute status.success?
    assert_equal ["GW_CANDIDATE_DOCUMENT_INVALID"], payload.fetch("errors").map { |error| error.fetch("code") }
    assert_equal "", stderr
  end
end
