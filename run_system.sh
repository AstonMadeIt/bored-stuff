#!/bin/bash
# Complete System Runner - One Command to Rule Them All
# Generates predictions, updates dashboard, updates results

echo "🚀 PRO SPORTS INTEL AI™ - FULL SYSTEM RUN"
echo "========================================"
echo ""

# Step 1: Generate predictions (NFL + NBA with enhanced features)
echo "📊 Step 1: Generating predictions..."
python3 generate_all_predictions.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Predictions generated!"
    echo ""
    
    # Step 2: Update dashboard
    echo "📊 Step 2: Updating dashboard..."
    python3 create_apple_dashboard.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Dashboard updated!"
        echo ""
        
        # Step 3: Update results (for yesterday's games)
        echo "📊 Step 3: Updating results (if games completed)..."
        python3 update_results.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Results updated!"
            echo ""
            
            # Step 4: Generate results pages
            echo "📊 Step 4: Generating results pages..."
            python3 generate_results_pages.py
            
            echo ""
            echo "🎉 SYSTEM COMPLETE!"
            echo ""
            echo "📁 Output Files:"
            echo "   - predictions/dashboard.html (Main dashboard)"
            echo "   - predictions/results.html (Recent results)"
            echo "   - predictions/historical-performance.html (Performance stats)"
            echo ""
            echo "🌐 View dashboard:"
            echo "   open predictions/dashboard.html"
        else
            echo "⚠️  Results update failed (may be no completed games)"
        fi
    else
        echo "❌ Dashboard update failed"
        exit 1
    fi
else
    echo "❌ Prediction generation failed"
    exit 1
fi


