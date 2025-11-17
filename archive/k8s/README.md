# Dedicated Data Collection Node Kubernetes Manifests

This directory contains Kubernetes manifests for the dedicated data collection node, isolated from the trading system.

## Directory Structure

```
k8s/data-collection-node/
├── 00-namespace.yaml              # Dedicated namespace
├── 01-configmaps.yaml             # Configuration management
├── 02-secrets.yaml                # API keys and credentials
├── 03-persistent-volumes.yaml     # Storage configuration
├── databases/
│   ├── mysql.yaml                 # Dedicated MySQL for data collection
│   ├── redis.yaml                 # Redis caching layer
│   ├── influxdb.yaml             # Time series database
│   └── minio.yaml                # Object storage for archives
├── collectors/
│   ├── crypto-prices.yaml         # Cryptocurrency price collector
│   ├── crypto-news.yaml          # Crypto news collector
│   ├── stock-news.yaml           # Stock news collector
│   ├── sentiment-analysis.yaml   # AI sentiment processing
│   ├── technical-indicators.yaml # Technical analysis processor
│   ├── social-media.yaml         # Social media collectors
│   ├── macro-economic.yaml       # Economic data collector
│   └── onchain-data.yaml         # Blockchain data collector
├── processing/
│   ├── ml-feature-engineer.yaml   # ML feature processing
│   ├── data-validator.yaml        # Data quality validation
│   └── scheduler.yaml             # Collection orchestrator
├── api/
│   ├── data-api-gateway.yaml      # Unified data API
│   ├── websocket-server.yaml      # Real-time streaming
│   └── graphql-server.yaml        # Complex queries
├── monitoring/
│   ├── prometheus.yaml            # Metrics collection
│   ├── grafana.yaml              # Dashboards
│   └── alertmanager.yaml         # Alert management
└── networking/
    ├── ingress.yaml               # External access
    ├── network-policies.yaml     # Security policies
    └── service-mesh.yaml         # Internal communication
```

## Deployment Commands

```bash
# Deploy in order
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-configmaps.yaml
kubectl apply -f 02-secrets.yaml
kubectl apply -f 03-persistent-volumes.yaml
kubectl apply -f databases/
kubectl apply -f collectors/
kubectl apply -f processing/
kubectl apply -f api/
kubectl apply -f monitoring/
kubectl apply -f networking/
```

## Validation Commands

```bash
# Check deployment status
kubectl get pods -n crypto-data-collection
kubectl get services -n crypto-data-collection
kubectl get ingress -n crypto-data-collection

# Check data collection health
curl http://data-collection-api/health
curl http://data-collection-api/api/v1/collectors/status
```