"""Static contracts for GoldenWave init."""

from __future__ import annotations

from pathlib import Path

RESULT_VERSION = "gw-init/v1"
INITIALIZER_VERSION = "0.1.0"
FORMAT_VERSION = "gwkb/v0.1"
SUPPORTED_RUNTIME = (3, 11)

COMMAND_PLAN = "plan"
COMMAND_APPLY = "apply"
COMMAND_DOCTOR = "doctor"
COMMAND_ADOPT_INVENTORY = "adopt inventory"

GIT_MODE_OFF = "off"
GIT_MODE_INIT = "init"

WIKI_TYPES = {
    "entities": "entity",
    "concepts": "concept",
    "methods": "method",
    "guides": "guide",
    "projects": "project",
    "syntheses": "synthesis",
    "comparisons": "comparison",
    "insights": "insight",
}

PROFILE_DOMAINS = [
    "01-body-health",
    "02-finance",
    "03-consumption",
    "04-social",
    "05-time-energy",
    "06-digital-legal",
    "07-spatial",
    "08-skills",
    "09-career-assets",
]

SOCIAL_INDEX_DIRS = [
    "people",
    "collectives",
    "relationships",
    "affiliations",
    "interactions",
    "commitments",
]

PERSONA_FILES = [
    "index.md",
    "expression-dna.md",
    "traits.md",
    "decision-style.md",
    "voice-samples.md",
]

MANAGED_FILES = [
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "INDEX.md",
    "kb-schema.md",
    "glossary.md",
    "wiki/index.md",
    *[f"wiki/{name}/index.md" for name in WIKI_TYPES],
    "profile/INDEX.md",
    "profile/kb-schema.md",
    "profile/console/agent-contract.md",
]

REQUIRED_DIRS = [
    ".kb",
    ".private",
    ".private/social",
    ".ephemeral",
    "projects",
    "inbox",
    "inbox/_pending",
    ".sources",
    "wiki",
    *[f"wiki/{name}" for name in WIKI_TYPES],
    "profile",
    "profile/console",
    "profile/persona",
    *[f"profile/{name}" for name in PROFILE_DOMAINS],
    *[f"profile/04-social/{name}" for name in SOCIAL_INDEX_DIRS],
]

REQUIRED_FILES = [
    *MANAGED_FILES,
    "profile/console/me.md",
    *[f"profile/persona/{name}" for name in PERSONA_FILES],
    ".kb/log.md",
    ".kb/goldenwave.json",
]

FRONTMATTER_FILES = [
    relative
    for relative in REQUIRED_FILES
    if relative.endswith(".md") and relative not in {"AGENTS.md", "CLAUDE.md", ".kb/log.md"}
]

IGNORE_RULES = [
    ".private/",
    ".ephemeral/",
    ".DS_Store",
    "Thumbs.db",
]

PRIVATE_SENTINEL = ".private/.gw-doctor-probe"
EPHEMERAL_SENTINEL = ".ephemeral/.gw-doctor-probe"

UNSAFE_CODES = {
    "root": "GW_TARGET_UNSAFE",
    "home": "GW_TARGET_UNSAFE",
    "repo": "GW_TARGET_UNSAFE",
    "symlink": "GW_TARGET_UNSAFE",
    "not_empty": "GW_TARGET_NOT_EMPTY",
    "changed": "GW_TARGET_CHANGED",
}

SKILL_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = SKILL_ROOT / "assets" / "kb-template"
REPO_ROOT = Path(__file__).resolve().parents[4]
