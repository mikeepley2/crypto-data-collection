# Data Collection System Integration Guide

This guide provides comprehensive information on how the data collection system integrates with trading nodes, other systems, and external services.

## 🏗️ **4-Node Kubernetes Architecture**

### **Node Specifications**

#### **Node 1: Control Plane** (`cryptoai-control`)
- **Role**: Kubernetes cluster management and coordination
- **Components**: 
  - kube-apiserver, kube-controller-manager, kube-scheduler
  - etcd cluster, CoreDNS
  - Ingress controller, Load balancer
  - Service mesh control plane

#### **Node 2: Data Collection** (`cryptoai-data-collection`) - **THIS SYSTEM**
- **Role**: Dedicated data collection and processing
- **Components**:
  - 14 data collector services
  - 4 AI processing services (CryptoBERT, FinBERT, ML Features)
  - 3 API services (Gateway, WebSocket, GraphQL)
  - Collection scheduler and orchestrator
- **Resources**: Optimized for I/O intensive workloads

#### **Node 3: Trading Engine** (`cryptoai-trading-engine`)
- **Role**: Live trading operations and ML signal generation
- **Components**:
  - XGBoost ML signal generator
  - Live trade execution engine
  - Portfolio management services
  - Risk management systems
- **Resources**: CPU optimized for ML inference

#### **Node 4: Analytics & Monitoring** (`cryptoai-analytics`)
- **Role**: Monitoring, observability, and analytics
- **Components**:
  - Grafana dashboards
  - Prometheus metrics collection
  - Alerting systems
  - Performance monitoring

### **Inter-Node Communication**

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES SERVICE MESH                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Data Collection ←→ Trading Engine                              │
│  • Real-time price feeds                                       │
│  • ML feature streams                                          │
│  • Sentiment analysis data                                     │
│  • Technical indicators                                        │
│                                                                 │
│  Data Collection ←→ Analytics                                   │
│  • Collection metrics                                          │
│  • Service health data                                         │
│  • Performance statistics                                      │
│  • Error rates and alerts                                      │
│                                                                 │
│  Trading Engine ←→ Analytics                                    │
│  • Trading performance                                         │
│  • Portfolio metrics                                           │
│  • ML model accuracy                                           │
│  • Risk assessments                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 **Database Integration Architecture**

### **Windows Database Host Integration**

The data collection system connects to existing Windows MySQL databases while running in Kubernetes:

```
┌──────────────────────────────────────────────────────────────┐
│                 KUBERNETES DATA COLLECTION                  │
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Collector 1 │   │ Collector 2 │   │ Collector N │       │
│  │             │   │             │   │             │       │
│  │    Pod      │   │    Pod      │   │    Pod      │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                    host.docker.internal:3306                │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   WINDOWS DATABASE HOST                     │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ MySQL Databases │  │ Redis Cache     │  │ File Storage │ │
│  │                 │  │                 │  │              │ │
│  │• crypto_prices  │  │• Real-time data │  │• Backups     │ │
│  │• crypto_trans.. │  │• Session cache  │  │• Logs        │ │
│  │• stock_market.. │  │• ML features    │  │• ML models   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### **Database Connection Configuration**

All Kubernetes services use standardized database connectivity:

```yaml
# Kubernetes ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: database-config
  namespace: crypto-collectors
data:
  MYSQL_HOST: "host.docker.internal"
  MYSQL_PORT: "3306"
  MYSQL_USER: "news_collector"
  MYSQL_DATABASE_PRICES: "crypto_prices"
  MYSQL_DATABASE_TRADING: "crypto_transactions"
  MYSQL_DATABASE_STOCK: "stock_market_news"
  REDIS_HOST: "host.docker.internal"
  REDIS_PORT: "6379"
```

### **Database Schema Integration**

#### **crypto_prices Database**
- **ml_features_materialized**: 1.4M ML training records with 80+ features
- **trading_signals**: AI-generated signals from XGBoost models
- **price_data**: Real-time cryptocurrency price feeds
- **technical_indicators**: RSI, MACD, Bollinger Bands calculations
- **sentiment_data**: Multi-source sentiment analysis results

#### **crypto_transactions Database**
- **trade_recommendations**: AI trade recommendations with confidence scores
- **trades**: Executed trade history with performance tracking
- **portfolio_positions**: Current holdings and position management
- **performance_metrics**: Trading system performance analytics

#### **stock_market_news Database**
- **news_articles**: Financial news with content and metadata
- **sentiment_analysis**: FinBERT sentiment scores for stock news
- **market_events**: Significant market events and announcements

## 🌐 **API Integration Patterns**

### **Unified Data API Gateway**

The API Gateway provides unified access to all collected data:

```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Port 8000)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  REST API Endpoints:                                       │
│  • GET /api/v1/prices/current/{symbol}                     │
│  • GET /api/v1/sentiment/crypto/{symbol}                   │
│  • GET /api/v1/technical/{symbol}                          │
│  • GET /api/v1/ml-features/{symbol}                        │
│  • GET /api/v1/news/crypto/latest                          │
│                                                             │
│  WebSocket Streams:                                        │
│  • ws://gateway:8000/ws/prices                             │
│  • ws://gateway:8000/ws/sentiment                          │
│  • ws://gateway:8000/ws/news                               │
│                                                             │
│  GraphQL Endpoint:                                         │
│  • POST /graphql (unified query interface)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Trading System Integration**

The trading system can consume data through multiple patterns:

#### **Pattern 1: Direct Database Access**
```python
# Trading system direct MySQL access
import mysql.connector

config = {
    'host': 'host.docker.internal',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

# Query latest ML features for signal generation
conn = mysql.connector.connect(**config)
cursor = conn.cursor()
cursor.execute("""
    SELECT * FROM ml_features_materialized 
    WHERE symbol = %s AND timestamp = (
        SELECT MAX(timestamp) FROM ml_features_materialized WHERE symbol = %s
    )
""", (symbol, symbol))
```

#### **Pattern 2: API Gateway Access**
```python
# Trading system API access
import requests

# Get current price data
response = requests.get(
    f"http://data-api-gateway.crypto-collectors.svc.cluster.local:8000/api/v1/prices/current/{symbol}",
    headers={"Authorization": f"Bearer {api_key}"}
)

# Get ML features
features = requests.get(
    f"http://data-api-gateway.crypto-collectors.svc.cluster.local:8000/api/v1/ml-features/{symbol}"
).json()
```

#### **Pattern 3: WebSocket Streaming**
```python
# Real-time data streaming
import websocket

def on_price_update(ws, message):
    data = json.loads(message)
    process_price_update(data)

ws = websocket.WebSocketApp(
    "ws://data-api-gateway.crypto-collectors.svc.cluster.local:8000/ws/prices",
    on_message=on_price_update
)
ws.run_forever()
```

### **External API Integration**

The data collection system integrates with multiple external APIs:

```
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL API SOURCES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Financial Data:                                           │
│  • CoinGecko Premium API (500k/month)                      │
│  • FRED Economic Data API                                  │
│  • Alpha Vantage Stock Data                                │
│  • Coinbase Advanced Trade API                             │
│                                                             │
│  News & Social:                                            │
│  • Guardian News API                                       │
│  • Reddit API (r/cryptocurrency, r/bitcoin)                │
│  • Twitter API (crypto sentiment)                          │
│  • NewsAPI Financial News                                  │
│                                                             │
│  AI Services:                                              │
│  • OpenAI GPT-4 (sentiment analysis)                       │
│  • Anthropic Claude (content analysis)                     │
│  • Custom CryptoBERT deployment                            │
│  • Custom FinBERT deployment                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 **Security & Authentication**

### **API Authentication**

All data collection APIs use bearer token authentication:

```yaml
# API Key format
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Scope-based access control
{
  "user_id": "trading-system",
  "scopes": ["read:prices", "read:sentiment", "read:ml-features"],
  "rate_limit": "1000/hour"
}
```

### **Network Security**

```yaml
# Kubernetes Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: data-collection-policy
  namespace: crypto-collectors
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: crypto-trading
    - namespaceSelector:
        matchLabels:
          name: crypto-analytics
  egress:
  - to: []  # Allow all egress for external APIs
```

### **Secrets Management**

```yaml
# Kubernetes Secrets for API keys
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: crypto-collectors
type: Opaque
data:
  COINGECKO_API_KEY: <base64_encoded>
  FRED_API_KEY: <base64_encoded>
  GUARDIAN_API_KEY: <base64_encoded>
  OPENAI_API_KEY: <base64_encoded>
  MYSQL_PASSWORD: <base64_encoded>
```

## 📈 **Monitoring & Observability**

### **Metrics Collection**

All services expose Prometheus metrics:

```
# Collector metrics
crypto_collector_requests_total{collector="prices", status="success"}
crypto_collector_duration_seconds{collector="prices"}
crypto_collector_errors_total{collector="prices", error_type="api_timeout"}

# API Gateway metrics
api_gateway_requests_total{endpoint="/api/v1/prices", method="GET", status="200"}
api_gateway_request_duration_seconds{endpoint="/api/v1/prices"}
api_gateway_active_websockets{stream="prices"}

# Database metrics
mysql_connections_active{database="crypto_prices"}
mysql_query_duration_seconds{table="ml_features_materialized"}
redis_cache_hits_total{cache_type="prices"}
```

### **Grafana Dashboard Integration**

The analytics node provides comprehensive monitoring:

```yaml
# Grafana dashboard for data collection
{
  "dashboard": {
    "title": "Data Collection System",
    "panels": [
      {
        "title": "Collection Rate",
        "targets": [
          "rate(crypto_collector_requests_total[5m])"
        ]
      },
      {
        "title": "API Gateway Performance",
        "targets": [
          "histogram_quantile(0.95, api_gateway_request_duration_seconds)"
        ]
      },
      {
        "title": "Database Connection Pool",
        "targets": [
          "mysql_connections_active"
        ]
      }
    ]
  }
}
```

### **Alerting Rules**

Critical system alerts:

```yaml
# Prometheus alerting rules
groups:
- name: data_collection_alerts
  rules:
  - alert: CollectorDown
    expr: up{job="crypto-collectors"} == 0
    for: 2m
    annotations:
      summary: "Data collector {{ $labels.instance }} is down"
      
  - alert: HighErrorRate
    expr: rate(crypto_collector_errors_total[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate in {{ $labels.collector }}"
      
  - alert: DatabaseConnectionFailed
    expr: mysql_up == 0
    for: 1m
    annotations:
      summary: "Cannot connect to MySQL database"
```

## 🔄 **Data Flow Orchestration**

### **Collection Scheduling**

The collection scheduler orchestrates all data collection activities:

```python
# Collection schedule configuration
COLLECTION_SCHEDULE = {
    "crypto_prices": {
        "interval": "5m",
        "priority": "high",
        "dependencies": []
    },
    "crypto_news": {
        "interval": "15m", 
        "priority": "medium",
        "dependencies": ["crypto_prices"]
    },
    "technical_indicators": {
        "interval": "5m",
        "priority": "high",
        "dependencies": ["crypto_prices"]
    },
    "ml_features": {
        "interval": "15m",
        "priority": "critical",
        "dependencies": ["crypto_prices", "technical_indicators", "sentiment_analysis"]
    }
}
```

### **Real-time Data Pipeline**

```
External APIs → Collectors → Processing → Database → API Gateway → Consumers
     ↓             ↓           ↓          ↓           ↓           ↓
  Raw Data    Validation   Enrichment   Storage   Caching    Delivery
 Rate Limit   Transform    Sentiment    MySQL     Redis      Real-time
  Retry       Format       Features     Persist   Cache      Streaming
  Buffer      Clean        Technical    Index     TTL        WebSocket
```

### **Error Handling & Recovery**

```python
# Retry logic with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(APIException)
)
async def collect_data(source: str, symbols: List[str]):
    try:
        data = await external_api.fetch(symbols)
        await validate_and_store(data)
    except RateLimitException:
        await asyncio.sleep(60)  # Wait for rate limit reset
        raise  # Retry
    except ValidationException as e:
        logger.error(f"Data validation failed: {e}")
        # Don't retry validation errors
```

## 🚀 **Deployment Integration**

### **Helm Chart Structure**

```
charts/crypto-data-collection/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── collectors/
│   │   ├── crypto-prices.yaml
│   │   ├── crypto-news.yaml
│   │   └── ...
│   ├── processing/
│   │   ├── sentiment-analysis.yaml
│   │   ├── ml-features.yaml
│   │   └── ...
│   └── api/
│       ├── gateway.yaml
│       ├── websocket.yaml
│       └── ...
└── values/
    ├── development.yaml
    ├── staging.yaml
    └── production.yaml
```

### **Environment-Specific Configuration**

```yaml
# values/production.yaml
environment: production
replicaCount: 3
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

database:
  host: "host.docker.internal"
  maxConnections: 100
  connectionTimeout: 30s

apiKeys:
  coingecko:
    tier: "premium"
    rateLimit: "500000/month"
  fred:
    tier: "standard"
    rateLimit: "120/minute"
```

This integration guide provides the foundation for understanding how the data collection system integrates with the broader cryptocurrency trading ecosystem while maintaining isolation and reliability.