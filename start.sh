#!/bin/bash
# Production startup script

echo "🚀 Starting NFL Prediction System..."
echo ""

# Check if API server is already running
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  API server already running on port 5000"
else
    echo "📡 Starting API server..."
    python3 api_server.py &
    API_PID=$!
    echo "   API server started (PID: $API_PID)"
    sleep 3
fi

# Check API health
echo ""
echo "🏥 Checking API health..."
if curl -s http://localhost:5000/health > /dev/null; then
    echo "   ✅ API is healthy"
else
    echo "   ❌ API health check failed"
    exit 1
fi

echo ""
echo "✅ System ready!"
echo ""
echo "📡 API Server: http://localhost:5000"
echo "📊 Dashboard: http://localhost:5000/"
echo ""
echo "API Endpoints:"
echo "  GET  /api/predictions/upcoming"
echo "  GET  /api/predictions/high-confidence"
echo "  GET  /api/results/completed"
echo "  GET  /api/metrics"
echo "  POST /api/predictions/generate"
echo "  POST /api/results/update"
echo ""
echo "Press Ctrl+C to stop"

# Wait for interrupt
wait $API_PID


