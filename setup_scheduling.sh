#!/bin/bash
# Setup Automated Scheduling for Pro Sports Intel AI
# Installs launchd plists for macOS (recommended) or cron jobs

echo "🚀 PRO SPORTS INTEL AI™ - SCHEDULING SETUP"
echo "=========================================="
echo ""

PROJECT_DIR="/Users/a.fleming/nfl-predictions"
cd "$PROJECT_DIR"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  This script is optimized for macOS. Using cron instead."
    USE_CRON=true
else
    echo "✅ macOS detected - Using launchd (recommended)"
    USE_CRON=false
fi

if [ "$USE_CRON" = false ]; then
    # macOS launchd setup
    echo ""
    echo "📋 Setting up launchd plists..."
    
    # Load the plists
    echo "   Loading morning job (7am)..."
    launchctl unload ~/Library/LaunchAgents/com.prosportsintel.morning.plist 2>/dev/null
    cp "$PROJECT_DIR/com.prosportsintel.morning.plist" ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/com.prosportsintel.morning.plist
    echo "   ✅ Morning job loaded"
    
    echo "   Loading 11pm results job..."
    launchctl unload ~/Library/LaunchAgents/com.prosportsintel.results-11pm.plist 2>/dev/null
    cp "$PROJECT_DIR/com.prosportsintel.results-11pm.plist" ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/com.prosportsintel.results-11pm.plist
    echo "   ✅ 11pm job loaded"
    
    echo "   Loading 2am results job..."
    launchctl unload ~/Library/LaunchAgents/com.prosportsintel.results-2am.plist 2>/dev/null
    cp "$PROJECT_DIR/com.prosportsintel.results-2am.plist" ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/com.prosportsintel.results-2am.plist
    echo "   ✅ 2am job loaded"
    
    echo ""
    echo "✅ All launchd jobs installed!"
    echo ""
    echo "📋 To check status:"
    echo "   launchctl list | grep prosportsintel"
    echo ""
    echo "📋 To unload jobs:"
    echo "   launchctl unload ~/Library/LaunchAgents/com.prosportsintel.*.plist"
    
else
    # Cron setup (fallback for non-macOS)
    echo ""
    echo "📋 Setting up cron jobs..."
    
    CRON_FILE=$(mktemp)
    crontab -l > "$CRON_FILE" 2>/dev/null || true
    
    # Remove existing entries
    grep -v "scheduled_morning_run.sh\|scheduled_results_update.sh" "$CRON_FILE" > "${CRON_FILE}.new" || true
    mv "${CRON_FILE}.new" "$CRON_FILE"
    
    # Add new entries
    echo "# Pro Sports Intel AI - Morning predictions (7am)" >> "$CRON_FILE"
    echo "0 7 * * * cd $PROJECT_DIR && bash scheduled_morning_run.sh" >> "$CRON_FILE"
    echo "" >> "$CRON_FILE"
    echo "# Pro Sports Intel AI - Results update (11pm)" >> "$CRON_FILE"
    echo "0 23 * * * cd $PROJECT_DIR && bash scheduled_results_update.sh" >> "$CRON_FILE"
    echo "" >> "$CRON_FILE"
    echo "# Pro Sports Intel AI - Results update (2am for West Coast)" >> "$CRON_FILE"
    echo "0 2 * * * cd $PROJECT_DIR && bash scheduled_results_update.sh" >> "$CRON_FILE"
    
    crontab "$CRON_FILE"
    rm "$CRON_FILE"
    
    echo "✅ Cron jobs installed!"
    echo ""
    echo "📋 To view cron jobs:"
    echo "   crontab -l"
fi

echo ""
echo "🎉 Scheduling setup complete!"
echo ""
echo "📅 Schedule:"
echo "   • 7:00 AM - Generate predictions & dashboard"
echo "   • 11:00 PM - Update results & commit to git"
echo "   • 2:00 AM - Update results & commit to git (West Coast games)"
echo ""

