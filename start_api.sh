#!/bin/bash
# Simple API server startup script

cd "$(dirname "$0")"

echo "🚀 Starting NFL Prediction API Server..."
echo ""

# Kill any existing process on port 5000
if lsof -ti:5000 > /dev/null 2>&1; then
    echo "⚠️  Killing existing process on port 5000..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed!"
    echo "   Install with: pip install flask flask-cors"
    exit 1
fi

# Start the server
echo "📡 Starting server on http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

python3 api_server.py


