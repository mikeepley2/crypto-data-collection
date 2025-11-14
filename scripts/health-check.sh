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

# Function to restart unhealthy deployment
restart_deployment() {
    local deployment=$1
    echo "🔄 Restarting $deployment..."
    kubectl rollout restart deployment/$deployment -n $NAMESPACE
    kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=300s
}

# Function to clean up failed resources
cleanup_failed_resources() {
    echo "🧹 Cleaning up failed resources..."
    
    # Delete failed pods
    kubectl delete pods --field-selector=status.phase=Failed -n $NAMESPACE --ignore-not-found=true
    
    # Delete completed jobs older than 1 day
    kubectl get jobs -n $NAMESPACE -o json | jq -r '
        .items[] | 
        select(.status.conditions[]?.type=="Complete" and 
               .status.conditions[]?.status=="True" and 
               (now - (.status.completionTime | fromdateiso8601)) > 86400) | 
        .metadata.name' | xargs -r kubectl delete job -n $NAMESPACE
    
    # Delete pods in ImagePullBackOff state
    kubectl get pods -n $NAMESPACE --field-selector=status.phase=Pending -o json | jq -r '
        .items[] | 
        select(.status.containerStatuses[]?.state.waiting.reason == "ErrImageNeverPull" or 
               .status.containerStatuses[]?.state.waiting.reason == "ImagePullBackOff") | 
        .metadata.name' | xargs -r kubectl delete pod -n $NAMESPACE
    
    echo "✅ Cleanup completed"
}

# Function to check for duplicate pods
check_duplicates() {
    echo "🔍 Checking for duplicate/excess pods..."
    
    kubectl get deployments -n $NAMESPACE -o json | jq -r '
        .items[] | 
        select(.status.replicas > .spec.replicas) | 
        "⚠️ " + .metadata.name + " has excess replicas: " + (.status.replicas|tostring) + "/" + (.spec.replicas|tostring)'
}

# Function to validate resource usage
check_resource_usage() {
    echo "📊 Resource Usage Summary:"
    
    # Get node resource usage
    kubectl top nodes 2>/dev/null | head -5
    
    # Get pod resource usage
    echo "Top 5 CPU consuming pods:"
    kubectl top pods -n $NAMESPACE --sort-by=cpu 2>/dev/null | head -6
    
    echo "Top 5 Memory consuming pods:"
    kubectl top pods -n $NAMESPACE --sort-by=memory 2>/dev/null | head -6
}

# Function to check CronJob status
check_cronjobs() {
    echo "⏰ CronJob Status:"
    kubectl get cronjobs -n $NAMESPACE -o custom-columns=NAME:.metadata.name,SCHEDULE:.spec.schedule,SUSPEND:.spec.suspend,ACTIVE:.status.active,LAST-SCHEDULE:.status.lastScheduleTime
}

# Main execution
main() {
    echo "📅 $(date)"
    echo ""
    
    # Core deployments to monitor
    CORE_DEPLOYMENTS=(
        "enhanced-crypto-prices"
        "crypto-news-collector" 
        "reddit-sentiment-collector"
        "stock-sentiment-collector"
        "sentiment-microservice"
        "realtime-materialized-updater"
        "onchain-data-collector"
        "social-other"
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
    
    # Auto-restart unhealthy services if requested
    if [ "$1" = "--auto-heal" ] && [ $unhealthy_count -gt 0 ]; then
        echo "🚑 Auto-healing mode: Restarting unhealthy services..."
        for deployment in "${CORE_DEPLOYMENTS[@]}"; do
            if ! check_deployment_health $deployment >/dev/null 2>&1; then
                restart_deployment $deployment
            fi
        done
    fi
    
    # Other checks
    check_duplicates
    echo ""
    check_cronjobs
    echo ""
    check_resource_usage
    echo ""
    
    # Cleanup if requested
    if [ "$1" = "--cleanup" ] || [ "$2" = "--cleanup" ]; then
        cleanup_failed_resources
    fi
    
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