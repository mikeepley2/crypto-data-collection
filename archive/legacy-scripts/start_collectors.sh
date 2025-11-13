#!/bin/bash

# Collector Services Startup Script
# Starts macro and onchain collectors as background services with centralized scheduling

echo "🚀 Starting Crypto Data Collectors"
echo "=================================="

# Change to the repo directory
cd /mnt/e/git/crypto-data-collection

# Set up environment
export PYTHONPATH="/mnt/e/git/crypto-data-collection"

# Check if collectors are already running
if pgrep -f "macro_collector.py" > /dev/null; then
    echo "⚠️  Macro collector already running (PID: $(pgrep -f macro_collector.py))"
else
    echo "🏛️  Starting Macro Collector..."
    cd services/macro-collection
    nohup python macro_collector.py > /tmp/macro_collector.log 2>&1 &
    MACRO_PID=$!
    echo "   Started with PID: $MACRO_PID"
    cd ../..
fi

if pgrep -f "onchain_collector.py" > /dev/null; then
    echo "⚠️  Onchain collector already running (PID: $(pgrep -f onchain_collector.py))"
else
    echo "⛓️   Starting Onchain Collector..."
    cd services/onchain-collection  
    nohup python onchain_collector.py > /tmp/onchain_collector.log 2>&1 &
    ONCHAIN_PID=$!
    echo "   Started with PID: $ONCHAIN_PID"
    cd ../..
fi

echo ""
echo "✅ Collector Services Status:"
echo "   Macro Collector:   $(pgrep -f macro_collector.py > /dev/null && echo 'RUNNING' || echo 'STOPPED') (PID: $(pgrep -f macro_collector.py || echo 'N/A'))"
echo "   Onchain Collector: $(pgrep -f onchain_collector.py > /dev/null && echo 'RUNNING' || echo 'STOPPED') (PID: $(pgrep -f onchain_collector.py || echo 'N/A'))"

echo ""
echo "📊 Expected Collection Schedule:"
echo "   Macro:   Every 1 hour  (next run within 60 minutes)"
echo "   Onchain: Every 6 hours (next run within 6 hours)"

echo ""
echo "📋 Monitoring Commands:"
echo "   tail -f /tmp/macro_collector.log    # Watch macro collector logs"
echo "   tail -f /tmp/onchain_collector.log  # Watch onchain collector logs"
echo "   ps aux | grep collector             # Check running status"
echo "   python quick_health_check.py       # Verify data collection"

echo ""
echo "🛑 To stop collectors:"
echo "   pkill -f macro_collector.py"
echo "   pkill -f onchain_collector.py"