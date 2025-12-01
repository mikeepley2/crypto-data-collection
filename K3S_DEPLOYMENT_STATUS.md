# 🚀 K3s Deployment Status - Crypto Data Collection Platform

**Last Updated:** December 1, 2025  
**Status:** ✅ Deployments Active - Pods Starting

---

## 📊 Current Deployment Status

### Cluster Information
- **Cluster Name:** `crypto-k3s` (K3d)
- **Nodes:** 4 (1 server + 3 agents)
- **Kubernetes Version:** v1.31.5+k3s1
- **Namespace:** `crypto-core-production`
- **Database:** MySQL on host via `host.k3d.internal:3306`
- **Cache:** Redis on host via `host.k3d.internal:6379`

### Services Deployed

| Service | Status | Replicas | Port | Purpose |
|---------|--------|----------|------|---------|
| `enhanced-news-collector` | 🟡 Starting | 1/1 | 8001 | News article collection |
| `enhanced-sentiment-ml-analysis` | 🟡 Starting | 1/1 | 8002 | ML sentiment analysis |
| `enhanced-technical-calculator` | 🟡 Starting | 1/1 | 8003 | Technical calculations |
| `enhanced-materialized-updater` | 🟡 Starting | 1/1 | 8004 | View updates |
| `enhanced-crypto-prices-service` | 🟡 Starting | 2/2 | 8005 | Real-time prices |
| `enhanced-crypto-news-collector-sub` | 🟡 Starting | 1/1 | 8006 | Secondary news sources |
| `enhanced-onchain-collector` | 🟡 Starting | 1/1 | 8007 | On-chain metrics |
| `enhanced-technical-indicators-collector` | 🟡 Starting | 1/1 | 8008 | Technical indicators |
| `enhanced-macro-collector-v2` | 🟡 Starting | 1/1 | 8009 | Macro indicators |
| `enhanced-crypto-derivatives-collector` | 🟡 Starting | 1/1 | 8010 | Derivatives data |
| `ml-market-collector` | 🟡 Starting | 1/1 | 8011 | ML market analysis |
| `enhanced-ohlc-collector` | 🟡 Starting | 1/1 | 8012 | OHLC data |
| `crypto-api-gateway` | ✅ Running | 1/1 | 30080 | API Gateway (NodePort) |

**Total:** 13/13 deployments created, pods starting

---

## ✅ Completed Actions

### Infrastructure Setup
- [x] K3d cluster created with 4 nodes
- [x] Self-hosted GitHub Actions runner installed and online
- [x] GitHub Actions workflows configured for CI/CD
- [x] Database connectivity configured (host MySQL via `host.k3d.internal`)
- [x] Redis connectivity configured (host Redis via `host.k3d.internal`)

### Docker Images
- [x] All 12 collector images built (12.9GB each)
- [x] Images imported into K3d cluster
- [x] Deployments restarted to pick up images

### Kubernetes Resources
- [x] Namespaces created (`crypto-core-production`, `crypto-infrastructure`, `crypto-monitoring`)
- [x] ConfigMaps deployed (database config, environment variables)
- [x] Secrets deployed (database credentials, API keys)
- [x] Services created (ClusterIP for collectors, NodePort for gateway)
- [x] Network policies applied
- [x] Resource quotas and limits configured

### Deployment Configuration
- [x] Skipped MySQL/Redis StatefulSet deployment (using host databases)
- [x] Configured `host.k3d.internal` for host service access
- [x] All collector deployments created
- [x] Health check probes configured (`/health` endpoints)

---

## 🔍 Observability Setup

### Documentation Created
✅ **Complete Observability Integration Guide** created:
- File: `docs/OBSERVABILITY_INTEGRATION_GUIDE.md`
- Prometheus configuration for all 12 collectors + gateway
- Grafana dashboard configurations
- Loki log aggregation setup
- Alert rules for health monitoring
- Complete metrics reference

### Monitoring Endpoints Available

All collectors expose standardized endpoints:

#### Health & Status
- `GET /health` - Liveness probe (Kubernetes)
- `GET /ready` - Readiness probe (Kubernetes)
- `GET /status` - Detailed service status with stats

#### Metrics & Logs
- `GET /metrics` - Prometheus metrics (30s scrape interval)
- `GET /logs` - Service logs (Loki integration ready)

#### Data Quality
- `GET /data-quality` - Data quality reports
- `GET /performance` - Performance metrics

#### Control
- `POST /collect` - Manual collection trigger
- `POST /backfill` - Historical data backfill

---

## 🎯 Next Steps

### 1. Verify Pod Health (In Progress)
```bash
# Check pod status
kubectl get pods -n crypto-core-production

# Check running collectors
kubectl get pods -n crypto-core-production | grep Running

# Check service endpoints
kubectl get svc -n crypto-core-production
```

### 2. Test Collector Endpoints
```bash
# Port forward to test a collector
kubectl port-forward -n crypto-core-production svc/enhanced-news-collector-service 8001:8001

# Test health endpoint
curl http://localhost:8001/health

# Test metrics endpoint
curl http://localhost:8001/metrics

# Test status endpoint
curl http://localhost:8001/status | jq
```

### 3. Deploy Observability Stack
```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus (see OBSERVABILITY_INTEGRATION_GUIDE.md)
# Deploy Grafana (see OBSERVABILITY_INTEGRATION_GUIDE.md)
# Deploy Loki + Promtail (see OBSERVABILITY_INTEGRATION_GUIDE.md)
```

### 4. Configure Grafana
1. Access Grafana at `http://localhost:30300`
2. Add Prometheus data source
3. Add Loki data source
4. Import dashboards from guide

### 5. Set Up Alerts
1. Configure Alertmanager
2. Apply alert rules from guide
3. Test alert firing
4. Configure notification channels (Slack, PagerDuty, etc.)

---

## 🔧 Verification Commands

### Check Deployment Status
```bash
# All deployments
kubectl get deployments -n crypto-core-production

# Deployment details
kubectl describe deployment enhanced-news-collector -n crypto-core-production

# Rollout status
kubectl rollout status deployment/enhanced-news-collector -n crypto-core-production
```

### Check Pod Health
```bash
# Pod status
kubectl get pods -n crypto-core-production -o wide

# Pod logs
kubectl logs -n crypto-core-production deployment/enhanced-news-collector --tail=100

# Pod events
kubectl get events -n crypto-core-production --sort-by='.lastTimestamp'
```

### Test Service Connectivity
```bash
# From within cluster
kubectl run test-pod --rm -it --image=curlimages/curl --restart=Never -- \
  curl http://enhanced-news-collector-service.crypto-core-production.svc.cluster.local:8001/health

# Test database connectivity
kubectl run test-db --rm -it --image=mysql:8.0 --restart=Never -- \
  mysql -h host.k3d.internal -u news_collector -p99Rules! -e "SHOW DATABASES;"
```

### Check Resource Usage
```bash
# Pod resources
kubectl top pods -n crypto-core-production

# Node resources
kubectl top nodes

# Resource quotas
kubectl get resourcequota -n crypto-core-production
```

---

## 📈 Expected Metrics

Once pods are running, expect these metrics from each collector:

### Health Metrics
- `collector_health_score` - Service health (0-100)
- `collector_gap_hours` - Hours since last collection
- `collector_running` - Service running status (1=yes, 0=no)

### Collection Metrics
- `collector_total_collected` - Total records collected
- `collector_collection_errors` - Total errors
- `collector_api_calls_made` - API calls made
- `collector_database_writes` - Database write operations

### Performance Metrics
- `collector_collection_duration_seconds` - Collection time
- `collector_db_write_duration_seconds` - DB write latency
- `collector_memory_usage_bytes` - Memory usage
- `collector_cpu_usage_seconds_total` - CPU usage

---

## 🚨 Common Issues & Solutions

### Pods Stuck in ImagePullBackOff
**Solution:** Images imported and deployments restarted ✅

### Pods Failing to Start
```bash
# Check pod describe for errors
kubectl describe pod <pod-name> -n crypto-core-production

# Check logs
kubectl logs <pod-name> -n crypto-core-production

# Common issues:
# - Database connection: Check host.k3d.internal resolves
# - Missing secrets: Verify secrets exist
# - Resource limits: Check if pod is OOMKilled
```

### Database Connection Failures
```bash
# Test DNS resolution
kubectl run test-dns --rm -it --image=busybox --restart=Never -- \
  nslookup host.k3d.internal

# Test MySQL connectivity
kubectl run test-mysql --rm -it --image=mysql:8.0 --restart=Never -- \
  mysql -h host.k3d.internal -u news_collector -p99Rules! -e "SELECT 1;"
```

### High Memory Usage
```bash
# Check if pods are hitting memory limits
kubectl describe pod <pod-name> -n crypto-core-production | grep -A 5 "Last State"

# Increase memory limits in deployment if needed
kubectl set resources deployment <deployment-name> -n crypto-core-production \
  --limits=memory=4Gi --requests=memory=2Gi
```

---

## 📚 Documentation Reference

- **Observability Guide:** `docs/OBSERVABILITY_INTEGRATION_GUIDE.md`
- **K3d Cluster Setup:** `K3D_CLUSTER_SETUP_COMPLETE.md`
- **Deployment Script:** `scripts/deploy-to-k3s.sh`
- **GitHub Actions:** `.github/workflows/quick-k3s-deploy.yml`

---

## 🎉 Success Criteria

### Infrastructure ✅
- [x] K3d cluster running
- [x] Self-hosted runner operational
- [x] CI/CD pipeline configured

### Deployments 🟡 (In Progress)
- [ ] All 12 collector pods running
- [ ] All services healthy (`/health` returns 200)
- [ ] Database connectivity verified
- [ ] Data collection active

### Observability 🟡 (Ready to Deploy)
- [ ] Prometheus deployed and scraping
- [ ] Grafana deployed with dashboards
- [ ] Loki collecting logs
- [ ] Alerts configured

---

## 📞 Support

### Quick Commands
```bash
# Full status check
kubectl get all -n crypto-core-production

# Watch pod status
watch kubectl get pods -n crypto-core-production

# Stream logs from all collectors
kubectl logs -f -n crypto-core-production -l app=collector --all-containers=true

# Restart all deployments
for deploy in $(kubectl get deployments -n crypto-core-production -o name); do 
  kubectl rollout restart -n crypto-core-production $deploy
done
```

### GitHub Actions
- **Workflow:** https://github.com/mikeepley2/crypto-data-collection/actions/workflows/quick-k3s-deploy.yml
- **Runner Status:** Self-hosted runner "k3s-local-runner" online (green dot)

---

**Status Legend:**
- ✅ Complete
- 🟡 In Progress
- ⏳ Pending
- ❌ Failed
