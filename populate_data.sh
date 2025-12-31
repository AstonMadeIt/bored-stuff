#!/bin/bash
# Helper script to populate dashboard with data

API_BASE="http://localhost:5001"

echo "📊 Populating NFL Prediction Dashboard Data"
echo ""

# Generate predictions
echo "1️⃣ Generating predictions..."
curl -s -X POST ${API_BASE}/api/predictions/generate | python3 -m json.tool
echo ""

# Show upcoming predictions
echo "2️⃣ Upcoming predictions:"
curl -s ${API_BASE}/api/predictions/upcoming | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['success']:
    print(f\"   Found {data['count']} predictions\")
    for p in data['data'][:5]:
        print(f\"   • {p['away_team']} @ {p['home_team']}\")
        print(f\"     Predicted: {p['predicted_winner']} by {abs(p['predicted_spread']):.1f}\")
        if p.get('vegas_spread'):
            print(f\"     Vegas: {abs(p['vegas_spread']):.1f} | Divergence: {p.get('model_market_divergence', 0):.1f}\")
else:
    print(f\"   Error: {data.get('error')}\")
"
echo ""

# Update results (if any games finished)
echo "3️⃣ Updating game results..."
curl -s -X POST ${API_BASE}/api/results/update | python3 -m json.tool
echo ""

# Show metrics
echo "4️⃣ Current metrics:"
curl -s ${API_BASE}/api/metrics | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['success']:
    m = data['data']
    print(f\"   Total Predictions: {m.get('total_predictions', 0)}\")
    print(f\"   Accuracy: {m.get('accuracy', 0):.1f}%\")
    print(f\"   High Conf Accuracy: {m.get('high_conf_accuracy', 0):.1f}%\")
    print(f\"   Avg Spread Error: {m.get('avg_spread_error', 0):.1f} pts\")
"
echo ""

echo "✅ Done! Refresh your browser to see updates."
echo "🌐 Dashboard: http://localhost:5001"


