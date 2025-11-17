@echo off
echo Applying updated ConfigMap with fixed sentiment parsing...
kubectl apply -f k8s/configmaps/enhanced-sentiment-ml-code.yaml

echo Waiting 5 seconds...
timeout /t 5 /nobreak

echo Restarting deployment to pick up new code...
kubectl rollout restart deployment/enhanced-sentiment-collector -n crypto-data-collection

echo Waiting for deployment to be ready...
kubectl rollout status deployment/enhanced-sentiment-collector -n crypto-data-collection --timeout=5m

echo.
echo Deployment restarted! Testing sentiment endpoint...
timeout /t 10 /nobreak

kubectl exec deployment/enhanced-sentiment-collector -n crypto-data-collection -- python -c "import requests; r = requests.post('http://localhost:8000/sentiment', json={'text': 'Bitcoin soars to new highs! Bulls celebrate massive gains!', 'market_type': 'crypto'}, timeout=30); print('TEST 1 (positive crypto):', r.json())"

kubectl exec deployment/enhanced-sentiment-collector -n crypto-data-collection -- python -c "import requests; r = requests.post('http://localhost:8000/sentiment', json={'text': 'Market crashes! Investors panic as crypto wiped out!', 'market_type': 'crypto'}, timeout=30); print('TEST 2 (negative crypto):', r.json())"

kubectl exec deployment/enhanced-sentiment-collector -n crypto-data-collection -- python -c "import requests; r = requests.post('http://localhost:8000/sentiment', json={'text': 'Company reports steady earnings, maintains guidance', 'market_type': 'stock'}, timeout=30); print('TEST 3 (neutral stock):', r.json())"

echo.
echo Done! If you see non-zero sentiment scores above, the fix is working.
echo Now you can run the backfill script inside the pod.
pause


