# 📊 Monitoring Setup Guide

## Overview

This guide explains how to set up and use the comprehensive monitoring stack for the crypto data collection system.

## Monitoring Architecture

### Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Dashboards and visualization
- **Performance Monitor**: Real-time performance tracking
- **Cost Tracker**: Resource cost estimation
- **Cache Manager**: Redis cache monitoring
- **Resource Monitor**: Resource usage tracking
- **Metrics Server**: Kubernetes metrics for HPA

## Accessing Monitoring Services

### 1. Prometheus (Metrics Collection)

```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection

# Access Prometheus UI
# URL: http://localhost:9090
```

**Key Features:**
- Metrics collection from all services
- Query interface (PromQL)
- Alert rules and notifications
- Service discovery

**Useful Queries:**
```promql
# System health score
performance_score

# Service response times
service_response_time_seconds

# Database connections
database_connections_active

# Redis memory usage
redis_memory_usage_bytes

# Cost estimation
cost_total_usd_per_hour
```

### 2. Grafana (Dashboards)

```bash
# Port forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n crypto-data-collection

# Access Grafana UI
# URL: http://localhost:3000
# Credentials: admin/admin123
```

**Pre-configured Dashboards:**
- **Data Collection Overview**: System health and performance
- **Performance Monitoring**: Resource usage and optimization
- **Cost Tracking**: Resource costs and optimization scores

### 3. Performance Monitor (Real-time Tracking)

```bash
# Port forward Performance Monitor
kubectl port-forward svc/performance-monitor 8005:8000 -n crypto-data-collection

# Access Performance Monitor
# URL: http://localhost:8005
```

**Endpoints:**
- `/health`: Service health status
- `/performance`: Performance summary
- `/metrics`: Prometheus metrics

**Performance Metrics:**
- Overall performance score (0-100)
- Database connections and size
- Redis connections and memory
- Service count and status

### 4. Cost Tracker (Resource Costs)

```bash
# Port forward Cost Tracker
kubectl port-forward svc/cost-tracker 8006:8000 -n crypto-data-collection

# Access Cost Tracker
# URL: http://localhost:8006
```

**Endpoints:**
- `/health`: Service health status
- `/costs`: Cost summary
- `/metrics`: Prometheus metrics

**Cost Metrics:**
- Total cost per hour/day/month
- Cost breakdown by resource type
- Optimization score
- Resource efficiency

### 5. Cache Manager (Redis Monitoring)

```bash
# Port forward Cache Manager
kubectl port-forward svc/cache-manager 8007:8000 -n crypto-data-collection

# Access Cache Manager
# URL: http://localhost:8007
```

**Endpoints:**
- `/health`: Service health status
- `/cache/status`: Cache status for all types
- `/cache/clear/{cache_type}`: Clear specific cache
- `/cache/optimize`: Optimize all caches
- `/metrics`: Prometheus metrics

**Cache Types:**
- `price_data`: 5-minute TTL, 1000 max keys
- `news_data`: 15-minute TTL, 500 max keys
- `sentiment_data`: 30-minute TTL, 200 max keys

## Dashboard Configuration

### Grafana Dashboards

#### 1. Data Collection Overview Dashboard
- **System Health Score**: Overall performance (0-100)
- **Service Status**: All services running status
- **Data Collection Rates**: Price, news, sentiment collection
- **Error Rates**: Service error tracking
- **Database Performance**: Connections, size, query performance

#### 2. Performance Monitoring Dashboard
- **CPU Usage**: By pod and node
- **Memory Usage**: By pod and node
- **Resource Efficiency**: CPU and memory efficiency
- **HPA Status**: Autoscaling metrics
- **Service Response Times**: API response times

#### 3. Cost Tracking Dashboard
- **Total Costs**: Hourly, daily, monthly costs
- **Cost Breakdown**: By resource type (CPU, memory, storage, network)
- **Optimization Score**: Cost optimization metrics
- **Resource Usage**: CPU cores, memory GB, storage GB

### Prometheus Alerts

#### Critical Alerts
- **Service Down**: Any service pod not running
- **High Error Rate**: Service error rate > 5%
- **High Resource Usage**: CPU > 80% or Memory > 80%
- **Database Issues**: Connection failures or high query time
- **Cache Issues**: High cache miss rate or memory usage

#### Warning Alerts
- **Performance Degradation**: Performance score < 90
- **High Costs**: Cost per hour > $1.00
- **Resource Quota**: Approaching resource limits
- **Data Freshness**: Data older than expected

## Monitoring Best Practices

### 1. Regular Monitoring
- Check system health score daily (should be 100/100)
- Monitor resource usage trends
- Review error logs weekly
- Analyze cost trends monthly

### 2. Alert Management
- Set up notification channels (email, Slack)
- Configure alert severity levels
- Test alert delivery regularly
- Review and tune alert thresholds

### 3. Performance Optimization
- Monitor HPA scaling behavior
- Track resource efficiency metrics
- Optimize cache hit rates
- Review cost optimization scores

### 4. Troubleshooting
- Use Prometheus queries to investigate issues
- Check Grafana dashboards for trends
- Review service-specific metrics
- Correlate metrics across services

## Advanced Monitoring

### Custom Metrics

#### Adding Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Custom counter
custom_requests = Counter('custom_requests_total', 'Total custom requests', ['service'])

# Custom histogram
custom_duration = Histogram('custom_duration_seconds', 'Custom operation duration')

# Custom gauge
custom_value = Gauge('custom_value', 'Custom metric value')
```

#### Custom Dashboards
1. Access Grafana UI
2. Create new dashboard
3. Add panels with Prometheus queries
4. Configure alerts and notifications

### Log Monitoring

#### Structured Logging
All services use structured JSON logging:
```json
{
  "timestamp": "2025-10-15T15:50:00Z",
  "level": "INFO",
  "service": "enhanced-crypto-prices",
  "message": "Price collection completed",
  "records_collected": 92,
  "duration_seconds": 23.4
}
```

#### Log Analysis
```bash
# View service logs
kubectl logs -n crypto-data-collection <pod-name> --tail=100

# Filter logs by level
kubectl logs -n crypto-data-collection <pod-name> | grep ERROR

# Follow logs in real-time
kubectl logs -n crypto-data-collection <pod-name> -f
```

## Troubleshooting Monitoring

### Common Issues

#### 1. Prometheus Targets Down
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check service annotations
kubectl get pods -n crypto-data-collection -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.prometheus\.io/scrape}{"\n"}{end}'
```

#### 2. Grafana Dashboard Issues
```bash
# Check Grafana logs
kubectl logs -n crypto-data-collection grafana-<pod-id>

# Verify Prometheus datasource
# Go to Grafana UI > Configuration > Data Sources
```

#### 3. Metrics Not Appearing
```bash
# Check metrics endpoint
kubectl exec -n crypto-data-collection <pod-name> -- curl http://localhost:8000/metrics

# Check Prometheus configuration
kubectl get configmap prometheus-config -n crypto-data-collection -o yaml
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n crypto-data-collection

# Check Prometheus memory
kubectl exec -n crypto-data-collection prometheus-<pod-id> -- ps aux
```

#### Slow Queries
```bash
# Check Prometheus query performance
# Use Prometheus UI > Status > Targets
# Look for slow scrape times
```

## Security Considerations

### Access Control
- Use RBAC for Kubernetes access
- Secure Prometheus and Grafana access
- Rotate API keys regularly
- Monitor access logs

### Data Protection
- Encrypt metrics data in transit
- Secure dashboard access
- Protect sensitive configuration
- Regular security audits

## Backup and Recovery

### Configuration Backup
```bash
# Backup Prometheus configuration
kubectl get configmap prometheus-config -n crypto-data-collection -o yaml > prometheus-config-backup.yaml

# Backup Grafana dashboards
kubectl get configmap grafana-dashboards -n crypto-data-collection -o yaml > grafana-dashboards-backup.yaml
```

### Metrics Backup
```bash
# Backup Prometheus data (if using persistent volumes)
kubectl exec -n crypto-data-collection prometheus-<pod-id> -- tar -czf /tmp/prometheus-data-backup.tar.gz /prometheus
kubectl cp crypto-data-collection/prometheus-<pod-id>:/tmp/prometheus-data-backup.tar.gz ./prometheus-data-backup.tar.gz
```

## Maintenance

### Regular Tasks
- **Daily**: Check system health and alerts
- **Weekly**: Review performance trends and optimize
- **Monthly**: Update dashboards and review costs
- **Quarterly**: Security audit and backup verification

### Updates
- Keep Prometheus and Grafana updated
- Review and update alert rules
- Optimize dashboard performance
- Update monitoring documentation

## Support

### Getting Help
1. Check this documentation
2. Review service logs
3. Check Prometheus targets and queries
4. Contact system administrator

### Useful Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kubernetes Monitoring](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)