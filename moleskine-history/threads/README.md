# Antigravity Thread Exports

Place your two Antigravity thread exports here, for example:

- `thread_01.md`
- `thread_02.md`

Then ingest them:

```bash
python3 /Users/a.fleming/Projects/bored-stuff/moleskine-history/tools/ingest_antigravity_thread.py \
  --input /Users/a.fleming/Projects/bored-stuff/moleskine-history/threads/thread_01.md \
  --thread-id antigravity-01 \
  --output /Users/a.fleming/Projects/bored-stuff/moleskine-history/timeline/events.jsonl

python3 /Users/a.fleming/Projects/bored-stuff/moleskine-history/tools/ingest_antigravity_thread.py \
  --input /Users/a.fleming/Projects/bored-stuff/moleskine-history/threads/thread_02.md \
  --thread-id antigravity-02 \
  --output /Users/a.fleming/Projects/bored-stuff/moleskine-history/timeline/events.jsonl
```
