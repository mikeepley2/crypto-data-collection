#!/bin/bash

echo "🧪 Testing K8s Onchain Collector Deployment"
echo "============================================"

# Check namespace
echo "📁 Checking namespace..."
kubectl get namespace crypto-data-collection

# Check CronJob
echo ""
echo "⏰ Checking CronJob..."
kubectl get cronjobs -n crypto-data-collection | grep onchain || echo "No onchain CronJob found"

# Check recent jobs
echo ""
echo "📋 Recent onchain jobs..."
kubectl get jobs -n crypto-data-collection | grep onchain | tail -5

# Check pods
echo ""
echo "🔍 Recent onchain pods..."
kubectl get pods -n crypto-data-collection | grep onchain | tail -5

# Test manual job creation
echo ""
echo "🚀 Creating manual test job..."
kubectl create job --from=cronjob/onchain-collector onchain-deployment-test -n crypto-data-collection 2>/dev/null || echo "CronJob not found or job creation failed"

# Wait and check status
sleep 5
echo ""
echo "📊 Test job status..."
kubectl get jobs -n crypto-data-collection | grep onchain-deployment-test || echo "Test job not found"

echo ""
echo "✅ K8s deployment test completed"