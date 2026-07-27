#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "find"
require "json"
require "open3"
require "pathname"

target = Pathname.new(ARGV.fetch(0)).expand_path
entry = Pathname.new(ARGV.fetch(1)).expand_path
python = ARGV.fetch(2)

def metadata_digest(root)
  rows = []
  root.find do |path|
    relative = path.relative_path_from(root).to_s
    if relative == ".git"
      Find.prune
    elsif relative != "."
      stat = path.lstat
      rows << [relative, stat.ftype, stat.mode, stat.size, stat.mtime.to_i, stat.mtime.nsec].join("\0")
    end
  end
  Digest::SHA256.hexdigest(rows.sort.join("\n"))
end

def git_state_digest(root)
  stdout, status = Open3.capture2("git", "-C", root.to_s, "status", "--porcelain=v1", "-z")
  raise "git status failed" unless status.success?

  Digest::SHA256.hexdigest(stdout)
end

def finding_counts(payload)
  payload.fetch("findings").each_with_object(Hash.new(0)) do |item, counts|
    counts[item.fetch("code")] += 1
  end
end

before = {
  "metadata" => metadata_digest(target),
  "git_status" => git_state_digest(target)
}

doctor_stdout, doctor_stderr, doctor_status = Open3.capture3(
  python, entry.to_s, "doctor", "--target", target.to_s, "--format", "json"
)
adopt_stdout, adopt_stderr, adopt_status = Open3.capture3(
  python, entry.to_s, "adopt", "inventory", "--target", target.to_s, "--format", "json"
)

after = {
  "metadata" => metadata_digest(target),
  "git_status" => git_state_digest(target)
}

doctor = JSON.parse(doctor_stdout)
adopt = JSON.parse(adopt_stdout)
puts JSON.generate(
  "unchanged" => before == after,
  "doctor_exit" => doctor_status.exitstatus,
  "doctor_ok" => doctor.fetch("ok"),
  "doctor_findings" => finding_counts(doctor),
  "adopt_exit" => adopt_status.exitstatus,
  "adopt_ok" => adopt.fetch("ok"),
  "adopt_findings" => finding_counts(adopt),
  "stderr_empty" => doctor_stderr.empty? && adopt_stderr.empty?
)
