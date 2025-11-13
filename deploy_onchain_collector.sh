#!/bin/bash

echo "=== Deploying Onchain Collector ==="
echo "Current date: $(date)"

echo "1. Checking current resource usage..."
kubectl describe namespace crypto-data-collection | grep -A 5 "Resource Quotas" || echo "No quotas found"

echo "2. Checking existing deployments..."
kubectl get deployments -n crypto-data-collection

echo "3. Scaling down non-essential deployments to free resources..."
kubectl scale deployment crypto-news-collector --replicas=0 -n crypto-data-collection 2>/dev/null || echo "crypto-news-collector not found"
kubectl scale deployment macro-collector --replicas=0 -n crypto-data-collection 2>/dev/null || echo "macro-collector not found"
kubectl scale deployment technical-calculator --replicas=0 -n crypto-data-collection 2>/dev/null || echo "technical-calculator not found"
kubectl scale deployment enhanced-materialized-updater --replicas=0 -n crypto-data-collection 2>/dev/null || echo "enhanced-materialized-updater not found"

echo "4. Waiting 30 seconds for pods to terminate..."
sleep 30

echo "5. Checking resource usage after scaling down..."
kubectl get pods -n crypto-data-collection

echo "6. Deleting existing onchain collector if it exists..."
kubectl delete deployment onchain-collector -n crypto-data-collection --ignore-not-found=true
kubectl delete service onchain-collector -n crypto-data-collection --ignore-not-found=true
kubectl delete configmap crypto-config -n crypto-data-collection --ignore-not-found=true

echo "7. Applying new onchain collector deployment..."
kubectl apply -f build/k8s/base/onchain-collector.yaml

echo "8. Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/onchain-collector -n crypto-data-collection

echo "9. Checking deployment status..."
kubectl get deployment onchain-collector -n crypto-data-collection
kubectl get pods -l app=onchain-collector -n crypto-data-collection

echo "10. Checking pod logs..."
POD_NAME=$(kubectl get pods -l app=onchain-collector -n crypto-data-collection -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ ! -z "$POD_NAME" ]; then
    echo "Logs from pod $POD_NAME:"
    kubectl logs $POD_NAME -n crypto-data-collection --tail=20
else
    echo "No pods found for onchain-collector"
fi

echo "=== Deployment Complete ==="