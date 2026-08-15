"""Frozen values for context-candidate/v0.1."""

CONTRACT = "context-candidate/v0.1"
CONTRACT_STATUS = "experimental"
RESULT_VERSION = "gw-candidate-validator/v0.1"

ROOT_FIELDS = {
    "contract",
    "contract_status",
    "candidate_id",
    "created_at",
    "expires_at",
    "storage_class",
    "target",
    "provenance",
    "content",
}
TARGET_FIELDS = {"kind", "path"}
PROVENANCE_FIELDS = {"source_type", "source_ref", "observed_at"}
CONTENT_FIELDS = {"media_type", "treat_as", "text"}

STORAGE_CLASSES = {"git_tracked", "local_private", "ephemeral"}
TARGET_ROOTS = {
    "profile": ("profile/",),
    "knowledge": ("wiki/",),
    "experience": ("wiki/",),
    "project": ("projects/",),
}
SOURCE_TYPES = {
    "user_statement",
    "repository_document",
    "local_document",
    "agent_output",
    "tool_output",
}
MEDIA_TYPES = {"text/markdown", "text/plain"}

CANDIDATE_ID_PATTERN = r"^cand_[0-9A-HJKMNP-TV-Z]{26}$"
