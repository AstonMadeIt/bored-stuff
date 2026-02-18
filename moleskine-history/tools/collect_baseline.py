#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_FILES = {".DS_Store"}


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        rel_parts = path.relative_to(root).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if path.is_dir():
            continue
        if path.name in EXCLUDE_FILES:
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue
        yield path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _scan_root(label: str, root: Path) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    bytes_total = 0
    for path in _iter_files(root):
        stat = path.stat()
        rel = path.relative_to(root).as_posix()
        digest = _sha256(path)
        mtime = dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat()
        row = {
            "dataset": label,
            "relative_path": rel,
            "size_bytes": stat.st_size,
            "mtime_utc": mtime,
            "sha256": digest,
        }
        rows.append(row)
        bytes_total += stat.st_size

    summary = {
        "dataset": label,
        "root": str(root),
        "file_count": len(rows),
        "total_bytes": bytes_total,
    }
    return rows, summary


def _write_tsv(path: Path, rows: List[Dict[str, object]]) -> None:
    header = ["dataset", "relative_path", "size_bytes", "mtime_utc", "sha256"]
    with path.open("w", encoding="utf-8") as f:
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(str(row[k]) for k in header) + "\n")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Collect forensic baseline hashes for MOLESKINE sources.")
    p.add_argument("--subs-root", type=Path, required=True)
    p.add_argument("--cooper-root", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    return p


def main() -> int:
    args = _build_parser().parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    subs_rows, subs_summary = _scan_root("subs_moleskine", args.subs_root)
    cooper_rows, cooper_summary = _scan_root("cooper_moleskine", args.cooper_root)

    _write_tsv(out / "subs_files.tsv", subs_rows)
    _write_tsv(out / "cooper_files.tsv", cooper_rows)

    manifest = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": [subs_summary, cooper_summary],
        "excluded_dirs": sorted(EXCLUDE_DIRS),
        "excluded_suffixes": sorted(EXCLUDE_SUFFIXES),
        "excluded_files": sorted(EXCLUDE_FILES),
    }
    (out / "baseline_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
