# 🏗️ **Crypto Data Collection Architecture Overview**

## 🎯 **System Architecture (October 2025)**

### **High-Level Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   External APIs │────│   Data Flow     │────│   Consumers     │
│                 │    │                 │    │                 │
│ • CoinGecko     │    │ Kubernetes      │    │ • Trading Bots  │
│ • Yahoo Finance │    │ Cluster         │    │ • ML Models     │
│ • Reddit/News   │    │                 │    │ • Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                       ┌───────┴───────┐
                       │               │
                   ┌───▼───┐       ┌───▼───┐
                   │ Data  │       │  API  │
                   │Store  │       │Gateway│
                   │(MySQL)│       │       │
                   └───────┘       └───────┘
```

### **Component Architecture**
```
External APIs → Collectors → Processing → Database → API Gateway → Consumers
     │              │           │           │          │            │
     ├─ CoinGecko   ├─ Prices   ├─ ML Feat ├─ MySQL   ├─ REST     ├─ aitest
     ├─ FRED        ├─ News     ├─ Sentiment├─ Redis   ├─ WebSock  ├─ Trading
     ├─ Guardian    ├─ Social   ├─ Tech Ind └─ Storage └─ Auth     ├─ Research
     └─ Reddit      └─ Macro    └─ Analysis                       └─ Monitor
```

## 🚀 **Kubernetes Services Architecture**

### **Service Communication (DNS-Based)**
All internal communication uses Kubernetes DNS for service discovery:

```
simple-api-gateway.crypto-collectors.svc.cluster.local:8000
    │
    ├── enhanced-crypto-prices.crypto-collectors.svc.cluster.local:8000
    ├── crypto-news-collector.crypto-collectors.svc.cluster.local:8000
    ├── simple-sentiment-collector.crypto-collectors.svc.cluster.local:8000
    └── sentiment-microservice.crypto-collectors.svc.cluster.local:8000
```

### **Data Flow Architecture**

#### **1. Real-Time Price Collection**
```
CoinGecko API → enhanced-crypto-prices → price_data_real (MySQL)
    │                    │                       │
    └─ 124 symbols      └─ Every 5 minutes      └─ OHLC + metadata
```

#### **2. ML Feature Pipeline**
```
price_data_real → materialized-updater → ml_features_materialized
    │                    │                       │
    └─ Raw prices       └─ Real-time           └─ 3.3M+ records
```

#### **3. Sentiment Analysis Pipeline**
```
News/Social APIs → sentiment-collectors → sentiment_data (MySQL)
    │                      │                     │
    └─ Multi-source       └─ CryptoBERT        └─ Processed sentiment
```

#### **4. API Gateway Integration**
```
All Data Sources → simple-api-gateway → External Consumers
    │                      │                 │
    └─ MySQL/Redis        └─ REST/WebSocket  └─ Trading systems
```

## 📊 **Database Schema Architecture**

### **Core Tables**
```sql
-- Price data (real-time)
price_data_real
├── symbol (VARCHAR)
├── current_price (DECIMAL)
├── market_cap (DECIMAL)
├── volume_24h (DECIMAL)
├── price_change_24h (DECIMAL)
├── high_24h (DECIMAL)
├── low_24h (DECIMAL)
├── open_24h (DECIMAL)
└── collected_at (TIMESTAMP)

-- ML Features (materialized)
ml_features_materialized
├── symbol (VARCHAR)
├── timestamp (TIMESTAMP)
├── price (DECIMAL)
├── rsi_14 (DECIMAL)
├── macd_line (DECIMAL)
├── bb_upper (DECIMAL)
├── sentiment_score (DECIMAL)
└── 75+ more features...

-- Sentiment data
sentiment_data
├── symbol (VARCHAR)
├── sentiment_score (DECIMAL)
├── confidence (DECIMAL)
├── source (VARCHAR)
└── analyzed_at (TIMESTAMP)
```

## 🔧 **Technical Stack**

### **Container Technology**
- **Runtime**: Docker containers on Kubernetes
- **Orchestration**: Kind cluster (multi-node)
- **Images**: Custom-built Python services
- **Registry**: Local Docker registry

### **Application Stack**
- **API Framework**: FastAPI + Uvicorn
- **Data Processing**: Python + Pandas + NumPy
- **ML Libraries**: scikit-learn, TA-Lib, transformers
- **Database**: MySQL 8.0 (Windows host)
- **Caching**: Redis (planned)
- **Monitoring**: Custom Python scripts

### **Data Sources**
- **CoinGecko Premium**: 500k API calls/month
- **Yahoo Finance**: Macro economic data
- **Reddit API**: Social sentiment
- **Guardian News**: Financial news
- **FRED API**: Federal Reserve data

## 🎯 **Deployment Architecture**

### **Kubernetes Resources**
```yaml
Namespace: crypto-collectors
├── Deployments (7)
│   ├── simple-api-gateway
│   ├── enhanced-crypto-prices
│   ├── crypto-news-collector
│   ├── simple-sentiment-collector
│   ├── sentiment-microservice
│   ├── stock-sentiment-collector
│   └── social-sentiment-collector
├── Services (8)
├── CronJobs (2)
│   ├── enhanced-crypto-prices-collector
│   └── crypto-health-monitor
└── ConfigMaps/Secrets (API keys)
```

### **Resource Allocation**
```yaml
# Standard service resources
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi
```

## 📈 **Scalability Design**

### **Horizontal Scaling**
- **API Gateway**: 1-3 replicas (auto-scaling capable)
- **Collectors**: 1 replica each (stateless)
- **Processing**: 1-2 replicas (CPU-bound)

### **Performance Optimization**
- **Database Connection Pooling**: Shared connections
- **Caching Strategy**: Redis for frequently accessed data
- **Batch Processing**: ML features updated in batches
- **Async Operations**: Non-blocking I/O for API calls

## 🔍 **Monitoring Architecture**

### **Health Monitoring**
- **Kubernetes Probes**: liveness/readiness checks
- **Custom Scripts**: `monitor_ml_features.py`
- **Log Aggregation**: Kubernetes logs
- **Metrics Collection**: Performance tracking

### **Data Quality Monitoring**
- **Freshness Checks**: Data collection gaps
- **Schema Validation**: Data integrity
- **Performance Metrics**: Processing latency
- **Error Tracking**: Failed operations

## 🚀 **Future Architecture Goals**

### **Enhanced Reliability**
- **Multi-region deployment**: Geographic redundancy
- **Database clustering**: High availability MySQL
- **Circuit breakers**: Fault tolerance
- **Backup strategies**: Data recovery

### **Performance Improvements**
- **Caching layer**: Redis cluster
- **Message queues**: Async processing
- **Load balancing**: Traffic distribution
- **CDN integration**: Global access

---

**Updated**: October 2025  
**Architecture Version**: 2.0  
**Status**: Production Ready ✅
