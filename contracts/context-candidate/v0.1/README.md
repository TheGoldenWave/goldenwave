# context-candidate/v0.1

Status: `experimental`

This contract carries proposed context as inert data. Validation never writes to the
Knowledge Base. Review, acceptance, rejection, and injection are separate governed
operations.

## Required envelope

- `contract`: exactly `context-candidate/v0.1`
- `contract_status`: exactly `experimental`
- `candidate_id`: `cand_` plus a 26-character uppercase Crockford identifier
- `created_at`, `expires_at`: timezone-aware RFC 3339 timestamps; `expires_at` may be null
- `storage_class`: `git_tracked`, `local_private`, or `ephemeral`
- `target`: a supported kind and a relative Markdown path under its governed root
- `provenance`: source type, opaque source reference, and observation time
- `content`: `text/markdown` or `text/plain`, always marked `treat_as: data`

All objects are closed: unknown and duplicate fields fail validation. Candidate content
and source references are not included in validator diagnostics.

## Validation

```sh
python3 scripts/goldenwave_candidate.py validate candidate.json --now 2026-07-27T12:00:00Z
```

`--now` is explicit so freshness decisions and fixtures remain deterministic.

## Stable validation codes

- `GW_CANDIDATE_REQUIRED`, `GW_CANDIDATE_UNKNOWN_FIELD`, `GW_CANDIDATE_DUPLICATE_KEY`
- `GW_CANDIDATE_DOCUMENT_INVALID`, `GW_CANDIDATE_CONTRACT_UNSUPPORTED`, `GW_CANDIDATE_STATUS_INVALID`
- `GW_CANDIDATE_ID_INVALID`, `GW_CANDIDATE_ENUM`, `GW_CANDIDATE_TYPE`
- `GW_CANDIDATE_TIMESTAMP_INVALID`, `GW_CANDIDATE_FUTURE`, `GW_CANDIDATE_STALE`, `GW_CANDIDATE_TIME_ORDER`
- `GW_CANDIDATE_TARGET_UNSAFE`, `GW_CANDIDATE_SOURCE_INVALID`
- `GW_CANDIDATE_CONTENT_NOT_DATA`, `GW_CANDIDATE_CONTENT_INVALID`
