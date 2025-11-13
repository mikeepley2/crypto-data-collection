#!/bin/bash
# Complete ML Features Integration via K8s Pod
# Executes the comprehensive integration script

echo "🚀 Complete ML Features Integration Starting..."

# Find ML Market Collector pod
ML_POD=$(kubectl get pods -n crypto-data-collection -l app=ml-market-collector -o jsonpath='{.items[0].metadata.name}')

if [ -n "$ML_POD" ]; then
    echo "✅ Using ML Market Collector pod: $ML_POD"
else
    echo "❌ No suitable pods found"
    exit 1
fi

# Copy integration script to pod
echo "📤 Copying complete integration script..."
kubectl cp /mnt/e/git/crypto-data-collection/complete_ml_integration.py crypto-data-collection/$ML_POD:/tmp/complete_ml_integration.py

# Execute comprehensive integration
echo "🚀 Executing complete ML features integration..."
kubectl exec -n crypto-data-collection $ML_POD -- python3 /tmp/complete_ml_integration.py

echo "✅ Complete ML integration finished!"