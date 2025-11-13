# Data Collection System Deployment Guide

This guide provides step-by-step instructions for deploying the crypto data collection system across different environments and configurations.

## 🎯 **MANDATORY CENTRALIZED CONFIGURATION**

**⚠️ CRITICAL**: All deployments MUST use the centralized configuration system.

### **📋 Required Pre-Deployment Reading**
- **[Centralized Config Instructions](../CENTRALIZED_CONFIG_INSTRUCTIONS.md)** - **MANDATORY** reading
- **[Table Configuration](../shared/table_config.py)** - Master table registry
- **[Database Configuration](../shared/database_config.py)** - Centralized DB config

### **🔧 Configuration Standards**
All deployment configurations must:
- ✅ Reference centralized table configuration (`shared/table_config.py`)
- ✅ Use centralized database configuration (`shared/database_config.py`)
- ✅ Use environment variables for all external configuration
- ✅ Validate configurations before deployment
- ❌ Never hard-code table names, database credentials, or API keys

---

## 🎯 **Deployment Overview**

The data collection system supports multiple deployment scenarios:

- **Local Development**: Single-node Kubernetes (Docker Desktop, Kind)
- **Multi-Node Cluster**: 4-node specialized architecture
- **Cloud Deployment**: AWS EKS, Google GKE, Azure AKS
- **Hybrid Setup**: On-premises data collection with cloud analytics

## 🔧 **Prerequisites**

### **Required Software**
- **Kubernetes 1.21+**: kubectl, cluster access
- **Docker 20.10+**: Container runtime
- **Helm 3.8+**: Package manager (optional but recommended)
- **Git**: Repository access

### **System Requirements**

#### **Development Environment**
- **CPU**: 4 cores minimum, 8 cores recommended
- **Memory**: 8GB minimum, 16GB recommended
- **Storage**: 50GB available space
- **Network**: Stable internet for external API access

#### **Production Environment**
- **CPU**: 8 cores minimum, 16 cores recommended
- **Memory**: 16GB minimum, 32GB recommended
- **Storage**: 200GB SSD storage
- **Network**: Low latency, high bandwidth (1Gbps+)

### **External Services**
- **Windows MySQL Server**: Accessible via network ⚠️ **CRITICAL: MySQL must ONLY run on Windows host, NOT in Kubernetes**
- **API Keys**: CoinGecko Premium, FRED, Guardian, OpenAI
- **Network Access**: Outbound HTTPS (443) for external APIs
- **Monitoring Stack**: Prometheus, Grafana, Alertmanager (deployed in crypto-data-collection namespace)

## 🚀 **Quick Start Deployment**

### **1. Local Development Setup**

```bash
# 1. Clone the repository
git clone https://github.com/your-org/crypto-data-collection.git
cd crypto-data-collection

# 2. Start local Kubernetes cluster
kind create cluster --name crypto-data-collection

# 3. Deploy the system
./scripts/deploy.sh --environment development

# 4. Verify deployment
./scripts/validate.sh

# 5. Access the API
kubectl port-forward svc/data-api-gateway 8000:8000 -n crypto-collectors
curl http://localhost:8000/health
```

### **2. Production Deployment**

```bash
# 1. Configure production environment
cp config/secrets.example.yaml config/secrets.yaml
# Edit secrets.yaml with production API keys

# 2. Deploy to production cluster
export KUBECONFIG=/path/to/production/kubeconfig
./scripts/deploy.sh --environment production --validate

# 3. Configure ingress (if needed)
kubectl apply -f k8s/ingress/production-ingress.yaml

# 4. Set up monitoring
./scripts/setup-monitoring.sh
```

## 📋 **Step-by-Step Deployment**

### **Step 0: Centralized Configuration Validation**

**⚠️ MANDATORY**: Validate centralized configuration before any deployment.

```bash
# 1. Validate centralized table configuration
cd /path/to/crypto-data-collection
python3 shared/table_config.py

# Expected output:
# ✅ Master Onchain Table: crypto_onchain_data
# ✅ Approved Tables: [list of approved tables]
# ⚠️ Deprecated Tables: [list of deprecated tables]
```

```bash
# 2. Validate centralized database configuration
python3 shared/database_config.py

# Expected output:
# ✅ Database configuration is working correctly!
# 📊 Connection: news_collector@172.22.32.1:3306/crypto_prices
```

```bash
# 3. Validate environment variables are set
python3 -c "
from shared.table_config import CRYPTO_TABLES, validate_table_usage
from shared.database_config import test_db_connection

# Test table configuration
print('Testing table configuration...')
assert CRYPTO_TABLES['ONCHAIN_DATA'] == 'crypto_onchain_data'
print('✅ Table configuration validated')

# Test database connectivity  
print('Testing database connectivity...')
assert test_db_connection() == True
print('✅ Database connectivity validated')

print('🎉 All centralized configuration tests passed!')
"
```

**🚨 DEPLOYMENT RULE**: If any validation fails, DO NOT proceed with deployment.

### **Step 1: Environment Preparation**

#### **1.1 Kubernetes Cluster Setup**

For **Docker Desktop**:
```bash
# Enable Kubernetes in Docker Desktop settings
# Allocate at least 4GB RAM and 2 CPUs
```

For **Kind** (local development):
```bash
# Create cluster with custom configuration
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: crypto-data
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "node-type=data-collection"
  extraPortMappings:
  - containerPort: 8000
    hostPort: 8000
    protocol: TCP
EOF
```

For **Multi-Node Production**:
```bash
# Label nodes for specific workloads
kubectl label nodes cryptoai-data-collection node-type=data-collection
kubectl label nodes cryptoai-trading-engine node-type=trading
kubectl label nodes cryptoai-analytics node-type=analytics

# Verify node labels
kubectl get nodes --show-labels
```

#### **1.2 Database Connectivity Test**

⚠️ **IMPORTANT**: MySQL should ONLY run on Windows host, NOT in Kubernetes cluster.

```bash
# Test MySQL connectivity from Kubernetes
kubectl run mysql-test --image=mysql:8.0 --rm -it --restart=Never -- \
  mysql -h host.docker.internal -u news_collector -p99Rules! -e "SHOW DATABASES;"

# Expected output should include:
# crypto_prices
# crypto_transactions
# stock_market_news
```

### **Step 2: Centralized Configuration Setup**

#### **2.1 Validate Centralized Configuration Files**

**⚠️ MANDATORY**: Ensure centralized configuration files are present and valid.

```bash
# 1. Verify centralized table configuration exists
ls -la shared/table_config.py
python3 -c "from shared.table_config import CRYPTO_TABLES; print('✅ Table config loaded')"

# 2. Verify centralized database configuration exists  
ls -la shared/database_config.py
python3 -c "from shared.database_config import get_db_config; print('✅ DB config loaded')"

# 3. Test centralized configuration functionality
python3 -c "
from shared.table_config import validate_table_usage, get_master_onchain_table
print(f'✅ Master onchain table: {get_master_onchain_table()}')

# Test validation
result = validate_table_usage('crypto_onchain_data')
assert result['status'] == 'approved'
print('✅ Table validation working')

result = validate_table_usage('invalid_table')
assert result['status'] == 'unknown'
print('✅ Invalid table detection working')
"
```

#### **2.2 API Keys Configuration (Environment Variables)**

**RULE**: All API keys MUST be configured via environment variables, never hard-coded.

Create the secrets file:
```bash
cp config/secrets.example.yaml config/secrets.yaml
```

Edit `config/secrets.yaml` with proper environment variable references:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: crypto-collectors
type: Opaque
stringData:
  # External API Keys (NEVER hard-code these)
  COINGECKO_API_KEY: "CG-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  FRED_API_KEY: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  GUARDIAN_API_KEY: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  REDDIT_CLIENT_ID: "xxxxxxxxxxxxxxxxxxxx"
  REDDIT_CLIENT_SECRET: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  OPENAI_API_KEY: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  
  # Database Configuration (reference centralized config)
  DB_HOST: "172.22.32.1"
  DB_PORT: "3306"
  DB_USER: "news_collector"
  DB_PASSWORD: "99Rules!"
  DB_NAME: "crypto_prices"
  DB_CONNECTION_TIMEOUT: "30"
  DB_POOL_SIZE: "10"
```

#### **2.3 Environment Configuration Using Centralized Config**

**RULE**: All deployment configurations must reference centralized configuration.

**Development (`config/values/development.yaml`)**:
```yaml
environment: development
replicaCount: 1
autoscaling:
  enabled: false

# Reference centralized configuration
centralizedConfig:
  enabled: true
  tableConfigPath: "/app/shared/table_config.py"
  databaseConfigPath: "/app/shared/database_config.py"

resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "250m"

database:
  host: "host.docker.internal"
  maxConnections: 10

collectors:
  crypto_prices:
    interval: "5m"
    enabled: true
  crypto_news:
    interval: "15m"
    enabled: true
  technical_indicators:
    interval: "5m"
    enabled: true

monitoring:
  enabled: false
```

**Production (`config/values/production.yaml`)**:
```yaml
environment: production
replicaCount: 3
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

database:
  host: "host.docker.internal"
  maxConnections: 50
  connectionTimeout: 30s

collectors:
  crypto_prices:
    interval: "1m"
    enabled: true
  crypto_news:
    interval: "5m"
    enabled: true
  technical_indicators:
    interval: "1m"
    enabled: true

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true

ingress:
  enabled: true
  className: "nginx"
  hosts:
  - host: data-api.crypto-trading.local
    paths:
    - path: /
      pathType: Prefix
```

### **Step 3: Deployment Execution**

#### **3.1 Using Deployment Script (Recommended)**

```bash
# Deploy with validation
./scripts/deploy.sh --environment production --validate --wait

# Deploy specific components only
./scripts/deploy.sh --components collectors,api --environment development

# Deploy with custom values
./scripts/deploy.sh --values-file custom-values.yaml
```

#### **3.2 Manual Kubernetes Deployment**

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply configurations
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f config/secrets.yaml

# 3. Deploy collectors
kubectl apply -f k8s/collectors/

# 4. Deploy processing services
kubectl apply -f k8s/processing/

# 5. Deploy API services
kubectl apply -f k8s/api/

# 6. Deploy monitoring (optional)
kubectl apply -f k8s/monitoring/
```

#### **3.3 Using Helm (Advanced)**

```bash
# 1. Add Helm repository (if using custom charts)
helm repo add crypto-data-collection ./charts

# 2. Install with development values
helm install data-collection crypto-data-collection/crypto-data-collection \
  --namespace crypto-collectors \
  --create-namespace \
  --values config/values/development.yaml

# 3. Upgrade deployment
helm upgrade data-collection crypto-data-collection/crypto-data-collection \
  --values config/values/production.yaml

# 4. Rollback if needed
helm rollback data-collection 1
```

### **Step 4: Verification & Testing**

#### **4.1 Service Health Checks**

```bash
# Check all pods are running
kubectl get pods -n crypto-collectors

# Check service endpoints
kubectl get svc -n crypto-collectors

# Test API Gateway health
kubectl exec -n crypto-collectors deployment/data-api-gateway -- \
  curl http://localhost:8000/health

# Test collector health
for service in crypto-prices crypto-news technical-indicators; do
  echo "Testing $service:"
  kubectl exec -n crypto-collectors deployment/$service-collector -- \
    curl http://localhost:8080/health
done
```

#### **4.2 Database Connectivity**

```bash
# Test database connections from pods
kubectl exec -n crypto-collectors deployment/crypto-prices-collector -- \
  mysql -h host.docker.internal -u news_collector -p99Rules! \
  -e "SELECT COUNT(*) FROM crypto_prices.price_data;"

# Test Redis connectivity
kubectl exec -n crypto-collectors deployment/data-api-gateway -- \
  redis-cli -h host.docker.internal ping
```

#### **4.3 API Endpoint Testing**

```bash
# Port forward API Gateway
kubectl port-forward -n crypto-collectors svc/data-api-gateway 8000:8000 &

# Test REST endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/prices/current/bitcoin
curl http://localhost:8000/api/v1/sentiment/crypto/bitcoin

# Test WebSocket (using wscat)
npm install -g wscat
wscat -c ws://localhost:8000/ws/prices

# Test GraphQL
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ currentPrice(symbol: \"bitcoin\") { symbol price timestamp } }"
  }'
```

#### **4.4 Data Collection Validation**

```bash
# Check data collection is working
./scripts/validate.sh --comprehensive

# Monitor collection logs
kubectl logs -n crypto-collectors -l app=collector -f

# Check database for new data
kubectl exec -n crypto-collectors deployment/data-api-gateway -- \
  mysql -h host.docker.internal -u news_collector -p99Rules! \
  -e "SELECT symbol, COUNT(*) as records, MAX(timestamp) as latest 
      FROM crypto_prices.price_data 
      GROUP BY symbol 
      ORDER BY latest DESC 
      LIMIT 10;"
```

## 🌐 **Environment-Specific Deployments**

### **Development Environment**

Optimized for development and testing:

```bash
# Quick development setup
./scripts/dev-setup.sh

# Start with minimal resources
kubectl apply -f k8s/environments/development/

# Enable debug logging
kubectl set env deployment -n crypto-collectors --all LOG_LEVEL=DEBUG

# Hot reload for development
kubectl patch deployment data-api-gateway -n crypto-collectors -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"api-gateway","imagePullPolicy":"Always"}]}}}}'
```

### **Staging Environment**

Production-like environment for testing:

```bash
# Deploy staging environment
./scripts/deploy.sh --environment staging

# Configure staging-specific settings
kubectl apply -f k8s/environments/staging/

# Run integration tests
./scripts/test-integration.sh --environment staging
```

### **Production Environment**

High-availability production deployment:

```bash
# Pre-deployment checks
./scripts/pre-deployment-check.sh --environment production

# Deploy with validation
./scripts/deploy.sh --environment production --validate --wait

# Configure production monitoring
kubectl apply -f k8s/monitoring/production/

# Set up backup jobs
kubectl apply -f k8s/backup/production/
```

### **Multi-Region Deployment**

For global deployments across multiple regions:

```bash
# Deploy to multiple clusters
for region in us-east-1 eu-west-1 ap-southeast-1; do
  echo "Deploying to $region"
  export KUBECONFIG=~/.kube/config-$region
  ./scripts/deploy.sh --environment production --region $region
done

# Configure cross-region data replication
kubectl apply -f k8s/multi-region/
```

## ☁️ **Cloud Platform Deployments**

### **AWS EKS Deployment**

```bash
# 1. Create EKS cluster
eksctl create cluster --name crypto-data-collection \
  --region us-west-2 \
  --nodegroup-name data-collectors \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --node-type m5.xlarge

# 2. Configure AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --set clusterName=crypto-data-collection \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  -n kube-system

# 3. Deploy application
./scripts/deploy.sh --environment production --cloud aws
```

### **Google GKE Deployment**

```bash
# 1. Create GKE cluster
gcloud container clusters create crypto-data-collection \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --machine-type n1-standard-4

# 2. Get credentials
gcloud container clusters get-credentials crypto-data-collection --zone us-central1-a

# 3. Deploy application
./scripts/deploy.sh --environment production --cloud gcp
```

### **Azure AKS Deployment**

```bash
# 1. Create resource group
az group create --name crypto-data-collection --location eastus

# 2. Create AKS cluster
az aks create \
  --resource-group crypto-data-collection \
  --name crypto-data-collection \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# 3. Get credentials
az aks get-credentials --resource-group crypto-data-collection --name crypto-data-collection

# 4. Deploy application
./scripts/deploy.sh --environment production --cloud azure
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Database Connection Issues**
```bash
# Test connectivity
kubectl run mysql-test --image=mysql:8.0 --rm -it --restart=Never -- \
  mysql -h host.docker.internal -u news_collector -p99Rules! -e "SELECT 1;"

# Check firewall settings on Windows host
# Ensure MySQL is listening on all interfaces (0.0.0.0:3306)
```

#### **API Key Issues**
```bash
# Verify secrets are applied
kubectl get secrets -n crypto-collectors

# Check environment variables in pods
kubectl exec -n crypto-collectors deployment/crypto-prices-collector -- env | grep API_KEY

# Test external API connectivity
kubectl exec -n crypto-collectors deployment/crypto-prices-collector -- \
  curl -H "x-cg-demo-api-key: YOUR_API_KEY" \
  "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
```

#### **Resource Issues**
```bash
# Check resource usage
kubectl top pods -n crypto-collectors
kubectl describe nodes

# Scale down if needed
kubectl scale deployment --all --replicas=1 -n crypto-collectors

# Check logs for OOM kills
kubectl logs -n crypto-collectors deployment/crypto-prices-collector --previous
```

#### **Network Issues**
```bash
# Test inter-pod connectivity
kubectl exec -n crypto-collectors deployment/data-api-gateway -- \
  curl http://crypto-prices-collector.crypto-collectors.svc.cluster.local:8080/health

# Check DNS resolution
kubectl exec -n crypto-collectors deployment/data-api-gateway -- \
  nslookup crypto-prices-collector.crypto-collectors.svc.cluster.local

# Test external connectivity
kubectl exec -n crypto-collectors deployment/crypto-prices-collector -- \
  curl -I https://api.coingecko.com
```

### **Debugging Tools**

#### **Log Analysis**
```bash
# Centralized logging
kubectl logs -n crypto-collectors -l app=data-collection -f --tail=100

# Specific service logs
kubectl logs -n crypto-collectors deployment/crypto-prices-collector -f

# Log aggregation with stern (if available)
stern -n crypto-collectors ".*"
```

#### **Performance Monitoring**
```bash
# Resource usage
kubectl top pods -n crypto-collectors
kubectl top nodes

# Metrics endpoint
kubectl port-forward -n crypto-collectors svc/data-api-gateway 9090:9090
curl http://localhost:9090/metrics
```

#### **Network Debugging**
```bash
# Network policies
kubectl get networkpolicies -n crypto-collectors

# Service endpoints
kubectl get endpoints -n crypto-collectors

# Pod to pod connectivity
kubectl exec -n crypto-collectors deployment/data-api-gateway -- \
  ping crypto-prices-collector.crypto-collectors.svc.cluster.local
```

## 📊 **Post-Deployment Configuration**

### **Monitoring Setup**

```bash
# Deploy Prometheus and Grafana
kubectl apply -f k8s/monitoring/

# Import Grafana dashboards
kubectl create configmap grafana-dashboards \
  --from-file=dashboards/ \
  -n crypto-collectors

# Configure alerts
kubectl apply -f k8s/monitoring/alerts/
```

### **Backup Configuration**

```bash
# Set up database backups
kubectl apply -f k8s/backup/mysql-backup-cronjob.yaml

# Configure persistent volume backups
kubectl apply -f k8s/backup/pv-backup-cronjob.yaml
```

### **SSL/TLS Configuration**

```bash
# Install cert-manager
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.8.0/cert-manager.yaml

# Configure TLS certificates
kubectl apply -f k8s/tls/
```

This deployment guide provides comprehensive instructions for setting up the crypto data collection system across various environments and platforms.