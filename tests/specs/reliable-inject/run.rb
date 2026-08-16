#!/usr/bin/env ruby

repo = File.expand_path("../../..", __dir__)
python = ENV.fetch("GW_CANDIDATE_PYTHON", "python3")
test = File.join(__dir__, "test_reliable.py")
exec(python, test, chdir: repo)
