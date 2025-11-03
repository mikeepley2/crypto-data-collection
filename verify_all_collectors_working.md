# Verify All Collectors Are Working - Action Plan

## ✅ What We Fixed

### 1. Onchain Collector - CoinGecko Premium API
- ✅ Added `COINGECKO_API_KEY` environment variable to deployment
- ✅ Fixed API header from `x-cg-demo-api-key` to `x-cg-pro-api-key`
- ✅ Added premium API URL support (`https://pro-api.coingecko.com/api/v3`)
- ✅ Added rate limiting (0.5s for premium, 2s for free)
- ✅ Updated both `services/onchain-collection/onchain_collector.py` and `k8s/collectors/collector-configmaps.yaml`

**API Key Found**: `CG-5eCTSYNvLjBYz7gxS3jXCLrq`

### 2. Technical Calculator ✅
- **Status**: WORKING
- **Evidence**: Processing 326 symbols, updating 2782 records
- **Logs show**: "Technical indicators sync complete: 326 symbols processed"

### 3. Macro Collector ⚠️
- **Status**: Running but updating with `None` values
- **Issue**: Logs show "Updated dxy with value None for 370670 records"
- **Needs**: Check why FRED API is returning None

### 4. Materialized Updater ✅
- **Status**: WORKING
- **Evidence**: Processing 7900+ symbols, updating records continuously
- **Technical indicators**: rsi_14 improving (6.9% → 8.9%)

## 🔧 Next Steps

### Step 1: Apply ConfigMap Updates
The ConfigMap needs to be updated in Kubernetes:
```bash
kubectl apply -f k8s/collectors/collector-configmaps.yaml
```

### Step 2: Restart Onchain Collector
```bash
kubectl rollout restart deployment/onchain-collector -n crypto-data-collection
```

### Step 3: Verify CoinGecko API Key in Secrets
Ensure the secret exists:
```bash
# Check if secret has COINGECKO_API_KEY
kubectl get secret data-collection-secrets -n crypto-data-collection -o jsonpath='{.data.COINGECKO_API_KEY}' | base64 -d
```

If missing, add it:
```bash
kubectl create secret generic data-collection-secrets \
  --from-literal=COINGECKO_API_KEY='CG-5eCTSYNvLjBYz7gxS3jXCLrq' \
  --dry-run=client -o yaml | kubectl apply -n crypto-data-collection -f -
```

### Step 4: Verify Collectors
After restart, check logs:
```bash
# Onchain collector
kubectl logs -n crypto-data-collection -l app=onchain-collector --tail=20 | findstr /i "premium rate limit collected"

# Technical calculator  
kubectl logs -n crypto-data-collection -l app=technical-calculator --tail=20 | findstr /i "processed symbols"

# Macro collector
kubectl logs -n crypto-data-collection -l app=macro-collector --tail=20 | findstr /i "fred collected"
```

## 📊 Expected Results

After fixes:
1. **Onchain Collector**: Should use premium API, no more 429 errors
2. **Technical Calculator**: Already working (326 symbols)
3. **Macro Collector**: Should collect FRED data properly (investigate None values)
4. **Materialized Updater**: Should populate onchain data once source data is available

## ⚠️ Known Issues

1. **Macro Collector returning None**: Need to check FRED API key and API responses
2. **Database queries hanging**: Database is heavily loaded, verification via SQL is difficult
3. **SMA_20 dropped to 0%**: This is concerning - may indicate technical calculator issue


