#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue
            event_id = item.get("event_id")
            if isinstance(event_id, str):
                ids.add(event_id)
    return ids


def _build_event_id(event: Dict[str, Any]) -> str:
    raw = json.dumps(event, sort_keys=True, ensure_ascii=True)
    return "RT-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_router_event(raw: Dict[str, Any], source_path: str) -> Dict[str, Any]:
    ts = raw.get("timestamp")
    if not isinstance(ts, str) or not ts:
        ts = dt.datetime.now(dt.timezone.utc).isoformat()

    norm = {
        "timestamp_utc": ts,
        "source": "runtime_router_events",
        "provenance_tier": "tier_a_primary",
        "category": str(raw.get("event", "unknown")),
        "task_type": raw.get("task_type"),
        "model_alias": raw.get("model_alias"),
        "latency_ms": raw.get("latency_ms"),
        "cost_estimate_usd": raw.get("cost_estimate_usd"),
        "success": raw.get("event") == "task_success",
        "metadata": raw.get("metadata", {}),
        "source_path": source_path,
        "raw": raw,
    }
    norm["event_id"] = _build_event_id(norm)
    return norm


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ingest router JSONL events into forensic timeline.")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p


def main() -> int:
    args = _build_parser().parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_existing_ids(args.output)
    written = 0
    with args.input.open("r", encoding="utf-8") as src, args.output.open("a", encoding="utf-8") as out:
        for line in src:
            raw = line.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            norm = _normalize_router_event(event, str(args.input))
            if norm["event_id"] in existing:
                continue
            out.write(json.dumps(norm, ensure_ascii=True) + "\n")
            existing.add(norm["event_id"])
            written += 1

    print(json.dumps({"written": written, "output": str(args.output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
