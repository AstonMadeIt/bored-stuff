#!/bin/bash
# Results Update - Update Results and Commit to Git
# Runs at 11pm and 2am to update results and commit HTML files

cd "$(dirname "$0")"
LOG_FILE="logs/scheduled_results.log"
mkdir -p logs

{
    echo "=========================================="
    echo "🌙 RESULTS UPDATE - $(date)"
    echo "=========================================="
    echo ""
    
    # Step 1: Update results
    echo "📊 Updating results..."
    python3 update_results.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Results updated!"
        echo ""
        
        # Step 2: Generate results pages (in case update_results.py didn't)
        echo "📄 Generating results pages..."
        python3 generate_results_pages.py
        
        echo ""
        echo "✅ Results pages generated!"
        echo ""
        
        # Step 3: Commit to git
        echo "📦 Committing to git..."
        
        # Check if git repo exists, initialize if needed
        if [ ! -d .git ]; then
            echo "   ℹ️  Initializing git repository..."
            git init >> "$LOG_FILE" 2>&1
        fi
        
        # Set remote if not configured
        if ! git remote | grep -q origin; then
            echo "   ℹ️  Setting up git remote..."
            git remote add origin https://github.com/AstonMadeIt/bored-stuff.git 2>/dev/null || \
            git remote set-url origin https://github.com/AstonMadeIt/bored-stuff.git
        fi
        
        # Stage the HTML files
        git add predictions/dashboard.html 2>/dev/null
        git add predictions/results.html 2>/dev/null
        git add predictions/historical-performance.html 2>/dev/null
        
        # Check if there are changes to commit
        if git diff --staged --quiet; then
            echo "   ℹ️  No changes to commit"
        else
            # Commit with timestamp
            COMMIT_MSG="Auto-update: Results and dashboard $(date '+%Y-%m-%d %H:%M')"
            git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1
            
            if [ $? -eq 0 ]; then
                echo "   ✅ Committed: $COMMIT_MSG"
                
                # Configure git for automated pulls (merge strategy)
                git config pull.rebase false >> "$LOG_FILE" 2>&1 || true
                
                # Fetch latest changes first
                echo "   📥 Fetching latest changes..."
                BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
                git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1 || \
                git fetch origin main >> "$LOG_FILE" 2>&1 || \
                git fetch origin >> "$LOG_FILE" 2>&1 || true
                
                # Try to merge remote changes
                echo "   🔀 Merging remote changes..."
                git merge origin/"$BRANCH" --no-edit -m "Auto-merge: $(date '+%Y-%m-%d %H:%M')" >> "$LOG_FILE" 2>&1 || \
                git merge origin/main --no-edit -m "Auto-merge: $(date '+%Y-%m-%d %H:%M')" >> "$LOG_FILE" 2>&1 || true
                
                # Push to remote
                echo "   📤 Pushing to remote..."
                BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
                git push -u origin "$BRANCH" >> "$LOG_FILE" 2>&1 || \
                git push origin HEAD >> "$LOG_FILE" 2>&1
                
                if [ $? -eq 0 ]; then
                    echo "   ✅ Pushed to remote"
                else
                    echo "   ⚠️  Push failed (check logs: $LOG_FILE)"
                    echo "   ℹ️  Authentication works, but may need to resolve conflicts manually"
                fi
            else
                echo "   ⚠️  Commit failed"
            fi
        fi
        
        echo ""
        echo "🎉 Results update complete!"
    else
        echo "⚠️  Results update failed (may be no completed games)"
    fi
    
    echo ""
    echo "=========================================="
    echo "✅ Results update finished at $(date)"
    echo "=========================================="
    
} >> "$LOG_FILE" 2>&1

