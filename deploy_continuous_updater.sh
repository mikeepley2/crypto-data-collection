#!/bin/bash
# Complete cleanup and deployment script for materialized updater

echo "🧹 Phase 1: Cleaning up CronJob mess..."

# Delete the problematic CronJob
kubectl delete cronjob materialized-updater-cron -n crypto-collectors --ignore-not-found=true
echo "   ✅ Deleted CronJob"

# Delete all materialized-updater jobs (this may take a while)
echo "   🗑️ Deleting all materialized-updater jobs..."
kubectl get jobs -n crypto-collectors -o name | grep materialized-updater-cron | head -20 | xargs kubectl delete -n crypto-collectors --ignore-not-found=true
sleep 2
kubectl get jobs -n crypto-collectors -o name | grep materialized-updater-cron | head -20 | xargs kubectl delete -n crypto-collectors --ignore-not-found=true
sleep 2
kubectl get jobs -n crypto-collectors -o name | grep materialized-updater-cron | head -20 | xargs kubectl delete -n crypto-collectors --ignore-not-found=true

echo "   ⏳ Waiting for cleanup to complete..."
sleep 10

echo "🔧 Phase 2: Building and deploying continuous service..."

# Build updated Docker image with continuous mode
docker build -f Dockerfile.materialized -t aitest-materialized-updater:continuous .
kind load docker-image aitest-materialized-updater:continuous --name cryptoai-multinode

# Deploy the continuous service
kubectl apply -f materialized-updater-deployment.yaml

echo "✅ Phase 3: Verification..."
sleep 5

echo "📊 Current status:"
kubectl get deployment materialized-updater -n crypto-collectors
kubectl get pods -l app=materialized-updater -n crypto-collectors
kubectl get jobs -n crypto-collectors | grep materialized | wc -l

echo "🎉 Deployment complete!"