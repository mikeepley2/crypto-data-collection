# 🔍 Onchain Data Collection Frequency Analysis

## 📊 Current Analysis: Is Hourly Sufficient for Signal Detection?

### **Signal Types & Required Frequencies**

#### **🚨 Strong Signals That Need Higher Frequency (Sub-hourly)**
1. **Network Congestion Events**
   - Gas fee spikes (can happen in minutes)
   - Transaction backlog formation
   - **Optimal**: Every 15-30 minutes

2. **Large Transaction Activity**
   - Whale movements (immediate market impact)
   - Exchange inflows/outflows
   - **Optimal**: Every 10-15 minutes

3. **Validator/Mining Changes**
   - Hash rate drops/spikes
   - Validator slashing events
   - **Optimal**: Every 15-30 minutes

#### **✅ Signals Adequately Captured Hourly**
1. **Developer Activity**
   - GitHub commits (batched activity)
   - Repository metrics
   - **Hourly is sufficient**

2. **Supply Changes**
   - Token burns (usually planned events)
   - Staking ratio changes (gradual)
   - **Hourly is sufficient**

3. **Social Metrics**
   - Community growth
   - Sentiment shifts
   - **Hourly is sufficient**

#### **📈 Trend Detection Analysis**

**Current Data Types in Collector:**
- Supply metrics ✅ (slow-changing, hourly OK)
- Price changes ⚠️ (could benefit from higher frequency)
- GitHub activity ✅ (hourly sufficient)
- Social metrics ✅ (hourly sufficient)

**Missing High-Frequency Signals:**
- ❌ Network transaction volume
- ❌ Active address counts
- ❌ Gas fees / transaction costs
- ❌ Hash rate / network security metrics
- ❌ Exchange flows

## 🎯 **Recommendation: Tiered Collection Strategy**

### **Tier 1: High-Frequency (Every 15 minutes)**
For rapid-changing network metrics:
- Transaction volume
- Active addresses
- Network fees
- Hash rate (for PoW)
- Exchange flows

### **Tier 2: Medium-Frequency (Every Hour)**  
For development and fundamental metrics:
- Supply changes
- Developer activity
- Social metrics
- Staking ratios

### **Tier 3: Low-Frequency (Daily)**
For comprehensive analysis:
- Historical correlations
- Long-term trend analysis
- Weekly/monthly aggregations

## 🚀 **Proposed Implementation**

### **Option A: Multi-Schedule Approach**
```yaml
# High-frequency onchain metrics
onchain-network-collector:
  schedule: "*/15 * * * *"  # Every 15 minutes
  
# Current fundamental metrics  
onchain-fundamental-collector:
  schedule: "0 * * * *"     # Every hour
```

### **Option B: Smart Collection Logic**
- Collect core metrics every 15 minutes
- Skip expensive API calls during low-activity periods
- Use different endpoints for different frequencies

## 📊 **Signal Detection Capabilities**

### **With Current Hourly Collection:**
- ✅ **Long-term trends**: Well captured
- ✅ **Development activity**: Adequate
- ✅ **Supply changes**: Sufficient
- ⚠️ **Network activity**: May miss rapid changes
- ❌ **Market anomalies**: Could miss short-term signals

### **With 15-Minute Collection:**
- ✅ **All above PLUS**
- ✅ **Network congestion**: Real-time detection
- ✅ **Transaction spikes**: Immediate capture
- ✅ **Security events**: Rapid identification
- ✅ **Market correlation**: Better signal timing

## 💡 **Recommendation**

**For strong signal detection, implement a dual approach:**

1. **Keep current hourly collector** for fundamental metrics
2. **Add 15-minute network collector** for activity metrics

This provides:
- ✅ **Cost efficiency** (fewer expensive API calls for slow metrics)
- ✅ **Signal sensitivity** (catch rapid network changes)
- ✅ **Comprehensive coverage** (both fundamental and activity data)