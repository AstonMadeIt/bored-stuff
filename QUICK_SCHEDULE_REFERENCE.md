# Quick Schedule Reference

## ✅ Installed Jobs

All jobs are now running automatically via `launchd`:

- **7:00 AM** - `scheduled_morning_run.sh` (Generate predictions & dashboard)
- **11:00 PM** - `scheduled_results_update.sh` (Update results & git commit)
- **2:00 AM** - `scheduled_results_update.sh` (Update results & git commit - West Coast)

## Quick Commands

**Check if jobs are running:**
```bash
launchctl list | grep prosportsintel
```

**View logs:**
```bash
tail -f logs/scheduled_morning.log
tail -f logs/scheduled_results.log
```

**Stop all jobs:**
```bash
launchctl unload ~/Library/LaunchAgents/com.prosportsintel.*.plist
```

**Restart all jobs:**
```bash
cd /Users/a.fleming/nfl-predictions
./setup_scheduling.sh
```

**Test manually:**
```bash
./scheduled_morning_run.sh      # Test morning run
./scheduled_results_update.sh   # Test results update
```

## Git Repository

- Remote: `https://github.com/AstonMadeIt/bored-stuff`
- Auto-commits: `dashboard.html`, `results.html`, `historical-performance.html`
- Commits happen automatically after results updates (11pm & 2am)

## What Gets Committed

The scripts automatically commit these files to git:
- `predictions/dashboard.html` - Main dashboard
- `predictions/results.html` - Recent results
- `predictions/historical-performance.html` - Performance stats

