#!/bin/bash
# Morning Run - Generate Predictions and Dashboard
# Runs at 7am daily to find new games and generate predictions

cd "$(dirname "$0")"
LOG_FILE="logs/scheduled_morning.log"
mkdir -p logs

# Load environment variables (including ANTHROPIC_API_KEY if set)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Load API key from setup_ai.sh if it exists
if [ -z "$ANTHROPIC_API_KEY" ] && [ -f setup_ai.sh ]; then
    # Extract API key from setup_ai.sh
    ANTHROPIC_API_KEY=$(grep 'ANTHROPIC_API_KEY=' setup_ai.sh | head -1 | sed 's/.*ANTHROPIC_API_KEY="\([^"]*\)".*/\1/')
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        export ANTHROPIC_API_KEY
    fi
fi

# Also check common locations for API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -f ~/.anthropic_key ]; then
    export ANTHROPIC_API_KEY=$(cat ~/.anthropic_key)
fi
if [ -z "$ANTHROPIC_API_KEY" ] && [ -f ~/.config/anthropic_key ]; then
    export ANTHROPIC_API_KEY=$(cat ~/.config/anthropic_key)
fi

{
    echo "=========================================="
    echo "🌅 MORNING RUN - $(date)"
    echo "=========================================="
    echo ""
    
    # Step 1: Generate predictions
    echo "📊 Generating predictions..."
    python3 generate_all_predictions.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Predictions generated!"
        echo ""
        
        # Step 2: Update dashboard
        echo "📊 Updating dashboard..."
        python3 create_apple_dashboard.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Dashboard updated!"
            echo ""
            
            # Step 3: Commit and push to git
            echo "📦 Committing to git..."
            
            # Check if git repo exists
            if [ -d .git ]; then
                # Configure git for automated pulls
                git config pull.rebase false >> "$LOG_FILE" 2>&1 || true
                
                # Fetch and merge latest changes
                BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
                git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1 || git fetch origin >> "$LOG_FILE" 2>&1 || true
                git merge origin/"$BRANCH" --no-edit -m "Auto-merge: $(date '+%Y-%m-%d %H:%M')" >> "$LOG_FILE" 2>&1 || \
                git merge origin/main --no-edit -m "Auto-merge: $(date '+%Y-%m-%d %H:%M')" >> "$LOG_FILE" 2>&1 || true
                
                # Copy dashboard to root for GitHub Pages (if it exists in predictions/)
                if [ -f predictions/dashboard.html ]; then
                    cp predictions/dashboard.html dashboard.html
                    echo "   📋 Copied dashboard to root for GitHub Pages"
                fi
                
                # Stage dashboard files (both locations)
                git add dashboard.html >> "$LOG_FILE" 2>&1
                git add predictions/dashboard.html >> "$LOG_FILE" 2>&1
                git add predictions/all_predictions.json >> "$LOG_FILE" 2>&1
                
                # Check if there are changes to commit
                if git diff --staged --quiet; then
                    echo "   ℹ️  No changes to commit"
                else
                    # Commit with timestamp
                    COMMIT_MSG="Auto-update: Morning predictions and dashboard $(date '+%Y-%m-%d %H:%M')"
                    git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1
                    
                    if [ $? -eq 0 ]; then
                        echo "   ✅ Committed: $COMMIT_MSG"
                        
                        # Push to remote
                        echo "   📤 Pushing to remote..."
                        git push origin "$BRANCH" >> "$LOG_FILE" 2>&1 || \
                        git push origin main >> "$LOG_FILE" 2>&1 || \
                        git push origin HEAD >> "$LOG_FILE" 2>&1
                        
                        if [ $? -eq 0 ]; then
                            echo "   ✅ Pushed to remote"
                        else
                            echo "   ⚠️  Push failed (check logs: $LOG_FILE)"
                        fi
                    else
                        echo "   ⚠️  Commit failed"
                    fi
                fi
            else
                echo "   ℹ️  Not a git repository, skipping commit"
            fi
            
            echo ""
            echo "🎉 Morning run complete!"
        else
            echo "❌ Dashboard update failed"
            exit 1
        fi
    else
        echo "❌ Prediction generation failed"
        exit 1
    fi
    
    echo ""
    echo "=========================================="
    echo "✅ Morning run finished at $(date)"
    echo "=========================================="
    
} >> "$LOG_FILE" 2>&1

