# Monitoring Setup Guide
# ======================

## Overview

This guide explains how to set up and configure the monitoring stack for the Crypto Data Collection system, including Prometheus, Grafana, and Alertmanager.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Collection │    │   Analytics     │    │   Alerting      │
│     Node         │    │     Node        │    │                 │
│                 │    │                 │    │                 │
│ • News Collector │───▶│ • Prometheus    │───▶│ • Alertmanager  │
│ • Sentiment     │    │ • Grafana       │    │ • Notifications │
│ • Price Collector│    │ • Dashboards    │    │                 │
│ • Health Monitor│    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

1. **Kubernetes Cluster** with Kind
2. **Analytics Node** properly labeled
3. **Data Collection Services** deployed and running
4. **Network Connectivity** between nodes

## Deployment Steps

### 1. Deploy Monitoring Stack

```bash
# Apply all monitoring components
kubectl apply -f k8s/monitoring/prometheus-config.yaml
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml
kubectl apply -f k8s/monitoring/alertmanager-config.yaml
```

### 2. Verify Deployments

```bash
# Check all monitoring pods are running
kubectl get pods -n crypto-data-collection -l component=monitoring

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# prometheus-xxx                 1/1     Running   0          2m
# grafana-xxx                    1/1     Running   0          2m
# alertmanager-xxx               1/1     Running   0          2m
```

### 3. Access Monitoring UIs

```bash
# Prometheus UI
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection
# Open: http://localhost:9090

# Grafana UI
kubectl port-forward svc/grafana 3000:3000 -n crypto-data-collection
# Open: http://localhost:3000
# Login: admin / admin123

# Alertmanager UI
kubectl port-forward svc/alertmanager 9093:9093 -n crypto-data-collection
# Open: http://localhost:9093
```

## Configuration Details

### Prometheus Configuration

**File:** `k8s/monitoring/prometheus-config.yaml`

**Key Features:**
- Automatic service discovery for data collection services
- Kubernetes API server and node monitoring
- Custom alert rules for crypto data collection
- 15-day data retention

**Scrape Targets:**
- `crypto-data-collection-services` - All data collection services
- `kubernetes-apiservers` - Kubernetes API server metrics
- `kubernetes-nodes` - Node-level metrics
- `kubernetes-pods` - Pod-level metrics
- `kubernetes-cadvisor` - Container metrics

### Grafana Configuration

**File:** `k8s/monitoring/grafana-deployment.yaml`

**Key Features:**
- Pre-configured Prometheus datasource
- Crypto Data Collection dashboard
- Admin user: `admin` / `admin123`
- Dashboard auto-provisioning

**Dashboard Panels:**
1. **System Health Scores** - Overall health metrics
2. **Service Availability** - Service up/down status
3. **Data Freshness** - Data age monitoring
4. **News Collection Rate** - Collection performance
5. **Sentiment Analysis Rate** - Analysis performance
6. **Database Connections** - DB connection monitoring
7. **Error Rates** - Error tracking
8. **Circuit Breaker States** - Resilience monitoring

### Alertmanager Configuration

**File:** `k8s/monitoring/alertmanager-config.yaml`

**Key Features:**
- Multi-channel alerting (Email, Slack)
- Alert grouping and routing
- Inhibition rules to reduce noise
- Template-based alert formatting

**Alert Routes:**
- **Critical Alerts** → Immediate notification
- **Warning Alerts** → Less frequent notification
- **Data Collection Alerts** → Dedicated team channel

## Service Integration

### Prometheus Metrics

All data collection services expose metrics on `/metrics` endpoint:

**News Collector Metrics:**
```
news_collection_requests_total{source, status}
news_collection_duration_seconds{source}
news_collection_errors_total{source, error_type}
news_items_stored_total{source}
news_sources_active
circuit_breaker_state{source}
```

**Sentiment Collector Metrics:**
```
sentiment_analysis_total{source, model}
sentiment_analysis_duration_seconds{model}
sentiment_score_distribution{source, model}
sentiment_sources_processed_total{source}
sentiment_errors_total{source, error_type}
sentiment_cache_hits_total{source}
```

**Health Monitor Metrics:**
```
health_check_total{component, status}
health_check_duration_seconds{component}
health_score{component}
data_freshness_seconds{data_type}
service_availability{service}
database_connections_active{database}
```

### Service Annotations

All services include Prometheus annotations for auto-discovery:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics"
    prometheus.io/port: "8000"
```

## Alert Rules

### Critical Alerts

1. **ServiceDown** - Service unavailable for > 1 minute
2. **DataVeryStale** - Data older than 2 hours
3. **HealthScoreCritical** - Health score < 60
4. **DatabaseDown** - Database connection failed
5. **NewsSourcesDown** - Too many news sources offline

### Warning Alerts

1. **ServiceHighErrorRate** - Error rate > 10%
2. **DataStale** - Data older than 1 hour
3. **HealthScoreLow** - Health score < 80
4. **DatabaseConnectionsHigh** - Too many DB connections
5. **CircuitBreakerOpen** - Circuit breaker activated

## Dashboard Usage

### Crypto Data Collection Dashboard

**Access:** Grafana → Dashboards → Crypto Data Collection

**Key Panels:**

1. **System Health Scores**
   - Shows health score for each component (0-100)
   - Green: > 80, Yellow: 60-80, Red: < 60

2. **Service Availability**
   - Real-time service up/down status
   - Green: Up, Red: Down

3. **Data Freshness**
   - Age of data in seconds
   - Alert if > 3600 seconds (1 hour)

4. **Collection Rates**
   - Requests per second for news and sentiment
   - Shows system throughput

5. **Error Rates**
   - Error rate per service
   - Helps identify problematic sources

6. **Circuit Breaker States**
   - Resilience status (0=closed, 1=open, 2=half-open)
   - Indicates service degradation

### Custom Queries

**Check specific service health:**
```promql
health_score{component="enhanced-crypto-prices"}
```

**Monitor data collection rate:**
```promql
rate(news_collection_requests_total[5m])
```

**Check error rates:**
```promql
rate(news_collection_errors_total[5m]) / rate(news_collection_requests_total[5m])
```

## Troubleshooting

### Prometheus Issues

**Problem:** Targets not showing up
```bash
# Check service discovery
kubectl get pods -n crypto-data-collection -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.prometheus\.io/scrape}{"\n"}{end}'

# Verify Prometheus config
kubectl get configmap prometheus-config -n crypto-data-collection -o yaml
```

**Problem:** Metrics not being scraped
```bash
# Check target status in Prometheus UI
# Go to Status → Targets

# Test metrics endpoint manually
kubectl port-forward svc/enhanced-crypto-prices 8001:8000 -n crypto-data-collection
curl http://localhost:8001/metrics
```

### Grafana Issues

**Problem:** Dashboard not loading
```bash
# Check Grafana logs
kubectl logs -n crypto-data-collection deployment/grafana

# Verify datasource configuration
# Go to Configuration → Data Sources → Prometheus
```

**Problem:** No data in panels
```bash
# Check Prometheus datasource
# Verify URL: http://prometheus.crypto-data-collection.svc.cluster.local:9090

# Test query in Prometheus UI first
# Then use same query in Grafana
```

### Alertmanager Issues

**Problem:** Alerts not firing
```bash
# Check Prometheus alert rules
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection
# Go to Alerts tab

# Check Alertmanager configuration
kubectl get configmap alertmanager-config -n crypto-data-collection -o yaml
```

**Problem:** Notifications not received
```bash
# Check Alertmanager logs
kubectl logs -n crypto-data-collection deployment/alertmanager

# Test webhook endpoint
curl -X POST http://localhost:9093/api/v1/alerts -d '[{"labels":{"alertname":"TestAlert"}}]'
```

## Performance Tuning

### Prometheus Tuning

**Memory Usage:**
```yaml
# In prometheus-deployment.yaml
resources:
  requests:
    memory: 512Mi
  limits:
    memory: 2Gi
```

**Retention:**
```yaml
# In prometheus-config.yaml
args:
  - '--storage.tsdb.retention.time=15d'
```

### Grafana Tuning

**Refresh Intervals:**
- Dashboard: 30s
- Individual panels: 15s
- Time range: 1 hour default

**Data Source Settings:**
- Scrape interval: 15s
- Query timeout: 60s
- Max concurrent queries: 20

## Security Considerations

### Access Control

**Grafana:**
- Change default admin password
- Create service accounts for automation
- Use LDAP/SSO integration for production

**Prometheus:**
- Enable authentication for production
- Use TLS for external access
- Restrict network access

**Alertmanager:**
- Secure webhook endpoints
- Use authentication for API access
- Encrypt sensitive configuration

### Network Security

```bash
# Create network policies
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: monitoring-network-policy
  namespace: crypto-data-collection
spec:
  podSelector:
    matchLabels:
      component: monitoring
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: crypto-data-collection
    ports:
    - protocol: TCP
      port: 9090  # Prometheus
    - protocol: TCP
      port: 3000  # Grafana
    - protocol: TCP
      port: 9093  # Alertmanager
EOF
```

## Backup and Recovery

### Prometheus Data

```bash
# Backup Prometheus data
kubectl exec -n crypto-data-collection deployment/prometheus -- tar czf /tmp/prometheus-backup.tar.gz /prometheus/
kubectl cp crypto-data-collection/prometheus-xxx:/tmp/prometheus-backup.tar.gz ./prometheus-backup.tar.gz

# Restore Prometheus data
kubectl cp ./prometheus-backup.tar.gz crypto-data-collection/prometheus-xxx:/tmp/
kubectl exec -n crypto-data-collection deployment/prometheus -- tar xzf /tmp/prometheus-backup.tar.gz -C /
```

### Grafana Configuration

```bash
# Backup Grafana dashboards
kubectl get configmap grafana-dashboards -n crypto-data-collection -o yaml > grafana-dashboards-backup.yaml

# Restore Grafana dashboards
kubectl apply -f grafana-dashboards-backup.yaml
```

## Monitoring Best Practices

### 1. Alert Fatigue Prevention

- Use appropriate alert thresholds
- Implement alert grouping
- Set up alert inhibition rules
- Regular alert review and cleanup

### 2. Dashboard Design

- Keep dashboards focused and simple
- Use consistent color schemes
- Include context and documentation
- Regular dashboard review and updates

### 3. Performance Monitoring

- Monitor monitoring system itself
- Set up alerts for monitoring failures
- Regular performance reviews
- Capacity planning

### 4. Documentation

- Keep runbooks updated
- Document alert meanings
- Maintain troubleshooting guides
- Regular team training

## Useful Commands

```bash
# Monitoring Stack Management
kubectl get pods -n crypto-data-collection -l component=monitoring
kubectl logs -n crypto-data-collection deployment/prometheus
kubectl logs -n crypto-data-collection deployment/grafana
kubectl logs -n crypto-data-collection deployment/alertmanager

# Port Forwarding
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection
kubectl port-forward svc/grafana 3000:3000 -n crypto-data-collection
kubectl port-forward svc/alertmanager 9093:9093 -n crypto-data-collection

# Configuration Updates
kubectl apply -f k8s/monitoring/prometheus-config.yaml
kubectl apply -f k8s/monitoring/alertmanager-config.yaml

# Reload Configurations
curl -X POST http://localhost:9090/-/reload  # Prometheus
curl -X POST http://localhost:9093/-/reload  # Alertmanager
```

## Next Steps

1. **Custom Dashboards** - Create additional dashboards for specific use cases
2. **Advanced Alerting** - Implement more sophisticated alert rules
3. **Integration** - Connect with external monitoring systems
4. **Automation** - Set up automated responses to common issues
5. **Scaling** - Plan for monitoring system scaling as data grows
