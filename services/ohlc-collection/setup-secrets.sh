#!/bin/bash
# Setup required Kubernetes secrets for OHLC collector

NAMESPACE="crypto-data-collection"

echo "🔐 Setting up Kubernetes secrets for OHLC collector"
echo "=================================================="

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# MySQL secret
echo "📝 Creating MySQL secret..."
kubectl create secret generic mysql-secret \
    --namespace=$NAMESPACE \
    --from-literal=username=root \
    --from-literal=password="" \
    --dry-run=client -o yaml | kubectl apply -f -

# CoinGecko API secret
echo "📝 Creating CoinGecko API secret..."
kubectl create secret generic coingecko-secret \
    --namespace=$NAMESPACE \
    --from-literal=api-key="CG-94NCcVD2euxaGTZe94bS2oYz" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets created successfully"
echo ""
echo "📋 Verify secrets:"
echo "kubectl get secrets -n $NAMESPACE"