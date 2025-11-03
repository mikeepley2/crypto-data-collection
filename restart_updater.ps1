# PowerShell script to restart materialized updater

Write-Host "=========================================="
Write-Host "RESTARTING MATERIALIZED UPDATER"
Write-Host "=========================================="
Write-Host ""

# Check if Kubernetes deployment exists
$deployment = kubectl get deployment materialized-updater -n crypto-data-collection 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Found Kubernetes deployment"
    Write-Host "Restarting deployment..."
    kubectl rollout restart deployment/materialized-updater -n crypto-data-collection
    Write-Host ""
    Write-Host "Waiting for rollout..."
    kubectl rollout status deployment/materialized-updater -n crypto-data-collection --timeout=60s
    Write-Host ""
    Write-Host "✅ Materialized updater restarted"
    Write-Host ""
    Write-Host "Checking pod status..."
    kubectl get pods -n crypto-data-collection -l app=materialized-updater
    Write-Host ""
    Write-Host "Recent logs:"
    kubectl logs -n crypto-data-collection -l app=materialized-updater --tail=20 2>&1
}
else {
    Write-Host "⚠️  Kubernetes deployment not found"
    Write-Host "The updater may be running as a local service or Docker container"
    Write-Host "Please restart it manually"
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Next steps:"
Write-Host "1. Wait 5-10 minutes for updater to process new records"
Write-Host "2. Run: python check_updater_working.py"
Write-Host "3. Check logs: kubectl logs -n crypto-data-collection -l app=materialized-updater -f"
Write-Host "=========================================="


