# PowerShell script to apply onchain collector premium API fixes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Applying Onchain Collector Premium API Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Update ConfigMap
Write-Host "Step 1: Updating ConfigMap..." -ForegroundColor Yellow
kubectl apply -f k8s/collectors/collector-configmaps.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to apply ConfigMap" -ForegroundColor Red
    exit 1
}
Write-Host "✅ ConfigMap updated" -ForegroundColor Green
Write-Host ""

# Step 2: Update Deployment
Write-Host "Step 2: Updating Deployment..." -ForegroundColor Yellow
kubectl apply -f k8s/collectors/data-collectors-deployment.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to apply Deployment" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Deployment updated" -ForegroundColor Green
Write-Host ""

# Step 3: Check if COINGECKO_API_KEY exists in secrets
Write-Host "Step 3: Checking for COINGECKO_API_KEY in secrets..." -ForegroundColor Yellow
$keyExists = kubectl get secret data-collection-secrets -n crypto-data-collection -o jsonpath='{.data.COINGECKO_API_KEY}' 2>$null

if ($keyExists) {
    Write-Host "✅ COINGECKO_API_KEY already exists in secrets" -ForegroundColor Green
} else {
    Write-Host "⚠️  COINGECKO_API_KEY not found - adding it..." -ForegroundColor Yellow
    
    # Try to patch the existing secret
    $apiKeyBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("CG-5eCTSYNvLjBYz7gxS3jXCLrq"))
    
    # Check if secret exists
    $secretExists = kubectl get secret data-collection-secrets -n crypto-data-collection 2>$null
    if ($secretExists) {
        # Patch existing secret
        kubectl patch secret data-collection-secrets -n crypto-data-collection --type='json' -p="[{\`"op\`":\`"add\`",\`"path\`":\`"/data/COINGECKO_API_KEY\`",\`"value\`":\`"$apiKeyBase64\`"}]" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Added COINGECKO_API_KEY to existing secret" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Could not patch secret - you may need to manually add it:" -ForegroundColor Yellow
            Write-Host "   kubectl create secret generic data-collection-secrets \" -ForegroundColor Gray
            Write-Host "     --from-literal=COINGECKO_API_KEY='CG-5eCTSYNvLjBYz7gxS3jXCLrq' \" -ForegroundColor Gray
            Write-Host "     --dry-run=client -o yaml | kubectl apply -n crypto-data-collection -f -" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️  Secret does not exist - you need to create it first" -ForegroundColor Yellow
        Write-Host "   Run the kubectl create secret command manually" -ForegroundColor Gray
    }
}
Write-Host ""

# Step 4: Restart onchain collector
Write-Host "Step 4: Restarting onchain collector..." -ForegroundColor Yellow
kubectl rollout restart deployment/onchain-collector -n crypto-data-collection
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Onchain collector restart initiated" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for rollout to complete..." -ForegroundColor Yellow
    kubectl rollout status deployment/onchain-collector -n crypto-data-collection --timeout=60s
} else {
    Write-Host "⚠️  Could not restart deployment (may already be restarting)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Fixes Applied!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify, check logs with:" -ForegroundColor Yellow
Write-Host "  kubectl logs -n crypto-data-collection -l app=onchain-collector --tail=30" -ForegroundColor Gray
Write-Host ""
Write-Host "Look for: '✅ Using CoinGecko Premium API for onchain data'" -ForegroundColor Yellow


