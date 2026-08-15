require "json"
require "minitest/autorun"
require "open3"
require "pathname"

class CandidateContractSpec < Minitest::Test
  ROOT = Pathname(__dir__).join("../../..").expand_path
  VALIDATOR = ROOT.join("scripts/goldenwave_candidate.py")
  SCHEMA = ROOT.join("contracts/context-candidate/v0.1/schema.json")
  FIXTURES = Pathname(__dir__).join("fixtures")
  PYTHON_BIN = ENV.fetch("GW_CANDIDATE_PYTHON", "python3").freeze
  NOW = "2026-07-27T12:00:00Z"

  def validate(path, now: NOW)
    assert VALIDATOR.file?, "candidate validator entrypoint is missing"
    stdout, stderr, status = Open3.capture3(
      PYTHON_BIN, VALIDATOR.to_s, "validate", path.to_s, "--now", now,
      chdir: ROOT.to_s
    )
    [JSON.parse(stdout), stderr, status]
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
end
