# Database Cleanup Analysis Report

## 🔍 **Analysis Summary - September 30, 2025**

### 📊 **Database Overview**
- **Total Tables**: 27
- **Total Database Size**: 4,487 MB (4.4 GB)
- **Tables Analyzed**: All tables examined for usage patterns

---

## 🗑️ **SAFE TO DELETE (8 tables - 0.43 MB)**

### ✅ **Definitely Unused Tables**
These tables are empty or contain minimal data not used by current collectors:

1. **daily_regime_summary** - Empty view (0 rows)
2. **sentiment_data** - Empty view (0 rows) 
3. **social_media_posts** - Empty table (0 rows)
4. **social_platform_stats** - Empty table (0 rows)
5. **trading_engine_v2_summary** - Empty view (0 rows)
6. **collection_monitoring** - 12 rows, 0.05 MB
7. **crypto_metadata** - 34 rows, 0.11 MB
8. **monitoring_alerts** - 17 rows, 0.05 MB

**Space Savings**: 0.43 MB

---

## ⚠️ **ARCHIVE CANDIDATES (2 tables - 8.09 MB)**

### 📦 **Potentially Unused Tables**
These should be archived but NOT deleted until confirmed:

1. **assets_archived** - 315 rows, 0.03 MB (archived asset data)
2. **macro_indicators** - 48,816 rows, 8.06 MB (economic data, may still be used)

**Recommendation**: Keep these for now, investigate further

---

## 🔍 **INVESTIGATION RESULTS - LARGE TABLES**

### 📊 **Tables Requiring Action**

#### **KEEP - Active/Valuable Data**
1. **trading_signals** (16.81 MB, 25,962 rows)
   - ✅ **KEEP**: Contains recent trading signals (20,678 recent rows)
   - Used by trading systems, has data from last 30 days

2. **sentiment_aggregation** (16.09 MB, 67,721 rows) 
   - ⚠️ **ARCHIVE OLD**: No recent data (last update Aug 13)
   - May contain valuable historical patterns

3. **real_time_sentiment_signals** (26.09 MB, 113,853 rows)
   - ⚠️ **ARCHIVE OLD**: No recent data (last update Aug 26)
   - Contains sentiment signals that may be valuable for ML

4. **hourly_data** (Large, 3.3M rows)
   - ✅ **KEEP**: Contains hourly OHLC data from 2019-2025
   - 13,558 recent rows, actively updated
   - **Critical data** - DO NOT DELETE

5. **onchain_metrics** (111,956 rows)
   - ✅ **KEEP**: Likely used by onchain-data-collector
   - Contains blockchain metrics data

#### **ARCHIVE CANDIDATES**
6. **service_monitoring** (63.16 MB, 223,673 rows)
   - 📦 **ARCHIVE OLD**: Contains service health monitoring
   - 3,372 recent rows, can archive data older than 90 days

---

## 🚀 **RECOMMENDED CLEANUP ACTIONS**

### **Phase 1: Safe Immediate Cleanup**
Execute these deletions immediately (minimal risk):

```sql
-- SAFE TO DELETE - Empty or minimal tables
DROP TABLE IF EXISTS `daily_regime_summary`;
DROP TABLE IF EXISTS `sentiment_data`;
DROP TABLE IF EXISTS `social_media_posts`;
DROP TABLE IF EXISTS `social_platform_stats`;
DROP TABLE IF EXISTS `trading_engine_v2_summary`;
DROP TABLE IF EXISTS `collection_monitoring`;
DROP TABLE IF EXISTS `crypto_metadata`;
DROP TABLE IF EXISTS `monitoring_alerts`;
```

**Space Saved**: ~0.43 MB

### **Phase 2: Archive Old Data (Optional)**
For larger space savings, archive old data from these tables:

1. **service_monitoring**: Archive records older than 90 days
2. **real_time_sentiment_signals**: Archive if not used by current ML models
3. **sentiment_aggregation**: Archive if not used by current sentiment services

**Potential Additional Space**: ~105 MB

### **Phase 3: DO NOT DELETE**
These tables contain critical data:
- ✅ **hourly_data** - Historical OHLC data (CRITICAL)
- ✅ **trading_signals** - Recent trading signals
- ✅ **onchain_metrics** - Blockchain data
- ✅ **macro_indicators** - Economic indicators

---

## 📋 **Execution Plan**

### **Step 1: Backup Database**
```bash
# Create full backup
mysqldump -h 192.168.230.162 -u news_collector -p99Rules! crypto_prices > crypto_prices_backup_$(date +%Y%m%d_%H%M%S).sql
```

### **Step 2: Execute Safe Cleanup**
Run the cleanup script for definitely unused tables only.

### **Step 3: Monitor Collectors**
After cleanup, monitor all collectors for 24 hours to ensure no issues.

### **Step 4: Optional Archival**
If needed, implement archival for old monitoring data.

---

## 💾 **Space Impact**
- **Current Database Size**: 4,487 MB
- **Safe Cleanup**: 0.43 MB (minimal impact)
- **Potential with Archival**: ~105 MB (2.3% reduction)

**Recommendation**: Proceed with Phase 1 safe cleanup only. The database is well-maintained with minimal unused data.

---

## ✅ **Conclusion**

The database is in excellent condition with minimal cleanup needed. Most tables contain valuable data that supports the active collection infrastructure. The safe cleanup will remove empty/minimal tables without risking data loss.

**Status**: Ready for safe cleanup execution
**Risk Level**: ✅ Low (only removing empty/minimal tables)
**Monitoring Required**: 24 hours post-cleanup

---

**Analysis Date**: September 30, 2025  
**Analyst**: Database Cleanup Tool  
**Recommendation**: Proceed with Phase 1 cleanup only