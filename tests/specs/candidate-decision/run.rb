require "open3"
require "pathname"

ROOT = Pathname(__dir__).join("../../..").expand_path
ENVIRONMENT = {
  "PYTHONPATH" => ROOT.join("scripts").to_s,
  "PYTHONDONTWRITEBYTECODE" => "1"
}.freeze
COMMANDS = [
  ["ruby", Pathname(__dir__).join("candidate-decision.spec.rb").to_s],
  ["python3", "-m", "unittest", Pathname(__dir__).join("test_safe_write.py").to_s],
  ["python3", "-m", "unittest", Pathname(__dir__).join("test_workflow.py").to_s]
].freeze

failed = COMMANDS.each_with_object([]) do |command, failures|
  stdout, stderr, status = Open3.capture3(ENVIRONMENT, *command, chdir: ROOT.to_s)
  $stdout.write(stdout)
  $stderr.write(stderr)
  failures << command.join(" ") unless status.success?
end

unless failed.empty?
  warn "Candidate Decision suites failed: #{failed.join('; ')}"
  exit 1
end
