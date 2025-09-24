#!/bin/bash
# Comprehensive Service Maintenance Script
# ========================================

NAMESPACE="crypto-collectors"
LOG_FILE="/tmp/crypto-maintenance-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

colored_log() {
    local color=$1
    local message=$2
    echo -e "${color}$(date '+%Y-%m-%d %H:%M:%S') - $message${NC}" | tee -a $LOG_FILE
}

# Function to perform automated maintenance
automated_maintenance() {
    colored_log $BLUE "🔧 Starting automated maintenance..."
    
    # 1. Clean up failed/completed resources
    colored_log $YELLOW "🧹 Cleaning up failed resources..."
    
    # Delete failed pods
    failed_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed --no-headers 2>/dev/null | wc -l)
    if [ $failed_pods -gt 0 ]; then
        kubectl delete pods --field-selector=status.phase=Failed -n $NAMESPACE --ignore-not-found=true
        colored_log $GREEN "✅ Cleaned up $failed_pods failed pods"
    fi
    
    # Delete completed jobs older than 1 day
    old_jobs=$(kubectl get jobs -n $NAMESPACE -o json 2>/dev/null | jq -r '
        .items[] | 
        select(.status.conditions[]?.type=="Complete" and 
               .status.conditions[]?.status=="True" and 
               (now - (.status.completionTime | fromdateiso8601)) > 86400) | 
        .metadata.name' | wc -l)
    
    if [ $old_jobs -gt 0 ]; then
        kubectl get jobs -n $NAMESPACE -o json | jq -r '
            .items[] | 
            select(.status.conditions[]?.type=="Complete" and 
                   .status.conditions[]?.status=="True" and 
                   (now - (.status.completionTime | fromdateiso8601)) > 86400) | 
            .metadata.name' | xargs -r kubectl delete job -n $NAMESPACE
        colored_log $GREEN "✅ Cleaned up $old_jobs old completed jobs"
    fi
    
    # 2. Check for resource leaks
    colored_log $YELLOW "🔍 Checking for resource leaks..."
    
    # Find pods consuming too much memory
    kubectl top pods -n $NAMESPACE --sort-by=memory 2>/dev/null | head -6 | tail -5 | while read line; do
        memory=$(echo $line | awk '{print $3}' | sed 's/Mi//')
        pod=$(echo $line | awk '{print $1}')
        if [ "$memory" -gt 1000 ] 2>/dev/null; then
            colored_log $YELLOW "⚠️ High memory usage: $pod using ${memory}Mi"
        fi
    done
    
    # 3. Restart unhealthy services
    colored_log $YELLOW "🏥 Checking service health..."
    
    CORE_SERVICES=("enhanced-crypto-prices" "crypto-news-collector" "stock-sentiment-collector" "realtime-materialized-updater")
    
    for service in "${CORE_SERVICES[@]}"; do
        # Check if deployment exists and get replica status
        if kubectl get deployment $service -n $NAMESPACE >/dev/null 2>&1; then
            ready=$(kubectl get deployment $service -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            desired=$(kubectl get deployment $service -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
            
            if [ "$ready" != "$desired" ] || [ "$ready" = "0" ]; then
                colored_log $RED "❌ $service unhealthy ($ready/$desired), restarting..."
                kubectl rollout restart deployment/$service -n $NAMESPACE
                kubectl rollout status deployment/$service -n $NAMESPACE --timeout=300s
                
                if [ $? -eq 0 ]; then
                    colored_log $GREEN "✅ $service restarted successfully"
                else
                    colored_log $RED "❌ $service restart failed"
                fi
            else
                colored_log $GREEN "✅ $service healthy ($ready/$desired)"
            fi
        fi
    done
    
    # 4. Update resource quotas if needed
    colored_log $YELLOW "📊 Checking resource usage..."
    
    total_cpu_requests=$(kubectl get pods -n $NAMESPACE -o json | jq -r '
        [.items[].spec.containers[].resources.requests.cpu? // "0m"] | 
        map(rtrimstr("m") | tonumber) | add')
    
    if [ "$total_cpu_requests" -gt 8000 ]; then  # > 8 CPU cores
        colored_log $YELLOW "⚠️ High CPU requests: ${total_cpu_requests}m"
    fi
    
    # 5. Check for configuration drift
    colored_log $YELLOW "🎯 Checking for configuration drift..."
    
    # Ensure all core services have proper labels
    kubectl get deployments -n $NAMESPACE -l component!=data-collector -o name | while read deployment; do
        kubectl patch $deployment -n $NAMESPACE -p '{"metadata":{"labels":{"component":"data-collector"}}}'
    done
    
    colored_log $GREEN "✅ Automated maintenance completed"
}

# Function to generate health report
generate_health_report() {
    colored_log $BLUE "📋 Generating health report..."
    
    echo "================================" >> $LOG_FILE
    echo "CRYPTO DATA COLLECTION HEALTH REPORT" >> $LOG_FILE
    echo "Generated: $(date)" >> $LOG_FILE
    echo "================================" >> $LOG_FILE
    
    # Deployment status
    echo "" >> $LOG_FILE
    echo "DEPLOYMENT STATUS:" >> $LOG_FILE
    kubectl get deployments -n $NAMESPACE -o custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,AVAILABLE:.status.availableReplicas,UP-TO-DATE:.status.updatedReplicas >> $LOG_FILE
    
    # Pod resource usage
    echo "" >> $LOG_FILE
    echo "TOP RESOURCE CONSUMERS:" >> $LOG_FILE
    kubectl top pods -n $NAMESPACE --sort-by=memory 2>/dev/null | head -6 >> $LOG_FILE || echo "Resource metrics not available" >> $LOG_FILE
    
    # CronJob status
    echo "" >> $LOG_FILE
    echo "CRONJOB STATUS:" >> $LOG_FILE
    kubectl get cronjobs -n $NAMESPACE >> $LOG_FILE
    
    # Recent events
    echo "" >> $LOG_FILE
    echo "RECENT EVENTS:" >> $LOG_FILE
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10 >> $LOG_FILE
    
    colored_log $GREEN "✅ Health report generated: $LOG_FILE"
}

# Function to validate data flow
validate_data_flow() {
    colored_log $BLUE "🔄 Validating data flow..."
    
    # Check if services are accessible
    services=("enhanced-crypto-prices" "crypto-news-collector" "stock-sentiment-collector")
    
    for service in "${services[@]}"; do
        if kubectl get service $service -n $NAMESPACE >/dev/null 2>&1; then
            # Try to reach health endpoint
            kubectl run test-$service --rm -i --restart=Never --image=curlimages/curl:latest -n $NAMESPACE -- \
                curl -sf http://$service.$NAMESPACE.svc.cluster.local:8000/health >/dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                colored_log $GREEN "✅ $service data flow healthy"
            else
                colored_log $RED "❌ $service data flow issues"
            fi
        fi
    done
}

# Function to setup monitoring alerts
setup_alerts() {
    colored_log $BLUE "🚨 Setting up monitoring alerts..."
    
    # Create a simple webhook for alerts (example)
    kubectl create configmap alert-webhook -n $NAMESPACE --from-literal=webhook.sh='
#!/bin/bash
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:8080/webhook}"
curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d "{
    \"service\": \"$1\",
    \"status\": \"$2\",
    \"message\": \"$3\",
    \"timestamp\": \"$(date -Iseconds)\"
}"
' --dry-run=client -o yaml | kubectl apply -f -
    
    colored_log $GREEN "✅ Alert system configured"
}

# Main execution
main() {
    colored_log $BLUE "🚀 Starting Crypto Data Collection Maintenance"
    echo "Log file: $LOG_FILE"
    
    case "${1:-auto}" in
        "auto")
            automated_maintenance
            generate_health_report
            ;;
        "health-check")
            generate_health_report
            ;;
        "data-flow")
            validate_data_flow
            ;;
        "alerts")
            setup_alerts
            ;;
        "full")
            automated_maintenance
            validate_data_flow
            generate_health_report
            setup_alerts
            ;;
        *)
            echo "Usage: $0 {auto|health-check|data-flow|alerts|full}"
            echo ""
            echo "Commands:"
            echo "  auto        - Run automated maintenance (default)"
            echo "  health-check - Generate health report only"
            echo "  data-flow   - Validate data flow"
            echo "  alerts      - Setup monitoring alerts"
            echo "  full        - Run all maintenance tasks"
            exit 1
            ;;
    esac
    
    colored_log $GREEN "🎉 Maintenance completed successfully!"
    echo "Detailed logs available at: $LOG_FILE"
}

# Make it executable and run
main "$@"