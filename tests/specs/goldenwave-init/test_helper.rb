#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "fileutils"
require "find"
require "json"
require "minitest/autorun"
require "open3"
require "pathname"
require "tmpdir"

module GoldenwaveInitTestHelper
  ROOT = Pathname.new(__dir__).join("..", "..", "..").expand_path.freeze
  SCRIPT_PATH = ROOT.join("skills", "goldenwave-init", "scripts", "goldenwave_init.py").freeze
  PYTHON_BIN = ENV.fetch("GW_INIT_PYTHON", "python3.11").freeze
  FORMAT_VERSION = "gwkb/v0.1"
  RESULT_VERSION = "gw-init/v1"
  WIKI_TYPES = {
    "entities" => "entity",
    "concepts" => "concept",
    "methods" => "method",
    "guides" => "guide",
    "projects" => "project",
    "syntheses" => "synthesis",
    "comparisons" => "comparison",
    "insights" => "insight"
  }.freeze
  PROFILE_DOMAINS = %w[
    01-body-health
    02-finance
    03-consumption
    04-social
    05-time-energy
    06-digital-legal
    07-spatial
    08-skills
    09-career-assets
  ].freeze
  PERSONA_FILES = %w[
    index.md
    expression-dna.md
    traits.md
    decision-style.md
    voice-samples.md
  ].freeze
  SOCIAL_INDEX_DIRS = %w[
    people
    collectives
    relationships
    affiliations
    interactions
    commitments
  ].freeze
  MANAGED_FILES = %w[
    .gitignore
    AGENTS.md
    CLAUDE.md
    INDEX.md
    kb-schema.md
    glossary.md
    wiki/index.md
    profile/INDEX.md
    profile/kb-schema.md
    profile/console/agent-contract.md
  ].freeze

  def with_workspace(prefix)
    Dir.mktmpdir(prefix) do |dir|
      yield Pathname.new(dir)
    end
  end

  def run_init(*args, chdir: ROOT)
    Open3.capture3(PYTHON_BIN, SCRIPT_PATH.to_s, *args.map(&:to_s), chdir: chdir.to_s)
  end

  def run_git(repo_path, *args)
    Open3.capture3(
      {"GIT_AUTHOR_NAME" => "QA", "GIT_AUTHOR_EMAIL" => "qa@example.invalid",
       "GIT_COMMITTER_NAME" => "QA", "GIT_COMMITTER_EMAIL" => "qa@example.invalid"},
      "git", *args, chdir: repo_path.to_s
    )
  end

  def parse_json!(stdout, stderr)
    if stdout.strip.empty? && stderr.include?(SCRIPT_PATH.to_s)
      flunk("expected JSON on stdout but the init entry is missing\nSTDOUT:\n#{stdout}\nSTDERR:\n#{stderr}")
    end

    JSON.parse(stdout)
  rescue JSON::ParserError => e
    flunk("expected JSON on stdout\nSTDOUT:\n#{stdout}\nSTDERR:\n#{stderr}\n#{e.message}")
  end

  def snapshot_tree(path)
    return {} unless path.exist?

    snapshot = {}
    Find.find(path.to_s) do |entry|
      next if entry == path.to_s

      pathname = Pathname.new(entry)
      relative = pathname.relative_path_from(path).to_s
      snapshot[relative] =
        if pathname.symlink?
          "symlink:#{pathname.readlink}"
        elsif pathname.directory?
          "dir"
        else
          "file:#{Digest::SHA256.hexdigest(pathname.binread)}"
        end
    end
    snapshot
  end

  def assert_relative_path_payload!(payload)
    serialized = JSON.dump(payload)

    refute_match(%r{https?://}, serialized)
    refute_match(%r{/Users/[^/]+}, serialized)
    refute_match(/qa@example\.invalid/, serialized)
  end

  def build_valid_kb(target, format_version: FORMAT_VERSION)
    target.mkpath
    (target / ".kb").mkpath
    (target / ".private" / "social").mkpath
    (target / ".ephemeral").mkpath
    (target / ".private").chmod(0o700)
    (target / ".ephemeral").chmod(0o700)
    (target / "projects").mkpath
    (target / "inbox" / "_pending").mkpath
    (target / ".sources").mkpath

    WIKI_TYPES.each_key { |type| (target / "wiki" / type).mkpath }
    PROFILE_DOMAINS.each { |domain| (target / "profile" / domain).mkpath }
    SOCIAL_INDEX_DIRS.each { |name| (target / "profile" / "04-social" / name).mkpath }
    PERSONA_FILES.each { |name| write_markdown(target / "profile" / "persona" / name, "title" => name) }

    write_markdown(target / "AGENTS.md")
    write_markdown(target / "CLAUDE.md")
    write_markdown(target / "INDEX.md")
    write_markdown(target / "kb-schema.md")
    write_markdown(target / "glossary.md")
    write_markdown(target / "wiki" / "index.md")
    WIKI_TYPES.each do |directory, type|
      write_markdown(target / "wiki" / directory / "index.md", "type" => type)
    end
    write_markdown(target / "profile" / "INDEX.md")
    write_markdown(target / "profile" / "kb-schema.md")
    write_markdown(target / "profile" / "console" / "me.md")
    write_markdown(target / "profile" / "console" / "agent-contract.md", "remote_model" => "deny")
    write_markdown(target / ".kb" / "log.md")
    (target / ".kb" / "reliable-inject").mkpath
    File.write(
      target / ".kb" / "reliable-inject" / "active.json",
      "{\"active_base\":\"base_#{"0" * 64}\",\"manifest\":null,\"version\":\"gw-reliable-inject/v0.1\"}\n"
    )
    File.write(target / ".kb" / "reliable-inject" / "lock", "")
    File.write(target / ".gitignore", ".private/\n.ephemeral/\n.DS_Store\nThumbs.db\n")

    managed_paths = MANAGED_FILES + WIKI_TYPES.each_key.map { |type| "wiki/#{type}/index.md" }
    managed_templates = managed_paths.each_with_object({}) do |relative, acc|
      acc[relative] = digest_for(target / relative)
    end
    manifest = {
      "format_version" => format_version,
      "initializer_version" => "0.1.0",
      "created_at" => "2026-07-27T00:00:00Z",
      "managed_templates" => managed_templates
    }
    write_json(target / ".kb" / "goldenwave.json", manifest)
  end

  def write_markdown(path, frontmatter = {})
    path.parent.mkpath
    body = +"---\n"
    frontmatter.each { |key, value| body << "#{key}: #{value}\n" }
    body << "---\n\nplaceholder\n"
    File.write(path, body)
  end

  def write_json(path, payload)
    path.parent.mkpath
    File.write(path, JSON.pretty_generate(payload) + "\n")
  end

  def digest_for(path)
    "sha256:#{Digest::SHA256.hexdigest(path.binread)}"
  end
end
