# Automated Scheduling Setup

This guide explains how to set up automated scheduling for Pro Sports Intel AI™.

## Schedule Overview

- **7:00 AM** - Generate new predictions and update dashboard
- **11:00 PM** - Update results and commit to git (East Coast games)
- **2:00 AM** - Update results and commit to git (West Coast games)

## macOS (Recommended: launchd)

`launchd` is Apple's native job scheduler and is **better than cron** on macOS because:
- ✅ Survives reboots automatically
- ✅ Better error handling and logging
- ✅ Runs even when you're logged out
- ✅ More reliable scheduling

### Quick Setup

```bash
cd /Users/a.fleming/nfl-predictions
./setup_scheduling.sh
```

### Manual Setup

1. **Copy plist files to LaunchAgents:**
   ```bash
   mkdir -p ~/Library/LaunchAgents
   cp com.prosportsintel.morning.plist ~/Library/LaunchAgents/
   cp com.prosportsintel.results-11pm.plist ~/Library/LaunchAgents/
   cp com.prosportsintel.results-2am.plist ~/Library/LaunchAgents/
   ```

2. **Load the jobs:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.prosportsintel.morning.plist
   launchctl load ~/Library/LaunchAgents/com.prosportsintel.results-11pm.plist
   launchctl load ~/Library/LaunchAgents/com.prosportsintel.results-2am.plist
   ```

### Managing Jobs

**Check status:**
```bash
launchctl list | grep prosportsintel
```

**Unload (stop) jobs:**
```bash
launchctl unload ~/Library/LaunchAgents/com.prosportsintel.morning.plist
launchctl unload ~/Library/LaunchAgents/com.prosportsintel.results-11pm.plist
launchctl unload ~/Library/LaunchAgents/com.prosportsintel.results-2am.plist
```

**Reload after changes:**
```bash
launchctl unload ~/Library/LaunchAgents/com.prosportsintel.morning.plist
launchctl load ~/Library/LaunchAgents/com.prosportsintel.morning.plist
```

## Alternative: Cron Jobs

If you prefer cron (or on non-macOS systems):

```bash
crontab -e
```

Add these lines:
```
# Pro Sports Intel AI - Morning predictions (7am)
0 7 * * * cd /Users/a.fleming/nfl-predictions && bash scheduled_morning_run.sh

# Pro Sports Intel AI - Results update (11pm)
0 23 * * * cd /Users/a.fleming/nfl-predictions && bash scheduled_results_update.sh

# Pro Sports Intel AI - Results update (2am for West Coast)
0 2 * * * cd /Users/a.fleming/nfl-predictions && bash scheduled_results_update.sh
```

## Git Setup

The scripts automatically:
1. Initialize git repo if needed
2. Set remote to `https://github.com/AstonMadeIt/bored-stuff.git`
3. Commit HTML files (dashboard.html, results.html, historical-performance.html)
4. Push to GitHub

**First-time setup:**
```bash
cd /Users/a.fleming/nfl-predictions
git init
git remote add origin https://github.com/AstonMadeIt/bored-stuff.git
git branch -M main  # or master
```

**Note:** You may need to set up GitHub authentication:
- Personal Access Token (recommended)
- SSH keys
- GitHub CLI (`gh auth login`)

## Logs

All scheduled runs log to:
- `logs/scheduled_morning.log` - Morning runs
- `logs/scheduled_results.log` - Results updates
- `logs/morning_launchd.log` - launchd stdout (morning)
- `logs/results-11pm_launchd.log` - launchd stdout (11pm)
- `logs/results-2am_launchd.log` - launchd stdout (2am)

## Testing

**Test morning script:**
```bash
./scheduled_morning_run.sh
```

**Test results update:**
```bash
./scheduled_results_update.sh
```

**Test manually:**
```bash
# Generate predictions
python3 generate_all_predictions.py

# Update dashboard
python3 create_apple_dashboard.py

# Update results
python3 update_results.py

# Generate results pages
python3 generate_results_pages.py
```

## Troubleshooting

**Jobs not running?**
- Check logs: `tail -f logs/scheduled_morning.log`
- Verify launchd: `launchctl list | grep prosportsintel`
- Check file permissions: `chmod +x scheduled_*.sh`

**Git push failing?**
- Check authentication: `git remote -v`
- Test manually: `git push origin main`
- May need to set up GitHub credentials

**Scripts not found?**
- Ensure you're in the right directory: `cd /Users/a.fleming/nfl-predictions`
- Check paths in plist files match your setup

