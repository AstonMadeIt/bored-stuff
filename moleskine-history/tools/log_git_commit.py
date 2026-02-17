#!/usr/bin/env python3
import json
import subprocess
import datetime as dt
from pathlib import Path

def main():
    timeline_path = Path("/Users/a.fleming/Projects/bored-stuff/moleskine-history/timeline/events.jsonl")
    
    # Get latest commit info
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        author = subprocess.check_output(["git", "log", "-1", "--format=%an"]).decode().strip()
        message = subprocess.check_output(["git", "log", "-1", "--format=%s"]).decode().strip()
    except Exception as e:
        print(f"Error getting git info: {e}")
        return

    event = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "git_hook",
        "provenance_tier": "tier_a_primary",
        "category": "git_commit",
        "commit_hash": commit_hash,
        "author": author,
        "summary": message,
        "event_id": f"GIT-{commit_hash[:12]}"
    }

    with open(timeline_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

if __name__ == "__main__":
    main()
