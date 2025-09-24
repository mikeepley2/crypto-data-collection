# Node/Pod Health Visibility - Quick Reference
# =============================================

## 🎯 **Where to Find Node/Pod Health Information**

### ✅ **CORRECT APPROACH** - Use Analytics/Observability Node:

#### **Node Health Monitoring:**
- **Location**: Analytics Node → Grafana Dashboard
- **URL**: `http://analytics-node:3000/d/kubernetes-nodes`
- **Metrics**: CPU, Memory, Disk, Network usage per node
- **Alerts**: Node down, high resource usage, disk space

#### **Pod Health Monitoring:**  
- **Location**: Analytics Node → Grafana Dashboard
- **URL**: `http://analytics-node:3000/d/kubernetes-pods`
- **Metrics**: Pod status, restarts, resource consumption
- **Alerts**: Pod crashes, OOMKilled, ImagePullBackOff

#### **Centralized Logging:**
- **Location**: Analytics Node → Kibana
- **URL**: `http://analytics-node:5601`
- **Index**: `crypto-logs-*`
- **Search**: Pod names, error messages, structured logs

### ❌ **AVOID** - Local Node/Pod Monitoring Scripts:
- Don't create local monitoring dashboards
- Don't use kubectl for regular health monitoring  
- Don't build separate alerting systems

### ✅ **LOCAL TOOLS** - Service-Level Health Only:
```bash
# Service application health (Data Collection Node)
./scripts/service-manager.sh        # Interactive management
./scripts/health-check.sh           # Service status
curl http://service:8000/health     # Individual service health

# Emergency kubectl (when Analytics Node unavailable)
kubectl get pods -n crypto-collectors
kubectl top nodes
kubectl describe pod <pod-name>
```

## 🔧 **Integration Requirements**

### **For New Services:**
1. **Add metrics endpoint**: `/metrics` for Prometheus scraping
2. **Use structured logging**: JSON format for Elasticsearch
3. **Add health checks**: `/health` and `/ready` endpoints
4. **Configure annotations**: Enable Prometheus scraping

### **Analytics Node Integration:**
```yaml
# Add to each service deployment
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics" 
    prometheus.io/port: "8000"
```

## 📚 **Documentation Links**

- **Full Setup**: [docs/MONITORING_OBSERVABILITY.md](./MONITORING_OBSERVABILITY.md)
- **Integration Guide**: [docs/NODE_POD_MONITORING_INTEGRATION.md](./NODE_POD_MONITORING_INTEGRATION.md)
- **Service Management**: [scripts/service-manager.sh](../scripts/service-manager.sh)

## 🚨 **Quick Troubleshooting**

| **Issue** | **Check Location** | **Action** |
|-----------|-------------------|------------|
| Node offline | Analytics Node → Node dashboard | Check node status, restart if needed |
| Pod crashing | Analytics Node → Pod dashboard | Check logs in Kibana, analyze restart patterns |
| High resource usage | Analytics Node → Resource dashboard | Scale services, optimize resource limits |
| Service errors | Data Collection Node → `/health` endpoints | Use local service management tools |

## 📞 **Emergency Contacts**
- **Analytics Node Issues**: Contact Analytics team
- **Service Issues**: Use Data Collection Node tools
- **Infrastructure Issues**: Check Analytics Node dashboards first