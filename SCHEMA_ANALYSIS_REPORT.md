# Database Schema Analysis Report

## Major Discrepancies Found Between Schema Files and Actual Database

After analyzing the actual database structure, I found significant discrepancies between our schema definition files and the real database tables. Here's a comprehensive analysis:

## 1. **Technical Indicators Table - MAJOR MISMATCH**

### **Actual Database Structure:**
- **113 columns** in production
- Uses `timestamp_iso` (datetime) as primary timestamp field
- Extensive technical indicators including:
  - `rsi` (not `rsi_14`) - DECIMAL(10,4)
  - `bollinger_upper`, `bollinger_middle`, `bollinger_lower` - DECIMAL(20,8)
  - Advanced indicators: `atr`, `adx`, `cci`, `momentum`, `roc`, `vwap`, `obv`, `ppo`, `tsi`
  - Volume indicators: `volume_sma_20`, `volume_ratio`, `klinger_oscillator`
  - Ichimoku indicators: `ichimoku_base`, `ichimoku_conversion`, `ichimoku_span_a/b`
  - Support/resistance: `support_level`, `resistance_level`, `pivot_point`
  - Fibonacci levels: `fibonaci_38`, `fibonaci_50`, `fibonaci_62`
  - Pattern recognition: `candlestick_pattern`

### **Schema Files Have:**
- Simplified version with ~16 columns
- Uses `timestamp` (timestamp) field
- Basic indicators only: `rsi_14`, `sma_20/50/200`, `macd`, `bollinger_upper/middle/lower`

## 2. **Crypto Assets Table - Structure Mismatch**

### **Actual Database:**
```sql
CREATE TABLE `crypto_assets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `symbol` varchar(16) NOT NULL,
  `name` varchar(64) NOT NULL,
  `aliases` json DEFAULT NULL,
  `category` varchar(32) DEFAULT 'crypto',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `coingecko_id` varchar(150) DEFAULT NULL,
  `description` text,
  `market_cap_rank` int DEFAULT NULL,
  `coingecko_score` decimal(5,2) DEFAULT NULL,
  `homepage` varchar(255) DEFAULT NULL,
  -- Plus many exchange support fields...
)
```

### **Schema Files Have:**
```sql
CREATE TABLE crypto_assets (
    id VARCHAR(50) PRIMARY KEY,  -- Wrong type!
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    market_cap_rank INT,
    current_price DECIMAL(20,8),  -- Not in actual table
    market_cap BIGINT,  -- Not in actual table
    total_volume BIGINT  -- Not in actual table
)
```

## 3. **Price Data Table - Real vs Expected**

### **Actual Table Name:** `price_data_real` 
- **47 columns** with extensive price and market data
- Uses `timestamp_iso` (datetime) and `timestamp` (bigint)
- Has fields like: `high_24h`, `low_24h`, `volume_usd_24h`, `market_cap`, `coin_id`
- Includes complex indexes and market cap ranking

### **Views Available:**
- `crypto_prices` (view)
- `crypto_prices_view` (view) 
- `crypto_prices_working` (view)

## 4. **Missing Tables in Schema Files**

The actual database has many tables not reflected in our schema files:

### **Core Tables:**
- `backtesting_results`
- `backtesting_trades`  
- `crypto_derivatives_ml` (187,846 records)
- `crypto_news` (52,778 records)
- `trading_signals` (extensive trading signal data)
- `trade_recommendations`
- `service_monitoring`

### **ML/Analytics Tables:**
- `enhanced_derivatives_data`
- `enhanced_trading_signals`
- Multiple sentiment aggregation tables

## 5. **Schema File Issues**

### **create_missing_tables.py Problems:**
1. **Wrong database name**: References `crypto_news` but actual database is different
2. **Simplified schemas**: Tables have basic fields vs complex production structure  
3. **Missing tables**: Only defines 6 tables vs 30+ in production
4. **Wrong data types**: ID fields should be `int AUTO_INCREMENT`, not `VARCHAR(50)`

### **init_ci_database.py Problems:**
1. **Schema mismatch**: Uses simplified versions instead of production structure
2. **Field name conflicts**: `rsi_14` vs `rsi`, `bollinger_*` vs `bb_*`
3. **Missing critical fields**: Lacks `timestamp_iso`, extensive indicators, exchange support fields

## 6. **Critical Fixes Needed**

### **Immediate Actions:**

1. **Update create_missing_tables.py** to match actual production schemas
2. **Fix init_ci_database.py** to use exact production table structures  
3. **Update documentation** to reflect 30+ tables, not just 6
4. **Add missing tables** to schema definitions
5. **Correct data types** and field names throughout

### **Technical Indicators Fix:**
```sql
-- Replace simplified version with actual 113-column structure
-- Key fields: timestamp_iso, rsi (not rsi_14), bollinger_upper/middle/lower
-- Add all advanced indicators: atr, adx, vwap, ichimoku_*, fibonacci levels
```

### **Crypto Assets Fix:**  
```sql
-- Change id from VARCHAR(50) to int AUTO_INCREMENT
-- Add missing fields: aliases, category, is_active, coingecko_id, description
-- Remove non-existent fields: current_price, market_cap, total_volume
```

## 7. **Impact Assessment**

### **High Risk:**
- Integration tests likely failing due to schema mismatches
- CI/CD database doesn't reflect production structure
- Data collection scripts may fail on production

### **Medium Risk:**
- Documentation doesn't match reality
- New developers will be confused by schema differences
- Backup/restore operations may fail

## Next Steps
1. Generate accurate schema definitions from production database
2. Update all schema files to match production exactly  
3. Test CI/CD with corrected schemas
4. Update documentation and README files