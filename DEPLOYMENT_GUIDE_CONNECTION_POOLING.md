# Database Connection Pooling Deployment Guide

## 🎯 Overview

This guide covers the deployment and management of database connection pooling across the crypto data collection infrastructure.

## 📋 Prerequisites

- Kubernetes cluster with `crypto-collectors` namespace
- MySQL database running on Windows host
- kubectl configured and connected
- Python services ready for pooling integration

## 🚀 Deployment Steps

### 1. Deploy Shared Connection Pool Module

The shared connection pool is located at `src/shared/database_pool.py`:

```python
from src.shared.database_pool import DatabasePool

# Initialize singleton pool
pool = DatabasePool()

# Get connection from pool
connection = pool.get_connection()

# Use connection normally
cursor = connection.cursor()
# ... database operations

# Connection automatically returned to pool when closed
connection.close()
```

### 2. Configure Kubernetes Environment

Apply the database pool configuration:

```bash
kubectl apply -f fixed-database-pool-config.yaml
```

This creates a ConfigMap with:
- `MYSQL_HOST`: Windows host IP (192.168.230.162)
- `MYSQL_USER`: news_collector
- `MYSQL_DATABASE`: crypto_prices
- `DB_POOL_SIZE`: 15 connections per service

### 3. Update Service Deployments

Add environment configuration to service deployments:

```yaml
spec:
  template:
    spec:
      containers:
      - name: service-container
        envFrom:
        - configMapRef:
            name: database-pool-config
```

### 4. Restart Services

Restart all services to pick up the new configuration:

```bash
kubectl rollout restart deployment enhanced-crypto-prices -n crypto-collectors
kubectl rollout restart deployment sentiment-microservice -n crypto-collectors
kubectl rollout restart deployment unified-ohlc-collector -n crypto-collectors
# ... repeat for all services
```

### 5. Verify Deployment

Check that services are using connection pooling:

```bash
# Verify ConfigMap
kubectl get configmap database-pool-config -n crypto-collectors -o yaml

# Check pod environment
kubectl exec -it <pod-name> -n crypto-collectors -- printenv | grep MYSQL

# Monitor pod logs for connection pool messages
kubectl logs <pod-name> -n crypto-collectors | grep -i pool
```

## 📊 Monitoring and Validation

### Performance Metrics

Monitor these key indicators:

1. **Database Connection Count**: Should stabilize at 15 * number of services
2. **Deadlock Error Rate**: Should drop by 95%+
3. **Query Response Times**: Should improve by 50-80%
4. **Service Restart Frequency**: Should decrease significantly

### Health Checks

```bash
# Check service health
kubectl get pods -n crypto-collectors

# Verify connectivity
kubectl exec -it <pod-name> -n crypto-collectors -- python -c "
from src.shared.database_pool import DatabasePool
pool = DatabasePool()
conn = pool.get_connection()
print('Connection successful!')
conn.close()
"
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Refused**: Verify MySQL host IP is correct
2. **Pool Exhaustion**: Check for connection leaks in application code
3. **Authentication Errors**: Verify MySQL credentials in ConfigMap
4. **Import Errors**: Ensure `src/shared/database_pool.py` is in Python path

### Recovery Procedures

If services fail to start:

```bash
# Check pod logs
kubectl logs <pod-name> -n crypto-collectors

# Verify ConfigMap
kubectl describe configmap database-pool-config -n crypto-collectors

# Reset deployment
kubectl rollout undo deployment <service-name> -n crypto-collectors
```

## 📈 Expected Benefits

- **95%+ reduction** in database deadlock errors
- **50-80% improvement** in database query performance
- **Better resource utilization** across all services
- **Enhanced system stability** under high concurrent load
- **Reduced MySQL connection overhead**

## 🔄 Maintenance

### Regular Tasks

1. Monitor connection pool metrics
2. Review service logs for pool-related messages
3. Update pool size if needed based on load patterns
4. Verify all new services integrate with pooling

### Updates and Changes

When adding new services:

1. Import `DatabasePool` in service code
2. Replace direct MySQL connections with pool connections
3. Add `envFrom` configuration to Kubernetes deployment
4. Test connectivity before production deployment

---

**Last Updated**: September 30, 2025
**Status**: Production Ready
**Contact**: Development Team