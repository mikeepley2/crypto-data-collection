#!/bin/bash
# Kubernetes Deployment Script for Crypto Data Collection

echo "🚀 Deploying Crypto Data Collection to Kubernetes"
echo "=================================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f k8s/database-config.yaml

# Wait for namespace to be ready
echo "⏳ Waiting for namespace to be ready..."
sleep 3

# Apply database configuration and secrets
echo "🔧 Applying database configuration..."
kubectl apply -f k8s/database-config.yaml

# Verify ConfigMap and Secret creation
echo "🔍 Verifying configuration..."
kubectl get configmap database-config -n crypto-data-collection
kubectl get secret database-secrets -n crypto-data-collection

# Deploy collectors
echo "📊 Deploying News Collector..."
kubectl apply -f k8s/news-collector-deployment.yaml

echo "⛓️  Deploying Onchain Collector..."
kubectl apply -f k8s/onchain-collector-deployment.yaml

echo "💰 Deploying OHLC Collector..."
kubectl apply -f k8s/ohlc-collector-deployment.yaml

# Wait for deployments to be ready
echo "⏳ Waiting for deployments..."
sleep 10

# Check deployment status
echo "🔍 Checking deployment status..."
kubectl get pods -n crypto-data-collection
kubectl get services -n crypto-data-collection
kubectl get deployments -n crypto-data-collection

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Useful commands:"
echo "Monitor pods:     kubectl get pods -n crypto-data-collection -w"
echo "Check logs:       kubectl logs -f deployment/news-collector -n crypto-data-collection"
echo "Port forward:     kubectl port-forward svc/news-collector-service 8000:8000 -n crypto-data-collection"
echo "Health check:     curl http://localhost:8000/health"
echo ""
echo "🔧 Troubleshooting:"
echo "Describe pod:     kubectl describe pod <pod-name> -n crypto-data-collection"
echo "Get events:       kubectl get events -n crypto-data-collection --sort-by='.lastTimestamp'"
echo ""
echo "🗑️  To cleanup:"
echo "Delete namespace: kubectl delete namespace crypto-data-collection"