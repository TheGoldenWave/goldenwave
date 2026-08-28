"""Structural contract values loaded from the JSON Schema SSOT."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "contracts/context-candidate/v0.1/schema.json"


def _load_schema() -> dict[str, Any]:
    value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("candidate schema must be an object")
    return value


SCHEMA = _load_schema()
PROPERTIES = SCHEMA["properties"]
CONTRACT = PROPERTIES["contract"]["const"]
CONTRACT_STATUS = PROPERTIES["contract_status"]["const"]
CANDIDATE_ID_PATTERN = PROPERTIES["candidate_id"]["pattern"]
ROOT_FIELDS = frozenset(PROPERTIES)
ROOT_REQUIRED_FIELDS = frozenset(SCHEMA["required"])
TARGET_FIELDS = frozenset(PROPERTIES["target"]["properties"])
TARGET_REQUIRED_FIELDS = frozenset(PROPERTIES["target"]["required"])
PROVENANCE_FIELDS = frozenset(PROPERTIES["provenance"]["properties"])
PROVENANCE_REQUIRED_FIELDS = frozenset(PROPERTIES["provenance"]["required"])
CONTENT_FIELDS = frozenset(PROPERTIES["content"]["properties"])
CONTENT_REQUIRED_FIELDS = frozenset(PROPERTIES["content"]["required"])
STORAGE_CLASSES = frozenset(PROPERTIES["storage_class"]["enum"])
SOURCE_TYPES = frozenset(PROPERTIES["provenance"]["properties"]["source_type"]["enum"])
MEDIA_TYPES = frozenset(PROPERTIES["content"]["properties"]["media_type"]["enum"])
CONTENT_TREAT_AS = PROPERTIES["content"]["properties"]["treat_as"]["const"]
