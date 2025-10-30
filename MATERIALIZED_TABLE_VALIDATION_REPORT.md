# Materialized Table Validation Report

## 📊 **OVERALL STATUS**

**Total Records**: 3,524,866  
**Date Range**: 2019-12-31 to 2025-10-21  
**Unique Symbols**: 333  
**Unique Dates**: 2,098  

## 🎯 **DATA COMPLETENESS ANALYSIS**

### **1. Price Data Coverage** ✅ **EXCELLENT**
- Current Price: **100.0%** (3,524,765 records)
- Price Change 24h: **99.0%** (3,487,937 records)
- Volume 24h: **96.5%** (3,402,626 records)
- Market Cap: **82.0%** (2,891,961 records)
- **Overall Price Completeness: 94.4%**

### **2. Sentiment Data Coverage** ⚠️ **NEEDS IMPROVEMENT**
- Crypto Sentiment: **0.8%** (29,616 records)
- Stock Sentiment: **0.0%** (370 records)
- Social Sentiment: **0.1%** (3,402 records)
- Overall Sentiment: **0.8%** (29,947 records)
- Sentiment Volume: **100.0%** (3,524,866 records)
- **Overall Sentiment Completeness: 20.4%**

### **3. Onchain Data Coverage** ⚠️ **NEEDS SIGNIFICANT IMPROVEMENT**
- Active Addresses 24h: **0.4%** (15,837 records)
- Transaction Count 24h: **0.5%** (17,546 records)
- Exchange Net Flow 24h: **4.6%** (162,375 records)
- Price Volatility 7d: **0.4%** (12,775 records)
- **Overall Onchain Completeness: 1.5%**

## 🔍 **KEY FINDINGS**

### **✅ STRENGTHS**
1. **Price Data**: Excellent coverage (94.4%) - nearly complete
2. **Data Volume**: 3.5M+ records with good historical depth
3. **Symbol Coverage**: 333 unique symbols processed
4. **Recent Activity**: 15,449 records updated in last hour
5. **Complete Records**: 5,365 records have all data types (0.2%)

### **⚠️ AREAS NEEDING ATTENTION**

#### **1. Sentiment Data (20.4% completeness)**
- **Issue**: Very low sentiment coverage across all types
- **Impact**: ML models lack sentiment features for most records
- **Root Cause**: Sentiment service may not be processing all symbols
- **Action Needed**: Verify sentiment service is running and processing all symbols

#### **2. Onchain Data (1.5% completeness)**
- **Issue**: Extremely low onchain coverage
- **Impact**: ML models lack onchain features for 98.5% of records
- **Root Cause**: Onchain collector was limited to 50 symbols (now fixed)
- **Action Needed**: Continue onchain backfill to improve coverage

#### **3. Complete Records (0.2%)**
- **Issue**: Only 5,365 records have all data types
- **Impact**: Very few records suitable for comprehensive ML training
- **Root Cause**: Combination of low sentiment and onchain coverage
- **Action Needed**: Improve both sentiment and onchain data collection

## 📈 **RECOMMENDATIONS**

### **Immediate Actions**
1. **Verify Sentiment Service**: Check if sentiment service is processing all symbols
2. **Continue Onchain Backfill**: Run additional onchain backfill cycles
3. **Monitor Data Flow**: Ensure all collectors are running and processing all symbols

### **Medium-term Goals**
1. **Target Sentiment Coverage**: Aim for 80%+ sentiment coverage
2. **Target Onchain Coverage**: Aim for 50%+ onchain coverage
3. **Target Complete Records**: Aim for 10%+ complete records

### **Success Metrics**
- **Price Data**: ✅ Already excellent (94.4%)
- **Sentiment Data**: 🎯 Target 80% (currently 20.4%)
- **Onchain Data**: 🎯 Target 50% (currently 1.5%)
- **Overall Completeness**: 🎯 Target 70% (currently 38.7%)

## 🔧 **NEXT STEPS**

1. **Investigate Sentiment Service**: Check why sentiment coverage is so low
2. **Continue Onchain Collection**: Let the fixed onchain collector run and collect more data
3. **Monitor Progress**: Track improvements over time
4. **Optimize Data Flow**: Ensure all services are working efficiently

## 📊 **SAMPLE COMPLETE RECORDS**

Recent complete records show the system is working:
- **UNI**: $6.53, sentiment=0.000, active=99,407, volatility=11.33%
- **SOL**: $194.07, sentiment=0.000, active=104,886, volatility=4.99%
- **PEPE**: $0.00, sentiment=0.000, active=5,098, volatility=8.40%
- **VET**: $0.02, sentiment=0.000, active=42,215, volatility=21.73%
- **FLOKI**: $0.00, sentiment=0.000, active=18,401, volatility=10.59%

## 🎯 **CONCLUSION**

The materialized table has **excellent price data coverage** but needs significant improvement in **sentiment and onchain data coverage**. The recent fixes to the onchain collector should help improve onchain coverage over time. The next priority should be investigating and fixing the sentiment data collection to achieve better overall completeness.

**Current Status**: 🟡 **PARTIALLY COMPLETE** - Good foundation, needs sentiment and onchain improvements


