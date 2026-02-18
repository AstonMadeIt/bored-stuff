# Moleskine Forensic History

This folder is the canonical reconstruction and forward-only audit trail for MOLESKINE + Float work.

## Goal

Preserve:

1. What we started with.
2. Every change made.
3. Why each change was made.
4. How each change was implemented.

## Provenance Model

We use three evidence tiers:

- `tier_a_primary`: machine logs and git commits (highest confidence).
- `tier_b_structured`: JSON state files, decision ledgers, generated artifacts.
- `tier_c_reconstructed`: inferred events from file timestamps or thread text.

## Current Scope

- Source roots:
  - `/Users/a.fleming/Projects/Subs/MOLESKINE`
  - `/Users/a.fleming/Projects/cooper/MOLESKINE`
- Runtime event stream:
  - `/Users/a.fleming/Projects/cooper/MOLESKINE/runtime/logs/router_events.jsonl`

## How To Use

1. Rebuild baseline manifests:

```bash
python3 /Users/a.fleming/Projects/bored-stuff/moleskine-history/tools/collect_baseline.py \
  --subs-root /Users/a.fleming/Projects/Subs/MOLESKINE \
  --cooper-root /Users/a.fleming/Projects/cooper/MOLESKINE \
  --out-dir /Users/a.fleming/Projects/bored-stuff/moleskine-history/baseline
```

2. Ingest runtime router events:

```bash
python3 /Users/a.fleming/Projects/bored-stuff/moleskine-history/tools/ingest_router_events.py \
  --input /Users/a.fleming/Projects/cooper/MOLESKINE/runtime/logs/router_events.jsonl \
  --output /Users/a.fleming/Projects/bored-stuff/moleskine-history/timeline/events.jsonl
```

3. Ingest Antigravity thread exports (recommended for full pre-git reconstruction):

```bash
python3 /Users/a.fleming/Projects/bored-stuff/moleskine-history/tools/ingest_antigravity_thread.py \
  --input /absolute/path/to/thread_export.md \
  --thread-id antigravity-thread-1 \
  --output /Users/a.fleming/Projects/bored-stuff/moleskine-history/timeline/events.jsonl
```

## What "Every Single Change" Means Here

- From this point forward: guaranteed by git + timeline ingestion.
- Before git adoption: achievable if both Antigravity threads are exported and ingested, plus runtime/state artifacts are preserved.
