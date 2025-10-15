# Production Operations Guide
# ===========================

## Overview

This guide provides operational procedures for the Crypto Data Collection system in production. It covers common issues, troubleshooting steps, and maintenance procedures.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Data Collection │    │   Analytics     │
│                 │    │     Node         │    │     Node        │
│ • RSS Feeds     │───▶│ • News Collector │    │ • Prometheus    │
│ • CryptoPanic   │    │ • Sentiment      │    │ • Grafana       │
│ • CoinGecko     │    │ • Price Collector│    │ • Alertmanager  │
│ • Coinbase      │    │ • Health Monitor │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Windows Host  │
                       │                 │
                       │ • MySQL Server  │
                       │ • Redis Cache   │
                       └─────────────────┘
```

## Service Status Commands

### Check All Services
```bash
# Check pod status
kubectl get pods -n crypto-data-collection

# Check service health
kubectl get svc -n crypto-data-collection

# Check node status
kubectl get nodes --show-labels
```

### Individual Service Health
```bash
# Enhanced Crypto Prices
kubectl port-forward svc/enhanced-crypto-prices 8001:8000 -n crypto-data-collection
curl http://localhost:8001/health

# News Collector
kubectl port-forward svc/crypto-news-collector 8002:8000 -n crypto-data-collection
curl http://localhost:8002/health

# Sentiment Collector
kubectl port-forward svc/sentiment-collector 8003:8000 -n crypto-data-collection
curl http://localhost:8003/health

# Health Monitor
kubectl port-forward svc/data-collection-health-monitor 8004:8000 -n crypto-data-collection
curl http://localhost:8004/health
```

## Common Issues and Solutions

### 1. Service CrashLoopBackOff

**Symptoms:**
- Pods restarting repeatedly
- `kubectl get pods` shows CrashLoopBackOff status

**Diagnosis:**
```bash
# Check pod logs
kubectl logs -n crypto-data-collection deployment/<service-name> --tail=50

# Check pod events
kubectl describe pod -n crypto-data-collection <pod-name>
```

**Common Causes:**
- Database connection issues
- Missing environment variables
- Resource limits exceeded
- Application startup errors

**Solutions:**
1. **Database Connection Issues:**
   ```bash
   # Verify MySQL is running on Windows host
   # Check centralized config
   kubectl get configmap centralized-db-config -n crypto-data-collection -o yaml
   
   # Test database connectivity
   kubectl exec -it -n crypto-data-collection <pod-name> -- python -c "
   import mysql.connector
   conn = mysql.connector.connect(
       host='host.docker.internal',
       user='news_collector',
       password='99Rules!',
       database='crypto_prices'
   )
   print('Database connection successful')
   conn.close()
   "
   ```

2. **Resource Issues:**
   ```bash
   # Check resource usage
   kubectl top pods -n crypto-data-collection
   
   # Increase resource limits in deployment YAML
   kubectl edit deployment <service-name> -n crypto-data-collection
   ```

3. **Environment Variables:**
   ```bash
   # Check environment variables
   kubectl exec -it -n crypto-data-collection <pod-name> -- env | grep -E "(MYSQL|REDIS)"
   ```

### 2. Data Collection Stopped

**Symptoms:**
- No new data in database
- Health monitor shows stale data alerts

**Diagnosis:**
```bash
# Check data freshness
kubectl port-forward svc/data-collection-health-monitor 8004:8000 -n crypto-data-collection
curl http://localhost:8004/status

# Check database directly
mysql -h localhost -u news_collector -p99Rules! crypto_prices -e "
SELECT 
    MAX(timestamp_iso) as latest_price,
    COUNT(*) as total_records
FROM price_data_real 
WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR);
"
```

**Solutions:**
1. **Restart Collection Services:**
   ```bash
   kubectl rollout restart deployment/enhanced-crypto-prices -n crypto-data-collection
   kubectl rollout restart deployment/crypto-news-collector -n crypto-data-collection
   ```

2. **Check API Rate Limits:**
   ```bash
   # Check service logs for rate limit errors
   kubectl logs -n crypto-data-collection deployment/enhanced-crypto-prices --tail=100 | grep -i "rate\|limit\|quota"
   ```

3. **Verify External APIs:**
   ```bash
   # Test CoinGecko API
   curl "https://api.coingecko.com/api/v3/ping"
   
   # Test Coinbase API
   curl "https://api.coinbase.com/v2/time"
   ```

### 3. Database Connection Issues

**Symptoms:**
- Services can't connect to MySQL
- Database-related errors in logs

**Diagnosis:**
```bash
# Check MySQL service on Windows host
# Verify MySQL is running and accessible
netstat -an | findstr :3306

# Test connection from Kubernetes
kubectl run mysql-test --image=mysql:8.0 --rm -it --restart=Never -- \
  mysql -h host.docker.internal -u news_collector -p99Rules! crypto_prices -e "SELECT 1"
```

**Solutions:**
1. **MySQL Service Issues:**
   ```bash
   # On Windows host, restart MySQL service
   net stop mysql
   net start mysql
   
   # Check MySQL logs
   # Windows: C:\ProgramData\MySQL\MySQL Server 8.0\Data\*.err
   ```

2. **Network Connectivity:**
   ```bash
   # Test host.docker.internal resolution
   kubectl run network-test --image=busybox --rm -it --restart=Never -- \
     nslookup host.docker.internal
   ```

3. **Authentication Issues:**
   ```bash
   # Verify user exists and has correct permissions
   mysql -h localhost -u root -p -e "
   SELECT User, Host FROM mysql.user WHERE User='news_collector';
   SHOW GRANTS FOR 'news_collector'@'%';
   "
   ```

### 4. Monitoring Issues

**Symptoms:**
- Prometheus not scraping metrics
- Grafana dashboards not updating
- Alerts not firing

**Diagnosis:**
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection
# Open http://localhost:9090/targets

# Check Grafana datasource
kubectl port-forward svc/grafana 3000:3000 -n crypto-data-collection
# Open http://localhost:3000 (admin/admin123)
```

**Solutions:**
1. **Prometheus Configuration:**
   ```bash
   # Check Prometheus config
   kubectl get configmap prometheus-config -n crypto-data-collection -o yaml
   
   # Reload Prometheus config
   kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection
   curl -X POST http://localhost:9090/-/reload
   ```

2. **Service Discovery Issues:**
   ```bash
   # Check pod annotations
   kubectl get pods -n crypto-data-collection -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.prometheus\.io/scrape}{"\n"}{end}'
   ```

## Maintenance Procedures

### Daily Checks

1. **Service Health:**
   ```bash
   # Quick health check
   kubectl get pods -n crypto-data-collection
   
   # Check health monitor status
   kubectl port-forward svc/data-collection-health-monitor 8004:8000 -n crypto-data-collection
   curl http://localhost:8004/status
   ```

2. **Data Freshness:**
   ```bash
   # Check latest data timestamps
   mysql -h localhost -u news_collector -p99Rules! crypto_prices -e "
   SELECT 
       'price_data' as table_name,
       MAX(timestamp_iso) as latest_data,
       COUNT(*) as total_records
   FROM price_data_real 
   WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR)
   UNION ALL
   SELECT 
       'ml_features' as table_name,
       MAX(timestamp_iso) as latest_data,
       COUNT(*) as total_records
   FROM ml_features_materialized 
   WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR);
   "
   ```

3. **Error Rates:**
   ```bash
   # Check for errors in logs
   kubectl logs -n crypto-data-collection deployment/enhanced-crypto-prices --since=1h | grep -i error | wc -l
   kubectl logs -n crypto-data-collection deployment/crypto-news-collector --since=1h | grep -i error | wc -l
   ```

### Weekly Maintenance

1. **Database Maintenance:**
   ```bash
   # Check database size and performance
   mysql -h localhost -u news_collector -p99Rules! crypto_prices -e "
   SELECT 
       table_name,
       ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)',
       table_rows
   FROM information_schema.tables 
   WHERE table_schema = 'crypto_prices'
   ORDER BY (data_length + index_length) DESC;
   "
   
   # Clean up old data (optional)
   mysql -h localhost -u news_collector -p99Rules! crypto_prices -e "
   DELETE FROM price_data_real 
   WHERE timestamp_iso < DATE_SUB(NOW(), INTERVAL 30 DAY);
   
   DELETE FROM crypto_news 
   WHERE published_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
   "
   ```

2. **Log Rotation:**
   ```bash
   # Check log sizes
   kubectl exec -n crypto-data-collection deployment/enhanced-crypto-prices -- du -sh /var/log/*
   
   # Restart services to rotate logs
   kubectl rollout restart deployment/enhanced-crypto-prices -n crypto-data-collection
   kubectl rollout restart deployment/crypto-news-collector -n crypto-data-collection
   kubectl rollout restart deployment/sentiment-collector -n crypto-data-collection
   ```

### Monthly Maintenance

1. **Security Updates:**
   ```bash
   # Update base images
   kubectl set image deployment/enhanced-crypto-prices enhanced-crypto-prices=python:3.11-slim -n crypto-data-collection
   kubectl set image deployment/crypto-news-collector crypto-news-collector=python:3.11-slim -n crypto-data-collection
   kubectl set image deployment/sentiment-collector sentiment-collector=python:3.11-slim -n crypto-data-collection
   ```

2. **Performance Review:**
   ```bash
   # Check resource usage trends
   kubectl top pods -n crypto-data-collection --sort-by=memory
   kubectl top pods -n crypto-data-collection --sort-by=cpu
   
   # Review Prometheus metrics
   # Access Grafana dashboards and review performance trends
   ```

## Emergency Procedures

### Complete System Restart

1. **Stop All Services:**
   ```bash
   kubectl scale deployment --replicas=0 --all -n crypto-data-collection
   ```

2. **Restart in Order:**
   ```bash
   # Start core services first
   kubectl scale deployment enhanced-crypto-prices --replicas=1 -n crypto-data-collection
   kubectl scale deployment materialized-updater --replicas=1 -n crypto-data-collection
   
   # Wait for core services to be ready
   kubectl wait --for=condition=available deployment/enhanced-crypto-prices -n crypto-data-collection --timeout=300s
   
   # Start secondary services
   kubectl scale deployment crypto-news-collector --replicas=1 -n crypto-data-collection
   kubectl scale deployment sentiment-collector --replicas=1 -n crypto-data-collection
   kubectl scale deployment data-collection-health-monitor --replicas=1 -n crypto-data-collection
   ```

### Database Recovery

1. **Backup Current State:**
   ```bash
   mysqldump -h localhost -u news_collector -p99Rules! crypto_prices > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Restore from Backup:**
   ```bash
   mysql -h localhost -u news_collector -p99Rules! crypto_prices < backup_20231014_120000.sql
   ```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Service Health:**
   - `up{job="crypto-data-collection-services"}` - Service availability
   - `health_score` - Overall system health
   - `service_availability` - Individual service status

2. **Data Quality:**
   - `data_freshness_seconds` - Data age
   - `news_collection_requests_total` - Collection rate
   - `sentiment_analysis_total` - Analysis rate

3. **Performance:**
   - `http_request_duration_seconds` - Response times
   - `database_connections_active` - DB connections
   - `circuit_breaker_state` - Circuit breaker status

### Alert Thresholds

- **Critical:** Health score < 60, Data age > 2 hours, Service down > 1 minute
- **Warning:** Health score < 80, Data age > 1 hour, High error rate > 10%

### Notification Channels

- **Critical Alerts:** Email + Slack #alerts-critical
- **Warning Alerts:** Email + Slack #alerts-warning  
- **Data Collection:** Slack #data-collection

## Troubleshooting Checklist

### Before Escalating

1. ✅ Check pod status: `kubectl get pods -n crypto-data-collection`
2. ✅ Check service logs: `kubectl logs -n crypto-data-collection deployment/<service> --tail=50`
3. ✅ Verify database connectivity
4. ✅ Check external API availability
5. ✅ Review Prometheus targets and alerts
6. ✅ Check resource usage: `kubectl top pods -n crypto-data-collection`
7. ✅ Verify configuration: `kubectl get configmap -n crypto-data-collection`

### Escalation Contacts

- **Level 1:** Data Collection Team (Slack #data-collection)
- **Level 2:** Platform Team (Slack #platform)
- **Level 3:** On-call Engineer (PagerDuty)

## Useful Commands Reference

```bash
# Service Management
kubectl get pods -n crypto-data-collection
kubectl logs -n crypto-data-collection deployment/<service> --tail=100
kubectl describe pod -n crypto-data-collection <pod-name>
kubectl rollout restart deployment/<service> -n crypto-data-collection

# Port Forwarding
kubectl port-forward svc/enhanced-crypto-prices 8001:8000 -n crypto-data-collection
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection
kubectl port-forward svc/grafana 3000:3000 -n crypto-data-collection

# Database Access
mysql -h localhost -u news_collector -p99Rules! crypto_prices

# Monitoring
kubectl top pods -n crypto-data-collection
kubectl get events -n crypto-data-collection --sort-by='.lastTimestamp'
```

## Documentation Links

- [Monitoring Setup Guide](MONITORING_SETUP.md)
- [Quick Status Reference](../QUICK_STATUS_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md)
