#!/bin/bash

# Create FRED API Secret for Enhanced Macro Collector

echo "🔐 Creating FRED API secret for Enhanced Macro Collector..."

# Check if the secret exists and delete it
kubectl get secret fred-secret -n crypto-data-collection >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "📝 Updating existing fred-secret..."
    kubectl delete secret fred-secret -n crypto-data-collection
fi

# Create the FRED API secret
kubectl create secret generic fred-secret \
  --from-literal=api-key="35478996c5e061d0fc99fc73f5ce348d" \
  -n crypto-data-collection

if [ $? -eq 0 ]; then
    echo "✅ FRED API secret created successfully"
    kubectl get secret fred-secret -n crypto-data-collection -o yaml | head -10
else
    echo "❌ Failed to create FRED API secret"
    exit 1
fi

echo "🔍 Verifying secrets..."
kubectl get secrets -n crypto-data-collection | grep -E "(mysql-secret|fred-secret)"

echo "✅ Secret setup complete for Enhanced Macro Collector"