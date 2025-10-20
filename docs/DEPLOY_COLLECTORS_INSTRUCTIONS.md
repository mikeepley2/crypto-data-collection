# Deploy Data Collectors to Kubernetes

**Status:** Ready to Deploy  
**Created:** October 20, 2025  
**Effort:** ~30 minutes setup + ongoing monitoring

---

## Overview

Deploy three data collectors to Kubernetes:
1. **Onchain Collector** - Blockchain metrics (every 6 hours)
2. **Macro Collector** - Economic indicators (every 1 hour)
3. **Technical Calculator** - Technical indicators (every 5 minutes)

---

## Prerequisites

✅ **Already Done:**
- Kubernetes cluster running (`kind`)
- `crypto-data-collection` namespace exists
- MySQL database accessible
- ConfigMaps with data collection config present

**Need to Add:**
- [ ] API keys in Kubernetes secrets

---

## Step 1: Update Kubernetes Secrets with API Keys

### 1.1 Get Current Secrets
```bash
kubectl get secret data-collection-secrets -n crypto-data-collection -o yaml
```

### 1.2 Add/Update FRED API Key

```bash
kubectl patch secret data-collection-secrets \
  -n crypto-data-collection \
  --type merge \
  -p '{"stringData":{"FRED_API_KEY":"1e8b4e2b6b7e8f9b5c9d8f7e6d5c4b3a"}}'
```

### 1.3 Add Glassnode API Key (Optional - for Onchain)

Once you have a Glassnode API key, add it:
```bash
kubectl patch secret data-collection-secrets \
  -n crypto-data-collection \
  --type merge \
  -p '{"stringData":{"GLASSNODE_API_KEY":"your-glassnode-key-here"}}'
```

**Note:** Without Glassnode key, onchain collector will run but not fetch real data. Technical calculator doesn't need external APIs.

---

## Step 2: Apply ConfigMaps for Collector Code

```bash
kubectl apply -f k8s/collectors/collector-configmaps.yaml
```

**Verify:**
```bash
kubectl get configmaps -n crypto-data-collection | grep collector
```

Expected output:
```
onchain-collector-code
macro-collector-code
technical-calculator-code
```

---

## Step 3: Deploy Collectors

```bash
kubectl apply -f k8s/collectors/data-collectors-deployment.yaml
```

**Verify deployments created:**
```bash
kubectl get deployments -n crypto-data-collection
```

Expected output:
```
NAME                     READY   UP-TO-DATE   AVAILABLE
onchain-collector        1/1     1            1
macro-collector          1/1     1            1
technical-calculator     1/1     1            1
```

---

## Step 4: Monitor Collectors

### Check Pod Status
```bash
kubectl get pods -n crypto-data-collection -l component=data-collection
```

### View Logs
```bash
# Onchain collector
kubectl logs -f deployment/onchain-collector -n crypto-data-collection

# Macro collector
kubectl logs -f deployment/macro-collector -n crypto-data-collection

# Technical calculator
kubectl logs -f deployment/technical-calculator -n crypto-data-collection
```

### Expected Output
```
2025-10-20 17:30:45 - onchain-collector - INFO - Onchain Data Collector starting...
2025-10-20 17:30:45 - onchain-collector - INFO - Starting onchain metrics collection...
2025-10-20 17:30:50 - onchain-collector - INFO - Processed 50 onchain metrics
```

---

## Step 5: Verify Data Collection

### Check Database for New Data

```bash
# Onchain metrics
mysql -h 127.0.0.1 -u news_collector -p99Rules! crypto_prices \
  -e "SELECT * FROM onchain_metrics ORDER BY updated_at DESC LIMIT 5;"

# Macro indicators
mysql -h 127.0.0.1 -u news_collector -p99Rules! crypto_prices \
  -e "SELECT * FROM macro_indicators ORDER BY updated_at DESC LIMIT 5;"

# Technical indicators
mysql -h 127.0.0.1 -u news_collector -p99Rules! crypto_prices \
  -e "SELECT * FROM technical_indicators ORDER BY updated_at DESC LIMIT 5;"
```

---

## Monitoring & Troubleshooting

### Health Checks

Each collector has liveness and readiness probes:
```bash
# Check probe status
kubectl describe pod <pod-name> -n crypto-data-collection | grep -A 5 Liveness
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Pod in CrashLoopBackOff | Check logs: `kubectl logs <pod> -n crypto-data-collection` |
| Database connection fails | Verify MySQL is running and credentials are correct |
| API key missing | Add to secrets: `kubectl patch secret data-collection-secrets ...` |
| Collector not running | Check resource limits: `kubectl top pods -n crypto-data-collection` |

### View Metrics

```bash
# CPU and Memory usage
kubectl top pods -n crypto-data-collection

# Recent events
kubectl get events -n crypto-data-collection --sort-by='.lastTimestamp'
```

---

## Collection Schedules

| Collector | Interval | Data Updated |
|-----------|----------|--------------|
| Onchain | Every 6 hours | onchain_metrics |
| Macro | Every 1 hour | macro_indicators |
| Technical | Every 5 minutes | technical_indicators |

---

## Next Steps

### After Deployment

1. **Monitor for 24 hours** - Ensure collectors are running smoothly
2. **Verify data quality** - Check database records are being populated
3. **Set up alerting** - Configure Prometheus alerts for collection failures
4. **Integrate with ML** - Include new data in feature materialization

### Additional Configuration

- Get actual Glassnode API key for onchain data
- Configure FRED API calls (currently placeholder data)
- Implement real technical indicator calculations (currently simplified)

---

## Rollback Instructions

If issues occur, rollback collectors:

```bash
# Delete deployments
kubectl delete deployment onchain-collector -n crypto-data-collection
kubectl delete deployment macro-collector -n crypto-data-collection
kubectl delete deployment technical-calculator -n crypto-data-collection

# Delete ConfigMaps
kubectl delete configmap onchain-collector-code -n crypto-data-collection
kubectl delete configmap macro-collector-code -n crypto-data-collection
kubectl delete configmap technical-calculator-code -n crypto-data-collection
```

---

## Files Reference

- **Deployments:** `k8s/collectors/data-collectors-deployment.yaml`
- **ConfigMaps:** `k8s/collectors/collector-configmaps.yaml`
- **Source Code:** `services/{onchain,macro,technical}-collection/`
- **Documentation:** `docs/DATA_COLLECTORS_DEPLOYMENT.md`

---

## Support

For issues or questions:
1. Check logs: `kubectl logs -f deployment/<collector> -n crypto-data-collection`
2. Verify database: `mysql ... -e "SHOW TABLES;"`
3. Check Kubernetes events: `kubectl describe pod <pod> -n crypto-data-collection`
