#!/bin/bash
# Real-time Service Dashboard
# ==========================

NAMESPACE="crypto-collectors"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to clear screen and show header
show_header() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              CRYPTO DATA COLLECTION DASHBOARD               ║${NC}"
    echo -e "${BLUE}║                    $(date +'%Y-%m-%d %H:%M:%S')                     ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Function to show service status
show_service_status() {
    echo -e "${CYAN}📊 SERVICE STATUS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get deployment status
    kubectl get deployments -n $NAMESPACE -o custom-columns="NAME:.metadata.name,READY:.status.readyReplicas,DESIRED:.spec.replicas,STATUS:.status.conditions[0].type" --no-headers 2>/dev/null | while read line; do
        name=$(echo $line | awk '{print $1}')
        ready=$(echo $line | awk '{print $2}')
        desired=$(echo $line | awk '{print $3}')
        status=$(echo $line | awk '{print $4}')
        
        if [ "$ready" = "$desired" ] && [ "$ready" != "0" ] && [ "$status" = "Available" ]; then
            echo -e "  ${GREEN}✅ $name${NC} ($ready/$desired)"
        elif [ "$ready" != "$desired" ]; then
            echo -e "  ${RED}❌ $name${NC} ($ready/$desired) - Scaling"
        elif [ "$status" = "Progressing" ]; then
            echo -e "  ${YELLOW}⏳ $name${NC} ($ready/$desired) - Updating"
        else
            echo -e "  ${RED}💥 $name${NC} ($ready/$desired) - $status"
        fi
    done
    echo
}

# Function to show resource usage
show_resource_usage() {
    echo -e "${PURPLE}💾 RESOURCE USAGE${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Node resource usage
    if kubectl top nodes >/dev/null 2>&1; then
        echo "  Node Resources:"
        kubectl top nodes 2>/dev/null | tail -n +2 | while read line; do
            node=$(echo $line | awk '{print $1}')
            cpu=$(echo $line | awk '{print $2}')
            memory=$(echo $line | awk '{print $4}')
            echo "    🖥️  $node: CPU=$cpu, Memory=$memory"
        done
        echo
        
        # Top resource consumers
        echo "  Top Resource Consumers:"
        kubectl top pods -n $NAMESPACE --sort-by=memory 2>/dev/null | head -4 | tail -3 | while read line; do
            pod=$(echo $line | awk '{print $1}')
            cpu=$(echo $line | awk '{print $2}')
            memory=$(echo $line | awk '{print $3}')
            echo "    📦 $pod: CPU=$cpu, Memory=$memory"
        done
    else
        echo "  📊 Resource metrics not available"
    fi
    echo
}

# Function to show data collection stats
show_data_stats() {
    echo -e "${YELLOW}📈 DATA COLLECTION STATS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Try to get data stats from database (simplified)
    kubectl exec -n $NAMESPACE deployment/realtime-materialized-updater -- python3 -c "
import mysql.connector
import os
try:
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'host.docker.internal'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'crypto_prices'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'password')
    )
    cursor = conn.cursor()
    
    # Price data stats
    cursor.execute('SELECT COUNT(*) FROM price_data WHERE timestamp >= NOW() - INTERVAL 1 HOUR')
    price_records = cursor.fetchone()[0]
    
    # Sentiment signals
    cursor.execute('SELECT COUNT(*) FROM real_time_sentiment_signals')
    sentiment_total = cursor.fetchone()[0]
    
    # News articles
    cursor.execute('SELECT COUNT(*) FROM crypto_news_articles')
    news_count = cursor.fetchone()[0]
    
    print(f'  📊 Price records (1h): {price_records}')
    print(f'  🎭 Total sentiment signals: {sentiment_total:,}')
    print(f'  📰 News articles: {news_count}')
    
    conn.close()
except Exception as e:
    print(f'  ❌ Database connection failed: {str(e)[:50]}...')
" 2>/dev/null || echo "  ❌ Unable to fetch data statistics"
    echo
}

# Function to show recent events
show_recent_events() {
    echo -e "${RED}⚠️  RECENT EVENTS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get recent events
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' 2>/dev/null | tail -5 | while read line; do
        if echo "$line" | grep -q "Warning"; then
            echo -e "  ${YELLOW}⚠️  $(echo $line | cut -c 1-70)...${NC}"
        elif echo "$line" | grep -q "Error"; then
            echo -e "  ${RED}❌ $(echo $line | cut -c 1-70)...${NC}"
        else
            echo -e "  ${GREEN}ℹ️  $(echo $line | cut -c 1-70)...${NC}"
        fi
    done
    echo
}

# Function to show active CronJobs
show_cronjobs() {
    echo -e "${BLUE}⏰ CRONJOB STATUS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    kubectl get cronjobs -n $NAMESPACE --no-headers 2>/dev/null | while read line; do
        name=$(echo $line | awk '{print $1}')
        schedule=$(echo $line | awk '{print $2}')
        suspend=$(echo $line | awk '{print $3}')
        active=$(echo $line | awk '{print $4}')
        last_schedule=$(echo $line | awk '{print $5}')
        
        if [ "$suspend" = "True" ]; then
            echo -e "  ${YELLOW}⏸️  $name${NC} (suspended)"
        elif [ "$active" != "0" ]; then
            echo -e "  ${GREEN}▶️  $name${NC} (active: $active)"
        else
            echo -e "  ${BLUE}⏲️  $name${NC} (schedule: $schedule)"
        fi
    done
    echo
}

# Main dashboard loop
main() {
    local refresh_rate=${1:-5}  # Default 5 seconds
    
    echo -e "${GREEN}Starting dashboard... Press Ctrl+C to exit${NC}"
    sleep 2
    
    while true; do
        show_header
        show_service_status
        show_resource_usage
        show_data_stats
        show_cronjobs
        show_recent_events
        
        echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
        echo -e "${CYAN}Refreshing in $refresh_rate seconds... (Press Ctrl+C to exit)${NC}"
        
        sleep $refresh_rate
    done
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${GREEN}Dashboard stopped.${NC}"; exit 0' INT

# Run dashboard
main "$@"