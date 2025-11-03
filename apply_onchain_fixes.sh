#!/bin/bash
# Apply onchain collector fixes

echo "Applying onchain collector fixes..."

# 1. Update ConfigMap
echo "Step 1: Updating ConfigMap..."
kubectl apply -f k8s/collectors/collector-configmaps.yaml

# 2. Update Deployment
echo "Step 2: Updating Deployment..."
kubectl apply -f k8s/collectors/data-collectors-deployment.yaml

# 3. Check if COINGECKO_API_KEY exists in secrets
echo "Step 3: Checking for COINGECKO_API_KEY in secrets..."
if kubectl get secret data-collection-secrets -n crypto-data-collection -o jsonpath='{.data.COINGECKO_API_KEY}' > /dev/null 2>&1; then
    echo "✅ COINGECKO_API_KEY exists in secrets"
else
    echo "⚠️  COINGECKO_API_KEY not found - need to add it"
    echo "Run: kubectl create secret generic data-collection-secrets \\"
    echo "  --from-literal=COINGECKO_API_KEY='CG-5eCTSYNvLjBYz7gxS3jXCLrq' \\"
    echo "  --dry-run=client -o yaml | kubectl apply -n crypto-data-collection -f -"
fi

# 4. Restart onchain collector
echo "Step 4: Restarting onchain collector..."
kubectl rollout restart deployment/onchain-collector -n crypto-data-collection

echo "✅ Fixes applied. Check logs with:"
echo "   kubectl logs -n crypto-data-collection -l app=onchain-collector --tail=20"


