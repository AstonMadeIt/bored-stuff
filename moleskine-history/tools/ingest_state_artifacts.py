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


def _eid(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return "ST-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _build_events(world_state: Dict[str, Any], decision_ledger: Dict[str, Any], source_root: Path) -> List[Dict[str, Any]]:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    events: List[Dict[str, Any]] = []

    session = world_state.get("session", {}) if isinstance(world_state.get("session"), dict) else {}
    ws_event = {
        "timestamp_utc": world_state.get("generated_at", now),
        "source": "world_state",
        "provenance_tier": "tier_b_structured",
        "category": "world_state_snapshot",
        "session_id": session.get("session_id"),
        "summary": session.get("summary"),
        "source_path": str(source_root / "world_state.json"),
    }
    ws_event["event_id"] = _eid(ws_event)
    events.append(ws_event)

    decisions = decision_ledger.get("decisions", [])
    if isinstance(decisions, list):
        for d in decisions:
            if not isinstance(d, dict):
                continue
            event = {
                "timestamp_utc": d.get("updated_at") or d.get("created_at") or decision_ledger.get("generated_at", now),
                "source": "decision_ledger",
                "provenance_tier": "tier_b_structured",
                "category": "decision",
                "decision_id": d.get("decision_id"),
                "title": d.get("title"),
                "status": d.get("status"),
                "summary": d.get("decision_statement"),
                "source_path": str(source_root / "decision_ledger.json"),
            }
            event["event_id"] = _eid(event)
            events.append(event)

    return events


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ingest world_state + decision_ledger into timeline.")
    p.add_argument("--state-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p


def main() -> int:
    args = _build_parser().parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    world_state = json.loads((args.state_dir / "world_state.json").read_text(encoding="utf-8"))
    decision_ledger = json.loads((args.state_dir / "decision_ledger.json").read_text(encoding="utf-8"))

    events = _build_events(world_state, decision_ledger, args.state_dir)
    existing = _load_existing_ids(args.output)
    written = 0

    with args.output.open("a", encoding="utf-8") as out:
        for event in events:
            if event["event_id"] in existing:
                continue
            out.write(json.dumps(event, ensure_ascii=True) + "\n")
            existing.add(event["event_id"])
            written += 1

    print(json.dumps({"written": written, "output": str(args.output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
