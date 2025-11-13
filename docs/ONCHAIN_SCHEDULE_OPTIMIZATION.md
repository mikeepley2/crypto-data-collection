# 🕐 Onchain Data Collection Schedule Optimization

## ❌ **Previous Schedule: Every 6 Hours - TOO INFREQUENT**

### Why 6 hours was inadequate:
- **Network Activity**: Blockchain metrics change continuously
- **Supply Changes**: Token burns, minting events, staking changes
- **Developer Activity**: GitHub commits, repository activity
- **Social Metrics**: Community growth, sentiment shifts
- **Market Dynamics**: Price impacts on network usage

## ✅ **Updated Schedule: Every Hour - OPTIMAL**

### Why hourly collection is better:

#### **1. Onchain Metrics Are Dynamic**
- **Transaction Volume**: Can fluctuate significantly within hours
- **Active Addresses**: Network usage patterns change throughout the day
- **Staking Ratios**: Validator changes and stake movements
- **Hash Rate**: Mining/validation power shifts (for applicable networks)

#### **2. Developer Activity Tracking**
- **GitHub Commits**: Development happens around the clock
- **Repository Activity**: Real-time project momentum indicators
- **Community Engagement**: Social metrics evolve continuously

#### **3. Market-Network Correlation**
- **Price Movements**: Affect network usage patterns quickly
- **Network Congestion**: Can spike during high-activity periods
- **Gas Fees/Transaction Costs**: Change based on network demand

#### **4. Data Freshness for ML/Analytics**
- **Trend Detection**: Hourly data enables better pattern recognition
- **Anomaly Detection**: Faster identification of unusual network behavior
- **Predictive Models**: More granular data improves model accuracy

## 📊 **Comparison with Other Data Types**

| Data Type | Optimal Frequency | Rationale |
|-----------|------------------|-----------|
| **Price Data** | Every 5-15 minutes | High volatility, trading decisions |
| **Onchain Data** | **Every 1 hour** | Network dynamics, development tracking |
| **News/Sentiment** | Every 2-4 hours | Information flow, sentiment shifts |
| **Macro Indicators** | Daily/Weekly | Economic data release cycles |
| **Technical Indicators** | Every 15-30 minutes | Trading signal generation |

## 🔧 **New Schedule Configuration**

**CronJob Schedule**: `"0 * * * *"` (every hour at minute 0)

**Resource Considerations**:
- **API Calls**: ~7-10 symbols × 24 hours = 168-240 API calls/day
- **Premium CoinGecko**: 10 req/sec limit easily handles this load
- **Database Storage**: Minimal increase (24x vs 4x daily records)
- **Compute Resources**: 1-2 minute job runtime every hour

## 🎯 **Benefits of Hourly Collection**

### **Immediate**
- ✅ Fresh onchain metrics for trading decisions
- ✅ Real-time developer activity tracking
- ✅ Better trend detection capabilities

### **Analytics**
- ✅ Higher resolution data for ML models
- ✅ Improved anomaly detection sensitivity
- ✅ Better correlation analysis between metrics

### **Operational**
- ✅ Faster detection of data collection issues
- ✅ More granular backfill capabilities
- ✅ Better alignment with trading timeframes

## 🚀 **Implementation Status**

- ✅ **Updated**: `onchain-collector-working.yaml` → hourly schedule
- ✅ **Updated**: `onchain-collector-simple-cron.yaml` → hourly schedule  
- ✅ **Updated**: `onchain-collector-cronjob.yaml` → hourly schedule
- ✅ **Applied**: Kubernetes deployment updated to run every hour

**Result**: Onchain data collection now runs every hour for optimal data freshness and analytics capabilities! ⏰