#!/bin/bash
# Restart materialized updater and verify it's working

echo "=========================================="
echo "RESTARTING MATERIALIZED UPDATER"
echo "=========================================="

# Check if running in Kubernetes
if kubectl get deployment materialized-updater -n crypto-data-collection &>/dev/null; then
    echo "Found Kubernetes deployment, restarting..."
    kubectl rollout restart deployment/materialized-updater -n crypto-data-collection
    echo "Waiting for rollout to complete..."
    kubectl rollout status deployment/materialized-updater -n crypto-data-collection --timeout=120s
    echo "✅ Materialized updater restarted"
else
    echo "No Kubernetes deployment found - updater may be running as a local service"
    echo "Please restart it manually or check if it's running as a Docker container"
fi

echo ""
echo "=========================================="
echo "VERIFICATION - Check in 30 seconds:"
echo "=========================================="
echo "1. Run: python verify_updater_status.py"
echo "2. Check Kubernetes logs: kubectl logs -n crypto-data-collection -l app=materialized-updater --tail=50"
echo "3. Monitor for new records being populated"
echo "=========================================="


