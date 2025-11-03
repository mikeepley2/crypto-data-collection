# Materialized Updater Restart Guide

## ✅ Fixes Applied

The `src/docker/materialized_updater/realtime_materialized_updater.py` has been fixed with:

1. **OHLC Data** - Fixed to use `timestamp_iso` correctly
2. **Technical Indicators** - Fixed to use `(symbol, date)` lookup instead of `(date, hour)`
3. **Macro Indicators** - Fixed to query `macro_indicators` table correctly
4. **Onchain Data** - Added batch lookup integration (lines 861-890, 1263-1293)

## 🔄 Restart the Materialized Updater

### Option 1: Kubernetes Deployment

```bash
# Restart the deployment
kubectl rollout restart deployment/materialized-updater -n crypto-data-collection

# Wait for rollout
kubectl rollout status deployment/materialized-updater -n crypto-data-collection --timeout=120s

# Check logs
kubectl logs -n crypto-data-collection -l app=materialized-updater --tail=50 -f
```

### Option 2: If Running Locally or in Docker

1. Stop the current service
2. Ensure the updated code from `src/docker/materialized_updater/realtime_materialized_updater.py` is deployed
3. Restart the service

## ✅ Verify It's Working

After restart, wait 5-10 minutes, then run:

```bash
python verify_updater_status.py
```

This will check:
- Recent record updates
- Column completeness for key fields
- Source data availability

## 📊 Expected Behavior

The updater should now:
- ✅ Process new price data automatically
- ✅ Populate technical indicators using `(symbol, date)` lookup
- ✅ Populate macro indicators from `macro_indicators` table
- ✅ Populate OHLC data correctly
- ✅ Populate onchain data for symbols with onchain metrics

## 🔍 Monitoring

Monitor the updater logs for:
- "Starting materialized table update cycle..."
- "Finished processing for symbol: ..."
- Check for any errors in the logs

The updater will process records as new price data arrives and backfill missing fields automatically.


