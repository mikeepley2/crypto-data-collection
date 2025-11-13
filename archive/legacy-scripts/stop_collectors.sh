#!/bin/bash
"""
Stop All Crypto Data Collectors
Gracefully stops all running collectors
"""

cd /mnt/e/git/crypto-data-collection

echo "🛑 Stopping All Crypto Data Collectors"
echo "======================================"

if [ -d "pids" ]; then
    for pidfile in pids/*.pid; do
        if [ -f "$pidfile" ]; then
            name=$(basename "$pidfile" .pid)
            pid=$(cat "$pidfile")
            
            echo "🔄 Stopping $name (PID: $pid)..."
            
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                sleep 2
                
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    echo "   ⚡ Force stopping $name..."
                    kill -9 "$pid"
                fi
                
                echo "   ✅ Stopped $name"
            else
                echo "   ⚠️ $name was not running"
            fi
            
            rm -f "$pidfile"
        fi
    done
    
    rmdir pids 2>/dev/null
else
    echo "⚠️ No PID files found - collectors may not be running"
fi

echo ""
echo "✨ All collectors stopped!"