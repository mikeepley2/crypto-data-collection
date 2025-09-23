# Crypto Data Collection System

A **dedicated, isolated** data collection solution for cryptocurrency and financial markets. This system operates independently from trading infrastructure, providing comprehensive data collection, processing, and API services.

## 🎯 **Project Overview**

This repository contains the **isolated data collection node** that was separated from the main CryptoAI Trading System to ensure:
- **Zero Impact**: Data collection operations don't affect live trading
- **Independent Scaling**: Scale data collection based on collection workloads
- **Clean Separation**: Clear boundaries between data collection and trading
- **API-First Design**: Unified data access through well-defined APIs

### **4-Node Architecture Integration**

This data collection system is designed to operate as **Node 2** in a 4-node Kubernetes cluster:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Control Node  │  │ Data Collection │  │ Trading Engine  │  │  Analytics Node │
│                 │  │     (THIS)      │  │      Node       │  │                 │
│ • K8s Control   │  │ • Data APIs     │  │ • ML Signals    │  │ • Grafana       │
│ • Ingress       │  │ • Collectors    │  │ • Live Trading  │  │ • Monitoring    │
│ • Load Balancer │  │ • Sentiment AI  │  │ • Risk Mgmt     │  │ • Dashboards    │
│ • Service Mesh  │  │ • ML Features   │  │ • Portfolio     │  │ • Observability │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
          │                    │                    │                    │
          └────────────────────┼────────────────────┼────────────────────┘
                               │                    │
                    ┌─────────────────────────────────────┐
                    │         Windows Database            │
                    │ • MySQL (crypto_prices, trading)   │
                    │ • Redis Cache                      │
                    │ • Connection: host.docker.internal │
                    └─────────────────────────────────────┘
```

### **Integration Benefits**
- **Dedicated Resources**: Specialized hardware for data-intensive operations
- **Network Isolation**: Data collection network separated from trading
- **Independent Scaling**: Scale data services without affecting trading
- **Fault Isolation**: Data collection failures don't impact live trading
- **Security**: Clear security boundaries between data and trading operations

## 🏗️ **System Architecture**

### **Multi-Node Data Collection Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│          DATA COLLECTION NODE (Kubernetes Namespace)           │
├─────────────────────────────────────────────────────────────────┤
│  Node: cryptoai-data-collection | Namespace: crypto-collectors  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Collectors    │  │   Processing    │  │   Data APIs     │ │
│  │  (14 Services)  │  │   (4 Services)  │  │  (3 Services)   │ │
│  │                 │  │                 │  │                 │ │
│  │ • Crypto Prices │  │ • CryptoBERT    │  │ • API Gateway   │ │
│  │ • Stock News    │  │ • FinBERT       │  │ • WebSocket     │ │
│  │ • Social Media  │  │ • ML Features   │  │ • GraphQL       │ │
│  │ • Macro Data    │  │ • Aggregator    │  │ • Streaming     │ │
│  │ • OnChain Data  │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                     WINDOWS DATABASE HOST                      │
│  • MySQL: crypto_prices (1.4M ML records)                     │
│  • MySQL: crypto_transactions (live trading data)             │
│  • MySQL: stock_market_news (financial news)                  │
│  • Redis: Real-time caching and streaming                     │
│  Connection: host.docker.internal:3306                        │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CONSUMING SYSTEMS                           │
├─────────────────────────────────────────────────────────────────┤
│  Trading Engine Node    │  Analytics Node    │  External APIs   │
│  • ML Signal Generator │  • Grafana         │  • Trading Bots  │
│  • Portfolio Manager   │  • Monitoring      │  • Research      │
│  • Risk Assessment     │  • Dashboards      │  • Third Party   │
│  • Live Trading        │  • Alerting        │  • Mobile Apps   │
└─────────────────────────────────────────────────────────────────┘
```

### **Data Flow & Integration Patterns**

```
External APIs → Collectors → Processing → Database → API Gateway → Consumers
     ↓              ↓           ↓          ↓           ↓           ↓
CoinGecko      Price Data   Sentiment   MySQL     REST API   Trading Engine
FRED API       News Data    ML Features Redis     WebSocket  Analytics Node
Guardian       Social Data  Technical   Indexes   GraphQL    External Apps
Reddit         Macro Data   Validation  Backups   Streaming  Research Tools
```

### **Service Discovery & Networking**

- **Internal Communication**: `service-name.crypto-collectors.svc.cluster.local`
- **Cross-Node Access**: Via Kubernetes service mesh and ingress
- **Database Access**: Direct connection to Windows MySQL via `host.docker.internal`
- **API Exposure**: LoadBalancer services for external access
- **Security**: Network policies, RBAC, and API authentication

## 📊 **Data Sources & Collection**

### **Real-time Data Sources**
- **CoinGecko Premium API**: Cryptocurrency prices and market data (500k/month)
- **FRED API**: Federal Reserve economic data and indicators
- **Guardian News API**: Financial news and market commentary
- **Reddit API**: Social media sentiment and discussions
- **Twitter API**: Real-time social sentiment analysis

### **AI-Powered Processing**
- **CryptoBERT**: Cryptocurrency-specific sentiment analysis
- **FinBERT**: Financial news sentiment analysis for stock markets
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **ML Feature Engineering**: 80+ features for trading model training
- **Cross-Market Analysis**: Crypto-stock correlation and risk sentiment

### **Data Collection Scope**
- **35+ Cryptocurrencies**: Bitcoin, Ethereum, Solana, and all major assets
- **Stock Market News**: Financial news with sentiment analysis
- **Social Media**: Reddit, Twitter sentiment processing
- **Economic Data**: GDP, inflation, Fed policy, unemployment data
- **OnChain Metrics**: Blockchain transaction data and analysis

## 🚀 **Quick Start**

### **Prerequisites**
- Kubernetes cluster (Kind, Docker Desktop, or cloud)
- Access to Windows MySQL database
- API keys for external data sources

### **Deployment**
```bash
# 1. Clone the repository
git clone https://github.com/your-org/crypto-data-collection.git
cd crypto-data-collection

# 2. Configure API keys and database credentials
cp config/secrets.example.yaml config/secrets.yaml
# Edit secrets.yaml with your API keys

# 3. Deploy to Kubernetes
./scripts/deploy.sh

# 4. Verify deployment
./scripts/validate.sh

# 5. Access the API
kubectl port-forward svc/data-api-gateway 8000:8000 -n crypto-data-collection
curl http://localhost:8000/health
```

## 🔧 **Development**

### **Local Development Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Run API Gateway locally
cd src/api_gateway
python -m uvicorn main:app --reload --port 8000

# Run individual collectors locally
cd src/collectors/crypto_prices
python main.py
```

### **Project Structure**
```
crypto-data-collection/
├── src/                         # Source code
│   ├── api_gateway/            # Unified data API
│   ├── collectors/             # Data collection services
│   ├── processing/             # Data processing services
│   └── shared/                 # Shared libraries
├── k8s/                        # Kubernetes manifests
│   ├── namespace.yaml         # Namespace and resources
│   ├── configmaps.yaml        # Configuration
│   ├── secrets.yaml           # API keys and credentials
│   ├── api/                   # API Gateway deployment
│   └── collectors/            # Collector deployments
├── scripts/                   # Deployment and management scripts
├── tests/                     # Test suites
├── docs/                      # Documentation
└── config/                    # Configuration files
```

## 📋 **Services Overview**

### **API Gateway** (`data-api-gateway`)
- **Purpose**: Unified access to all collected data
- **Endpoints**: REST, WebSocket, GraphQL
- **Features**: Authentication, rate limiting, caching
- **Port**: 8000

### **Data Collectors**
| Collector | Purpose | Interval | Status |
|-----------|---------|----------|--------|
| **crypto-prices** | Real-time crypto prices | 5 minutes | ✅ Active |
| **crypto-news** | Crypto news with sentiment | 15 minutes | ✅ Active |
| **stock-news** | Stock market news | 15 minutes | ✅ Active |
| **social-reddit** | Reddit sentiment | 30 minutes | ✅ Active |
| **macro-economic** | Economic indicators | 1 hour | ✅ Active |
| **technical-indicators** | Chart analysis | 5 minutes | ✅ Active |
| **onchain-data** | Blockchain metrics | 30 minutes | ✅ Active |

### **Processing Services**
- **ML Feature Engineer**: Creates training features for ML models
- **Sentiment Analyzer**: AI-powered sentiment analysis (CryptoBERT + FinBERT)
- **Data Validator**: Ensures data quality and consistency
- **Collection Scheduler**: Orchestrates all collection activities

## 🔗 **API Reference**

### **Base URL**
- **Production**: `http://data-api-gateway.crypto-data-collection.svc.cluster.local:8000`
- **Local**: `http://localhost:8000`

### **Key Endpoints**
```
GET  /health                           # System health check
GET  /api/v1/prices/current/{symbol}   # Current price data
GET  /api/v1/sentiment/crypto/{symbol} # Crypto sentiment analysis
GET  /api/v1/news/crypto/latest        # Latest crypto news
GET  /api/v1/technical/{symbol}        # Technical indicators
GET  /api/v1/ml-features/{symbol}      # ML features for models
WS   /ws/prices                        # Real-time price stream
```

### **Authentication**
All API endpoints require authentication:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/api/v1/prices/current/bitcoin
```

## 🔒 **Security & Configuration**

### **API Keys Required**
- **CoinGecko Premium**: For cryptocurrency data
- **FRED API**: For economic data
- **Guardian API**: For news data
- **Reddit API**: For social sentiment
- **OpenAI API**: For advanced sentiment analysis

### **Database Configuration**
- **MySQL**: Windows MySQL via `host.docker.internal:3306`
- **Databases**: `crypto_prices`, `crypto_transactions`, `stock_market_news`
- **User**: `news_collector` with appropriate permissions

## 📈 **Monitoring & Operations**

### **Health Monitoring**
```bash
# Check all service health
kubectl get pods -n crypto-data-collection

# Check API Gateway health
curl http://localhost:8000/health

# View collection statistics
curl http://localhost:8000/api/v1/stats/collectors
```

### **Logging**
```bash
# View API Gateway logs
kubectl logs -f deployment/data-api-gateway -n crypto-data-collection

# View specific collector logs
kubectl logs -f deployment/crypto-prices-collector -n crypto-data-collection
```

### **Metrics**
- **Prometheus**: Metrics collection enabled
- **Grafana**: Dashboard available for monitoring
- **Alerts**: Configurable alerts for collection failures

## 🧪 **Testing**

### **Unit Tests**
```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/api/
pytest tests/collectors/
```

### **Integration Tests**
```bash
# Test full data pipeline
./scripts/test-integration.sh

# Test API endpoints
./scripts/test-api.sh
```

### **Load Testing**
```bash
# Test API performance
./scripts/test-load.sh
```

## 📚 **Documentation**

### **🚀 Getting Started**
- **[Quick Start Guide](README.md#-quick-start)** - Get up and running in minutes
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Comprehensive deployment instructions for all environments
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - 4-node architecture and system integration patterns

### **🔧 Development & Operations**
- **[API Documentation](docs/api.md)** - Complete API reference with examples and SDKs
- **[Copilot Instructions](.copilot-instructions.md)** - GitHub Copilot guidelines for this architecture
- **[Monitoring & Observability](docs/MONITORING_OBSERVABILITY.md)** - Grafana dashboards, alerting, and operational procedures

### **🏗️ Architecture & Design**
- **[System Architecture](README.md#%EF%B8%8F-system-architecture)** - Multi-node data collection architecture
- **[4-Node Integration](docs/INTEGRATION_GUIDE.md#%EF%B8%8F-4-node-kubernetes-architecture)** - How this system integrates with trading and analytics nodes
- **[Data Flow Patterns](docs/INTEGRATION_GUIDE.md#-data-flow-orchestration)** - Real-time data pipeline and processing

### **📊 Operational Guides**
- **[Health Monitoring](docs/MONITORING_OBSERVABILITY.md#-health-checks--probes)** - Service health checks and Kubernetes probes
- **[Troubleshooting](docs/DEPLOYMENT_GUIDE.md#-troubleshooting)** - Common issues and solutions
- **[Incident Response](docs/MONITORING_OBSERVABILITY.md#-operational-procedures)** - Step-by-step incident response procedures

### **🔐 Security & Configuration**
- **[API Authentication](docs/api.md#-authentication)** - API key management and security
- **[Database Integration](docs/INTEGRATION_GUIDE.md#-database-integration-architecture)** - Windows MySQL connectivity patterns
- **[Secrets Management](docs/INTEGRATION_GUIDE.md#-security--authentication)** - Kubernetes secrets and API key configuration

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 **Related Projects**

- **[CryptoAI Trading System](https://github.com/mikeepley2/cryptoaitest)** - Main trading system that consumes this data
- **[Trading Engine Node](../k8s/crypto-trading/)** - Live trading operations and ML signal generation
- **[Analytics Node](../k8s/crypto-monitoring/)** - Monitoring, dashboards, and observability
- **[Main System README](../README.md)** - Overview of the complete 4-node architecture

## 📞 **Support**

For issues and questions:
- **[Troubleshooting Guide](docs/DEPLOYMENT_GUIDE.md#-troubleshooting)** - Common issues and solutions
- **[API Documentation](docs/api.md)** - Complete API reference and examples  
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - Architecture and integration patterns
- **[Monitoring Guide](docs/MONITORING_OBSERVABILITY.md)** - Health checks and observability
- **[GitHub Issues](../../issues)** - Create an issue for bugs or feature requests

### **Quick Reference**
- **Health Check**: `curl http://localhost:8000/health`
- **API Status**: `curl http://localhost:8000/metrics`
- **Service Logs**: `kubectl logs -n crypto-collectors deployment/SERVICE_NAME -f`
- **Pod Status**: `kubectl get pods -n crypto-collectors`

---

**Built with ❤️ for reliable, scalable cryptocurrency data collection**