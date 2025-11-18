# 📋 SERVICE INVENTORY SUMMARY

> **Quick Reference**: 9 Production-Ready Microservices  
> **Last Updated**: November 18, 2025  
> **Full Documentation**: [docs/SERVICE_INVENTORY.md](docs/SERVICE_INVENTORY.md)

## 🚀 **CORE SERVICES (Template Compliant)**

| Service | Path | Port | Status |
|---------|------|------|--------|
| **Enhanced News Collector** | `services/enhanced_news_collector.py` | 8001 | ✅ Template Compliant |
| **Enhanced Onchain Collector V2** | `services/onchain-collection/enhanced_onchain_collector_v2.py` | 8004 | ✅ Production V2 |
| **Enhanced Macro Collector V2** | `services/macro-collection/enhanced_macro_collector_v2.py` | 8002 | ✅ Template Compliant |

## 📊 **MARKET SERVICES**

| Service | Path | Port | Status |
|---------|------|------|--------|
| **ML Market Collector** | `services/market-collection/ml_market_collector.py` | 8005 | ✅ Ready |
| **Enhanced Price Collector** | `services/price-collection/enhanced_price_collector.py` | 8006 | ✅ Ready |
| **Technical Analysis Collector** | `services/technical-analysis/technical_analysis_collector.py` | 8007 | ✅ Ready |

## 🧠 **SPECIALIZED SERVICES**

| Service | Path | Port | Status |
|---------|------|------|--------|
| **Sentiment Analysis Service** | `services/sentiment-analysis/enhanced_sentiment_analyzer.py` | 8008 | ✅ Ready |
| **Data Validation Service** | `services/validation/data_validation_service.py` | 8009 | ✅ Ready |
| **Gap Detection Service** | `services/gap-detection/gap_detection_service.py` | 8010 | ✅ Ready |

## 🚫 **EXCLUDED (Duplicates/Legacy)**

- ❌ `services/news-collection/enhanced_crypto_news_collector.py` *(Non-template)*
- ❌ `services/onchain-collection/enhanced_onchain_collector.py` *(V1)*
- ❌ `enhanced_macro_collector_v2.py` *(Root duplicate)*

## 🎯 **SELECTION CRITERIA**

✅ **Template compliance** (standardized collector pattern)  
✅ **Latest version** (V2 over V1)  
✅ **Production features** (health endpoints, monitoring)  
✅ **Services directory location** (proper microservices structure)  

**Total Services**: 10 core production services (filtered from 16+ with duplicates)

---
*See [docs/SERVICE_INVENTORY.md](docs/SERVICE_INVENTORY.md) for complete documentation*