#!/bin/bash

# ML Market Collector Monitoring Script
# Monitors health, data collection, and ML feature generation

NAMESPACE="crypto-data-collection"
DEPLOYMENT_NAME="ml-market-collector"

echo "📊 ML Market Collector Monitoring Dashboard"
echo "==========================================="

# Check deployment status
echo ""
echo "🚀 Deployment Status:"
kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o wide

# Check pod status and resource usage
echo ""
echo "💻 Pod Status:"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o wide

echo ""
echo "📈 Resource Usage:"
kubectl top pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME 2>/dev/null || echo "   (Metrics server not available)"

# Check service status
echo ""
echo "🌐 Service Status:"
kubectl get service $DEPLOYMENT_NAME -n $NAMESPACE

# Get recent logs
echo ""
echo "📝 Recent Logs (last 20 lines):"
kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=20

# Check if API is responding
echo ""
echo "🔍 API Health Check:"

# Port forward to check API health
kubectl port-forward -n $NAMESPACE service/$DEPLOYMENT_NAME 8080:8000 &
PORT_FORWARD_PID=$!
sleep 3

# Test endpoints
echo "   Testing health endpoint..."
if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "   ✅ Health endpoint responding"
else
    echo "   ❌ Health endpoint not responding"
fi

echo "   Testing status endpoint..."
if curl -s -f http://localhost:8080/status > /dev/null 2>&1; then
    echo "   ✅ Status endpoint responding"
    echo "   📊 Current status:"
    curl -s http://localhost:8080/status | python3 -m json.tool 2>/dev/null || echo "   (Unable to format JSON)"
else
    echo "   ❌ Status endpoint not responding"
fi

echo "   Testing ML features endpoint..."
if curl -s -f http://localhost:8080/ml-features > /dev/null 2>&1; then
    echo "   ✅ ML features endpoint responding"
    ML_FEATURE_COUNT=$(curl -s http://localhost:8080/ml-features | python3 -c "import json, sys; data=json.load(sys.stdin); print(len(data.get('features', {})))" 2>/dev/null || echo "0")
    echo "   📈 ML feature count: $ML_FEATURE_COUNT"
    
    if [ "$ML_FEATURE_COUNT" -gt "30" ]; then
        echo "   ✅ Feature count looks healthy (target: ~40)"
    else
        echo "   ⚠️  Low feature count (target: ~40)"
    fi
else
    echo "   ❌ ML features endpoint not responding"
fi

# Clean up port forward
kill $PORT_FORWARD_PID 2>/dev/null

# Check for errors in logs
echo ""
echo "🔍 Error Analysis:"
ERROR_COUNT=$(kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=100 | grep -i error | wc -l)
WARNING_COUNT=$(kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=100 | grep -i warning | wc -l)

echo "   Errors in last 100 log lines: $ERROR_COUNT"
echo "   Warnings in last 100 log lines: $WARNING_COUNT"

if [ "$ERROR_COUNT" -gt "0" ]; then
    echo "   ⚠️  Recent errors found:"
    kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=100 | grep -i error | tail -3
fi

# Check database connectivity
echo ""
echo "🗄️  Database Connectivity:"
DB_HOST=$(kubectl get configmap centralized-db-config -n $NAMESPACE -o jsonpath='{.data.MYSQL_HOST}' 2>/dev/null || echo "unknown")
echo "   Database host: $DB_HOST"

# Test manual collection trigger
echo ""
echo "🚀 Testing Manual Collection Trigger:"
kubectl port-forward -n $NAMESPACE service/$DEPLOYMENT_NAME 8081:8000 &
TRIGGER_PID=$!
sleep 2

if curl -s -X POST http://localhost:8081/collect > /dev/null 2>&1; then
    echo "   ✅ Manual collection trigger successful"
else
    echo "   ❌ Manual collection trigger failed"
fi

kill $TRIGGER_PID 2>/dev/null

# Check CronJob status
echo ""
echo "⏰ Scheduled Collection Status:"
kubectl get cronjob ml-market-collector-manual-trigger -n $NAMESPACE 2>/dev/null || echo "   CronJob not found"

# Configuration summary
echo ""
echo "⚙️  Configuration Summary:"
echo "   Collection interval: $(kubectl get configmap ml-market-collector-config -n $NAMESPACE -o jsonpath='{.data.COLLECTION_INTERVAL_MINUTES}' 2>/dev/null || echo 'unknown') minutes"
echo "   Log level: $(kubectl get configmap ml-market-collector-config -n $NAMESPACE -o jsonpath='{.data.LOG_LEVEL}' 2>/dev/null || echo 'unknown')"
echo "   Target ML features: $(kubectl get configmap ml-market-collector-config -n $NAMESPACE -o jsonpath='{.data.ML_FEATURE_COUNT_TARGET}' 2>/dev/null || echo 'unknown')"

echo ""
echo "📋 Troubleshooting Commands:"
echo "   View live logs: kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME -f"
echo "   Restart pods: kubectl rollout restart deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
echo "   Scale up: kubectl scale deployment/$DEPLOYMENT_NAME --replicas=2 -n $NAMESPACE"
echo "   Get pod shell: kubectl exec -it deployment/$DEPLOYMENT_NAME -n $NAMESPACE -- /bin/bash"
echo "   Port forward: kubectl port-forward -n $NAMESPACE service/$DEPLOYMENT_NAME 8080:8000"