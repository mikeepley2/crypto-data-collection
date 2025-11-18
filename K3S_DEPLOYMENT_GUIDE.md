# K3s + KIND Hybrid Deployment Guide
# Complete setup guide for development and production environments

## 🎯 **Architecture Overview**

This setup provides a **hybrid Kubernetes deployment strategy**:

- **🧪 Development & Testing**: KIND (Kubernetes in Docker) for fast CI/CD testing
- **🚀 Production**: K3s multi-node cluster for production deployment
- **🔄 CI/CD Integration**: Automatic deployment pipeline with GitHub Actions

## 📁 **Directory Structure**

```
crypto-data-collection/
├── k8s/
│   ├── k3s-production/          # K3s production manifests
│   │   ├── namespace.yaml       # Production namespaces
│   │   ├── config.yaml          # ConfigMaps and Secrets
│   │   ├── services-deployment.yaml # All 10 microservices
│   │   ├── services.yaml        # Service definitions
│   │   └── infrastructure.yaml  # MySQL + Redis
│   └── production/              # Original KIND testing manifests
├── scripts/
│   ├── install-k3s-cluster.sh  # Multi-server K3s installation
│   └── deploy-to-k3s.sh        # Deployment automation
└── .github/workflows/
    └── complete-ci-cd.yml       # Hybrid CI/CD pipeline
```

## 🛠️ **Quick Start Guide**

### **Step 1: Install K3s Cluster**

#### **Primary Server (Master Node)**:
```bash
# On your first server (e.g., 192.168.1.10)
sudo ./scripts/install-k3s-cluster.sh server-primary 192.168.1.10

# Save the token that appears (you'll need it for other nodes)
sudo cat /var/lib/rancher/k3s/server/node-token
```

#### **Additional Worker Nodes**:
```bash
# On additional servers (e.g., 192.168.1.11, 192.168.1.12)
sudo K3S_TOKEN=<token-from-primary> ./scripts/install-k3s-cluster.sh agent https://192.168.1.10:6443 192.168.1.11
```

### **Step 2: Deploy Production Services**

```bash
# Deploy all crypto data collection services
./scripts/deploy-to-k3s.sh deploy

# Check deployment status
./scripts/deploy-to-k3s.sh status

# Run health checks
./scripts/deploy-to-k3s.sh health
```

### **Step 3: Access Your Services**

```bash
# Get node IPs
kubectl get nodes -o wide

# Access API Gateway
curl http://<node-ip>:30080/health

# Port forward specific services
kubectl port-forward -n crypto-core-production svc/news-collector-service 8001:8001 &
curl http://localhost:8001/health
```

## 🔧 **Environment Configuration**

### **GitHub Secrets (Required for Production Deployment)**

Add these secrets to your GitHub repository (`Settings` → `Secrets and variables` → `Actions`):

```yaml
# K3s Cluster Access
K3S_KUBECONFIG: <base64-encoded-kubeconfig-file>

# Database Credentials
MYSQL_USER: news_collector
MYSQL_PASSWORD: your_secure_password
REDIS_PASSWORD: your_redis_password

# API Keys
COINGECKO_API_KEY: your_coingecko_api_key
NEWSAPI_KEY: your_newsapi_api_key
POLYGON_API_KEY: your_polygon_api_key
```

### **Local Development Secrets**

```bash
# Update k8s/k3s-production/config.yaml with your actual secrets
# Replace the base64 encoded placeholders:

# Encode your secrets
echo -n "your_actual_password" | base64
echo -n "your_api_key" | base64

# Update the config.yaml file with real encoded values
```

## 🚀 **Deployment Workflows**

### **Automatic Deployment (CI/CD)**

1. **Development Testing**: Every push runs KIND-based testing
2. **Production Deployment**: Main branch pushes trigger K3s deployment
3. **Manual Deployment**: Use GitHub Actions workflow dispatch

```yaml
# Trigger manual production deployment
gh workflow run complete-ci-cd.yml --ref main -f deploy_to_production=true
```

### **Manual Deployment**

```bash
# Deploy to K3s manually
kubectl apply -f k8s/k3s-production/namespace.yaml
kubectl apply -f k8s/k3s-production/config.yaml
kubectl apply -f k8s/k3s-production/infrastructure.yaml
kubectl apply -f k8s/k3s-production/services-deployment.yaml
kubectl apply -f k8s/k3s-production/services.yaml
```

## 📊 **Service Architecture**

### **10 Production Microservices**:

| Service | Port | Purpose | Resources |
|---------|------|---------|-----------|
| 📰 News Collector | 8001 | Crypto news aggregation | 512Mi/250m CPU |
| 🧠 Sentiment Analyzer | 8002 | News sentiment analysis | 2Gi/1000m CPU |
| 📊 Technical Analysis | 8003 | Technical indicators | 2Gi/1000m CPU |
| 🌍 Macro Economics | 8004 | Economic data collection | 1Gi/500m CPU |
| ⛓️ On-chain Data | 8005 | Blockchain metrics | 2Gi/1000m CPU |
| 💬 Social Sentiment | 8006 | Social media analysis | 1Gi/500m CPU |
| 📈 OHLC Collector | 8007 | Candlestick data | 1Gi/500m CPU |
| 💰 Price Collector | 8008 | Real-time prices | 1Gi/500m CPU |
| 🤖 ML Pipeline | 8009 | Machine learning | 4Gi/2000m CPU |
| 📊 Portfolio Optimization | 8010 | Portfolio analysis | 2Gi/1000m CPU |

### **Infrastructure Services**:
- **MySQL 8.0**: Primary database with 100GB storage
- **Redis 7**: Caching and session storage with 20GB storage

## 🔍 **Monitoring & Management**

### **Health Checks**:
```bash
# Check all pod status
kubectl get pods -n crypto-core-production

# View service logs
kubectl logs -f deployment/news-collector -n crypto-core-production

# Port forward for testing
kubectl port-forward -n crypto-core-production svc/news-collector-service 8001:8001
```

### **Scaling Services**:
```bash
# Scale high-demand services
kubectl scale deployment price-collector --replicas=5 -n crypto-core-production
kubectl scale deployment news-collector --replicas=3 -n crypto-core-production
```

### **Resource Monitoring**:
```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n crypto-core-production

# View detailed pod information
kubectl describe pod <pod-name> -n crypto-core-production
```

## 🛡️ **Security Features**

- **🔐 Secret Management**: Kubernetes secrets for sensitive data
- **🌐 Network Policies**: Isolated namespace communication
- **🔑 RBAC**: Role-based access control (planned)
- **🛡️ Pod Security**: Resource limits and security contexts
- **📊 Health Checks**: Comprehensive liveness and readiness probes

## 🚧 **Troubleshooting**

### **Common Issues**:

1. **Pod Stuck in Pending**:
   ```bash
   kubectl describe pod <pod-name> -n crypto-core-production
   # Check for resource constraints or node affinity issues
   ```

2. **Service Not Accessible**:
   ```bash
   kubectl get endpoints -n crypto-core-production
   # Verify service selector matches pod labels
   ```

3. **Database Connection Issues**:
   ```bash
   kubectl logs deployment/mysql -n crypto-infrastructure
   # Check MySQL pod logs and credentials
   ```

### **Cleanup**:
```bash
# Remove all services (WARNING: This deletes everything)
./scripts/deploy-to-k3s.sh cleanup

# Or manually delete namespaces
kubectl delete namespace crypto-core-production
kubectl delete namespace crypto-infrastructure
```

## 📈 **Performance Optimization**

### **Recommended Node Distribution**:

```yaml
# 3-Server Setup Example
server-1: Control plane + Core services (news, sentiment, technical)
server-2: Market services (price, ohlc) + Infrastructure (MySQL, Redis)  
server-3: Analytics services (ML, portfolio) + Specialized services
```

### **Resource Planning**:
- **Minimum**: 3 servers, 8GB RAM each, 100GB storage
- **Recommended**: 4+ servers, 16GB RAM each, 200GB+ SSD storage
- **High Availability**: 5+ servers with proper anti-affinity rules

## 🎯 **Next Steps**

1. **Install K3s cluster** using the provided scripts
2. **Configure GitHub secrets** for automatic deployment
3. **Deploy services** using the deployment script
4. **Monitor performance** and adjust resource allocations
5. **Scale services** based on your data collection needs

Your crypto data collection platform is now ready for production with enterprise-grade Kubernetes orchestration! 🚀