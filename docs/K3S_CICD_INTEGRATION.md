# 🚀 K3s Deployment CI/CD Integration Guide

This document explains how to use the GitHub Actions pipelines to automatically deploy the crypto data collection platform to your K3s cluster.

## 📋 Available Workflows

### 1. 🎯 Complete CI/CD Pipeline (`complete-ci-cd.yml`)
**Purpose:** Full testing and deployment pipeline with K3s production deployment
**Triggers:** 
- Push to `main` branch (automatic deployment)
- Manual dispatch with production deployment option

**Features:**
- Code quality checks (formatting, linting, security)
- Docker image building and pushing
- Database integration testing
- K3s production deployment
- Post-deployment health monitoring

### 2. 🚀 Dedicated K3s Pipeline (`k3s-deployment.yml`)
**Purpose:** Comprehensive K3s-focused deployment with Docker builds
**Triggers:**
- Push to `main` branch
- Pull requests to `main`
- Manual dispatch with deployment options

**Features:**
- Pre-deployment validation
- Custom Docker image building
- Full 12-service deployment
- Extended health monitoring
- Rollback capabilities

### 3. ⚡ Quick K3s Actions (`quick-k3s-deploy.yml`)
**Purpose:** Fast management actions using existing scripts
**Triggers:** Manual dispatch only

**Available Actions:**
- `deploy` - Full deployment using scripts
- `status` - Check current deployment status  
- `health` - Run health checks
- `restart` - Restart all services
- `cleanup` - Remove deployments

## 🔧 Setup Requirements

### 1. GitHub Secrets Configuration

Add these secrets to your GitHub repository settings:

#### K3s Access Secrets
```
K3S_KUBECONFIG          # Base64 encoded kubeconfig file for K3s cluster
```

#### Database Secrets  
```
MYSQL_USER              # MySQL username (default: news_collector)
MYSQL_PASSWORD          # MySQL password (default: 99Rules!)
MYSQL_ROOT_PASSWORD     # MySQL root password (default: 99Rules!)
MYSQL_DATABASE          # MySQL database name (default: crypto_data)
REDIS_PASSWORD          # Redis password (optional)
```

#### API Keys (Optional)
```
COINGECKO_API_KEY       # CoinGecko API key for price data
NEWSAPI_KEY             # News API key for news collection
```

#### Docker Registry Secrets
```
DOCKER_USERNAME         # Docker Hub username
DOCKER_PASSWORD         # Docker Hub password/token
```

### 2. Environment Configuration

Create GitHub environments in your repository settings:

#### `k3s-production` Environment
- Add protection rules as needed
- Configure required reviewers for production deployments
- Set all K3s and production secrets here

### 3. K3s Cluster Preparation

Ensure your K3s cluster has:

```bash
# Node labels for specialized placement
kubectl label node <worker1> kubernetes.io/hostname=cryptoai-k8s-trading-engine-worker
kubectl label node <worker2> kubernetes.io/hostname=cryptoai-k8s-trading-engine-worker2  
kubectl label node <worker3> kubernetes.io/hostname=cryptoai-k8s-trading-engine-worker3

# Node taints for workload isolation
kubectl taint node <worker1> data-platform=true:NoSchedule
kubectl taint node <worker2> trading-engine=true:NoSchedule
kubectl taint node <worker3> analytics-infrastructure=true:NoSchedule
```

## 🎯 Usage Examples

### Automatic Deployment (Production)
```bash
# Simply push to main branch
git push origin main

# The complete-ci-cd.yml workflow will:
# 1. Run tests and build containers
# 2. Deploy to K3s automatically
# 3. Verify health and send notifications
```

### Manual Deployment with Options
```bash
# Navigate to Actions tab in GitHub
# Select "🚀 K3s Production Deployment Pipeline"  
# Click "Run workflow"
# Choose options:
#   - deployment_type: full|services-only|infrastructure-only
#   - force_rebuild: true|false
#   - skip_tests: true|false (emergency deployments)
```

### Quick Management Actions
```bash
# Navigate to Actions tab in GitHub
# Select "🎯 Quick K3s Deploy"
# Click "Run workflow" 
# Choose action: deploy|status|health|restart|cleanup
```

## 📊 Deployment Architecture

### Container Strategy
The pipelines support multiple container build strategies:

1. **Full Build Mode** (>10GB available)
   - Builds all 12 individual service containers
   - Optimized images for each collector type
   - Production-ready with health checks

2. **Core Build Mode** (6-10GB available) 
   - Builds 3 core services (news, prices, onchain)
   - Creates lightweight placeholders for remaining services
   - Suitable for testing and development

3. **Minimal Build Mode** (<6GB available)
   - Uses simplified Python base images
   - Dynamic dependency installation at runtime
   - Fastest deployment option

### Service Deployment
The deployed services include:

**Core Services (Always Deployed):**
- Enhanced News Collector (`analytics-infrastructure` node)
- Enhanced Crypto Prices Service (`trading-engine` node, 2 replicas)
- Enhanced Onchain Collector (`data-platform` node)

**Full Deployment (12 Services):**
- Sentiment Analysis Service
- Technical Indicators Calculator  
- Macro Economic Collector
- Derivatives Data Collector
- ML Market Analysis Service
- OHLC Data Collector
- Materialized View Updater
- Data Quality Validator
- Gap Detection Service

### Infrastructure Components
- **MySQL 8.0** - Primary data storage with persistent volumes
- **Redis** - Caching and session storage  
- **Kubernetes Services** - ClusterIP for internal communication
- **NodePort Gateway** - External access on port 30080

## 🔍 Monitoring & Troubleshooting

### Viewing Deployment Status
```bash
# Quick status check
./scripts/deploy-to-k3s.sh status

# Detailed pod information
kubectl get pods -n crypto-core-production -o wide

# Service logs
kubectl logs -f deployment/enhanced-news-collector -n crypto-core-production
```

### Health Checks
```bash
# Run comprehensive health check
./scripts/deploy-to-k3s.sh health

# Check resource usage
kubectl top pods -n crypto-core-production

# View recent events
kubectl get events -n crypto-core-production --sort-by='.firstTimestamp'
```

### Common Issues & Solutions

#### 1. Pod Stuck in Pending State
```bash
# Check node resources and scheduling constraints
kubectl describe pod <pod-name> -n crypto-core-production

# Verify node taints and tolerations
kubectl describe node <node-name>
```

#### 2. Image Pull Errors
```bash
# Verify Docker credentials
kubectl get secret crypto-core-secrets -n crypto-core-production -o yaml

# Check image availability
docker pull <image-name>
```

#### 3. Service Connection Issues
```bash
# Test internal connectivity
kubectl run test-pod --image=curlimages/curl --rm -it --restart=Never \
  -- curl -f http://<service-name>.crypto-core-production.svc.cluster.local:<port>

# Check service endpoints
kubectl get endpoints -n crypto-core-production
```

## 🔄 Rollback Procedures

### Automatic Rollback
If deployment fails, the pipeline includes automatic rollback capabilities:

```bash
# Rollback is triggered automatically on deployment failure
# You can also manually rollback:
kubectl rollout undo deployment/<deployment-name> -n crypto-core-production
```

### Manual Rollback
```bash
# Use the quick actions workflow
# Select action: cleanup (removes all deployments)
# Then re-run with action: deploy (fresh deployment)
```

## 📈 Scaling & Performance

### Horizontal Scaling
```bash
# Scale individual services
kubectl scale deployment enhanced-crypto-prices-service --replicas=3 -n crypto-core-production

# Scale multiple services
for deployment in enhanced-news-collector enhanced-onchain-collector; do
  kubectl scale deployment $deployment --replicas=2 -n crypto-core-production
done
```

### Resource Monitoring
```bash
# Check resource usage
kubectl top pods -n crypto-core-production
kubectl top nodes

# View resource requests and limits
kubectl describe deployment <deployment-name> -n crypto-core-production
```

## 🔐 Security Considerations

### Secrets Management
- All sensitive data stored as Kubernetes secrets
- Secrets are base64 encoded in transit
- Environment-specific secret isolation
- Automatic secret rotation supported

### Network Security
- Internal services use ClusterIP (not externally accessible)
- External access only through designated NodePort gateway
- Service mesh ready (can add Istio/Linkerd later)

### Image Security
- Container images scanned with Trivy during CI/CD
- Vulnerability reports uploaded to GitHub Security
- Only minimal required packages installed
- Non-root user execution where possible

## 📞 Support & Maintenance

### Useful Commands
```bash
# View all crypto-related resources
kubectl get all -n crypto-core-production
kubectl get all -n crypto-infrastructure

# Export current configuration
kubectl get deployment enhanced-news-collector -n crypto-core-production -o yaml > backup.yaml

# Apply configuration updates
kubectl apply -f k8s/k3s-production/

# Restart all services
./scripts/deploy-to-k3s.sh restart
```

### Maintenance Windows
- Schedule deployments during low-traffic periods
- Use rolling deployments to minimize downtime
- Monitor service health during and after deployments
- Keep rollback procedures tested and ready

### Performance Tuning
- Adjust replica counts based on load patterns
- Monitor resource usage and adjust requests/limits
- Use node affinity for optimal placement
- Consider adding horizontal pod autoscaling (HPA)

---

**🎉 Your crypto data collection platform is now ready for automated CI/CD deployment!**

For additional support, check the deployment logs in GitHub Actions or examine pod logs using the kubectl commands provided above.