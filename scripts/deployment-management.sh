#!/bin/bash
# Deployment Management Script
# ============================

NAMESPACE="crypto-collectors"

# Function to safely update deployment
safe_deployment_update() {
    local deployment=$1
    local image=$2
    local max_unavailable=${3:-0}
    local max_surge=${4:-1}
    
    echo "🚀 Safely updating $deployment to $image..."
    
    # Update deployment strategy first
    kubectl patch deployment $deployment -n $NAMESPACE -p '{
        "spec": {
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {
                    "maxUnavailable": "'$max_unavailable'",
                    "maxSurge": "'$max_surge'"
                }
            }
        }
    }'
    
    # Update image
    kubectl set image deployment/$deployment -n $NAMESPACE \
        $deployment=$image
    
    # Wait for rollout
    if kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=600s; then
        echo "✅ $deployment updated successfully"
        return 0
    else
        echo "❌ $deployment update failed, rolling back..."
        kubectl rollout undo deployment/$deployment -n $NAMESPACE
        return 1
    fi
}

# Function to scale deployment safely
safe_scale() {
    local deployment=$1
    local replicas=$2
    
    echo "📏 Scaling $deployment to $replicas replicas..."
    
    kubectl scale deployment $deployment -n $NAMESPACE --replicas=$replicas
    kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=300s
    
    if [ $? -eq 0 ]; then
        echo "✅ $deployment scaled successfully"
    else
        echo "❌ $deployment scaling failed"
        return 1
    fi
}

# Function to check for resource conflicts
check_resource_conflicts() {
    echo "🔍 Checking for resource conflicts..."
    
    # Check for duplicate service ports
    kubectl get services -n $NAMESPACE -o json | jq -r '
        .items[] | 
        {name: .metadata.name, ports: [.spec.ports[]?.port]} |
        @json' | \
    jq -s 'group_by(.ports) | map(select(length > 1)) | 
           map("⚠️ Port conflict: " + (.[0].ports | @json) + " used by: " + ([.[].name] | join(", ")))'
    
    # Check for pods with same labels but different owners
    kubectl get pods -n $NAMESPACE -o json | jq -r '
        .items[] | 
        select(.metadata.ownerReferences | length > 0) |
        {
            name: .metadata.name,
            owner: .metadata.ownerReferences[0].name,
            labels: .metadata.labels | to_entries | map(.key + "=" + .value) | sort
        }' | \
    jq -s 'group_by(.labels) | map(select(length > 1 and ([.[].owner] | unique | length) > 1)) | 
           map("⚠️ Label conflict: " + (.[0].labels | @json) + " used by: " + ([.[].owner] | unique | join(", ")))'
}

# Function to implement circuit breaker pattern
circuit_breaker_check() {
    local service=$1
    local health_endpoint="http://$service.crypto-collectors.svc.cluster.local:8000/health"
    local failure_threshold=3
    local recovery_timeout=300
    
    echo "🔌 Circuit breaker check for $service..."
    
    failures=0
    for i in {1..5}; do
        if ! curl -sf $health_endpoint >/dev/null 2>&1; then
            ((failures++))
            echo "❌ Health check $i failed for $service"
        else
            echo "✅ Health check $i passed for $service"
        fi
        sleep 2
    done
    
    if [ $failures -ge $failure_threshold ]; then
        echo "🚨 Circuit breaker OPEN for $service (failures: $failures/$failure_threshold)"
        echo "   Implementing recovery strategy..."
        
        # Scale down to 0, then back up (forced restart)
        kubectl scale deployment $service -n $NAMESPACE --replicas=0
        sleep 10
        kubectl scale deployment $service -n $NAMESPACE --replicas=1
        
        # Wait for recovery
        sleep $recovery_timeout
        
        # Test again
        if curl -sf $health_endpoint >/dev/null 2>&1; then
            echo "✅ Circuit breaker CLOSED for $service - service recovered"
        else
            echo "❌ Circuit breaker remains OPEN for $service - manual intervention needed"
        fi
    else
        echo "✅ Circuit breaker CLOSED for $service"
    fi
}

# Function to prevent deployment drift
prevent_drift() {
    echo "🎯 Checking for configuration drift..."
    
    # Check if deployments match expected configuration
    kubectl get deployments -n $NAMESPACE -o json | jq -r '
        .items[] | 
        select(.metadata.labels.component == "data-collector") |
        {
            name: .metadata.name,
            replicas: .spec.replicas,
            image: .spec.template.spec.containers[0].image,
            resources: .spec.template.spec.containers[0].resources // "not_set"
        } | 
        @json' | while read deployment; do
            name=$(echo $deployment | jq -r '.name')
            replicas=$(echo $deployment | jq -r '.replicas')
            resources=$(echo $deployment | jq -r '.resources')
            
            # Check if core services have proper replica count
            if [[ "$name" =~ ^(enhanced-crypto-prices|stock-sentiment-collector|crypto-news-collector)$ ]]; then
                if [ "$replicas" != "1" ]; then
                    echo "⚠️ $name should have 1 replica, has $replicas"
                fi
            fi
            
            # Check if resources are set
            if [ "$resources" == "not_set" ]; then
                echo "⚠️ $name missing resource limits/requests"
            fi
        done
}

# Main execution based on command
case "${1:-check}" in
    "update")
        safe_deployment_update "$2" "$3" "$4" "$5"
        ;;
    "scale")
        safe_scale "$2" "$3"
        ;;
    "circuit-breaker")
        circuit_breaker_check "$2"
        ;;
    "conflict-check")
        check_resource_conflicts
        ;;
    "drift-check")
        prevent_drift
        ;;
    "full-check")
        echo "🔍 Running full deployment health check..."
        check_resource_conflicts
        echo ""
        prevent_drift
        echo ""
        # Check circuit breakers for core services
        for service in enhanced-crypto-prices crypto-news-collector stock-sentiment-collector; do
            circuit_breaker_check $service
            echo ""
        done
        ;;
    *)
        echo "Usage: $0 {update|scale|circuit-breaker|conflict-check|drift-check|full-check}"
        echo ""
        echo "Commands:"
        echo "  update <deployment> <image> [max-unavailable] [max-surge]"
        echo "  scale <deployment> <replicas>"
        echo "  circuit-breaker <service>"
        echo "  conflict-check"
        echo "  drift-check"
        echo "  full-check"
        exit 1
        ;;
esac