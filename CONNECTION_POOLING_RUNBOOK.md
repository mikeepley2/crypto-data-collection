# Connection Pooling Operations Runbook

## 🚨 Emergency Procedures

### Service Not Starting
```bash
# 1. Check pod status
kubectl get pods -n crypto-collectors | grep <service-name>

# 2. Check pod logs
kubectl logs <pod-name> -n crypto-collectors

# 3. Verify ConfigMap
kubectl get configmap database-pool-config -n crypto-collectors -o yaml

# 4. Test database connectivity
kubectl exec -it <pod-name> -n crypto-collectors -- ping 192.168.230.162
```

### Database Connection Issues
```bash
# 1. Check MySQL status on Windows host
netstat -an | findstr :3306

# 2. Verify MySQL is accepting connections
telnet 192.168.230.162 3306

# 3. Check MySQL user permissions
mysql -u news_collector -p -h 192.168.230.162 -e "SHOW GRANTS;"
```

### Pool Exhaustion
```bash
# 1. Check for connection leaks in logs
kubectl logs <pod-name> -n crypto-collectors | grep -i "pool\|connection"

# 2. Restart affected service
kubectl rollout restart deployment <service-name> -n crypto-collectors

# 3. Monitor pool usage
kubectl exec -it <pod-name> -n crypto-collectors -- python -c "
from src.shared.database_pool import DatabasePool
pool = DatabasePool()
print(f'Pool stats: {pool._pool._pool.qsize()} available connections')
"
```

## 📊 Regular Monitoring

### Daily Checks
1. ✅ Verify all services are running
2. ✅ Check for connection pool errors in logs
3. ✅ Monitor database deadlock rates
4. ✅ Validate query performance metrics

### Weekly Reviews
1. 📈 Analyze connection pool utilization trends
2. 📈 Review service performance improvements
3. 📈 Check for any pool configuration optimizations needed

### Monthly Assessments
1. 📋 Evaluate overall system stability improvements
2. 📋 Review deadlock reduction metrics (target: 95%+)
3. 📋 Assess query performance gains (target: 50-80%)

## 🔧 Configuration Updates

### Scaling Pool Size
```yaml
# Update ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: database-pool-config
  namespace: crypto-collectors
data:
  DB_POOL_SIZE: "20"  # Increase if needed
  # ... other settings
```

### Updating MySQL Host
```bash
# 1. Update ConfigMap
kubectl patch configmap database-pool-config -n crypto-collectors --type merge -p '{"data":{"MYSQL_HOST":"NEW_IP_ADDRESS"}}'

# 2. Restart all services
kubectl rollout restart deployment -n crypto-collectors --selector=app=crypto-collector
```

## 📞 Escalation Procedures

### Level 1: Service Issues
- Check pod logs and restart individual services
- Verify ConfigMap settings
- Test basic connectivity

### Level 2: Database Issues  
- Check MySQL server status
- Verify network connectivity
- Review MySQL user permissions

### Level 3: System-wide Issues
- Contact database administrator
- Review infrastructure changes
- Consider fallback procedures

## 📈 Success Metrics

- **Deadlock Errors**: < 5% of previous rate
- **Query Performance**: 50-80% improvement
- **Service Uptime**: 99.9%+
- **Connection Pool Utilization**: 60-80%

---

**Last Updated**: September 30, 2025
**On-Call Contact**: Development Team
**Emergency Escalation**: Database Admin Team