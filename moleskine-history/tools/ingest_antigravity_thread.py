#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?Z?)?)\b")


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


def _event_id(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return "TH-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_markdown_blocks(text: str) -> List[str]:
    # Split by blank lines; this keeps ingestion robust for different export formats.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    return blocks


def _timestamp_for_block(block: str) -> str:
    m = DATE_RE.search(block)
    if m:
        token = m.group(1).replace(" ", "T")
        if len(token) == 10:
            token += "T00:00:00Z"
        elif token.endswith("Z"):
            pass
        elif "T" in token and len(token) == 16:
            token += ":00Z"
        elif "T" in token and len(token) == 19:
            token += "Z"
        return token
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ingest Antigravity thread export (markdown/json text) into timeline.")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--thread-id", required=True)
    p.add_argument("--output", type=Path, required=True)
    return p


def main() -> int:
    args = _build_parser().parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_existing_ids(args.output)

    text = args.input.read_text(encoding="utf-8")
    blocks = _normalize_markdown_blocks(text)
    written = 0

    with args.output.open("a", encoding="utf-8") as out:
        for idx, block in enumerate(blocks, 1):
            event = {
                "timestamp_utc": _timestamp_for_block(block),
                "source": "antigravity_thread_export",
                "provenance_tier": "tier_c_reconstructed",
                "category": "thread_block",
                "thread_id": args.thread_id,
                "sequence": idx,
                "summary": block[:220],
                "source_path": str(args.input),
                "raw": block,
            }
            event["event_id"] = _event_id(event)
            if event["event_id"] in existing:
                continue
            out.write(json.dumps(event, ensure_ascii=True) + "\n")
            existing.add(event["event_id"])
            written += 1

    print(json.dumps({"written": written, "output": str(args.output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
