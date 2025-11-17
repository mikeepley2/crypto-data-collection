Write-Host "Applying updated ConfigMap with fixed sentiment parsing..." -ForegroundColor Green
kubectl apply -f k8s/configmaps/enhanced-sentiment-ml-code.yaml

Write-Host "Waiting 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Restarting deployment to pick up new code..." -ForegroundColor Green
kubectl rollout restart deployment/enhanced-sentiment-collector -n crypto-data-collection

Write-Host "Waiting for deployment to be ready..." -ForegroundColor Yellow
kubectl rollout status deployment/enhanced-sentiment-collector -n crypto-data-collection --timeout=5m

Write-Host "`nDeployment restarted! Testing sentiment endpoint..." -ForegroundColor Green
Start-Sleep -Seconds 10

Write-Host "TEST 1 (positive crypto):" -ForegroundColor Cyan
kubectl exec deployment/enhanced-sentiment-collector -n crypto-data-collection -- python -c "import requests; r = requests.post('http://localhost:8000/sentiment', json={'text': 'Bitcoin soars to new highs! Bulls celebrate massive gains!', 'market_type': 'crypto'}, timeout=30); print('Result:', r.json())"

Write-Host "`nTEST 2 (negative crypto):" -ForegroundColor Cyan
kubectl exec deployment/enhanced-sentiment-collector -n crypto-data-collection -- python -c "import requests; r = requests.post('http://localhost:8000/sentiment', json={'text': 'Market crashes! Investors panic as crypto wiped out!', 'market_type': 'crypto'}, timeout=30); print('Result:', r.json())"

Write-Host "`nTEST 3 (neutral stock):" -ForegroundColor Cyan
kubectl exec deployment/enhanced-sentiment-collector -n crypto-data-collection -- python -c "import requests; r = requests.post('http://localhost:8000/sentiment', json={'text': 'Company reports steady earnings, maintains guidance', 'market_type': 'stock'}, timeout=30); print('Result:', r.json())"

Write-Host "`nDone! If you see non-zero sentiment scores above, the fix is working." -ForegroundColor Green
Write-Host "Now you can run the backfill script inside the pod." -ForegroundColor Yellow

