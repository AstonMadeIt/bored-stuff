# Engineering Playbook: Top 1% Change Capture

## Decision Rule

Use git as immutable truth going forward, and reconstruct pre-git using highest-confidence artifacts first.

## Phase 1: Hard Baseline Freeze

1. Hash every file in both source roots.
2. Save baseline manifests in repo.
3. Record timestamp and tooling version.

## Phase 2: Pre-Git Reconstruction

1. Ingest runtime event logs (`router_events.jsonl`).
2. Ingest `world_state.json` and `decision_ledger.json` updates.
3. Ingest both Antigravity thread exports (required for full fidelity).
4. Create normalized events with provenance tier labels.

## Phase 3: Future-Proof Logging

1. Every change via PR/commit only.
2. Every commit linked to timeline event ID.
3. Auto-append commit metadata into `timeline/events.jsonl`.
4. Keep human `timeline/CHANGELOG.md` in sync.

## Confidence Policy

- `100%`: git commit + file diff.
- `90-99%`: machine log + deterministic payload.
- `60-89%`: structured state with inferred intent.
- `<60%`: free-text reconstruction.

## Definition of "Every Single Change"

Achievable with full confidence from the git adoption point forward.
For pre-git period, confidence reaches near-complete if both Antigravity threads are exported and ingested.
