# K3s Deployment Guide - Crypto Data Collection Platform

Complete deployment guide for running all 12 crypto data collectors on K3s.

## 🚀 Quick Start

### Prerequisites

1. **K3s installed and running** on your machine
2. **kubectl** configured to access your K3s cluster  
3. **Docker** installed for building container images
4. **Git** repository cloned locally

### One-Command Deployment

```bash
# Deploy everything (build images, deploy infrastructure, deploy services)
./scripts/deploy-to-k3s.sh deploy
```

### Step-by-Step Deployment

```bash
# 1. Build Docker images for all 12 collectors
./scripts/build-docker-images.sh build

# 2. Deploy to K3s
./scripts/deploy-to-k3s.sh deploy

# 3. Test the deployment
./scripts/test-k3s-deployment.sh test
```

## 📋 All 12 Collectors

Your deployment includes these crypto data collection services:

### Core Collectors (Top-level)
1. **enhanced-news-collector** - News article collection and processing
2. **enhanced-sentiment-ml-analysis** - AI-powered sentiment analysis  
3. **enhanced-technical-calculator** - Technical indicator calculations
4. **enhanced-materialized-updater** - Data materialization and updates

### Market Data Collectors (Subdirectories)  
5. **enhanced-crypto-prices-service** - Real-time price data (`services/price-collection`)
6. **enhanced-crypto-news-collector-sub** - Alternative news collector (`services/news-collection`)
7. **enhanced-onchain-collector** - On-chain metrics (`services/onchain-collection`)
8. **enhanced-technical-indicators-collector** - Technical analysis (`services/technical-collection`)
9. **enhanced-macro-collector-v2** - Macroeconomic data (`services/macro-collection`)
10. **enhanced-crypto-derivatives-collector** - Derivatives data (`services/derivatives-collection`)
11. **ml-market-collector** - ML market analysis (`services/market-collection`)
12. **enhanced-ohlc-collector** - OHLC candle data (`services/ohlc-collection`)

## 🗂️ Deployment Structure

```
k8s/k3s-production/
├── namespace.yaml                      # Namespaces and resource limits
├── config.yaml                         # Configuration and secrets
├── infrastructure.yaml                 # MySQL and Redis
├── services-deployment-updated.yaml    # All 12 collector deployments
└── services-updated.yaml              # Services and networking
```

## 🔧 Management Commands

### Deployment Management
```bash
# Full deployment
./scripts/deploy-to-k3s.sh deploy

# Check status
./scripts/deploy-to-k3s.sh status

# Detailed service status
./scripts/deploy-to-k3s.sh service-status enhanced-crypto-prices-service

# Restart all services
./scripts/deploy-to-k3s.sh restart

# Clean removal
./scripts/deploy-to-k3s.sh cleanup
```

### Testing and Validation
```bash
# Full test suite
./scripts/test-k3s-deployment.sh test

# Quick health check
./scripts/test-k3s-deployment.sh quick

# Test specific components
./scripts/test-k3s-deployment.sh infrastructure
./scripts/test-k3s-deployment.sh collectors
./scripts/test-k3s-deployment.sh imports
```

### Docker Image Management
```bash
# Build all images
./scripts/build-docker-images.sh build

# Push to registry (if available)
./scripts/build-docker-images.sh push

# Build and push
./scripts/build-docker-images.sh all

# Cleanup build files
./scripts/build-docker-images.sh cleanup
```

## 🌐 Access Your Services

### External Access
- **API Gateway**: `http://<node-ip>:30080`  
- **Load Balancer**: `http://<node-ip>:80` (if LoadBalancer available)

### Get Node IP
```bash
kubectl get nodes -o wide
```

### Port Forwarding (for testing)
```bash
# Forward specific service
kubectl port-forward -n crypto-core-production svc/enhanced-crypto-prices-service 8080:8005

# Test locally
curl http://localhost:8080/health
```

## 📊 Monitoring and Troubleshooting

### Check Pod Status
```bash
# All pods
kubectl get pods -n crypto-core-production

# Wide view with node assignments
kubectl get pods -n crypto-core-production -o wide

# Resource usage
kubectl top pods -n crypto-core-production
```

### View Logs
```bash
# Logs for specific service
kubectl logs -f deployment/enhanced-crypto-prices-service -n crypto-core-production

# All containers in a pod
kubectl logs -f pod/<pod-name> -n crypto-core-production --all-containers

# Recent logs from all pods
kubectl logs -l service-tier=market -n crypto-core-production --tail=50
```

### Debug Services
```bash
# Describe deployment
kubectl describe deployment enhanced-crypto-prices-service -n crypto-core-production

# Check endpoints
kubectl get endpoints -n crypto-core-production

# View recent events
kubectl get events -n crypto-core-production --sort-by='.lastTimestamp'
```

## 🔧 Configuration Management

### Database Credentials
Default credentials in `config.yaml` (update before production):
- MySQL: `news_collector` / `99Rules!`
- Redis: `99Rules!`

### Environment Variables
Key configuration in `config.yaml`:
- `MYSQL_HOST`: `mysql-service.crypto-infrastructure.svc.cluster.local`
- `REDIS_HOST`: `redis-service.crypto-infrastructure.svc.cluster.local`
- Collection intervals, rate limits, feature flags

### Scaling Services
```bash
# Scale specific service
kubectl scale deployment enhanced-crypto-prices-service --replicas=3 -n crypto-core-production

# Scale all market data services
kubectl scale deployment enhanced-crypto-prices-service enhanced-ohlc-collector enhanced-crypto-derivatives-collector --replicas=2 -n crypto-core-production
```

## 📈 Resource Requirements

### Minimum Resources
- **CPU**: 10 cores total (20 cores max)
- **Memory**: 20GB total (40GB max)  
- **Storage**: 100GB for MySQL, 20GB for Redis

### Per-Service Resources
- **Market services**: 250m CPU, 512Mi RAM
- **Analytics services**: 500m CPU, 1Gi RAM  
- **ML services**: 500m CPU, 1Gi RAM (up to 2Gi)

## 🚨 Troubleshooting Guide

### Common Issues

#### Pods Stuck in Pending
```bash
# Check node resources
kubectl describe nodes

# Check resource quotas
kubectl describe resourcequota -n crypto-core-production
```

#### Image Pull Errors
```bash
# Rebuild images
./scripts/build-docker-images.sh build

# Check image availability
docker images | grep crypto-
```

#### Database Connection Issues
```bash
# Check infrastructure pods
kubectl get pods -n crypto-infrastructure

# Test MySQL connectivity
kubectl exec -n crypto-infrastructure statefulset/mysql -- mysqladmin ping
```

#### Service Not Responding
```bash
# Check pod logs
kubectl logs deployment/<service-name> -n crypto-core-production

# Check service endpoints
kubectl get endpoints <service-name>-service -n crypto-core-production

# Restart service
kubectl rollout restart deployment/<service-name> -n crypto-core-production
```

### Emergency Procedures

#### Restart All Services
```bash
./scripts/deploy-to-k3s.sh restart
```

#### Full Redeployment
```bash
# Clean up
./scripts/deploy-to-k3s.sh cleanup

# Redeploy
./scripts/deploy-to-k3s.sh deploy
```

#### Backup Database
```bash
# MySQL backup
kubectl exec -n crypto-infrastructure statefulset/mysql -- mysqldump crypto_prices > backup.sql
```

## 📚 Additional Resources

### Useful kubectl Commands
```bash
# Switch context to crypto namespace
kubectl config set-context --current --namespace=crypto-core-production

# Watch pod status
kubectl get pods -w

# Shell into pod
kubectl exec -it pod/<pod-name> -- /bin/bash

# Copy files from pod
kubectl cp <pod-name>:/path/to/file ./local-file
```

### Service Architecture
- **Microservices**: 12 independent collector services
- **Infrastructure**: MySQL (StatefulSet), Redis (StatefulSet)  
- **Networking**: ClusterIP for internal, NodePort for external
- **Storage**: Persistent volumes for databases
- **Monitoring**: Prometheus metrics endpoints on all services

## 🎯 Next Steps

1. **Monitoring**: Set up Grafana/Prometheus for metrics
2. **Alerting**: Configure alerts for service health
3. **Backup**: Implement automated database backups  
4. **Security**: Add network policies and RBAC
5. **CI/CD**: Integrate with your deployment pipeline
6. **Scaling**: Configure HorizontalPodAutoscaler for high load

---

**🎉 Your crypto data collection platform is now running on K3s with all 12 collectors!**