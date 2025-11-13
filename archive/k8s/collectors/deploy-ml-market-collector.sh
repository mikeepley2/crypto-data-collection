#!/bin/bash

# ML Market Collector Deployment Script
# Deploys ML-focused traditional market data collector to K8s

set -e

NAMESPACE="crypto-data-collection"
DEPLOYMENT_NAME="ml-market-collector"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting ML Market Collector Deployment..."
echo "📁 Script directory: $SCRIPT_DIR"

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ Error: $1 is not installed"
        exit 1
    fi
}

# Check prerequisites
echo "🔧 Checking prerequisites..."
check_command kubectl
check_command kustomize

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo "📝 Creating namespace: $NAMESPACE"
    kubectl create namespace $NAMESPACE
else
    echo "✅ Namespace $NAMESPACE already exists"
fi

# Check if centralized database config exists
echo "🔍 Checking centralized database configuration..."
if ! kubectl get configmap centralized-db-config -n $NAMESPACE &> /dev/null; then
    echo "⚠️  Warning: centralized-db-config ConfigMap not found"
    echo "   Creating placeholder configuration..."
    
    kubectl create configmap centralized-db-config -n $NAMESPACE \
        --from-literal=MYSQL_HOST="mysql.default.svc.cluster.local" \
        --from-literal=MYSQL_PORT="3306" \
        --from-literal=MYSQL_DATABASE="crypto_data" \
        --dry-run=client -o yaml | kubectl apply -f -
fi

if ! kubectl get secret centralized-db-secrets -n $NAMESPACE &> /dev/null; then
    echo "⚠️  Warning: centralized-db-secrets Secret not found"
    echo "   Creating placeholder secrets..."
    
    kubectl create secret generic centralized-db-secrets -n $NAMESPACE \
        --from-literal=mysql-user="crypto_user" \
        --from-literal=mysql-password="changeme" \
        --dry-run=client -o yaml | kubectl apply -f -
fi

# Deploy using kustomize
echo "📦 Deploying ML Market Collector..."
cd "$SCRIPT_DIR"

# Apply kustomization
kubectl apply -k . --namespace $NAMESPACE

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s

# Check pod status
echo "🔍 Checking pod status..."
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME

# Get service information
echo "🌐 Service information:"
kubectl get service $DEPLOYMENT_NAME -n $NAMESPACE

# Show logs
echo "📝 Recent logs:"
kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=10

echo ""
echo "✅ ML Market Collector deployment completed!"
echo ""
echo "🔧 Management commands:"
echo "   View logs: kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME -f"
echo "   Check health: kubectl port-forward -n $NAMESPACE service/$DEPLOYMENT_NAME 8080:8000"
echo "   Scale up: kubectl scale deployment/$DEPLOYMENT_NAME --replicas=2 -n $NAMESPACE"
echo "   Delete: kubectl delete -k . --namespace $NAMESPACE"
echo ""
echo "🌐 API endpoints (after port-forward):"
echo "   Health check: http://localhost:8080/health"
echo "   Manual trigger: curl -X POST http://localhost:8080/collect"
echo "   ML features: http://localhost:8080/ml-features"
echo "   Status: http://localhost:8080/status"
echo ""
echo "📊 Expected ML features: ~40 (12 assets × 3 metrics + 7 calculated indicators)"
echo "   Traditional market assets: QQQ, ARKK, SPY, HYG, TLT, VIX, DXY, currencies"
echo "   Calculated indicators: Risk-on ratio, Innovation premium, Tech leadership"