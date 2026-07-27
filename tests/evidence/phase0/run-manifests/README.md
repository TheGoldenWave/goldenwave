# Phase 0 Run Manifests

This directory is the only repository location allowed for `p0-baseline-preflight.rb --runs`.

Allowed content:

- non-sensitive run metadata needed to validate baseline manifest structure
- `run_id` values and scorecard-shape metadata only

Forbidden content:

- raw model or agent outputs
- owner values or owner confirmation fixtures
- `local_private` or `ephemeral` payload copies
- L3 or private body text
- quarantined `.invalid` artifacts
