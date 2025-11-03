# Missing Data Analysis Report

**Date:** October 30, 2025  
**Period:** Last 7 days (Oct 24-31, 2025)

## Summary

Based on the completeness check, **104 out of 118 columns have <50% completeness** in the materialized table over the last week. Here's what should have been filled:

## Missing Data Breakdown

### 1. **Technical Indicators** ❌ CRITICAL ISSUE
**Status:** Should be populated but only 7.15% (rsi_14) and 7.86% (sma_20) complete

**Missing:**
- `sma_50`: 0% (0 records)
- `ema_12`: 0%
- `ema_26`: 0%
- `macd_line`: 0%
- `macd_signal`: 0%
- `macd_histogram`: 0%
- `bb_upper`, `bb_middle`, `bb_lower`: 0%
- `stoch_k`, `stoch_d`: 0%
- `atr_14`, `vwap`: 0%

**Source Data Available:**
- ✅ Technical indicators table has **161,646 records** for 87 symbols
- ✅ Date range: Oct 23-31
- ✅ Data exists in `technical_indicators` table

**Root Cause:** The materialized updater should be joining `technical_indicators` by `symbol` + `DATE(timestamp_iso)`, but it's only populating **7.15%** instead of ~95%+.

**Should Be Filled:** YES ✅ - Source data exists, updater should populate these fields.

---

### 2. **Macro Indicators** ❌ CRITICAL ISSUE  
**Status:** Should be populated but only 0.00% complete (1 record has VIX)

**Missing:**
- `vix`: 0.00% (only 1 record)
- `spx`: 0%
- `dxy`: 0%
- `tnx`: 0%
- `fed_funds_rate`: 0%
- `treasury_10y`: 0%
- `gold_price`: 0%
- `oil_price`: 0%
- `unemployment_rate`: 0%
- `inflation_rate`: 0%

**Source Data Available:**
- ⚠️ Macro indicators table has data for **Oct 23-27** (8 indicators per date)
- ❌ Missing Oct 28-30 (FRED API issue - data not available yet)

**Root Cause:** The materialized updater should be joining `macro_indicators` by `indicator_date`, but it's only populating **0.00%**.

**Should Be Filled:** YES ✅ for Oct 23-27 (source data exists). NO for Oct 28-30 (FRED data not available yet).

---

### 3. **Sentiment Indicators** ❌ CRITICAL ISSUE
**Status:** Should be populated but 0% complete

**Missing:**
- `avg_cryptobert_score`: 0%
- `avg_vader_score`: 0%
- `avg_textblob_score`: 0%
- `avg_crypto_keywords_score`: 0%
- `avg_finbert_sentiment_score`: 0%
- `avg_fear_greed_score`: 0%
- All other sentiment columns: 0%

**Source Data Available:**
- ❌ **No data** in `crypto_sentiment_data` for last 7 days
- ❌ **No data** in `stock_market_sentiment_data` for last 7 days

**Root Cause:** No source data available. Sentiment aggregation may not be running or may have stopped.

**Should Be Filled:** NO ❌ - No source data available. Need to check sentiment aggregation services.

---

### 4. **OHLC Data** ❌ CRITICAL ISSUE
**Status:** Should be populated but 0% complete

**Missing:**
- `open_price`: 0%
- `high_price`: 0%
- `low_price`: 0%
- `ohlc_volume`: 0%
- `ohlc_source`: 0%

**Source Data Available:**
- Need to check `ohlc_data` table

**Root Cause:** OHLC data may not be collected or not joined correctly.

**Should Be Filled:** UNKNOWN - Need to verify if `ohlc_data` table has data.

---

### 5. **Onchain Data** ⚠️ PARTIAL
**Status:** 33.42% complete

**Populated:**
- `active_addresses_24h`: 33.42%
- `transaction_count_24h`: 33.42%
- `exchange_net_flow_24h`: 33.42%
- `price_volatility_7d`: 33.42%

**Root Cause:** Only partially populated. Should be ~100% if onchain data exists.

**Should Be Filled:** YES ✅ - Should be closer to 100% if source data exists.

---

### 6. **Other Missing Columns**
- `hourly_volume`: 0%
- `price_change_percentage_24h`: 0%
- All social sentiment columns: 0%
- Most duplicate/alternative column names (price vs current_price, etc.)

---

## Root Causes

### Primary Issue: Materialized Table Updater
The `realtime_materialized_updater.py` should be:
1. ✅ Joining `technical_indicators` by `symbol` + `DATE(timestamp_iso)` - **NOT WORKING** (only 7% populated)
2. ✅ Joining `macro_indicators` by `indicator_date` - **NOT WORKING** (0% populated)
3. ❌ Joining `crypto_sentiment_data` by date - **NO SOURCE DATA**
4. ⚠️ Joining `crypto_onchain_data` by symbol + date - **PARTIALLY WORKING** (33%)

### Secondary Issues:
- Sentiment aggregation services may not be running
- OHLC data collection may not be active
- Macro data missing for Oct 28-30 (FRED API issue)

---

## Recommendations

### Immediate Actions:
1. **Fix Technical Indicators Population:** Materialized updater should populate ~95%+ of records with technical data (currently only 7%)
2. **Fix Macro Indicators Population:** Materialized updater should populate all records for dates where macro data exists (currently 0%)
3. **Check Sentiment Services:** Verify why no sentiment data exists for last 7 days
4. **Verify OHLC Collection:** Check if OHLC data collector is running
5. **Improve Onchain Population:** Increase from 33% to ~95%+

### Data That Should NOT Be Filled:
- Macro indicators for Oct 28-30 (FRED data not available yet - this is expected)
- Sentiment data if sentiment services are not running

### Expected Completeness (if sources are available):
- **Technical indicators:** 95%+ ✅
- **Macro indicators:** 95%+ ✅ (for dates with FRED data)
- **Onchain data:** 95%+ ✅
- **Sentiment data:** Depends on sentiment services
- **OHLC data:** Depends on OHLC collector

---

## Conclusion

**Most missing data SHOULD be filled** but isn't due to:
1. Materialized updater not properly joining/populating technical and macro indicators
2. Sentiment aggregation services not producing data
3. Possible OHLC collector issues

The updater logic needs to be reviewed and fixed to ensure it properly joins source tables and populates the materialized table.



