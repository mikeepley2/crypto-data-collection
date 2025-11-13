#!/bin/bash
# Build and deploy enhanced onchain collector

set -e

echo "🚀 Building Enhanced Onchain Collector..."

# Build the Docker image
docker build -f build/docker/Dockerfile.enhanced-onchain-collector -t megabob70/onchain-collector:latest .

echo "✅ Docker image built successfully"

# Push to registry
echo "📤 Pushing to Docker Hub..."
docker push megabob70/onchain-collector:latest

echo "✅ Image pushed successfully"

# Deploy to Kubernetes
echo "🚀 Deploying to Kubernetes..."

# Apply the deployment
kubectl apply -f build/k8s/onchain-collector-deployment-only.yaml

# Wait for rollout
echo "⏳ Waiting for deployment rollout..."
kubectl rollout status deployment/onchain-collector -n crypto-data-collection --timeout=300s

# Check pod status
echo "📊 Checking pod status..."
kubectl get pods -n crypto-data-collection -l app=onchain-collector

echo "🎉 Enhanced Onchain Collector deployed successfully!"

# Show logs
echo "📋 Recent logs:"
kubectl logs -n crypto-data-collection -l app=onchain-collector --tail=20