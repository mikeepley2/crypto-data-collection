#!/bin/bash

# FRED API Series Fix Script
# This script fixes the invalid FRED API series codes in the macro collector

echo "🔧 FRED API Series Fix Script"
echo "=============================="

# Set kubeconfig
export KUBECONFIG=~/.kube/config-crypto-trading

echo "📋 Current FRED series issues:"
echo "  - DFF10 (invalid) -> DGS10 (10-Year Treasury)"  
echo "  - GOLDAMND (invalid) -> GOLDAMGD228NLBM (Gold Price)"

# Get current configmap
echo "📥 Extracting current macro collector configuration..."
kubectl get configmap macro-collector-code -n crypto-data-collection -o yaml > /tmp/macro-config-original.yaml

# Create fixed version
echo "🔧 Creating fixed configuration..."
sed 's/"10Y_YIELD": "DFF10"/"10Y_YIELD": "DGS10"/g' /tmp/macro-config-original.yaml > /tmp/macro-config-fixed.yaml
sed -i 's/"GOLD_PRICE": "GOLDAMND"/"GOLD_PRICE": "GOLDAMGD228NLBM"/g' /tmp/macro-config-fixed.yaml

# Apply fix
echo "📤 Applying fixed configuration..."
kubectl apply -f /tmp/macro-config-fixed.yaml

# Restart deployment to pick up changes
echo "🔄 Restarting macro collector to apply changes..."
kubectl rollout restart deployment/macro-collector -n crypto-data-collection

# Wait for rollout
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/macro-collector -n crypto-data-collection --timeout=120s

# Check status
echo "📊 Checking new collector status..."
sleep 15

# Get new pod name
NEW_POD=$(kubectl get pods -n crypto-data-collection -l app=macro-collector --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')

if [ ! -z "$NEW_POD" ]; then
    echo "✅ New pod running: $NEW_POD"
    echo "📋 Recent logs:"
    kubectl logs -n crypto-data-collection $NEW_POD --tail=10
else
    echo "⚠️ Pod not ready yet, check status with:"
    echo "kubectl get pods -n crypto-data-collection -l app=macro-collector"
fi

echo ""
echo "🎯 Fix Summary:"
echo "  - Updated DFF10 -> DGS10 (10-Year Treasury)"
echo "  - Updated GOLDAMND -> GOLDAMGD228NLBM (Gold Price)"
echo "  - Restarted macro collector deployment"
echo ""
echo "🔍 Verify fix with:"
echo "kubectl logs -n crypto-data-collection \$NEW_POD | grep -E 'DGS10|GOLDAMGD228NLBM|Successfully|Error'"