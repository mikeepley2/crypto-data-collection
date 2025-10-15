# 🚀 Production Operations Guide

## Overview

This guide provides operational procedures for the crypto data collection system in production.

## System Architecture

### Core Services
- **enhanced-crypto-prices**: Collects cryptocurrency prices from CoinGecko API
- **crypto-news-collector**: Collects news from 26 RSS sources and APIs
- **sentiment-collector**: Analyzes sentiment from news articles
- **materialized-updater**: Updates materialized views for ML features
- **redis-data-collection**: Provides caching layer

### Monitoring Services
- **performance-monitor**: Real-time performance tracking
- **cost-tracker**: Resource cost estimation and optimization
- **cache-manager**: Intelligent Redis cache management
- **resource-monitor**: Resource usage and quota tracking
- **data-collection-health-monitor**: Overall system health monitoring

### Infrastructure
- **prometheus**: Metrics collection and alerting
- **grafana**: Dashboards and visualization
- **metrics-server**: Kubernetes metrics for HPA
- **mysql**: Primary database (Windows host)
- **redis**: Caching database

## Health Checks

### Service Health Endpoints

```bash
# Check all service health
kubectl get pods -n crypto-data-collection

# Check specific service health
kubectl exec -n crypto-data-collection <pod-name> -- curl http://localhost:8000/health

# Check performance monitor
kubectl port-forward svc/performance-monitor 8005:8000 -n crypto-data-collection
curl http://localhost:8005/performance

# Check cost tracker
kubectl port-forward svc/cost-tracker 8006:8000 -n crypto-data-collection
curl http://localhost:8006/costs
```

### Database Health

```bash
# Check MySQL connection
kubectl exec -n crypto-data-collection enhanced-crypto-prices-<pod-id> -- python -c "
import mysql.connector
import os
conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST', 'host.docker.internal'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_USER', 'news_collector'),
    password=os.getenv('MYSQL_PASSWORD', '99Rules!'),
    database=os.getenv('MYSQL_DATABASE', 'crypto_prices')
)
print('Database connection: OK')
conn.close()
"

# Check Redis connection
kubectl exec -n crypto-data-collection redis-data-collection-<pod-id> -- redis-cli ping
```

## Monitoring Access

### Prometheus
```bash
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection
# Access: http://localhost:9090
```

### Grafana
```bash
kubectl port-forward svc/grafana 3000:3000 -n crypto-data-collection
# Access: http://localhost:3000 (admin/admin123)
```

### Performance Monitor
```bash
kubectl port-forward svc/performance-monitor 8005:8000 -n crypto-data-collection
# Access: http://localhost:8005/performance
```

## Troubleshooting

### Common Issues

#### 1. Pod CrashLoopBackOff
```bash
# Check pod logs
kubectl logs -n crypto-data-collection <pod-name> --previous

# Check pod events
kubectl describe pod -n crypto-data-collection <pod-name>

# Common causes:
# - Database connection issues
# - Missing environment variables
# - Resource limits exceeded
```

#### 2. HPA Not Scaling
```bash
# Check HPA status
kubectl get hpa -n crypto-data-collection

# Check metrics-server
kubectl get pods -n kube-system | grep metrics-server

# Check pod metrics
kubectl top pods -n crypto-data-collection
```

#### 3. Database Connection Issues
```bash
# Check MySQL service on Windows host
# Ensure MySQL is running on port 3306
# Verify firewall allows connections from Kubernetes

# Test connection from pod
kubectl exec -n crypto-data-collection <pod-name> -- telnet host.docker.internal 3306
```

#### 4. Redis Connection Issues
```bash
# Check Redis pod
kubectl get pods -n crypto-data-collection | grep redis

# Check Redis logs
kubectl logs -n crypto-data-collection redis-data-collection-<pod-id>

# Test Redis connection
kubectl exec -n crypto-data-collection redis-data-collection-<pod-id> -- redis-cli ping
```

### Performance Issues

#### High CPU Usage
```bash
# Check resource usage
kubectl top pods -n crypto-data-collection

# Check HPA status
kubectl get hpa -n crypto-data-collection

# Scale manually if needed
kubectl scale deployment <deployment-name> --replicas=2 -n crypto-data-collection
```

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n crypto-data-collection

# Check for memory leaks in logs
kubectl logs -n crypto-data-collection <pod-name> | grep -i memory

# Restart pod if needed
kubectl delete pod -n crypto-data-collection <pod-name>
```

## Maintenance Procedures

### Regular Maintenance

#### Daily
- Check system health score (should be 100/100)
- Verify all services are running
- Check data collection rates
- Review error logs

#### Weekly
- Review resource usage trends
- Check database size and performance
- Verify backup procedures
- Update documentation

#### Monthly
- Review and update API keys
- Analyze cost trends
- Performance optimization review
- Security audit

### Scaling Procedures

#### Manual Scaling
```bash
# Scale specific deployment
kubectl scale deployment enhanced-crypto-prices --replicas=3 -n crypto-data-collection

# Scale all data collection services
kubectl scale deployment enhanced-crypto-prices --replicas=2 -n crypto-data-collection
kubectl scale deployment crypto-news-collector --replicas=2 -n crypto-data-collection
kubectl scale deployment sentiment-collector --replicas=2 -n crypto-data-collection
```

#### HPA Configuration
```bash
# Check HPA configuration
kubectl get hpa -n crypto-data-collection -o yaml

# Update HPA thresholds
kubectl patch hpa enhanced-crypto-prices-hpa -n crypto-data-collection -p '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":60}}}]}}'
```

## Backup and Recovery

### Database Backup
```bash
# Backup MySQL database
mysqldump -h host.docker.internal -u news_collector -p99Rules! crypto_prices > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
mysql -h host.docker.internal -u news_collector -p99Rules! crypto_prices < backup_file.sql
```

### Configuration Backup
```bash
# Backup Kubernetes configurations
kubectl get all -n crypto-data-collection -o yaml > k8s-backup-$(date +%Y%m%d_%H%M%S).yaml

# Backup secrets and configmaps
kubectl get secrets,configmaps -n crypto-data-collection -o yaml > config-backup-$(date +%Y%m%d_%H%M%S).yaml
```

## Security Considerations

### API Keys Management
- Store API keys in Kubernetes secrets
- Rotate keys regularly
- Monitor API usage for anomalies

### Network Security
- Use internal service communication
- Implement proper RBAC
- Monitor network traffic

### Data Protection
- Encrypt sensitive data at rest
- Use secure connections (TLS)
- Implement proper access controls

## Performance Optimization

### Resource Optimization
```bash
# Check resource quotas
kubectl get resourcequota -n crypto-data-collection

# Check limit ranges
kubectl get limitrange -n crypto-data-collection

# Optimize resource requests/limits
kubectl edit deployment <deployment-name> -n crypto-data-collection
```

### Caching Optimization
```bash
# Check cache status
kubectl port-forward svc/cache-manager 8007:8000 -n crypto-data-collection
curl http://localhost:8007/cache/status

# Clear cache if needed
curl -X POST http://localhost:8007/cache/clear/price_data
```

## Emergency Procedures

### Service Outage
1. Check pod status: `kubectl get pods -n crypto-data-collection`
2. Check logs: `kubectl logs -n crypto-data-collection <pod-name>`
3. Restart service: `kubectl rollout restart deployment <deployment-name> -n crypto-data-collection`
4. Scale up if needed: `kubectl scale deployment <deployment-name> --replicas=2 -n crypto-data-collection`

### Database Outage
1. Check MySQL service on Windows host
2. Verify network connectivity
3. Check firewall settings
4. Restart MySQL service if needed

### Complete System Recovery
1. Check cluster status: `kubectl cluster-info`
2. Restart all deployments: `kubectl rollout restart deployment --all -n crypto-data-collection`
3. Verify all services are running
4. Check data collection is working

## Contact Information

### Escalation Procedures
1. **Level 1**: Check logs and restart services
2. **Level 2**: Check infrastructure and network
3. **Level 3**: Contact system administrator

### Monitoring Alerts
- Prometheus alerts configured for critical issues
- Grafana dashboards for real-time monitoring
- Performance monitor for system health

## Appendix

### Useful Commands
```bash
# Get all resources
kubectl get all -n crypto-data-collection

# Check events
kubectl get events -n crypto-data-collection --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n crypto-data-collection
kubectl top nodes

# Check logs
kubectl logs -n crypto-data-collection <pod-name> --tail=100 -f

# Port forward multiple services
kubectl port-forward svc/prometheus 9090:9090 -n crypto-data-collection &
kubectl port-forward svc/grafana 3000:3000 -n crypto-data-collection &
kubectl port-forward svc/performance-monitor 8005:8000 -n crypto-data-collection &
```