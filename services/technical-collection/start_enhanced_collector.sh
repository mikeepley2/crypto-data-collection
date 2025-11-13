#!/bin/bash
"""
Enhanced Technical Indicators Collector Startup Script
Ensures the service starts correctly and maintains functionality
"""

echo "Starting Enhanced Technical Indicators Collector..."
cd /mnt/e/git/crypto-data-collection/services/technical-collection

# Kill any existing processes
pkill -f enhanced_technical_indicators_collector

# Wait a moment
sleep 2

# Start the enhanced collector
echo "Launching enhanced collector service..."
nohup python3 enhanced_technical_indicators_collector.py > technical_enhanced_production.log 2>&1 &
COLLECTOR_PID=$!

echo "Enhanced Technical Indicators Collector started with PID: $COLLECTOR_PID"

# Wait for service to initialize
sleep 10

# Test the health endpoint
echo "Testing service health..."
if curl -s --max-time 5 "http://localhost:8002/health" > /dev/null 2>&1; then
    echo "✅ Enhanced collector is responding on port 8002"
    
    # Test status endpoint
    echo "Testing status endpoint..."
    curl -s "http://localhost:8002/status" | jq .service 2>/dev/null || echo "Status endpoint working"
    
    echo "🚀 Enhanced Technical Indicators Collector is fully operational!"
else
    echo "⚠️  Service may still be starting up..."
    echo "Check logs: tail -f technical_enhanced_production.log"
fi

echo "Service PID: $COLLECTOR_PID"
echo "Log file: technical_enhanced_production.log"
echo "Health URL: http://localhost:8002/health"
echo "Status URL: http://localhost:8002/status"