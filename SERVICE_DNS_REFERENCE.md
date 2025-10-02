# 🌐 **Kubernetes Service DNS Reference**

This document provides the proper Kubernetes DNS names for all services in the crypto data collection system. **Always use these DNS names for internal service communication** to avoid port dependencies and ensure proper service discovery.

## 📋 **Core Services DNS Names**

### **Production Services (Always Use These)**

| Service | Kubernetes DNS | Purpose | Status |
|---------|----------------|---------|--------|
| **API Gateway** | `simple-api-gateway.crypto-collectors.svc.cluster.local:8000` | Unified REST API access | ✅ Active |
| **Crypto Prices** | `enhanced-crypto-prices.crypto-collectors.svc.cluster.local:8000` | Price data collection | ✅ Active |
| **News Collector** | `crypto-news-collector.crypto-collectors.svc.cluster.local:8000` | News and sentiment | ✅ Active |
| **Sentiment Collector** | `simple-sentiment-collector.crypto-collectors.svc.cluster.local:8000` | Core sentiment analysis | ✅ Active |
| **Sentiment Microservice** | `sentiment-microservice.crypto-collectors.svc.cluster.local:8000` | Advanced sentiment | ✅ Active |
| **Stock Sentiment** | `stock-sentiment-collector.crypto-collectors.svc.cluster.local:8000` | Stock market sentiment | ✅ Active |
| **Social Sentiment** | `social-sentiment-collector.crypto-collectors.svc.cluster.local:8000` | Social media sentiment | ✅ Active |

### **DNS Format Explanation**
```
<service-name>.crypto-collectors.svc.cluster.local:<port>
```

- `<service-name>`: The Kubernetes service name
- `crypto-collectors`: The namespace
- `svc.cluster.local`: Standard Kubernetes cluster domain
- `<port>`: Service port (typically 8000 for most services)

## 🔧 **Usage Examples**

### **Inter-Service Communication**
```python
# ✅ CORRECT: Use Kubernetes DNS
import requests

# API Gateway health check
response = requests.get("http://simple-api-gateway.crypto-collectors.svc.cluster.local:8000/health")

# Get crypto prices from price collector
prices = requests.get("http://enhanced-crypto-prices.crypto-collectors.svc.cluster.local:8000/api/v1/prices/current/bitcoin")
```

### **Configuration Files**
```yaml
# ✅ CORRECT: Environment variables using DNS
env:
- name: API_GATEWAY_URL
  value: "http://simple-api-gateway.crypto-collectors.svc.cluster.local:8000"
- name: PRICE_COLLECTOR_URL
  value: "http://enhanced-crypto-prices.crypto-collectors.svc.cluster.local:8000"
```

### **External Access (Development/Testing Only)**
```bash
# 🚧 EXTERNAL ACCESS: Use only for development/testing
curl http://localhost:30080/health  # API Gateway external port

# ✅ INTERNAL ACCESS: Use this for production
kubectl exec -it <pod> -- curl http://simple-api-gateway.crypto-collectors.svc.cluster.local:8000/health
```

## ⚡ **Benefits of Using Kubernetes DNS**

1. **Port Independence**: Services can change ports without breaking connections
2. **Load Balancing**: Automatic load balancing across multiple replicas
3. **Service Discovery**: Automatic discovery of healthy service instances
4. **High Availability**: Failover to healthy pods automatically
5. **Scalability**: Works seamlessly with horizontal pod autoscaling
6. **Cloud Native**: Follows Kubernetes best practices

## 🚨 **Important Notes**

- **External ports (30080, 31683, etc.) are ONLY for development and testing**
- **Production systems should NEVER use external ports for inter-service communication**
- **Always specify the full DNS name with namespace to avoid conflicts**
- **DNS resolution happens automatically within the Kubernetes cluster**

## 🔍 **Troubleshooting DNS**

### **Test DNS Resolution**
```bash
# Test from within a pod
kubectl exec -it <any-pod> -n crypto-collectors -- nslookup simple-api-gateway.crypto-collectors.svc.cluster.local

# Test service connectivity
kubectl exec -it <any-pod> -n crypto-collectors -- curl http://simple-api-gateway.crypto-collectors.svc.cluster.local:8000/health
```

### **Common Issues**
- **DNS not resolving**: Check namespace spelling and service existence
- **Connection refused**: Service may be down or port incorrect
- **Timeout**: Service may be overloaded or not ready

---

**Updated**: October 2025  
**Maintainer**: Crypto Data Collection Team  
**Version**: 1.0
