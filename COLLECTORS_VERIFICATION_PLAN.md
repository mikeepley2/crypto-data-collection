# Collectors Verification Plan

## Problem
Database queries are hanging due to heavy load/locks, so we can't verify collectors via SQL.

## Solution: Use Kubernetes Logs Instead

### Step 1: Check Collector Pods Are Running
```bash
kubectl get pods -n crypto-data-collection | grep collector
```

### Step 2: Check Recent Logs for Each Collector
```bash
# Onchain Collector
kubectl logs -n crypto-data-collection -l app=onchain-collector --tail=50

# Macro Collector  
kubectl logs -n crypto-data-collection -l app=macro-collector --tail=50

# Technical Calculator
kubectl logs -n crypto-data-collection -l app=technical-calculator --tail=50
```

### Step 3: Look for Success Indicators
- ✅ "Starting collection..." messages
- ✅ "Collected X records" messages
- ✅ "Finished processing" messages
- ❌ Error messages
- ❌ Connection timeout errors

## Alternative: Check Progress Monitor Output

The progress monitor already shows:
- ✅ Price data is flowing (22,000+ records)
- ✅ Technical indicators partially populated (rsi_14 at 8.9%)
- ⚠️ Macro/OHLC/Onchain at 0% (but may just be no recent source data)

## What We Know From Progress Monitor

Based on the attached terminal output:
1. **Price Collector**: ✅ Working (data flowing into materialized table)
2. **Technical Calculator**: ✅ Working (rsi_14 improving from 6.9% to 8.9%)
3. **Materialized Updater**: ✅ Working (processing ~400-2000 records every 10 min)
4. **Macro/OHLC/Onchain**: ⚠️ 0% - May be working but no recent source data

## Conclusion

**All core systems appear operational**. The 0% values for macro/OHLC/onchain may indicate:
- No recent source data available
- Collectors working but data not collected yet
- Need to check collector logs to confirm


