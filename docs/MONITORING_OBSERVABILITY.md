# Data Collection System Monitoring & Observability

> **🏗️ Architecture Note**: This system integrates with the **Analytics Node** for comprehensive infrastructure monitoring. The Data Collection Node focuses on **service-level observability** while the Analytics Node handles **infrastructure monitoring** (node health, pod status, resource utilization).

## 📋 **Monitoring Separation of Concerns**

| **Monitoring Type** | **Responsible Node** | **Tools Used** | **Access Method** |
|---------------------|---------------------|----------------|-------------------|
| **Infrastructure** (Node/Pod Health) | Analytics Node | Grafana + Prometheus | `http://analytics-node:3000` |
| **Application** (Service Health) | Data Collection Node | Service health endpoints | `http://data-node:8000/health` |
| **Logs** (Centralized) | Analytics Node | Elasticsearch + Kibana | `http://analytics-node:5601` |
| **Traces** (Distributed) | Analytics Node | Jaeger | `http://analytics-node:16686` |
| **Alerts** (All Types) | Analytics Node | Alertmanager | `http://analytics-node:9093` |

This guide provides comprehensive monitoring and observability practices for the crypto data collection system, including service-level metrics, application logs, and integration points with the Analytics Node observability stack.

## 🎯 **Observability Strategy**

### **Three Pillars of Observability**

1. **Metrics**: Quantitative measurements of system behavior
2. **Logs**: Structured records of events and operations
3. **Traces**: Request flow tracking across services

### **Monitoring Objectives**
- **Service Health**: Real-time status of all collection services
- **Data Quality**: Accuracy, completeness, and freshness of collected data
- **Performance**: Latency, throughput, and resource utilization
- **Business Metrics**: Collection rates, API quotas, data coverage
- **Alerting**: Proactive notification of issues and anomalies

## 📊 **Prometheus Metrics Collection**

### **Core Service Metrics**

#### **Standard Metrics (All Services)**
```yaml
# Service availability
up{job="crypto-collectors"}

# Request metrics
http_requests_total{service, endpoint, method, status}
http_request_duration_seconds{service, endpoint, method}
http_requests_in_flight{service}

# Error metrics
errors_total{service, error_type, severity}
error_rate{service}

# Resource metrics
cpu_usage_percent{service, container}
memory_usage_bytes{service, container}
memory_usage_percent{service, container}
disk_usage_bytes{service, mount_point}
network_bytes_total{service, interface, direction}
```

#### **Data Collection Metrics**
```yaml
# Collection performance
crypto_collection_requests_total{collector, symbol, status}
crypto_collection_duration_seconds{collector, symbol}
crypto_collection_records_total{collector, symbol}
crypto_collection_errors_total{collector, symbol, error_type}

# Data quality metrics
crypto_data_freshness_seconds{collector, symbol}
crypto_data_completeness_ratio{collector, symbol}
crypto_data_accuracy_score{collector, symbol}

# External API metrics
external_api_requests_total{provider, endpoint, status}
external_api_rate_limit_remaining{provider}
external_api_quota_usage_percent{provider}
external_api_latency_seconds{provider, endpoint}

# Database metrics
mysql_connections_active{database}
mysql_connections_max{database}
mysql_query_duration_seconds{database, query_type}
mysql_slow_queries_total{database}
redis_connected_clients{instance}
redis_memory_usage_bytes{instance}
redis_cache_hit_ratio{instance}
```

#### **Business Metrics**
```yaml
# Coverage metrics
crypto_symbols_monitored_total
crypto_news_sources_active_total
crypto_sentiment_coverage_ratio

# Processing metrics
ml_features_generated_total{symbol, feature_version}
sentiment_analysis_completed_total{model, source}
technical_indicators_calculated_total{symbol, indicator}

# SLA metrics
data_availability_sla_ratio{data_type}
api_response_time_sla_ratio{endpoint}
collection_frequency_sla_ratio{collector}
```

### **Metrics Configuration**

#### **Prometheus Configuration**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "crypto_data_collection_rules.yml"

scrape_configs:
  - job_name: 'crypto-collectors'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - crypto-collectors
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

  - job_name: 'crypto-api-gateway'
    static_configs:
      - targets: ['data-api-gateway.crypto-collectors.svc.cluster.local:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'crypto-database'
    static_configs:
      - targets: ['host.docker.internal:9104']  # MySQL exporter
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager.crypto-monitoring.svc.cluster.local:9093
```

#### **Service Metrics Implementation**
```python
# Example: Collector service metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Define metrics
COLLECTION_REQUESTS = Counter(
    'crypto_collection_requests_total',
    'Total collection requests',
    ['collector', 'symbol', 'status']
)

COLLECTION_DURATION = Histogram(
    'crypto_collection_duration_seconds',
    'Collection duration in seconds',
    ['collector', 'symbol']
)

DATA_FRESHNESS = Gauge(
    'crypto_data_freshness_seconds',
    'Seconds since last data update',
    ['collector', 'symbol']
)

EXTERNAL_API_REQUESTS = Counter(
    'external_api_requests_total',
    'External API requests',
    ['provider', 'endpoint', 'status']
)

API_RATE_LIMIT = Gauge(
    'external_api_rate_limit_remaining',
    'Remaining API rate limit',
    ['provider']
)

# Instrumentation example
class MetricsCollector:
    def __init__(self, collector_name: str):
        self.collector_name = collector_name
    
    async def collect_data_with_metrics(self, symbol: str):
        start_time = time.time()
        try:
            # Perform data collection
            data = await self.collect_data(symbol)
            
            # Record success metrics
            COLLECTION_REQUESTS.labels(
                collector=self.collector_name,
                symbol=symbol,
                status='success'
            ).inc()
            
            # Update data freshness
            DATA_FRESHNESS.labels(
                collector=self.collector_name,
                symbol=symbol
            ).set(0)  # Just collected, so freshness is 0
            
            return data
            
        except Exception as e:
            # Record error metrics
            COLLECTION_REQUESTS.labels(
                collector=self.collector_name,
                symbol=symbol,
                status='error'
            ).inc()
            
            raise
        finally:
            # Record duration
            duration = time.time() - start_time
            COLLECTION_DURATION.labels(
                collector=self.collector_name,
                symbol=symbol
            ).observe(duration)

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 📈 **Grafana Dashboards**

### **Main Data Collection Dashboard**

#### **Dashboard Configuration**
```json
{
  "dashboard": {
    "id": null,
    "title": "Crypto Data Collection System",
    "tags": ["crypto", "data-collection", "monitoring"],
    "timezone": "UTC",
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "System Overview",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"crypto-collectors\"}",
            "legendFormat": "{{service}} Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Collection Rates",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(crypto_collection_requests_total{status=\"success\"}[5m])",
            "legendFormat": "{{collector}} Success Rate"
          },
          {
            "expr": "rate(crypto_collection_requests_total{status=\"error\"}[5m])",
            "legendFormat": "{{collector}} Error Rate"
          }
        ]
      },
      {
        "id": 3,
        "title": "Data Freshness",
        "type": "heatmap",
        "targets": [
          {
            "expr": "crypto_data_freshness_seconds",
            "legendFormat": "{{collector}}/{{symbol}}"
          }
        ]
      },
      {
        "id": 4,
        "title": "API Rate Limits",
        "type": "gauge",
        "targets": [
          {
            "expr": "external_api_rate_limit_remaining",
            "legendFormat": "{{provider}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 20},
                {"color": "green", "value": 50}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "mysql_connections_active",
            "legendFormat": "Active Connections"
          },
          {
            "expr": "rate(mysql_queries_total[5m])",
            "legendFormat": "Query Rate"
          },
          {
            "expr": "mysql_query_duration_seconds{quantile=\"0.95\"}",
            "legendFormat": "95th Percentile Query Time"
          }
        ]
      },
      {
        "id": 6,
        "title": "Error Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (error_type) (crypto_collection_errors_total)",
            "legendFormat": "{{error_type}}"
          }
        ]
      },
      {
        "id": 7,
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "{{service}} CPU"
          },
          {
            "expr": "memory_usage_percent",
            "legendFormat": "{{service}} Memory"
          }
        ]
      }
    ]
  }
}
```

### **Service-Specific Dashboards**

#### **Crypto Prices Collector Dashboard**
```json
{
  "dashboard": {
    "title": "Crypto Prices Collector",
    "panels": [
      {
        "title": "Collection Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(crypto_collection_requests_total{collector=\"crypto-prices\", status=\"success\"}[5m]) / rate(crypto_collection_requests_total{collector=\"crypto-prices\"}[5m]) * 100",
            "legendFormat": "Success Rate %"
          }
        ]
      },
      {
        "title": "Price Updates by Symbol",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(crypto_collection_requests_total{collector=\"crypto-prices\", status=\"success\"}[5m])",
            "legendFormat": "{{symbol}}"
          }
        ]
      },
      {
        "title": "CoinGecko API Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "external_api_quota_usage_percent{provider=\"coingecko\"}",
            "legendFormat": "Quota Usage"
          }
        ]
      }
    ]
  }
}
```

#### **Sentiment Analysis Dashboard**
```json
{
  "dashboard": {
    "title": "Sentiment Analysis System",
    "panels": [
      {
        "title": "Sentiment Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(sentiment_analysis_completed_total[5m])",
            "legendFormat": "{{model}}/{{source}}"
          }
        ]
      },
      {
        "title": "Model Performance",
        "type": "table",
        "targets": [
          {
            "expr": "sentiment_model_accuracy_score",
            "legendFormat": "{{model}}"
          },
          {
            "expr": "sentiment_model_latency_seconds",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "title": "News Sources Coverage",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (source) (crypto_news_articles_total)",
            "legendFormat": "{{source}}"
          }
        ]
      }
    ]
  }
}
```

### **Business Intelligence Dashboard**
```json
{
  "dashboard": {
    "title": "Data Collection Business Metrics",
    "panels": [
      {
        "title": "Symbol Coverage",
        "type": "stat",
        "targets": [
          {
            "expr": "crypto_symbols_monitored_total",
            "legendFormat": "Total Symbols"
          }
        ]
      },
      {
        "title": "Data Completeness SLA",
        "type": "gauge",
        "targets": [
          {
            "expr": "data_availability_sla_ratio * 100",
            "legendFormat": "{{data_type}} SLA %"
          }
        ]
      },
      {
        "title": "Daily Collection Volume",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(crypto_collection_records_total[24h])",
            "legendFormat": "{{collector}}"
          }
        ]
      }
    ]
  }
}
```

## 🚨 **Alerting Rules**

### **Critical Alerts**

#### **Service Availability Alerts**
```yaml
# crypto_data_collection_rules.yml
groups:
- name: service_availability
  rules:
  - alert: ServiceDown
    expr: up{job="crypto-collectors"} == 0
    for: 2m
    labels:
      severity: critical
      team: data-collection
    annotations:
      summary: "Service {{ $labels.service }} is down"
      description: "{{ $labels.service }} has been down for more than 2 minutes"
      runbook_url: "https://docs.crypto-trading.com/runbooks/service-down"

  - alert: HighErrorRate
    expr: rate(crypto_collection_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
      team: data-collection
    annotations:
      summary: "High error rate in {{ $labels.collector }}"
      description: "{{ $labels.collector }} error rate is {{ $value | humanizePercentage }}"

  - alert: DataFreshnessAlert
    expr: crypto_data_freshness_seconds > 1800  # 30 minutes
    for: 10m
    labels:
      severity: warning
      team: data-collection
    annotations:
      summary: "Stale data in {{ $labels.collector }}"
      description: "{{ $labels.collector }}/{{ $labels.symbol }} data is {{ $value | humanizeDuration }} old"
```

#### **Resource Alerts**
```yaml
- name: resource_alerts
  rules:
  - alert: HighCPUUsage
    expr: cpu_usage_percent > 80
    for: 5m
    labels:
      severity: warning
      team: data-collection
    annotations:
      summary: "High CPU usage on {{ $labels.service }}"
      description: "CPU usage is {{ $value | humanizePercentage }} on {{ $labels.service }}"

  - alert: HighMemoryUsage
    expr: memory_usage_percent > 85
    for: 5m
    labels:
      severity: warning
      team: data-collection
    annotations:
      summary: "High memory usage on {{ $labels.service }}"
      description: "Memory usage is {{ $value | humanizePercentage }} on {{ $labels.service }}"

  - alert: DatabaseConnectionsHigh
    expr: mysql_connections_active / mysql_connections_max > 0.8
    for: 2m
    labels:
      severity: warning
      team: data-collection
    annotations:
      summary: "High database connection usage"
      description: "Database connection usage is {{ $value | humanizePercentage }}"
```

#### **Business Logic Alerts**
```yaml
- name: business_alerts
  rules:
  - alert: APIQuotaExhausted
    expr: external_api_rate_limit_remaining < 100
    for: 1m
    labels:
      severity: critical
      team: data-collection
    annotations:
      summary: "API quota nearly exhausted for {{ $labels.provider }}"
      description: "Only {{ $value }} requests remaining for {{ $labels.provider }}"

  - alert: LowDataCompleteness
    expr: crypto_data_completeness_ratio < 0.9
    for: 15m
    labels:
      severity: warning
      team: data-collection
    annotations:
      summary: "Low data completeness for {{ $labels.collector }}"
      description: "Data completeness is {{ $value | humanizePercentage }} for {{ $labels.collector }}/{{ $labels.symbol }}"

  - alert: SentimentModelDown
    expr: up{service=~".*sentiment.*"} == 0
    for: 3m
    labels:
      severity: critical
      team: data-collection
    annotations:
      summary: "Sentiment analysis service is down"
      description: "{{ $labels.service }} sentiment service is unavailable"
```

### **Alertmanager Configuration**
```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@crypto-trading.com'

route:
  group_by: ['alertname', 'team']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    continue: true
  - match:
      team: data-collection
    receiver: 'data-collection-team'

receivers:
- name: 'default'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts'
    title: 'Alert: {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@crypto-trading.com'
    subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Runbook: {{ .Annotations.runbook_url }}
      {{ end }}
  pagerduty_configs:
  - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
    description: '{{ .GroupLabels.alertname }}'

- name: 'data-collection-team'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#data-collection'
    title: 'Data Collection Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## 📋 **Structured Logging**

### **Log Format Standards**
```json
{
  "timestamp": "2025-01-15T10:30:00.000Z",
  "level": "INFO",
  "service": "crypto-prices-collector",
  "module": "price_collector",
  "function": "collect_prices",
  "message": "Successfully collected prices for 35 symbols",
  "context": {
    "symbols_count": 35,
    "collection_duration_ms": 2500,
    "api_provider": "coingecko",
    "batch_id": "batch_12345"
  },
  "correlation_id": "req_67890-abcdef",
  "trace_id": "trace_12345-67890",
  "labels": {
    "environment": "production",
    "cluster": "crypto-data-collection",
    "node": "cryptoai-data-collection",
    "namespace": "crypto-collectors"
  }
}
```

### **Log Level Guidelines**
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about system operation
- **WARN**: Warning conditions that don't stop operation
- **ERROR**: Error conditions that stop operation
- **FATAL**: Critical errors that may cause system shutdown

### **Logging Implementation**
```python
import logging
import json
from datetime import datetime
import uuid

class StructuredLogger:
    def __init__(self, service_name: str, module_name: str):
        self.service_name = service_name
        self.module_name = module_name
        self.logger = logging.getLogger(f"{service_name}.{module_name}")
        
        # Configure JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _create_log_entry(self, level: str, message: str, **kwargs):
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service_name,
            "module": self.module_name,
            "message": message,
            "context": kwargs.get('context', {}),
            "correlation_id": kwargs.get('correlation_id'),
            "trace_id": kwargs.get('trace_id'),
            "labels": {
                "environment": kwargs.get('environment', 'production'),
                "cluster": "crypto-data-collection",
                "namespace": "crypto-collectors"
            }
        }
    
    def info(self, message: str, **kwargs):
        log_entry = self._create_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(log_entry))
    
    def error(self, message: str, **kwargs):
        log_entry = self._create_log_entry("ERROR", message, **kwargs)
        if 'exception' in kwargs:
            log_entry['exception'] = str(kwargs['exception'])
            log_entry['stack_trace'] = kwargs.get('stack_trace')
        self.logger.error(json.dumps(log_entry))
    
    def warn(self, message: str, **kwargs):
        log_entry = self._create_log_entry("WARN", message, **kwargs)
        self.logger.warning(json.dumps(log_entry))

# Usage example
logger = StructuredLogger("crypto-prices-collector", "price_collector")

async def collect_prices():
    correlation_id = str(uuid.uuid4())
    
    logger.info(
        "Starting price collection",
        correlation_id=correlation_id,
        context={
            "symbols_requested": 35,
            "api_provider": "coingecko"
        }
    )
    
    try:
        prices = await fetch_prices()
        logger.info(
            "Price collection completed successfully",
            correlation_id=correlation_id,
            context={
                "symbols_collected": len(prices),
                "collection_duration_ms": duration,
                "records_stored": len(prices)
            }
        )
    except Exception as e:
        logger.error(
            "Price collection failed",
            correlation_id=correlation_id,
            context={
                "error_type": type(e).__name__,
                "symbols_attempted": 35
            },
            exception=e
        )
```

## 📊 **Log Aggregation with ELK Stack**

### **Elasticsearch Configuration**
```yaml
# elasticsearch.yml
cluster.name: crypto-data-collection-logs
node.name: elasticsearch-1
network.host: 0.0.0.0
discovery.type: single-node

# Index template for crypto logs
PUT _index_template/crypto-logs
{
  "index_patterns": ["crypto-logs-*"],
  "template": {
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "service": {"type": "keyword"},
        "module": {"type": "keyword"},
        "message": {"type": "text"},
        "context": {"type": "object"},
        "correlation_id": {"type": "keyword"},
        "trace_id": {"type": "keyword"},
        "labels": {
          "properties": {
            "environment": {"type": "keyword"},
            "cluster": {"type": "keyword"},
            "namespace": {"type": "keyword"}
          }
        }
      }
    }
  }
}
```

### **Logstash Pipeline**
```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [kubernetes][container][name] =~ /crypto-/ {
    json {
      source => "message"
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
      target => "@timestamp"
    }
    
    mutate {
      add_field => { "[@metadata][index]" => "crypto-logs-%{+YYYY.MM.dd}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index]}"
  }
}
```

### **Kibana Dashboards**
```json
{
  "dashboard": {
    "title": "Crypto Data Collection Logs",
    "panels": [
      {
        "title": "Log Volume by Service",
        "type": "histogram",
        "query": "service:crypto-*"
      },
      {
        "title": "Error Rate Trends",
        "type": "line",
        "query": "level:ERROR"
      },
      {
        "title": "Top Error Messages",
        "type": "data_table",
        "query": "level:ERROR",
        "columns": ["timestamp", "service", "message", "context.error_type"]
      }
    ]
  }
}
```

## 🔍 **Distributed Tracing**

### **Jaeger Integration**
```python
from jaeger_client import Config
from opentracing.ext import tags
import opentracing

def init_tracer(service_name: str):
    config = Config(
        config={
            'sampler': {'type': 'const', 'param': 1},
            'logging': True,
        },
        service_name=service_name,
    )
    return config.initialize_tracer()

tracer = init_tracer('crypto-prices-collector')

class TracedCollector:
    async def collect_data_with_tracing(self, symbol: str):
        with tracer.start_span('collect_data') as span:
            span.set_tag('symbol', symbol)
            span.set_tag('collector', 'crypto-prices')
            
            try:
                # External API call
                with tracer.start_span('external_api_call', child_of=span) as api_span:
                    api_span.set_tag('provider', 'coingecko')
                    api_span.set_tag('endpoint', '/simple/price')
                    data = await self.fetch_from_api(symbol)
                
                # Database storage
                with tracer.start_span('database_store', child_of=span) as db_span:
                    db_span.set_tag('database', 'mysql')
                    db_span.set_tag('table', 'price_data')
                    await self.store_data(data)
                
                span.set_tag('success', True)
                return data
                
            except Exception as e:
                span.set_tag('error', True)
                span.set_tag('error.message', str(e))
                span.log_kv({'event': 'error', 'error.object': e})
                raise
```

## 📱 **Health Checks & Probes**

### **Kubernetes Health Checks**
```yaml
# Deployment with health checks
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crypto-prices-collector
spec:
  template:
    spec:
      containers:
      - name: collector
        image: crypto-prices-collector:latest
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
```

### **Health Check Implementation**
```python
from fastapi import FastAPI, HTTPException
import asyncio
import mysql.connector
import redis

app = FastAPI()

class HealthChecker:
    def __init__(self):
        self.dependencies = {
            'mysql': self.check_mysql,
            'redis': self.check_redis,
            'external_api': self.check_external_api
        }
    
    async def check_mysql(self) -> bool:
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True
        except Exception:
            return False
    
    async def check_redis(self) -> bool:
        try:
            r = redis.Redis(**redis_config)
            return r.ping()
        except Exception:
            return False
    
    async def check_external_api(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.coingecko.com/api/v3/ping') as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def run_health_checks(self):
        results = {}
        for name, check in self.dependencies.items():
            try:
                results[name] = await check()
            except Exception:
                results[name] = False
        return results

health_checker = HealthChecker()

@app.get("/health")
async def health_check():
    checks = await health_checker.run_health_checks()
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    status_code = 200 if overall_status == "healthy" else 503
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "uptime_seconds": get_uptime_seconds()
    }

@app.get("/ready")
async def readiness_check():
    # Simpler check for readiness
    essential_checks = await health_checker.run_health_checks()
    
    # Service is ready if MySQL and core APIs are available
    ready = essential_checks.get('mysql', False)
    status_code = 200 if ready else 503
    
    return {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 🔧 **Operational Procedures**

### **Daily Operations Checklist**
```markdown
## Daily Data Collection Health Check

### Service Status
- [ ] All collector services running (14/14)
- [ ] API Gateway responding
- [ ] Database connections healthy
- [ ] Redis cache operational

### Data Quality
- [ ] Price data freshness < 5 minutes
- [ ] News collection within last hour
- [ ] Sentiment analysis current
- [ ] No missing data gaps > 1 hour

### External Dependencies
- [ ] CoinGecko API quota > 20%
- [ ] FRED API operational
- [ ] Guardian API responding
- [ ] OpenAI API within limits

### Performance Metrics
- [ ] Average response time < 500ms
- [ ] Error rate < 1%
- [ ] CPU usage < 70%
- [ ] Memory usage < 80%

### Business Metrics
- [ ] Symbol coverage at 100%
- [ ] SLA compliance > 99%
- [ ] Data completeness > 95%
```

### **Incident Response Procedures**

#### **Service Down Incident**
```bash
# 1. Identify failed service
kubectl get pods -n crypto-collectors

# 2. Check service logs
kubectl logs -n crypto-collectors deployment/FAILED_SERVICE --tail=100

# 3. Check resource usage
kubectl top pods -n crypto-collectors

# 4. Restart service if needed
kubectl rollout restart deployment/FAILED_SERVICE -n crypto-collectors

# 5. Verify recovery
kubectl get pods -n crypto-collectors
curl http://FAILED_SERVICE.crypto-collectors.svc.cluster.local:8080/health

# 6. Update incident tracking
# Document root cause and resolution
```

#### **Data Quality Incident**
```bash
# 1. Check data freshness
curl http://data-api-gateway:8000/api/v1/stats/collectors

# 2. Identify affected symbols/sources
mysql -h host.docker.internal -u news_collector -p99Rules! crypto_prices \
  -e "SELECT symbol, MAX(timestamp) as latest FROM price_data GROUP BY symbol ORDER BY latest;"

# 3. Manual data collection trigger
kubectl exec -n crypto-collectors deployment/crypto-prices-collector -- \
  python -c "import collect; collect.run_manual_collection(['bitcoin', 'ethereum'])"

# 4. Verify data recovery
# Check freshness metrics in Grafana
```

### **Capacity Planning**
```yaml
# Resource scaling guidelines
scaling_rules:
  cpu_threshold: 70%
  memory_threshold: 80%
  
  collectors:
    min_replicas: 1
    max_replicas: 5
    scale_up_trigger: "avg_cpu > 70% for 5m"
    scale_down_trigger: "avg_cpu < 30% for 10m"
  
  api_gateway:
    min_replicas: 2
    max_replicas: 10
    scale_up_trigger: "requests_per_second > 100"
    scale_down_trigger: "requests_per_second < 20"
  
  processing_services:
    min_replicas: 1
    max_replicas: 3
    scale_up_trigger: "queue_depth > 100"
    scale_down_trigger: "queue_depth < 10"
```

This comprehensive monitoring and observability setup ensures the crypto data collection system operates reliably with full visibility into performance, data quality, and system health.