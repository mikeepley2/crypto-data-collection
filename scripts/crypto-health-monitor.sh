#!/bin/bash
# Enhanced Crypto Data Collection Health Monitor
# 
# This script provides comprehensive monitoring of the crypto data collection system
# and can be run as a Kubernetes CronJob for regular health checks.

set -euo pipefail

# Configuration
NAMESPACE="crypto-collectors"
LOG_FILE="/tmp/crypto-health-$(date +%Y%m%d-%H%M%S).log"
ALERT_THRESHOLD_PRICE_SUCCESS_RATE=90
ALERT_THRESHOLD_TOTAL_DATA_SOURCES=4

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_colored() {
    local color=$1
    local message=$2
    echo -e "${color}$(date '+%Y-%m-%d %H:%M:%S') - $message${NC}" | tee -a "$LOG_FILE"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log_colored $RED "ERROR: kubectl not found"
    exit 1
fi

# Start health check
log_colored $BLUE "🏥 CRYPTO DATA COLLECTION HEALTH CHECK STARTED"
log_colored $BLUE "================================================"

# 1. Check Pod Health
log_colored $YELLOW "📊 Checking Pod Health..."
ENHANCED_CRYPTO_POD=$(kubectl get pods -n $NAMESPACE -l app=enhanced-crypto-prices -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
MATERIALIZED_POD=$(kubectl get pods -n $NAMESPACE -l app=materialized-updater -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [[ -n "$ENHANCED_CRYPTO_POD" ]]; then
    POD_STATUS=$(kubectl get pod $ENHANCED_CRYPTO_POD -n $NAMESPACE -o jsonpath='{.status.phase}')
    if [[ "$POD_STATUS" == "Running" ]]; then
        log_colored $GREEN "✅ Enhanced-crypto-prices pod: $ENHANCED_CRYPTO_POD (Running)"
    else
        log_colored $RED "❌ Enhanced-crypto-prices pod: $ENHANCED_CRYPTO_POD ($POD_STATUS)"
    fi
else
    log_colored $RED "❌ Enhanced-crypto-prices pod: NOT FOUND"
fi

if [[ -n "$MATERIALIZED_POD" ]]; then
    POD_STATUS=$(kubectl get pod $MATERIALIZED_POD -n $NAMESPACE -o jsonpath='{.status.phase}')
    if [[ "$POD_STATUS" == "Running" ]]; then
        log_colored $GREEN "✅ Materialized-updater pod: $MATERIALIZED_POD (Running)"
    else
        log_colored $RED "❌ Materialized-updater pod: $MATERIALIZED_POD ($POD_STATUS)"
    fi
else
    log_colored $RED "❌ Materialized-updater pod: NOT FOUND"
fi

# 2. Check CronJob Status
log_colored $YELLOW "⏰ Checking CronJob Status..."
CRONJOB_STATUS=$(kubectl get cronjob enhanced-crypto-prices-collector -n $NAMESPACE -o jsonpath='{.spec.suspend}' 2>/dev/null || echo "NOT_FOUND")
if [[ "$CRONJOB_STATUS" == "false" ]]; then
    log_colored $GREEN "✅ Price collection CronJob: Active"
    LAST_SCHEDULE=$(kubectl get cronjob enhanced-crypto-prices-collector -n $NAMESPACE -o jsonpath='{.status.lastScheduleTime}' 2>/dev/null || echo "")
    if [[ -n "$LAST_SCHEDULE" ]]; then
        log_colored $GREEN "   Last scheduled: $LAST_SCHEDULE"
    fi
elif [[ "$CRONJOB_STATUS" == "true" ]]; then
    log_colored $YELLOW "⚠️  Price collection CronJob: Suspended"
else
    log_colored $RED "❌ Price collection CronJob: NOT FOUND"
fi

# 3. Check Recent Data Collection (if pods are available)
if [[ -n "$ENHANCED_CRYPTO_POD" ]]; then
    log_colored $YELLOW "💰 Checking Recent Price Data..."
    
    # Get recent price data count
    RECENT_PRICE_COUNT=$(kubectl exec $ENHANCED_CRYPTO_POD -n $NAMESPACE -- python -c "
import sys; sys.path.append('/app'); 
from shared.database_pool import execute_query;
result = execute_query('SELECT COUNT(*) FROM crypto_prices.price_data_real WHERE timestamp > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 HOUR))', fetch_results=True);
print(result[0][0])
" 2>/dev/null || echo "0")
    
    if [[ "$RECENT_PRICE_COUNT" -gt 100 ]]; then
        log_colored $GREEN "✅ Recent price records (last hour): $RECENT_PRICE_COUNT"
    elif [[ "$RECENT_PRICE_COUNT" -gt 0 ]]; then
        log_colored $YELLOW "⚠️  Recent price records (last hour): $RECENT_PRICE_COUNT (Low)"
    else
        log_colored $RED "❌ Recent price records (last hour): $RECENT_PRICE_COUNT"
    fi
    
    # Check price data freshness
    LATEST_PRICE_TIME=$(kubectl exec $ENHANCED_CRYPTO_POD -n $NAMESPACE -- python -c "
import sys; sys.path.append('/app');
from shared.database_pool import execute_query;
result = execute_query('SELECT FROM_UNIXTIME(MAX(timestamp)) FROM crypto_prices.price_data_real', fetch_results=True);
print(result[0][0])
" 2>/dev/null || echo "None")
    
    if [[ "$LATEST_PRICE_TIME" != "None" ]]; then
        log_colored $GREEN "✅ Latest price data: $LATEST_PRICE_TIME"
    else
        log_colored $RED "❌ Latest price data: No recent data found"
    fi
fi

# 4. Check Other Data Sources
if [[ -n "$MATERIALIZED_POD" ]]; then
    log_colored $YELLOW "📈 Checking Other Data Sources..."
    
    # Check sentiment data
    SENTIMENT_COUNT=$(kubectl exec $MATERIALIZED_POD -n $NAMESPACE -- python -c "
import sys; sys.path.append('/app');
from shared.database_pool import execute_query;
result = execute_query('SELECT COUNT(*) FROM crypto_news.crypto_sentiment_data WHERE timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 DAY))', fetch_results=True);
print(result[0][0])
" 2>/dev/null || echo "0")
    
    if [[ "$SENTIMENT_COUNT" -gt 1000 ]]; then
        log_colored $GREEN "✅ Crypto sentiment (24h): $SENTIMENT_COUNT records"
    elif [[ "$SENTIMENT_COUNT" -gt 0 ]]; then
        log_colored $YELLOW "⚠️  Crypto sentiment (24h): $SENTIMENT_COUNT records (Low)"
    else
        log_colored $RED "❌ Crypto sentiment (24h): $SENTIMENT_COUNT records"
    fi
    
    # Check technical indicators
    TECH_INDICATORS_COUNT=$(kubectl exec $MATERIALIZED_POD -n $NAMESPACE -- python -c "
import sys; sys.path.append('/app');
from shared.database_pool import execute_query;
result = execute_query('SELECT COUNT(*) FROM crypto_news.technical_indicators WHERE timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 DAY))', fetch_results=True);
print(result[0][0])
" 2>/dev/null || echo "0")
    
    if [[ "$TECH_INDICATORS_COUNT" -gt 5000 ]]; then
        log_colored $GREEN "✅ Technical indicators (24h): $TECH_INDICATORS_COUNT records"
    elif [[ "$TECH_INDICATORS_COUNT" -gt 0 ]]; then
        log_colored $YELLOW "⚠️  Technical indicators (24h): $TECH_INDICATORS_COUNT records (Low)"
    else
        log_colored $RED "❌ Technical indicators (24h): $TECH_INDICATORS_COUNT records"
    fi
fi

# 5. Summary and Recommendations
log_colored $BLUE "📋 HEALTH CHECK SUMMARY"
log_colored $BLUE "======================="

# Calculate overall health score
HEALTH_SCORE=0
MAX_SCORE=10

# Pod health (2 points each)
if [[ -n "$ENHANCED_CRYPTO_POD" ]]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 2))
fi
if [[ -n "$MATERIALIZED_POD" ]]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 2))
fi

# CronJob health (2 points)
if [[ "$CRONJOB_STATUS" == "false" ]]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 2))
fi

# Data collection health (4 points total)
if [[ "$RECENT_PRICE_COUNT" -gt 100 ]]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 2))
elif [[ "$RECENT_PRICE_COUNT" -gt 0 ]]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
fi

if [[ "$SENTIMENT_COUNT" -gt 1000 && "$TECH_INDICATORS_COUNT" -gt 5000 ]]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 2))
elif [[ "$SENTIMENT_COUNT" -gt 0 || "$TECH_INDICATORS_COUNT" -gt 0 ]]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
fi

# Display health score
HEALTH_PERCENTAGE=$((HEALTH_SCORE * 100 / MAX_SCORE))
if [[ $HEALTH_PERCENTAGE -ge 90 ]]; then
    log_colored $GREEN "🟢 Overall System Health: $HEALTH_PERCENTAGE% ($HEALTH_SCORE/$MAX_SCORE) - EXCELLENT"
elif [[ $HEALTH_PERCENTAGE -ge 70 ]]; then
    log_colored $YELLOW "🟡 Overall System Health: $HEALTH_PERCENTAGE% ($HEALTH_SCORE/$MAX_SCORE) - GOOD"
elif [[ $HEALTH_PERCENTAGE -ge 50 ]]; then
    log_colored $YELLOW "🟠 Overall System Health: $HEALTH_PERCENTAGE% ($HEALTH_SCORE/$MAX_SCORE) - FAIR"
else
    log_colored $RED "🔴 Overall System Health: $HEALTH_PERCENTAGE% ($HEALTH_SCORE/$MAX_SCORE) - POOR"
fi

log_colored $BLUE "Health check completed. Log saved to: $LOG_FILE"
log_colored $BLUE "================================================"

exit 0