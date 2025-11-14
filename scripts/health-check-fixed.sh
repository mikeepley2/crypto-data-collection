#!/bin/bash
# Service Management Script
# =========================

echo "🔍 Crypto Data Collection Service Health Check"
echo "=============================================="

NAMESPACE="crypto-data-collection"

# Function to check deployment health
check_deployment_health() {
    local deployment=$1
    local replicas=$(kubectl get deployment $deployment -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local desired=$(kubectl get deployment $deployment -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")

    if [ "$replicas" = "$desired" ] && [ "$replicas" != "0" ]; then
        echo "✅ $deployment: $replicas/$desired ready"
        return 0
    else
        echo "❌ $deployment: $replicas/$desired ready"
        return 1
    fi
}

# Main execution
main() {
    echo "📅 $(date)"
    echo ""

    # Core deployments to monitor - UPDATED TO MATCH ACTUAL DEPLOYMENTS
    CORE_DEPLOYMENTS=(
        "enhanced-crypto-prices"
        "enhanced-crypto-news"
        "enhanced-macro-collector"
        "enhanced-technical-calculator"
        "enhanced-ohlc-collector"
        "derivatives-collector"
        "ml-market-collector"
        "enhanced-materialized-updater"
        "enhanced-onchain-collector"
        "enhanced-sentiment-collector-ml"
    )

    unhealthy_count=0

    # Check each core deployment
    echo "🏥 Health Status:"
    for deployment in "${CORE_DEPLOYMENTS[@]}"; do
        if ! check_deployment_health $deployment; then
            ((unhealthy_count++))
        fi
    done

    echo ""
    echo "📈 Summary: $((${#CORE_DEPLOYMENTS[@]} - unhealthy_count))/${#CORE_DEPLOYMENTS[@]} core services healthy"

    if [ $unhealthy_count -eq 0 ]; then
        echo "✅ All core services are healthy!"
        exit 0
    else
        echo "⚠️ $unhealthy_count service(s) need attention"
        exit 1
    fi
}

# Run with parameters
main "$@"
