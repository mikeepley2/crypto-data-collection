# Onchain Data Issues Analysis

## Executive Summary

🚨 **ROOT CAUSE IDENTIFIED** - Onchain data is being collected but NOT integrated into materialized table

## Issue Analysis

### ✅ **What's Working**
- **Onchain Collector**: Running and processing 50 metrics every 6 hours
- **Data Collection**: 950 records in last 7 days with real data
- **Data Quality**: 18/19 records have complete onchain metrics per symbol
- **Schema Compatibility**: All data types match between tables

### ❌ **What's Broken**
- **Materialized Integration**: 0.0% onchain coverage in materialized table
- **Updater Logic**: Materialized updater doesn't include onchain data
- **Data Flow**: Onchain data exists but never reaches ML features

## Technical Details

### 📊 **Data Flow Status**
```
Onchain Collector → crypto_onchain_data ✅ (Working)
crypto_onchain_data → ml_features_materialized ❌ (Broken)
```

### 🔍 **Evidence**
- **Onchain Data**: 950 recent records with real values (active_addresses_24h=842672)
- **Materialized Table**: 0 records with onchain data (0.0% coverage)
- **Schema Match**: All columns exist and data types are compatible
- **Join Test**: Data exists in onchain table but NULL in materialized table

### 🛠️ **Root Cause**
The materialized updater code only processes:
1. **Price data** from `price_data_real`
2. **Sentiment data** from `crypto_news`

**Missing**: Onchain data integration from `crypto_onchain_data`

## Required Fixes

### 1. **Update Materialized Updater Logic**
Add onchain data integration to the materialized updater:

```python
# Add onchain data JOIN to the materialized updater
cursor.execute('''
SELECT 
    o.active_addresses_24h,
    o.transaction_count_24h,
    o.exchange_net_flow_24h,
    o.price_volatility_7d
FROM crypto_onchain_data o
WHERE o.coin_symbol = %s 
AND o.collection_date >= DATE_SUB(%s, INTERVAL 24 HOUR)
ORDER BY o.collection_date DESC
LIMIT 1
''', (symbol, timestamp_iso))
```

### 2. **Update INSERT Statement**
Include onchain fields in the materialized table INSERT:

```sql
INSERT INTO ml_features_materialized 
(symbol, price_date, price_hour, timestamp_iso, current_price, 
 active_addresses_24h, transaction_count_24h, exchange_net_flow_24h, price_volatility_7d,
 ...)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, ...)
```

### 3. **Update ON DUPLICATE KEY UPDATE**
Include onchain fields in the update clause:

```sql
ON DUPLICATE KEY UPDATE
active_addresses_24h = VALUES(active_addresses_24h),
transaction_count_24h = VALUES(transaction_count_24h),
exchange_net_flow_24h = VALUES(exchange_net_flow_24h),
price_volatility_7d = VALUES(price_volatility_7d),
...
```

## Impact Assessment

### 📈 **Current State**
- **Onchain Data**: 950 records collected ✅
- **Materialized Integration**: 0 records (0.0%) ❌
- **ML Features**: Missing onchain data for model training ❌

### 🎯 **Expected After Fix**
- **Onchain Data**: 950 records collected ✅
- **Materialized Integration**: 950 records (100%) ✅
- **ML Features**: Complete onchain data for model training ✅

## Next Steps

1. **Update Materialized Updater**: Add onchain data integration logic
2. **Test Integration**: Verify onchain data flows to materialized table
3. **Monitor Coverage**: Ensure 100% onchain data integration
4. **Validate ML Features**: Confirm onchain data available for model training

## Conclusion

The onchain data collection is working perfectly, but the **materialized updater is missing onchain data integration**. This is a configuration issue, not a data collection issue. Once fixed, the onchain data will flow properly into the ML features materialized table.


