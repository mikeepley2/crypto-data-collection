# Onchain Collector - Free vs Paid Options

**Date:** October 20, 2025  
**Status:** Both options ready to deploy

---

## TL;DR

- ✅ **Free Version Ready:** Use without any API key
- 🔑 **Paid Version Ready:** Use if you get Glassnode key
- **Recommendation:** Start with FREE, upgrade to Glassnode later if needed

---

## Option 1: FREE Onchain Collector ✅ (Recommended to start)

### What It Does
Uses completely free blockchain data sources:
- **blockchain.info** - Bitcoin metrics (blocks, transactions)
- **Etherscan API** - Ethereum metrics (free tier 5 calls/sec)
- **Messari API** - General crypto metrics (free tier available)

### Setup
```bash
# No API key needed! Just deploy:
kubectl apply -f k8s/collectors/collector-configmaps.yaml
kubectl apply -f k8s/collectors/data-collectors-deployment.yaml
```

### Pros
✅ No API key required  
✅ No rate limits  
✅ Can deploy immediately  
✅ Works for all major crypto (BTC, ETH, etc.)

### Cons
❌ Limited to free APIs (less detailed metrics)  
❌ Messari free tier has fewer metrics  
❌ Some blockchains not covered

### Data Quality
- **Bitcoin:** ⭐⭐⭐⭐ (blockchain.info is reliable)
- **Ethereum:** ⭐⭐⭐⭐ (Etherscan free tier is reliable)
- **Others:** ⭐⭐ (Messari free tier limited)

### File Location
```
services/onchain-collection/onchain_collector_free.py
```

---

## Option 2: Glassnode Paid Onchain Collector

### What It Does
Uses Glassnode's professional API:
- **Active addresses** (precise daily counts)
- **Transaction volumes** (complete data)
- **Miner revenue** (block rewards)
- **Exchange flows** (in/out tracking)
- **All major blockchains** (100+ supported)

### Setup
1. Get Glassnode API key (free tier available - limited)
2. Add to Kubernetes secrets:
```bash
kubectl patch secret data-collection-secrets \
  -n crypto-data-collection \
  --type merge \
  -p '{"stringData":{"GLASSNODE_API_KEY":"your-key-here"}}'
```
3. Deploy as before

### Pros
✅ Most comprehensive onchain metrics  
✅ Supports 100+ blockchains  
✅ Enterprise-grade reliability  
✅ Historical data available

### Cons
❌ Requires API key (free tier limited)  
❌ Paid tier $$$  
❌ Rate limits on free tier

### Data Quality
- **All Blockchains:** ⭐⭐⭐⭐⭐ (most comprehensive)
- **Historical Data:** Complete archives
- **Real-time:** Live updates

### File Location
```
services/onchain-collection/onchain_collector.py (original)
```

---

## Comparison Table

| Feature | Free | Glassnode |
|---------|------|-----------|
| Setup Time | 5 min | 10 min (get key) |
| API Key Required | ❌ No | ✅ Yes |
| Bitcoin Support | ✅ Excellent | ✅ Excellent |
| Ethereum Support | ✅ Excellent | ✅ Excellent |
| Other Blockchains | ⚠️ Limited | ✅ Full |
| Real-time Updates | ✅ Yes | ✅ Yes |
| Historical Data | ⚠️ Limited | ✅ Complete |
| Rate Limits | None | Depends on plan |
| Cost | Free | Free (limited) / $$$ (pro) |

---

## Free Tier API Options

### 1. blockchain.info (Bitcoin)
- ✅ No API key required
- ✅ Reliable
- ✅ Fast
- Rate: Unlimited

### 2. Etherscan (Ethereum)
- ✅ Free tier available
- ✅ Official Ethereum data
- ✅ 5 calls/second free
- Rate: 1-100 calls/sec (tier dependent)

### 3. Messari (All Crypto)
- ✅ Free tier
- ✅ 300 calls/month free
- ✅ Basic metrics
- Rate: Limited

---

## Getting Started - Recommended Path

### Phase 1: Deploy FREE Version (Today)
```bash
# Deploy all three collectors (technical, macro, onchain-free)
kubectl apply -f k8s/collectors/collector-configmaps.yaml
kubectl apply -f k8s/collectors/data-collectors-deployment.yaml
# All work immediately, no keys needed
```

### Phase 2: Add Glassnode Later (Optional)
When you're ready:
1. Get Glassnode API key
2. Add to Kubernetes secrets
3. Switch deployment to use glassnode version

---

## Free API Keys You Can Get Right Now

### Etherscan API Key (Free!)
1. Go to https://etherscan.io/apis
2. Sign up (free)
3. Generate API key
4. Add to environment or secrets

```bash
kubectl patch secret data-collection-secrets \
  -n crypto-data-collection \
  --type merge \
  -p '{"stringData":{"ETHERSCAN_API_KEY":"your-key-here"}}'
```

### Messari API Key (Free!)
1. Go to https://messari.io/api
2. Free tier signup
3. Get API key
4. 300 calls/month free

---

## Deployment Instructions

### Step 1: Update ConfigMaps (Use Free Version)
```bash
# Already includes free version in ConfigMaps
kubectl apply -f k8s/collectors/collector-configmaps.yaml
```

### Step 2: Deploy (No API Key Needed)
```bash
kubectl apply -f k8s/collectors/data-collectors-deployment.yaml
```

### Step 3: Verify
```bash
kubectl logs -f deployment/onchain-collector -n crypto-data-collection
# Should see: "Using free data sources: blockchain.info, etherscan, messari"
```

### Step 4: Check Database
```bash
mysql -h 127.0.0.1 -u news_collector -p99Rules! crypto_prices \
  -e "SELECT * FROM onchain_metrics ORDER BY updated_at DESC LIMIT 5;"
```

---

## Switching to Glassnode (If You Get a Key)

### Option A: Keep Using Free Version
- Works fine indefinitely
- No changes needed
- Data quality is acceptable for most use cases

### Option B: Switch to Glassnode
1. Add key to secrets
2. Update deployment to use Glassnode ConfigMap
3. Restart pods

```bash
# Add key
kubectl patch secret data-collection-secrets \
  -n crypto-data-collection \
  --type merge \
  -p '{"stringData":{"GLASSNODE_API_KEY":"your-key-here"}}'

# Restart deployment (if you've updated the code)
kubectl rollout restart deployment/onchain-collector \
  -n crypto-data-collection
```

---

## Free vs Paid - Decision Matrix

**Use FREE if:**
- ✅ Just starting out
- ✅ Need BTC/ETH data
- ✅ Budget is $0
- ✅ Don't need comprehensive multi-chain data

**Use GLASSNODE if:**
- ✅ Need detailed comprehensive data
- ✅ Trading with multiple altcoins
- ✅ Need historical archives
- ✅ Have budget for pro tier

---

## Summary

| Task | Free | Glassnode |
|------|------|-----------|
| Deploy today | ✅ Yes | ❌ Need key |
| Get data flowing | ✅ Immediately | 🔧 Need config |
| BTC/ETH metrics | ✅ Full | ✅ Full |
| Multi-chain | ⚠️ Limited | ✅ 100+ chains |
| Upgradeable | ✅ Yes | ✅ Yes |

---

## Final Recommendation

**Start with FREE today:**
1. Deploy all three collectors now (no API keys needed)
2. Verify data flows into database
3. Monitor for 24 hours
4. Later: Optionally add Glassnode for enhanced data

This way you get onchain data flowing **right now** without any delays!

