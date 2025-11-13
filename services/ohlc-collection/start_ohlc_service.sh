#!/bin/bash
# Enhanced OHLC Collector Startup Script
# Usage: ./start_ohlc_service.sh [port]
# Default port: 8002

# Set default port
PORT=${1:-8002}

echo "🚀 Starting Enhanced OHLC Collector Service on port $PORT"
echo "📊 Service matches template standard with full FastAPI endpoints"
echo ""

# Check if port is in use
if netstat -tlpn 2>/dev/null | grep -q ":$PORT "; then
    echo "❌ Port $PORT is already in use"
    echo "Please choose a different port or stop the existing service"
    exit 1
fi

# Navigate to service directory
cd "$(dirname "$0")"

echo "🔄 Starting service..."
python3 enhanced_ohlc_collector.py --mode api --port $PORT

echo "🛑 Service stopped"