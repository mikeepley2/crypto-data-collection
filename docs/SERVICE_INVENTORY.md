# 📋 **PRODUCTION SERVICE INVENTORY**

> **Last Updated**: November 18, 2025  
> **Status**: Production Ready - Template Compliant Services Only  
> **Total Services**: 10 Core Microservices  

## 🎯 **OFFICIAL SERVICE REGISTRY**

This document maintains the **definitive list** of all production-ready services in the crypto data collection system. All services listed here are:

- ✅ **Template Compliant**: Follow the standardized collector template framework
- ✅ **Production Ready**: Include health endpoints, monitoring, and reliability features
- ✅ **Latest Versions**: Newest, most comprehensive implementations
- ✅ **No Duplicates**: Single source of truth for each data collection domain

---

## 🚀 **CORE DATA COLLECTION SERVICES**

### 1. **Enhanced News Collector** ⭐ Template Compliant
- **Service Path**: `services/enhanced_news_collector.py`
- **Container Port**: 8001
- **Purpose**: Cryptocurrency news collection with sentiment analysis
- **Template Status**: ✅ **FULLY COMPLIANT** - Uses standardized collector template
- **Features**: RSS feed processing, crypto mention detection, sentiment scoring
- **Data Sources**: CoinTelegraph, CryptoSlate, Decrypt, BeinCrypto, CoinJournal
- **Target Table**: `crypto_news`
- **Health Endpoints**: `/health`, `/status`, `/metrics`, `/data-quality`
- **Deployment**: `crypto-news-collector:8001`

### 2. **Enhanced Onchain Collector V2** ⭐ Latest Production
- **Service Path**: `services/onchain-collection/enhanced_onchain_collector_v2.py`
- **Container Port**: 8004
- **Purpose**: Blockchain metrics and on-chain data collection
- **Template Status**: ✅ **PRODUCTION V2** - Health scoring, FastAPI endpoints
- **Features**: Multi-source onchain metrics, health scoring system, comprehensive statistics
- **Data Sources**: CoinGecko, DeFiLlama, Messari APIs
- **Target Table**: `crypto_onchain_data`
- **Health Endpoints**: `/health`, `/ready`, `/metrics`, `/performance`
- **Deployment**: `onchain-collector-v2:8004`

### 3. **Enhanced Macro Collector V2** ⭐ Template Compliant
- **Service Path**: `services/macro-collection/enhanced_macro_collector_v2.py`
- **Container Port**: 8002
- **Purpose**: Macroeconomic indicators collection
- **Template Status**: ✅ **FULLY COMPLIANT** - Uses standardized collector template
- **Features**: Federal Reserve data, economic indicators, correlation analysis
- **Data Sources**: FRED API, Yahoo Finance
- **Target Table**: `macro_indicators`
- **Health Endpoints**: `/health`, `/status`, `/metrics`, `/backfill`
- **Deployment**: `macro-collector:8002`

---

## 📊 **MARKET & TECHNICAL SERVICES**

### 4. **ML Market Collector**
- **Service Path**: `services/market-collection/ml_market_collector.py`
- **Container Port**: 8005
- **Purpose**: ML-focused market data collection for trading models
- **Features**: Enhanced asset tracking, sector analysis, ML feature generation
- **Data Sources**: Yahoo Finance, yfinance library
- **Target Table**: `technical_indicators`
- **Deployment**: `ml-market-collector:8005`

### 5. **Enhanced Price Collector**
- **Service Path**: `services/price-collection/enhanced_price_collector.py`
- **Container Port**: 8006
- **Purpose**: Comprehensive cryptocurrency price collection
- **Features**: Multi-exchange price aggregation, real-time OHLC data
- **Data Sources**: CoinGecko Premium, Coinbase Pro
- **Target Table**: `technical_indicators`
- **Deployment**: `price-collector:8006`

### 6. **Technical Analysis Collector**
- **Service Path**: `services/technical-analysis/technical_analysis_collector.py`
- **Container Port**: 8007
- **Purpose**: Technical indicators calculation and analysis
- **Features**: RSI, MACD, Bollinger Bands, Moving Averages, volume indicators
- **Data Sources**: Price data from `technical_indicators` table
- **Target Table**: `technical_indicators`
- **Deployment**: `technical-analysis-collector:8007`

### 7. **OHLC Collection Collector**
- **Service Path**: `services/ohlc-collection/enhanced_ohlc_collector.py`
- **Container Port**: 8011
- **Purpose**: Open-High-Low-Close candlestick data collection
- **Features**: Multi-timeframe OHLC data, volume analysis, technical chart data
- **Data Sources**: CoinGecko Premium API
- **Target Table**: `ohlc_data`
- **Health Endpoints**: `/health`, `/status`, `/metrics`, `/ohlc-features`
- **Deployment**: `ohlc-collector:8011`

---

## 🧠 **SPECIALIZED SERVICES**

### 8. **Sentiment Analysis Service**
- **Service Path**: `services/sentiment-analysis/enhanced_sentiment_analyzer.py`
- **Container Port**: 8008
- **Purpose**: Advanced sentiment analysis with multiple AI models
- **Features**: CryptoBERT, FinBERT, TextBlob integration, emotion detection
- **Data Sources**: News content from `crypto_news` table
- **Target Table**: `sentiment_aggregation`
- **Deployment**: `sentiment-analyzer:8008`

### 9. **Data Validation Service**
- **Service Path**: `services/validation/data_validation_service.py`
- **Container Port**: 8009
- **Purpose**: Data quality validation and integrity checking
- **Features**: Schema validation, duplicate detection, data quality scoring
- **Data Sources**: All collection tables
- **Target Table**: `service_monitoring`
- **Deployment**: `data-validator:8009`

### 10. **Gap Detection Service**
- **Service Path**: `services/gap-detection/gap_detection_service.py`
- **Container Port**: 8010
- **Purpose**: Missing data detection and backfill coordination
- **Features**: Temporal gap analysis, backfill scheduling, coverage reporting
- **Data Sources**: All collection tables
- **Target Table**: `service_monitoring`
- **Deployment**: `gap-detector:8010`

---

## 🚫 **EXCLUDED SERVICES** (Duplicates/Legacy)

### **Removed Duplicates:**
- ❌ `services/news-collection/enhanced_crypto_news_collector.py` *(Non-template version)*
- ❌ `services/onchain-collection/enhanced_onchain_collector.py` *(V1 - superseded by V2)*
- ❌ `enhanced_macro_collector_v2.py` *(Root duplicate - identical to services version)*

### **Legacy/Archived:**
- ❌ All non-template compliant collectors
- ❌ Standalone Python scripts not following microservices pattern
- ❌ Services targeting deprecated tables

---

## 🐳 **DOCKER CONTAINER ARCHITECTURE**

### **Multi-Stage Build Targets**
Each service has its own Docker build target for optimized deployment:

```dockerfile
# Enhanced News Collection Service (Template Compliant)
FROM base as news-collector
COPY services/enhanced_news_collector.py ./
EXPOSE 8001
CMD ["python", "enhanced_news_collector.py"]

# Enhanced Onchain Collection Service V2 (Production)
FROM base as onchain-collector-v2
COPY services/onchain-collection/ ./services/onchain-collection/
EXPOSE 8004
CMD ["python", "services/onchain-collection/enhanced_onchain_collector_v2.py"]

# Enhanced Macro Collection Service (Template Compliant)
FROM base as macro-collector
COPY services/macro-collection/ ./services/macro-collection/
EXPOSE 8002
CMD ["python", "services/macro-collection/enhanced_macro_collector_v2.py"]

# Additional service targets...
```

---

## ⚙️ **CI/CD INTEGRATION**

### **Service-Specific Builds**
The CI/CD pipeline builds individual service containers:

```yaml
strategy:
  matrix:
    service:
      - news-collector
      - onchain-collector-v2
      - macro-collector
      - ml-market-collector
      - price-collector
      - technical-analysis-collector
      - sentiment-analyzer
      - data-validator
      - gap-detector

- name: Build ${{ matrix.service }}
  run: |
    docker build --target ${{ matrix.service }} \
      -t megabob70/crypto-${{ matrix.service }}:latest .
```

---

## 📈 **SERVICE DEPLOYMENT STATUS**

| Service | Status | Template | Health | Port | Container |
|---------|--------|----------|--------|------|-----------|
| **Enhanced News** | ✅ Ready | ✅ Compliant | 🟢 Healthy | 8001 | `megabob70/crypto-news-collector` |
| **Onchain V2** | ✅ Ready | ✅ Production | 🟢 Healthy | 8004 | `megabob70/crypto-onchain-collector-v2` |
| **Macro V2** | ✅ Ready | ✅ Compliant | 🟢 Healthy | 8002 | `megabob70/crypto-macro-collector` |
| **ML Market** | ✅ Ready | 🟡 Partial | 🟡 Good | 8005 | `megabob70/crypto-ml-market-collector` |
| **Enhanced Price** | ✅ Ready | 🟡 Partial | 🟡 Good | 8006 | `megabob70/crypto-price-collector` |
| **Technical Analysis** | ✅ Ready | 🟡 Partial | 🟡 Good | 8007 | `megabob70/crypto-technical-analysis-collector` |
| **OHLC Collector** | ✅ Ready | 🟡 Partial | 🟡 Good | 8011 | `megabob70/crypto-ohlc-collector` |
| **Sentiment Analyzer** | ✅ Ready | 🟡 Partial | 🟡 Good | 8008 | `megabob70/crypto-sentiment-analyzer` |
| **Data Validator** | ✅ Ready | 🟡 Partial | 🟡 Good | 8009 | `megabob70/crypto-data-validator` |
| **Gap Detector** | ✅ Ready | 🟡 Partial | 🟡 Good | 8010 | `megabob70/crypto-gap-detector` |

### **Legend:**
- ✅ **Ready**: Service is production-ready
- 🟢 **Healthy**: Full health endpoints and monitoring
- 🟡 **Good**: Basic functionality, may need template migration
- ✅ **Compliant**: Fully template-compliant
- 🟡 **Partial**: May benefit from template migration

---

## 🔧 **SERVICE SELECTION CRITERIA**

### **Why These Services Were Selected:**

1. **Template Compliance Priority**: Services following the standardized collector template pattern
2. **Version Precedence**: V2 versions selected over V1 for enhanced features
3. **Production Features**: Health endpoints, monitoring, reliability features
4. **Microservices Architecture**: Proper service directory structure
5. **No Duplication**: Single service per data collection domain

### **Template Compliance Standards:**
- ✅ Extends `BaseCollector` class
- ✅ Implements required abstract methods
- ✅ Uses standardized configuration
- ✅ Includes comprehensive health endpoints
- ✅ Provides Prometheus metrics
- ✅ Supports backfill operations
- ✅ Has data quality validation

---

## 🚀 **DEPLOYMENT COMMANDS**

### **Build All Services:**
```bash
# Build all service containers
docker build --target news-collector -t megabob70/crypto-news-collector:latest .
docker build --target onchain-collector-v2 -t megabob70/crypto-onchain-collector-v2:latest .
docker build --target macro-collector -t megabob70/crypto-macro-collector:latest .
# ... (additional services)
```

### **Deploy to Kubernetes:**
```bash
# Deploy services to K8s cluster
kubectl apply -f k8s/services/
kubectl rollout status deployment/news-collector -n crypto-data-collection
kubectl rollout status deployment/onchain-collector-v2 -n crypto-data-collection
```

### **Health Check All Services:**
```bash
# Verify all services are healthy
for port in 8001 8002 8004 8005 8006 8007 8008 8009 8010; do
  echo "Checking service on port $port..."
  curl -f http://localhost:$port/health || echo "Service on port $port not responding"
done
```

---

## 📚 **DOCUMENTATION REFERENCES**

### **Template Documentation:**
- **Base Template**: `templates/collector-template/base_collector_template.py`
- **Template README**: `templates/collector-template/README.md`
- **Deployment Template**: `templates/collector-template/k8s/deployment-template.yaml`

### **Service Documentation:**
- **Individual Service READMEs**: Each service directory contains specific documentation
- **API Documentation**: `/docs/api.md` - Complete API reference
- **Deployment Guide**: `/docs/DEPLOYMENT_GUIDE.md` - Comprehensive deployment instructions

### **Configuration References:**
- **Centralized Config**: `shared/table_config.py`, `shared/database_config.py`
- **Copilot Instructions**: `.copilot-instructions.md` - Development guidelines

---

## 🎯 **NEXT STEPS**

### **Template Migration Plan:**
1. **Priority 1**: Migrate remaining services to full template compliance
2. **Priority 2**: Enhance health endpoints for partial compliance services
3. **Priority 3**: Standardize deployment manifests across all services

### **Production Readiness:**
1. Update Dockerfile to include only these 9 services
2. Create individual Kubernetes deployments for each service
3. Set up service-specific monitoring and alerting
4. Implement service mesh for inter-service communication

### **Monitoring & Observability:**
1. Deploy Prometheus ServiceMonitors for each service
2. Create Grafana dashboards for service health
3. Set up alerting rules for service failures
4. Implement distributed tracing across services

---

**This service inventory provides the definitive reference for all production microservices in the crypto data collection system. Use this document as the single source of truth for service deployment, monitoring, and development decisions.**

---

*For questions about service architecture or deployment, refer to the [Development Guide](../docs/DEVELOPMENT_GUIDE.md) or [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md).*