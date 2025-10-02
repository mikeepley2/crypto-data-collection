#!/bin/bash
# Cleanup script to remove all running materialized-updater jobs

echo "🧹 Cleaning up materialized-updater jobs..."

# Delete the problematic CronJob first
kubectl delete cronjob materialized-updater-cron -n crypto-collectors --ignore-not-found=true

# Delete all materialized-updater jobs
kubectl delete jobs -l app=materialized-updater-cron -n crypto-collectors --ignore-not-found=true

# Delete any remaining materialized-updater pods
kubectl delete pods -l app=materialized-updater-cron -n crypto-collectors --ignore-not-found=true

echo "✅ Cleanup complete"

# Wait a moment for cleanup
sleep 5

# Apply the fixed CronJob
echo "🚀 Applying fixed CronJob configuration..."
kubectl apply -f materialized-updater-cron-fixed.yaml

echo "✅ Fixed CronJob deployed"

# Check status
echo "📊 Current status:"
kubectl get cronjobs -n crypto-collectors
kubectl get jobs -l app=materialized-updater-cron -n crypto-collectors
kubectl get pods -l app=materialized-updater-cron -n crypto-collectors