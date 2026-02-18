#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/a.fleming/Projects/bored-stuff/moleskine-history"
SUBS="/Users/a.fleming/Projects/Subs/MOLESKINE"
COOPER="/Users/a.fleming/Projects/cooper/MOLESKINE"

python3 "$ROOT/tools/collect_baseline.py" \
  --subs-root "$SUBS" \
  --cooper-root "$COOPER" \
  --out-dir "$ROOT/baseline"

python3 "$ROOT/tools/ingest_router_events.py" \
  --input "$COOPER/runtime/logs/router_events.jsonl" \
  --output "$ROOT/timeline/events.jsonl"

python3 "$ROOT/tools/ingest_state_artifacts.py" \
  --state-dir "$COOPER/schemas" \
  --output "$ROOT/timeline/events.jsonl"

echo "Rebuild complete: $ROOT"
