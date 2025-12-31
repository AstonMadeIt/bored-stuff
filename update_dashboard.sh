#!/bin/bash
# Quick script to update predictions and dashboard

echo "🚀 Updating Predictions & Dashboard..."
echo ""

# Step 1: Generate predictions (with new NBA features)
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
        echo "🎉 Dashboard updated!"
        echo ""
        echo "📁 View dashboard:"
        echo "   open predictions/dashboard.html"
        echo ""
        echo "💡 Or use production pipeline for full update:"
        echo "   python3 production_pipeline.py"
    else
        echo "❌ Dashboard update failed"
        exit 1
    fi
else
    echo "❌ Prediction generation failed"
    exit 1
fi


