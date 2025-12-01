# 🔍 Observability Integration Guide
## Grafana / Loki / Prometheus Integration for Crypto Data Collection Platform

> **Purpose:** Complete documentation for integrating Prometheus, Grafana, and Loki with the K3s-deployed crypto data collection services.

---

## 📋 Table of Contents
- [System Overview](#system-overview)
- [Services Inventory](#services-inventory)
- [Prometheus Configuration](#prometheus-configuration)
- [Grafana Dashboards](#grafana-dashboards)
- [Loki Log Aggregation](#loki-log-aggregation)
- [Alert Rules](#alert-rules)
- [Health Check Endpoints](#health-check-endpoints)
- [Metrics Reference](#metrics-reference)

---

## 🏗️ System Overview

### Architecture
```
┌─────────────────┐
│   Grafana       │ ← Visualization & Dashboards
└────────┬────────┘
         │
    ┌────┴────┬────────┐
    ▼         ▼        ▼
┌──────┐  ┌──────┐  ┌──────┐
│Prometheus Loki  │ Alertmanager
└───┬──┘  └──┬───┘  └───┬──┘
    │        │          │
    └────────┴──────────┘
             │
    ┌────────┴─────────┐
    │  K3d Cluster     │
    │  (crypto-k3s)    │
    │                  │
    │  12 Collectors   │
    │  + API Gateway   │
    └──────────────────┘
```

### Deployment Context
- **Cluster:** K3d cluster named `crypto-k3s`
- **Namespace:** `crypto-core-production`
- **Host Database:** MySQL on host (accessed via `host.k3d.internal:3306`)
- **Host Redis:** Redis on host (accessed via `host.k3d.internal:6379`)
- **Total Services:** 12 collectors + 1 API gateway

---

## 📦 Services Inventory

### Data Collection Services (12 Collectors)

| Service Name | Port | Purpose | Metrics Endpoint | Health Endpoint |
|-------------|------|---------|-----------------|----------------|
| `enhanced-news-collector` | 8001 | News article collection | `:8001/metrics` | `:8001/health` |
| `enhanced-sentiment-ml-analysis` | 8002 | ML sentiment analysis | `:8002/metrics` | `:8002/health` |
| `enhanced-technical-calculator` | 8003 | Technical indicator calculations | `:8003/metrics` | `:8003/health` |
| `enhanced-materialized-updater` | 8004 | Materialized view updates | `:8004/metrics` | `:8004/health` |
| `enhanced-crypto-prices-service` | 8005 | Real-time crypto prices | `:8005/metrics` | `:8005/health` |
| `enhanced-crypto-news-collector-sub` | 8006 | Supplementary news sources | `:8006/metrics` | `:8006/health` |
| `enhanced-onchain-collector` | 8007 | On-chain metrics (whale activity) | `:8007/metrics` | `:8007/health` |
| `enhanced-technical-indicators-collector` | 8008 | Advanced technical indicators | `:8008/metrics` | `:8008/health` |
| `enhanced-macro-collector-v2` | 8009 | Macroeconomic indicators | `:8009/metrics` | `:8009/health` |
| `enhanced-crypto-derivatives-collector` | 8010 | Derivatives data (funding rates) | `:8010/metrics` | `:8010/health` |
| `ml-market-collector` | 8011 | ML market analysis | `:8011/metrics` | `:8011/health` |
| `enhanced-ohlc-collector` | 8012 | OHLC candlestick data | `:8012/metrics` | `:8012/health` |

### Gateway Services

| Service Name | Port | Purpose | Metrics Endpoint | Health Endpoint |
|-------------|------|---------|-----------------|----------------|
| `crypto-api-gateway` | 30080 | External API access (NodePort) | `:8080/metrics` | `:8080/health` |

---

## 🎯 Prometheus Configuration

### Service Discovery
All services are deployed in the `crypto-core-production` namespace and expose metrics on their respective ports.

### Complete Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 30s
  evaluation_interval: 30s
  external_labels:
    cluster: 'crypto-k3s'
    environment: 'production'

# Scrape configurations
scrape_configs:
  # ==========================================
  # KUBERNETES SERVICE DISCOVERY
  # ==========================================
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - crypto-core-production
    
    relabel_configs:
      # Only scrape pods with prometheus.io/scrape annotation
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      
      # Use custom port if specified
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: (.+)
        replacement: $1:${1}
      
      # Use custom path if specified
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      
      # Add pod metadata
      - source_labels: [__meta_kubernetes_namespace]
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: kubernetes_pod_name
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app

  # ==========================================
  # COLLECTOR SERVICES (12 Services)
  # ==========================================
  
  - job_name: 'news-collector'
    static_configs:
      - targets: ['enhanced-news-collector-service.crypto-core-production.svc.cluster.local:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'sentiment-ml-analysis'
    static_configs:
      - targets: ['enhanced-sentiment-ml-analysis-service.crypto-core-production.svc.cluster.local:8002']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'technical-calculator'
    static_configs:
      - targets: ['enhanced-technical-calculator-service.crypto-core-production.svc.cluster.local:8003']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'materialized-updater'
    static_configs:
      - targets: ['enhanced-materialized-updater-service.crypto-core-production.svc.cluster.local:8004']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'crypto-prices'
    static_configs:
      - targets: ['enhanced-crypto-prices-service.crypto-core-production.svc.cluster.local:8005']
    metrics_path: '/metrics'
    scrape_interval: 15s  # More frequent for price data

  - job_name: 'news-collector-sub'
    static_configs:
      - targets: ['enhanced-crypto-news-collector-sub-service.crypto-core-production.svc.cluster.local:8006']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'onchain-collector'
    static_configs:
      - targets: ['enhanced-onchain-collector-service.crypto-core-production.svc.cluster.local:8007']
    metrics_path: '/metrics'
    scrape_interval: 60s  # Less frequent for on-chain data

  - job_name: 'technical-indicators'
    static_configs:
      - targets: ['enhanced-technical-indicators-collector-service.crypto-core-production.svc.cluster.local:8008']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'macro-collector'
    static_configs:
      - targets: ['enhanced-macro-collector-v2-service.crypto-core-production.svc.cluster.local:8009']
    metrics_path: '/metrics'
    scrape_interval: 300s  # 5 minutes for macro data

  - job_name: 'derivatives-collector'
    static_configs:
      - targets: ['enhanced-crypto-derivatives-collector-service.crypto-core-production.svc.cluster.local:8010']
    metrics_path: '/metrics'
    scrape_interval: 60s

  - job_name: 'ml-market-collector'
    static_configs:
      - targets: ['ml-market-collector-service.crypto-core-production.svc.cluster.local:8011']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'ohlc-collector'
    static_configs:
      - targets: ['enhanced-ohlc-collector-service.crypto-core-production.svc.cluster.local:8012']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # ==========================================
  # API GATEWAY
  # ==========================================
  
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['crypto-api-gateway.crypto-core-production.svc.cluster.local:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # ==========================================
  # INFRASTRUCTURE MONITORING
  # ==========================================
  
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  - job_name: 'kubernetes-cadvisor'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics/cadvisor

  # ==========================================
  # HOST SERVICES (MySQL, Redis)
  # ==========================================
  
  - job_name: 'host-mysql'
    static_configs:
      - targets: ['host.k3d.internal:9104']  # MySQL exporter port
    metrics_path: '/metrics'
    scrape_interval: 30s
    # Note: Requires mysqld_exporter running on host

  - job_name: 'host-redis'
    static_configs:
      - targets: ['host.k3d.internal:9121']  # Redis exporter port
    metrics_path: '/metrics'
    scrape_interval: 30s
    # Note: Requires redis_exporter running on host
```

### Kubernetes Service Monitor (Alternative)

If using Prometheus Operator, use ServiceMonitor CRDs:

```yaml
# crypto-collectors-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: crypto-collectors
  namespace: crypto-core-production
  labels:
    team: data-platform
spec:
  selector:
    matchLabels:
      prometheus: enabled
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
  namespaceSelector:
    matchNames:
      - crypto-core-production
```

---

## 📊 Grafana Dashboards

### Dashboard 1: Collectors Overview

**Dashboard JSON Variables:**
```json
{
  "dashboard": {
    "title": "Crypto Data Collection - Collectors Overview",
    "tags": ["crypto", "collectors", "overview"],
    "templating": {
      "list": [
        {
          "name": "collector",
          "type": "query",
          "query": "label_values(collector_health_score, job)",
          "multi": true,
          "includeAll": true
        }
      ]
    }
  }
}
```

**Key Panels:**

#### Panel 1: Health Score Overview
```promql
# Health scores for all collectors
collector_health_score{job=~"$collector"}

# Average health across all collectors
avg(collector_health_score)
```

#### Panel 2: Data Gap Monitoring
```promql
# Data gaps in hours
collector_gap_hours{job=~"$collector"}

# Alert when gap > 2 hours
collector_gap_hours > 2
```

#### Panel 3: Collection Rate
```promql
# Records collected per minute
rate(collector_total_collected[5m])

# Total records collected (24h)
increase(collector_total_collected[24h])
```

#### Panel 4: Error Rate
```promql
# Error rate percentage
rate(collector_collection_errors[5m]) / rate(collector_total_collected[5m]) * 100

# Total errors (24h)
increase(collector_collection_errors[24h])
```

#### Panel 5: API Call Rate
```promql
# API calls per minute
rate(collector_api_calls_made[5m])

# API call rate by collector
sum by (job) (rate(collector_api_calls_made[5m]))
```

#### Panel 6: Database Operations
```promql
# Database writes per minute
rate(collector_database_writes[5m])

# Write latency (if instrumented)
histogram_quantile(0.99, rate(collector_db_write_duration_bucket[5m]))
```

### Dashboard 2: Service-Specific Deep Dive

#### News Collector Panel
```promql
# News articles collected
increase(news_collector_articles_collected[1h])

# News sources active
news_collector_sources_active

# Processing time per article
news_collector_article_processing_seconds
```

#### Sentiment ML Analysis Panel
```promql
# Sentiment analyses performed
increase(sentiment_ml_total_analyses[1h])

# Sentiment distribution
sum by (sentiment_category) (sentiment_ml_category_count)

# ML model latency
histogram_quantile(0.95, rate(sentiment_ml_analysis_duration_bucket[5m]))
```

#### Crypto Prices Panel
```promql
# Price updates per minute
rate(prices_service_updates[1m])

# Symbols tracked
prices_service_symbols_tracked

# Price staleness (seconds since last update)
time() - prices_service_last_update_timestamp
```

#### Technical Indicators Panel
```promql
# Indicators calculated
increase(technical_indicators_calculated[1h])

# Symbols processed
technical_indicators_symbols_processed

# Calculation errors
increase(technical_indicators_calculation_errors[1h])
```

### Dashboard 3: Infrastructure & Resources

#### CPU Usage
```promql
# CPU usage by pod
sum by (pod_name) (rate(container_cpu_usage_seconds_total{namespace="crypto-core-production"}[5m]))

# CPU throttling
rate(container_cpu_cfs_throttled_seconds_total{namespace="crypto-core-production"}[5m])
```

#### Memory Usage
```promql
# Memory usage by pod
sum by (pod_name) (container_memory_usage_bytes{namespace="crypto-core-production"})

# Memory limit utilization
(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100
```

#### Network I/O
```promql
# Network received rate
rate(container_network_receive_bytes_total{namespace="crypto-core-production"}[5m])

# Network transmitted rate
rate(container_network_transmit_bytes_total{namespace="crypto-core-production"}[5m])
```

#### Database Connections
```promql
# MySQL connections from collectors
mysql_global_status_threads_connected

# MySQL query rate
rate(mysql_global_status_queries[1m])

# Redis connections
redis_connected_clients

# Redis command rate
rate(redis_commands_processed_total[1m])
```

---

## 📝 Loki Log Aggregation

### Loki Configuration

```yaml
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h  # 30 days
```

### Promtail Configuration

```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # ==========================================
  # KUBERNETES POD LOGS
  # ==========================================
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - crypto-core-production
    
    pipeline_stages:
      # Parse JSON logs
      - json:
          expressions:
            level: level
            timestamp: timestamp
            message: message
            collector: collector
            symbol: symbol
            error: error
      
      # Extract labels
      - labels:
          level:
          collector:
      
      # Add timestamp
      - timestamp:
          source: timestamp
          format: RFC3339
    
    relabel_configs:
      # Add namespace label
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      
      # Add pod name label
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      
      # Add container name label
      - source_labels: [__meta_kubernetes_pod_container_name]
        target_label: container
      
      # Add app label
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app
      
      # Path to pod logs
      - source_labels: [__meta_kubernetes_pod_uid, __meta_kubernetes_pod_container_name]
        target_label: __path__
        separator: /
        replacement: /var/log/pods/*$1/*.log
```

### LogQL Queries

#### View All Collector Logs
```logql
{namespace="crypto-core-production"}
```

#### Filter by Collector
```logql
{namespace="crypto-core-production", app="enhanced-news-collector"}
```

#### Error Logs Only
```logql
{namespace="crypto-core-production"} |= "ERROR" or "error"
```

#### Collection Success Events
```logql
{namespace="crypto-core-production"} |= "collected" | json | line_format "{{.timestamp}} {{.collector}}: {{.message}}"
```

#### Database Errors
```logql
{namespace="crypto-core-production"} |= "database" |= "error" | json
```

#### API Rate Limiting
```logql
{namespace="crypto-core-production"} |~ "rate limit|429|too many requests"
```

#### Performance Issues
```logql
{namespace="crypto-core-production"} |= "slow" or "timeout" | json | duration > 5s
```

---

## 🚨 Alert Rules

### Alert Configuration

```yaml
# prometheus-alerts.yml
groups:
  - name: crypto_collectors_health
    interval: 30s
    rules:
      # ==========================================
      # SERVICE HEALTH ALERTS
      # ==========================================
      
      - alert: CollectorHealthDegraded
        expr: collector_health_score < 50
        for: 5m
        labels:
          severity: warning
          team: data-platform
        annotations:
          summary: "Collector {{ $labels.job }} health degraded"
          description: "Health score is {{ $value }}, below threshold of 50"
          runbook_url: "https://docs.company.com/runbooks/collector-health"
      
      - alert: CollectorHealthCritical
        expr: collector_health_score < 30
        for: 2m
        labels:
          severity: critical
          team: data-platform
        annotations:
          summary: "Collector {{ $labels.job }} health critical"
          description: "Health score is {{ $value }}, below critical threshold of 30"
          runbook_url: "https://docs.company.com/runbooks/collector-health"
      
      # ==========================================
      # DATA FRESHNESS ALERTS
      # ==========================================
      
      - alert: CollectorDataStale
        expr: collector_gap_hours > 2
        for: 5m
        labels:
          severity: warning
          team: data-platform
        annotations:
          summary: "Collector {{ $labels.job }} data is stale"
          description: "No data collected for {{ $value }} hours"
      
      - alert: CollectorDataCriticallyStale
        expr: collector_gap_hours > 6
        for: 5m
        labels:
          severity: critical
          team: data-platform
        annotations:
          summary: "Collector {{ $labels.job }} data critically stale"
          description: "No data collected for {{ $value }} hours"
      
      # ==========================================
      # ERROR RATE ALERTS
      # ==========================================
      
      - alert: CollectorHighErrorRate
        expr: (rate(collector_collection_errors[5m]) / rate(collector_total_collected[5m])) > 0.20
        for: 10m
        labels:
          severity: warning
          team: data-platform
        annotations:
          summary: "High error rate for {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: CollectorCriticalErrorRate
        expr: (rate(collector_collection_errors[5m]) / rate(collector_total_collected[5m])) > 0.50
        for: 5m
        labels:
          severity: critical
          team: data-platform
        annotations:
          summary: "Critical error rate for {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      # ==========================================
      # SERVICE AVAILABILITY ALERTS
      # ==========================================
      
      - alert: CollectorDown
        expr: up{job=~".*-collector"} == 0
        for: 2m
        labels:
          severity: critical
          team: data-platform
        annotations:
          summary: "Collector {{ $labels.job }} is down"
          description: "Service has been unavailable for 2 minutes"
      
      - alert: CollectorRestarting
        expr: rate(kube_pod_container_status_restarts_total{namespace="crypto-core-production"}[15m]) > 0
        labels:
          severity: warning
          team: data-platform
        annotations:
          summary: "Collector {{ $labels.pod }} is restarting"
          description: "Pod has restarted {{ $value }} times in last 15 minutes"
      
      # ==========================================
      # RESOURCE ALERTS
      # ==========================================
      
      - alert: CollectorHighMemoryUsage
        expr: (container_memory_usage_bytes{namespace="crypto-core-production"} / container_spec_memory_limit_bytes) > 0.90
        for: 5m
        labels:
          severity: warning
          team: data-platform
        annotations:
          summary: "High memory usage for {{ $labels.pod }}"
          description: "Memory usage is {{ $value | humanizePercentage }} of limit"
      
      - alert: CollectorHighCPUUsage
        expr: (rate(container_cpu_usage_seconds_total{namespace="crypto-core-production"}[5m]) / container_spec_cpu_quota) > 0.90
        for: 10m
        labels:
          severity: warning
          team: data-platform
        annotations:
          summary: "High CPU usage for {{ $labels.pod }}"
          description: "CPU usage is {{ $value | humanizePercentage }} of limit"
      
      # ==========================================
      # DATABASE ALERTS
      # ==========================================
      
      - alert: HighDatabaseWriteLatency
        expr: histogram_quantile(0.99, rate(collector_db_write_duration_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
          team: data-platform
        annotations:
          summary: "High database write latency for {{ $labels.job }}"
          description: "P99 write latency is {{ $value }}s"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: collector_db_connections_active >= collector_db_connections_max
        for: 2m
        labels:
          severity: critical
          team: data-platform
        annotations:
          summary: "Database connection pool exhausted for {{ $labels.job }}"
          description: "All {{ $value }} connections in use"
      
      # ==========================================
      # PRICE DATA SPECIFIC ALERTS
      # ==========================================
      
      - alert: PriceDataStale
        expr: (time() - prices_service_last_update_timestamp) > 300
        for: 2m
        labels:
          severity: critical
          team: data-platform
        annotations:
          summary: "Price data is stale"
          description: "No price updates for {{ $value }}s"
      
      # ==========================================
      # SENTIMENT ANALYSIS SPECIFIC ALERTS
      # ==========================================
      
      - alert: SentimentMLModelSlow
        expr: histogram_quantile(0.95, rate(sentiment_ml_analysis_duration_bucket[5m])) > 10.0
        for: 10m
        labels:
          severity: warning
          team: ml-platform
        annotations:
          summary: "Sentiment ML model slow"
          description: "P95 analysis time is {{ $value }}s"
```

---

## 🏥 Health Check Endpoints

All 12 collectors expose standardized health check endpoints:

### `/health` - Liveness Probe
**Purpose:** Kubernetes liveness check - is the service running?

**Example Response:**
```json
{
  "status": "healthy",
  "service": "enhanced-news-collector",
  "timestamp": "2025-12-01T10:30:00Z"
}
```

### `/ready` - Readiness Probe
**Purpose:** Kubernetes readiness check - can service accept traffic?

**Example Response:**
```json
{
  "status": "ready",
  "database_connected": true,
  "redis_connected": true,
  "dependencies_healthy": true
}
```

### `/status` - Detailed Status
**Purpose:** Comprehensive service status and configuration

**Example Response:**
```json
{
  "service": "enhanced-news-collector",
  "version": "2.0.0",
  "uptime_seconds": 86400,
  "health": {
    "score": 87.5,
    "status": "healthy",
    "gap_hours": 0.5,
    "data_freshness": "healthy"
  },
  "stats": {
    "total_collected": 15420,
    "collection_errors": 3,
    "api_calls_made": 18543,
    "database_writes": 15420,
    "success_rate": 99.8
  },
  "config": {
    "collection_interval": 300,
    "symbols_tracked": 127,
    "batch_size": 50
  },
  "last_collection": {
    "timestamp": "2025-12-01T10:25:00Z",
    "records": 42,
    "duration_seconds": 3.2
  }
}
```

### `/metrics` - Prometheus Metrics
**Purpose:** Prometheus-compatible metrics export

**Example Output:**
```
# HELP news_collector_total_collected Total news articles collected
# TYPE news_collector_total_collected counter
news_collector_total_collected 15420

# HELP news_collector_collection_errors Total collection errors
# TYPE news_collector_collection_errors counter
news_collector_collection_errors 3

# HELP news_collector_health_score Service health score (0-100)
# TYPE news_collector_health_score gauge
news_collector_health_score 87.5

# HELP news_collector_gap_hours Hours since last collection
# TYPE news_collector_gap_hours gauge
news_collector_gap_hours 0.5

# HELP news_collector_api_calls_made Total API calls
# TYPE news_collector_api_calls_made counter
news_collector_api_calls_made 18543

# HELP news_collector_database_writes Total database writes
# TYPE news_collector_database_writes counter
news_collector_database_writes 15420

# HELP news_collector_running Service running status
# TYPE news_collector_running gauge
news_collector_running 1
```

---

## 📈 Metrics Reference

### Common Metrics (All Collectors)

| Metric Name | Type | Description | Labels |
|------------|------|-------------|--------|
| `<collector>_total_collected` | counter | Total records collected | job, namespace, pod |
| `<collector>_collection_errors` | counter | Total collection errors | job, namespace, pod, error_type |
| `<collector>_health_score` | gauge | Service health (0-100) | job, namespace, pod |
| `<collector>_gap_hours` | gauge | Hours since last collection | job, namespace, pod |
| `<collector>_api_calls_made` | counter | Total API calls | job, namespace, pod, api |
| `<collector>_database_writes` | counter | Total DB writes | job, namespace, pod, table |
| `<collector>_running` | gauge | Service running (1=yes, 0=no) | job, namespace, pod |

### Service-Specific Metrics

#### News Collector
```
news_collector_articles_collected
news_collector_sources_active
news_collector_article_processing_seconds
```

#### Sentiment ML Analysis
```
sentiment_ml_total_analyses
sentiment_ml_category_count{sentiment_category="positive|negative|neutral"}
sentiment_ml_analysis_duration_seconds
sentiment_ml_model_accuracy
```

#### Crypto Prices
```
prices_service_updates
prices_service_symbols_tracked
prices_service_last_update_timestamp
prices_service_price_change_24h
```

#### Technical Indicators
```
technical_indicators_calculated
technical_indicators_symbols_processed
technical_indicators_calculation_errors
technical_indicators_duration_seconds
```

#### On-Chain Collector
```
onchain_collector_whale_transactions
onchain_collector_network_activity
onchain_collector_gas_price_gwei
```

#### Derivatives Collector
```
derivatives_collector_funding_rates
derivatives_collector_open_interest
derivatives_collector_volume_24h
derivatives_collector_exchanges_tracked
```

#### OHLC Collector
```
ohlc_collector_candles_collected
ohlc_collector_timeframes_tracked
ohlc_collector_symbols_tracked
```

#### Macro Collector
```
macro_collector_indicators_updated
macro_collector_sources_polled
macro_collector_data_points_collected
```

---

## 🚀 Quick Start Deployment

### 1. Deploy Prometheus

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    $(cat prometheus.yml | sed 's/^/    /')
EOF

kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: data
          mountPath: /prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
spec:
  type: NodePort
  ports:
  - port: 9090
    targetPort: 9090
    nodePort: 30090
  selector:
    app: prometheus
EOF
```

### 2. Deploy Grafana

```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"
        volumeMounts:
        - name: data
          mountPath: /var/lib/grafana
      volumes:
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  type: NodePort
  ports:
  - port: 3000
    targetPort: 3000
    nodePort: 30300
  selector:
    app: grafana
EOF
```

### 3. Deploy Loki + Promtail

```bash
# Deploy Loki
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: monitoring
data:
  loki.yml: |
    $(cat loki-config.yaml | sed 's/^/    /')
EOF

kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
      - name: loki
        image: grafana/loki:latest
        ports:
        - containerPort: 3100
        volumeMounts:
        - name: config
          mountPath: /etc/loki
        - name: data
          mountPath: /loki
      volumes:
      - name: config
        configMap:
          name: loki-config
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: loki
  namespace: monitoring
spec:
  ports:
  - port: 3100
    targetPort: 3100
  selector:
    app: loki
EOF

# Deploy Promtail
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: promtail-config
  namespace: monitoring
data:
  promtail.yml: |
    $(cat promtail-config.yaml | sed 's/^/    /')
EOF

kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: promtail
  template:
    metadata:
      labels:
        app: promtail
    spec:
      serviceAccountName: promtail
      containers:
      - name: promtail
        image: grafana/promtail:latest
        volumeMounts:
        - name: config
          mountPath: /etc/promtail
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: promtail-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
EOF
```

### 4. Access Services

```bash
# Prometheus: http://localhost:30090
# Grafana: http://localhost:30300 (admin/admin)

# Port forward if needed
kubectl port-forward -n monitoring svc/prometheus 9090:9090
kubectl port-forward -n monitoring svc/grafana 3000:3000
kubectl port-forward -n monitoring svc/loki 3100:3100
```

### 5. Configure Grafana Data Sources

1. Login to Grafana (http://localhost:30300)
2. Add Prometheus data source:
   - URL: `http://prometheus.monitoring.svc.cluster.local:9090`
3. Add Loki data source:
   - URL: `http://loki.monitoring.svc.cluster.local:3100`

---

## 📚 Additional Resources

- **Prometheus Documentation:** https://prometheus.io/docs/
- **Grafana Documentation:** https://grafana.com/docs/
- **Loki Documentation:** https://grafana.com/docs/loki/
- **PromQL Cheat Sheet:** https://promlabs.com/promql-cheat-sheet/
- **LogQL Cheat Sheet:** https://grafana.com/docs/loki/latest/logql/

---

## 🔧 Troubleshooting

### No Metrics Showing Up

```bash
# Check if Prometheus can reach services
kubectl exec -n monitoring -it deployment/prometheus -- wget -O- http://enhanced-news-collector-service.crypto-core-production.svc.cluster.local:8001/metrics

# Check service discovery
kubectl get endpoints -n crypto-core-production

# Check Prometheus targets
# Navigate to Prometheus UI -> Status -> Targets
```

### Logs Not Appearing in Loki

```bash
# Check Promtail logs
kubectl logs -n monitoring daemonset/promtail

# Check Loki logs
kubectl logs -n monitoring deployment/loki

# Verify log path exists
kubectl exec -n monitoring -it daemonset/promtail -- ls -la /var/log/pods
```

### High Memory Usage

```bash
# Check actual memory usage
kubectl top pods -n crypto-core-production

# Check for memory leaks in collector logs
kubectl logs -n crypto-core-production deployment/enhanced-news-collector | grep -i "memory\|oom"
```

---

**Last Updated:** December 1, 2025  
**Version:** 1.0  
**Maintained By:** Data Platform Team
