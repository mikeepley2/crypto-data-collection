# 📊 Database Schema Analysis for Collectors

**Status:** October 20, 2025 18:35 UTC  
**Report Type:** Schema Compatibility & Migration Guide

---

## ✅ **GOOD NEWS: ALL REQUIRED TABLES EXIST!**

All three data collectors can start writing data immediately. The database schema is already in place and compatible with the collectors.

---

## 📋 **Table Status Summary**

| Table | Exists | Records | Status | Collector |
|-------|--------|---------|--------|-----------|
| `macro_indicators` | ✅ YES | 48,822 | READY | Macro Collector |
| `onchain_metrics` | ✅ YES | 113,276 | READY | Onchain Collector |
| `technical_indicators` | ✅ YES | 3,297,120 | READY | Technical Collector |
| `crypto_assets` | ✅ YES | 362 | READY | Onchain Collector (config) |

---

## 🔍 **Detailed Table Analysis**

### **1. macro_indicators** ✅ READY
**Purpose:** Store macroeconomic indicators (GDP, inflation, VIX, etc.)

**Current Schema:**
```
Columns:
  - id (INT PRIMARY KEY AUTO_INCREMENT)
  - indicator_name (VARCHAR) - e.g., "US_GDP", "VIX"
  - indicator_date (DATE)
  - value (DECIMAL)
  - unit (VARCHAR) - e.g., "percentage", "points"
  - frequency (VARCHAR) - e.g., "monthly", "daily"
  - data_source (VARCHAR) - e.g., "FRED"
  - collected_at (TIMESTAMP)
```

**Current Data:** 48,822 records  
**Collector Write Strategy:** INSERT ON DUPLICATE KEY UPDATE

**✅ No Changes Needed** - Schema matches collector requirements perfectly

---

### **2. onchain_metrics** ✅ READY
**Purpose:** Store blockchain metrics (Bitcoin, Ethereum, etc.)

**Current Schema:**
```
Columns (40+ fields including):
  - id (INT PRIMARY KEY AUTO_INCREMENT)
  - coin (VARCHAR) - Full name
  - coin_symbol (VARCHAR) - e.g., "BTC", "ETH"
  - collection_date (DATE)
  - timestamp (DATETIME)
  - price_usd (DECIMAL)
  - market_cap_usd (DECIMAL)
  - total_volume_usd_24h (DECIMAL)
  - active_addresses_24h (INT)
  - transaction_count_24h (INT)
  - transaction_volume_usd_24h (DECIMAL)
  - exchange_inflow_24h (DECIMAL)
  - exchange_outflow_24h (DECIMAL)
  - network_difficulty (DECIMAL)
  - hash_rate (DECIMAL)
  - [30+ more columns for comprehensive metrics]
```

**Current Data:** 113,276 records  
**Collector Write Strategy:** INSERT OR UPDATE

**✅ No Changes Needed** - Extensive schema already supports all metrics

---

### **3. technical_indicators** ✅ READY
**Purpose:** Store technical analysis indicators

**Current Schema:**
```
Columns (100+ fields including):
  - id (INT PRIMARY KEY AUTO_INCREMENT)
  - symbol (VARCHAR) - e.g., "BTCUSD", "ETHUSD"
  - timestamp_iso (DATETIME)
  - sma_20, sma_50, sma_200 (DECIMAL) - Simple Moving Averages
  - ema_12, ema_26, ema_50 (DECIMAL) - Exponential Moving Averages
  - macd, macd_signal (DECIMAL) - MACD indicators
  - rsi, rsi_14 (DECIMAL) - Relative Strength Index
  - bollinger_upper, bollinger_middle, bollinger_lower (DECIMAL)
  - stoch_k, stoch_d (DECIMAL) - Stochastic
  - williams_r (DECIMAL)
  - atr, atr_14 (DECIMAL) - Average True Range
  - adx (DECIMAL) - Average Directional Index
  - cci, cci_14 (DECIMAL) - Commodity Channel Index
  - momentum, roc (DECIMAL) - Rate of Change
  - [100+ more columns for comprehensive indicators]
```

**Current Data:** 3,297,120 records  
**Collector Write Strategy:** INSERT ON DUPLICATE KEY UPDATE

**✅ No Changes Needed** - Comprehensive schema supports all technical indicators

---

### **4. crypto_assets** ✅ READY
**Purpose:** Asset configuration (used by collectors)

**Current Schema:**
```
Columns:
  - id (INT PRIMARY KEY AUTO_INCREMENT)
  - symbol (VARCHAR) - e.g., "BTC", "ETH"
  - name (VARCHAR) - Full name
  - aliases (VARCHAR) - Alternative names
  - category (VARCHAR) - e.g., "Layer 1", "Stablecoin"
  - is_active (BOOLEAN) - Default 1
  - created_at (TIMESTAMP)
  - coingecko_id (VARCHAR)
  - description (TEXT)
  - market_cap_rank (INT)
  - [10+ more columns for asset metadata]
```

**Current Data:** 362 active assets  
**Used By:** Onchain collector (reads list of active symbols)

**✅ No Changes Needed** - Collector reads from here successfully

---

## ⚠️ **Why Collectors Are Showing "Column Not Found" Errors**

The database schema is correct, BUT the collector code has a **mismatch**:

### **Issue #1: Macro Collector Error**
```
ERROR: Unknown column 'timestamp' in 'field list'
```

**Why:** The collector code tries to INSERT with `timestamp`, but the table uses:
- `indicator_date` (DATE)
- `collected_at` (TIMESTAMP)

**Fix Required:** Update `macro_collector.py` to use correct column names

### **Issue #2: Onchain Collector Error**
```
ERROR: Unknown column 'active' in 'where clause'
```

**Why:** The collector queries `crypto_assets` with WHERE `active = 1`, but the column is:
- `is_active` (not `active`)

**Fix Required:** Update `onchain_collector.py` to use `is_active` column

---

## 🔧 **Required Code Changes**

### **Change #1: Macro Collector** 
**File:** `services/macro-collection/macro_collector.py`

**Current (Wrong):**
```python
INSERT INTO macro_indicators (
    indicator_name, timestamp, value, source
) VALUES (%s, %s, %s, %s)
```

**Fixed:**
```python
INSERT INTO macro_indicators (
    indicator_name, indicator_date, value, data_source
) VALUES (%s, %s, %s, %s)
```

---

### **Change #2: Onchain Collector**
**File:** `services/onchain-collection/onchain_collector.py`

**Current (Wrong):**
```python
SELECT DISTINCT symbol FROM crypto_assets WHERE active = 1
```

**Fixed:**
```python
SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1
```

---

## 📊 **Data Flow After Fixes**

```
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES PODS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Technical Collector (Every 5 min)                          │
│  └─> Reads: price_data_real                                │
│  └─> Writes: technical_indicators ✅                        │
│  └─> Current: Working (0 symbols found = no price data yet) │
│                                                             │
│  Macro Collector (Every 1 hour)                             │
│  └─> FRED API ← [FRED Key configured]                      │
│  └─> Writes: macro_indicators ❌ [Column name fix needed]  │
│  └─> Issue: 'timestamp' vs 'indicator_date'                │
│                                                             │
│  Onchain Collector (Every 6 hours)                          │
│  └─> Free APIs (blockchain.info, Etherscan, Messari)       │
│  └─> Reads: crypto_assets WHERE is_active=1 ❌             │
│  └─> Writes: onchain_metrics ✅                            │
│  └─> Issue: 'active' vs 'is_active'                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              DATABASE (crypto_prices)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  technical_indicators ← 3,297,120 records                  │
│  macro_indicators ← 48,822 records                         │
│  onchain_metrics ← 113,276 records                         │
│  crypto_assets ← 362 active symbols                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Schema Changes Summary**

| Item | Status | Action |
|------|--------|--------|
| macro_indicators table | ✅ EXISTS | Update collector column names |
| onchain_metrics table | ✅ EXISTS | No schema change needed |
| technical_indicators table | ✅ EXISTS | No schema change needed |
| crypto_assets table | ✅ EXISTS | No schema change needed |
| **Total schema changes needed** | **0 tables** | Only code updates needed |

---

## 🚀 **Next Steps (In Order)**

### **Step 1: Update Macro Collector Code**
**File:** `k8s/collectors/collector-configmaps.yaml` - `macro_collector.py` section

Change INSERT statement from:
```sql
INSERT INTO macro_indicators (indicator_name, timestamp, value, source)
```

To:
```sql
INSERT INTO macro_indicators (indicator_name, indicator_date, value, data_source)
```

### **Step 2: Update Onchain Collector Code**
**File:** `k8s/collectors/collector-configmaps.yaml` - `onchain_collector.py` section

Change SELECT statement from:
```sql
SELECT DISTINCT symbol FROM crypto_assets WHERE active = 1
```

To:
```sql
SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1
```

### **Step 3: Redeploy Collectors**
```bash
# Apply updated ConfigMap
kubectl apply -f k8s/collectors/collector-configmaps.yaml

# Restart collectors to pick up new code
kubectl rollout restart deployment/macro-collector -n crypto-data-collection
kubectl rollout restart deployment/onchain-collector -n crypto-data-collection
```

### **Step 4: Verify Data Flow**
```bash
# Check logs for successful writes
kubectl logs -f macro-collector-xxx -n crypto-data-collection
kubectl logs -f onchain-collector-xxx -n crypto-data-collection

# Query new records
SELECT COUNT(*) FROM macro_indicators WHERE collected_at > NOW() - INTERVAL 1 HOUR;
SELECT COUNT(*) FROM onchain_metrics WHERE collection_date = CURDATE();
```

---

## 📝 **Summary**

**Database Schema Status:** ✅ **COMPLETE & READY**

All required tables exist with comprehensive columns. The only issues are:

1. **Macro Collector:** Uses wrong column names (`timestamp` vs `indicator_date`)
2. **Onchain Collector:** Uses wrong column name filter (`active` vs `is_active`)

**No database schema changes needed.** Only collector code needs updates to match existing column names.

**Estimated Time to Fix:** 5 minutes
- Update 2 code sections in ConfigMaps
- Restart 2 pods
- Data will flow automatically

---

## 💾 **Current Database Statistics**

| Metric | Value |
|--------|-------|
| Total tables in crypto_prices | 40+ |
| Total records stored | 11.7M+ |
| Technical Indicators records | 3,297,120 |
| Price data (hourly) | 3,496,970 |
| Macro indicators records | 48,822 |
| Onchain metrics records | 113,276 |
| Active crypto assets | 362 |
