#!/bin/bash
# Fix Kubernetes onchain collector deployment

set -e

echo "🔧 Fixing Kubernetes onchain collector deployment..."

# Build fresh image with explicit tag
echo "📦 Building fresh Docker image..."
cd /mnt/e/git/crypto-data-collection
docker build -f build/docker/onchain-collector.Dockerfile -t onchain-collector:latest .

# Load image to all kind worker nodes
echo "🚛 Loading image to kind cluster nodes..."
kind load docker-image onchain-collector:latest --name cryptoai-k8s-trading-engine

# Verify image is loaded
echo "🔍 Verifying image in nodes..."
docker exec -i cryptoai-k8s-trading-engine-worker crictl images | grep onchain-collector || echo "Image not found in worker"

# Delete existing deployment
echo "🗑️ Cleaning up existing deployment..."
kubectl delete deployment onchain-collector --ignore-not-found=true

# Apply fresh deployment
echo "🚀 Applying fresh deployment..."
kubectl apply -f build/k8s/onchain-collector-deployment-only.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/onchain-collector

# Check status
echo "📊 Checking deployment status..."
kubectl get pods -l app=onchain-collector
kubectl describe deployment onchain-collector

echo "✅ Deployment fixed! Onchain collector should be running."