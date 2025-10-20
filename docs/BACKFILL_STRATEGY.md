# Backfill Strategy & Implementation Guide

**Date:** October 20, 2025 21:45 UTC  
**Status:** Ready for Implementation

---

## Overview

All three data collectors (technical, macro, onchain) now support backfilling historical data to replace placeholder NULL values with real, accurate data from APIs.

---

## Current Situation

### What We Have
- **Technical:** 3.3M calculated records (100% SMA/RSI)
- **Macro:** 48K records with placeholders (no real data)
- **Onchain:** 113K records with NULL values (no real data)

### What We Need
- Replace macro NULL placeholders with FRED API data
- Replace onchain NULL placeholders with Messari/blockchain.info data
- Expand technical coverage from 76-86% to 95%+

---

## Backfill Modes

### 1. Technical Indicators Backfill

**Trigger:**
```bash
kubectl set env deployment/technical-calculator BACKFILL_DAYS=90
```

**What it does:**
- Recalculates SMA 20, SMA 50, RSI 14, MACD from last 90 days of price data
- Processes up to 500 cryptocurrencies per run
- Overwrites existing data (ON DUPLICATE KEY UPDATE)
- Runs once and exits (not continuous)

**Timeline:**
- 90 days: ~30 minutes
- 365 days: ~2 hours
- All available: ~4 hours

**Expected improvement:**
- RSI: 76.4% → 95%+
- All technical: Complete coverage

**Command:**
```bash
# Set backfill mode
kubectl set env deployment/technical-calculator BACKFILL_DAYS=365

# Wait for pod to complete
kubectl logs -f deployment/technical-calculator

# Unset backfill when done
kubectl set env deployment/technical-calculator BACKFILL_DAYS=-
```

---

### 2. Macro Indicators Backfill

**Requirements:**
- FRED API Key (free from https://fred.stlouisfed.org/docs/api/fred/)
- Already found: Configured in Kubernetes secret

**Trigger:**
```bash
kubectl set env deployment/macro-collector BACKFILL_DAYS=730
```

**What it does:**
- Fetches from FRED API: unemployment, inflation, GDP, interest rates, VIX, DXY, gold, oil
- Gets last 730 days of historical data
- Replaces NULL placeholders with real values
- Runs once and exits

**Supported indicators (9 total):**
```
US_UNEMPLOYMENT      → UNRATE (Unemployment Rate)
US_INFLATION         → CPIAUCSL (Consumer Price Index)
US_GDP               → A191RO1Q156NBEA (Real GDP)
FEDERAL_FUNDS_RATE   → FEDFUNDS (Federal Funds Rate)
10Y_YIELD            → DFF10 (10-Year Treasury)
VIX                  → VIXCLS (VIX Index)
DXY                  → DEXUSEU (Dollar Index)
GOLD_PRICE           → GOLDAMND (Gold Price)
OIL_PRICE            → DCOILWTICO (Oil Price)
```

**Timeline:**
- 365 days: ~5 minutes
- 730 days (2 years): ~10 minutes
- All available: ~20 minutes

**Expected improvement:**
- Current: 95.8% unemployment/inflation, 0% GDP/rates
- After: 95.8% all 9 indicators

**Commands:**
```bash
# Set backfill mode for 2 years
kubectl set env deployment/macro-collector BACKFILL_DAYS=730

# Monitor progress
kubectl logs -f deployment/macro-collector

# After completion, resume normal operation
kubectl set env deployment/macro-collector BACKFILL_DAYS=-
```

---

### 3. Onchain Metrics Backfill

**Data Sources:**
- **Primary:** Messari API (free, no key needed)
- **Fallback:** blockchain.info for Bitcoin
- **Coverage:** Active addresses, transaction count, exchange flows, volatility

**Trigger:**
```bash
kubectl set env deployment/onchain-collector BACKFILL_DAYS=180
```

**What it does:**
- Fetches real onchain data from Messari API
- Gets last 180 days of metrics
- Replaces NULL placeholders with real values
- Tracks data source in database
- Falls back gracefully if API unavailable

**Metrics collected:**
```
active_addresses_24h       → Number of active addresses
transaction_count_24h      → Daily transaction count
exchange_net_flow_24h      → Net exchange inflows/outflows
price_volatility_7d        → 7-day price volatility
```

**Timeline:**
- 90 days: ~15 minutes
- 180 days: ~30 minutes
- 365 days: ~1 hour

**Expected improvement:**
- Current: 0.1% coverage (3,068 records out of 3.5M)
- After backfill: 40-60% coverage (depending on API data availability)

**Commands:**
```bash
# Set backfill mode for 6 months
kubectl set env deployment/onchain-collector BACKFILL_DAYS=180

# Monitor progress
kubectl logs -f deployment/onchain-collector

# After completion
kubectl set env deployment/onchain-collector BACKFILL_DAYS=-
```

---

## Full Backfill Implementation Plan

### Phase 1: Technical Indicators (Quick Win)
**Effort:** Low | **Time:** 1-2 hours | **Impact:** High

```bash
# Step 1: Trigger backfill
kubectl set env deployment/technical-calculator BACKFILL_DAYS=365

# Step 2: Monitor
kubectl logs -f deployment/technical-calculator

# Step 3: Verify
kubectl exec -it deployment/technical-calculator -- python -c \
  "import mysql.connector; c = mysql.connector.connect(...); \
   cursor = c.cursor(); \
   cursor.execute('SELECT COUNT(*) FROM technical_indicators WHERE sma_20 IS NOT NULL'); \
   print(f'Technical records: {cursor.fetchone()[0]:,}')"

# Step 4: Reset (after completion)
kubectl set env deployment/technical-calculator BACKFILL_DAYS=-
```

### Phase 2: Macro Indicators
**Effort:** Low | **Time:** 2-3 hours | **Impact:** Medium

```bash
# Backfill last 2 years of macro data
kubectl set env deployment/macro-collector BACKFILL_DAYS=730

# Monitor
kubectl logs -f deployment/macro-collector

# Verify
kubectl exec -it deployment/macro-collector -- python -c \
  "import mysql.connector; c = mysql.connector.connect(...); \
   cursor = c.cursor(); \
   cursor.execute('SELECT COUNT(*) FROM macro_indicators WHERE value IS NOT NULL'); \
   print(f'Macro records with data: {cursor.fetchone()[0]:,}')"

# Reset
kubectl set env deployment/macro-collector BACKFILL_DAYS=-
```

### Phase 3: Onchain Metrics
**Effort:** Medium | **Time:** 4-6 hours | **Impact:** High

```bash
# Backfill 6 months of onchain data
kubectl set env deployment/onchain-collector BACKFILL_DAYS=180

# Monitor
kubectl logs -f deployment/onchain-collector

# Verify (expect 40-60% coverage from Messari)
kubectl exec -it deployment/onchain-collector -- python -c \
  "import mysql.connector; c = mysql.connector.connect(...); \
   cursor = c.cursor(); \
   cursor.execute('SELECT COUNT(*) FROM crypto_onchain_data WHERE active_addresses_24h IS NOT NULL'); \
   print(f'Onchain records with data: {cursor.fetchone()[0]:,}')"

# Reset
kubectl set env deployment/onchain-collector BACKFILL_DAYS=-
```

---

## Backfill Results Tracking

### Before Backfill
```
Component      Records   Null%    Coverage
Technical      3.3M      14-24%   76-86%
Macro          48K       100%     0% (real values)
Onchain        113K      99%      0.1%
═══════════════════════════════════════════
Materialized   3.5M      Various  Mixed
```

### After Backfill
```
Component      Records   Null%    Coverage
Technical      3.3M      0-5%     95%+
Macro          48K       ~5%      95%+
Onchain        113K      40-60%   40-60%
═══════════════════════════════════════════
Materialized   3.5M      ~10%     80%+
```

---

## Verification Queries

### Technical Indicators
```sql
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as with_sma,
  SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as with_rsi,
  SUM(CASE WHEN macd IS NOT NULL THEN 1 ELSE 0 END) as with_macd
FROM technical_indicators;
```

### Macro Indicators
```sql
SELECT 
  indicator_name,
  COUNT(*) as total,
  SUM(CASE WHEN value IS NOT NULL THEN 1 ELSE 0 END) as with_data
FROM macro_indicators
GROUP BY indicator_name
ORDER BY with_data DESC;
```

### Onchain Metrics
```sql
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as with_addr,
  SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as with_txn,
  SUM(CASE WHEN exchange_net_flow_24h IS NOT NULL THEN 1 ELSE 0 END) as with_flow
FROM crypto_onchain_data;
```

### Materialized Impact
```sql
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as technical,
  SUM(CASE WHEN unemployment_rate IS NOT NULL THEN 1 ELSE 0 END) as macro,
  SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as onchain
FROM ml_features_materialized;
```

---

## Implementation Checklist

### Pre-Backfill
- [ ] Review current data state
- [ ] Verify API keys are configured
- [ ] Plan backfill window (off-peak hours)
- [ ] Set backup/snapshot

### During Backfill
- [ ] Monitor pod logs in real-time
- [ ] Track record counts
- [ ] Check for errors
- [ ] Verify data quality

### Post-Backfill
- [ ] Run verification queries
- [ ] Compare before/after statistics
- [ ] Update materialized views
- [ ] Document results
- [ ] Reset BACKFILL_DAYS environment variable

---

## Estimated Impact on ML Features

After full backfill:
```
3.5M records enriched with:
- 100% technical indicators
- 95% macro indicators
- 40-60% onchain metrics

Total: 50+ columns populated
Combined coverage: 80%+ complete data
```

---

## Troubleshooting

### Pod not completing backfill
```bash
# Check logs
kubectl logs deployment/technical-calculator

# Increase timeout if needed
kubectl patch deployment technical-calculator -p '{"spec":{"template":{"spec":{"activeDeadlineSeconds":14400}}}}'
```

### API errors
```bash
# Check if APIs are accessible
curl https://data.messari.io/api/v1/assets/bitcoin/metrics
curl https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key=YOUR_KEY

# Check API limits
# Most free APIs have rate limits (e.g., 120 requests/minute for FRED)
```

### Data not updating
```bash
# Verify ON DUPLICATE KEY UPDATE is working
# Check if records are being committed
kubectl exec -it deployment/technical-calculator -- \
  mysql -h127.0.0.1 -unews_collector -p crypto_prices \
  -e "SELECT MAX(updated_at) FROM technical_indicators;"
```

---

## Next Steps

1. **Implement Phase 1 (Technical)** - Complete in 1-2 hours
2. **Implement Phase 2 (Macro)** - Complete in 2-3 hours
3. **Implement Phase 3 (Onchain)** - Complete in 4-6 hours
4. **Verify total impact** - Run comprehensive query
5. **Trigger materialized view refresh** - Update aggregations

**Total Time:** ~8-12 hours of backfill operations

---

## Success Criteria

✓ Technical coverage: 95%+  
✓ Macro coverage: 95%+  
✓ Onchain coverage: 40%+  
✓ Materialized table: 80%+ complete  
✓ Zero NULL placeholders remaining (where API data available)  
✓ Data quality validated  

---

*This strategy replaces placeholder data with real, API-sourced metrics for accurate ML model training.*
