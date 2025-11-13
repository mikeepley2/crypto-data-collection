#!/bin/bash
# 🔍 ONCHAIN COLLECTOR MONITORING DASHBOARD
# Monitors onchain data collection progress every 60 seconds

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

check_pod_status() {
    echo ""
    print_status $CYAN "📊 ONCHAIN COLLECTOR POD STATUS"
    print_status $CYAN "================================"
    
    PODS=$(docker exec cryptoai-k8s-trading-engine-control-plane kubectl get pods -n crypto-data-collection -l app=onchain-collector --no-headers 2>/dev/null)
    
    if [ -z "$PODS" ]; then
        print_status $RED "❌ No onchain collector pods found"
        return 1
    fi
    
    echo "$PODS" | while read line; do
        if [ ! -z "$line" ]; then
            POD_NAME=$(echo $line | awk '{print $1}')
            STATUS=$(echo $line | awk '{print $3}')
            RESTARTS=$(echo $line | awk '{print $4}')
            AGE=$(echo $line | awk '{print $5}')
            
            if [ "$STATUS" = "Running" ]; then
                print_status $GREEN "✅ Pod: $POD_NAME - Status: $STATUS - Restarts: $RESTARTS - Age: $AGE"
            else
                print_status $YELLOW "⚠️  Pod: $POD_NAME - Status: $STATUS - Restarts: $RESTARTS - Age: $AGE"
            fi
        fi
    done
}

check_database_progress() {
    echo ""
    print_status $CYAN "🗄️  DATABASE COLLECTION PROGRESS"
    print_status $CYAN "================================="
    
    RUNNING_POD=$(docker exec cryptoai-k8s-trading-engine-control-plane kubectl get pods -n crypto-data-collection -l app=onchain-collector --field-selector=status.phase=Running --no-headers 2>/dev/null | head -1 | awk '{print $1}')
    
    if [ -z "$RUNNING_POD" ]; then
        print_status $RED "❌ No running pod to query database"
        return 1
    fi
    
    DB_STATS=$(docker exec cryptoai-k8s-trading-engine-control-plane kubectl exec -n crypto-data-collection $RUNNING_POD -- python3 -c "
import mysql.connector
try:
    db_config = {
        'host': 'host.docker.internal',
        'port': 3306,
        'user': 'news_collector',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM crypto_onchain_data')
    total_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM crypto_onchain_data WHERE timestamp >= NOW() - INTERVAL 1 HOUR')
    last_hour_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM crypto_onchain_data')
    unique_symbols = cursor.fetchone()[0]
    
    cursor.execute('SELECT symbol, timestamp FROM crypto_onchain_data ORDER BY timestamp DESC LIMIT 1')
    latest_record = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    print(f'{total_count}|{last_hour_count}|{unique_symbols}|{latest_record[0] if latest_record else \"None\"}|{latest_record[1] if latest_record else \"None\"}')
        
except Exception as e:
    print(f'ERROR:{e}')
" 2>/dev/null)

    if [[ $DB_STATS == *"ERROR"* ]]; then
        print_status $RED "❌ Database query failed"
        return 1
    fi
    
    IFS='|' read -r TOTAL_RECORDS LAST_HOUR UNIQUE_SYMBOLS LATEST_SYMBOL LATEST_TIME <<< "$DB_STATS"
    
    if [ ! -z "$TOTAL_RECORDS" ]; then
        print_status $GREEN "📊 Total Records: $TOTAL_RECORDS"
        print_status $GREEN "🔥 Unique Symbols: $UNIQUE_SYMBOLS"
        
        if [ "$LAST_HOUR" -gt 0 ]; then
            print_status $GREEN "⚡ Records (Last Hour): $LAST_HOUR"
        else
            print_status $YELLOW "⚡ Records (Last Hour): $LAST_HOUR"
        fi
        
        if [ "$LATEST_SYMBOL" != "None" ]; then
            print_status $BLUE "🎯 Latest Entry: $LATEST_SYMBOL at $LATEST_TIME"
        else
            print_status $YELLOW "🎯 Latest Entry: No data yet"
        fi
    else
        print_status $RED "❌ Could not retrieve database statistics"
    fi
}

check_recent_activity() {
    echo ""
    print_status $CYAN "📋 RECENT COLLECTOR ACTIVITY"
    print_status $CYAN "============================="
    
    RUNNING_POD=$(docker exec cryptoai-k8s-trading-engine-control-plane kubectl get pods -n crypto-data-collection -l app=onchain-collector --field-selector=status.phase=Running --no-headers 2>/dev/null | head -1 | awk '{print $1}')
    
    if [ -z "$RUNNING_POD" ]; then
        print_status $RED "❌ No running onchain collector pod found"
        return 1
    fi
    
    print_status $BLUE "📡 Active Pod: $RUNNING_POD"
    
    RECENT_LOGS=$(docker exec cryptoai-k8s-trading-engine-control-plane kubectl logs $RUNNING_POD -n crypto-data-collection --tail=3 --timestamps 2>/dev/null)
    
    if [ ! -z "$RECENT_LOGS" ]; then
        echo "$RECENT_LOGS" | while IFS= read -r line; do
            if [[ $line == *"ERROR"* ]] || [[ $line == *"error"* ]]; then
                print_status $RED "  $line"
            elif [[ $line == *"SUCCESS"* ]] || [[ $line == *"✅"* ]]; then
                print_status $GREEN "  $line"
            else
                echo "  $line"
            fi
        done
    else
        print_status $YELLOW "⚠️  No recent logs available"
    fi
}

main_monitor() {
    print_status $PURPLE "🚀 STARTING ONCHAIN COLLECTOR MONITORING"
    print_status $PURPLE "========================================"
    print_status $BLUE "⏰ Monitoring interval: 60 seconds"
    print_status $BLUE "🔄 Press Ctrl+C to stop"
    echo ""
    
    ITERATION=1
    
    while true; do
        clear
        print_status $PURPLE "🔍 ONCHAIN COLLECTOR MONITORING - Iteration #$ITERATION"
        print_status $PURPLE "========================================================="
        print_status $BLUE "📅 $(get_timestamp)"
        
        check_pod_status
        check_recent_activity
        check_database_progress
        
        echo ""
        print_status $YELLOW "⏱️  Next check in 60 seconds... (Ctrl+C to stop)"
        print_status $YELLOW "================================================="
        
        ITERATION=$((ITERATION + 1))
        sleep 60
    done
}

trap 'echo -e "\n\n${PURPLE}👋 Monitoring stopped by user${NC}"; exit 0' INT

main_monitor
