# GitHub Actions Integration Guide

## Overview
This document explains the changes made to integrate the optimized Docker build system with GitHub Actions CI/CD pipelines.

## Build System Changes

### Old System (Multi-Stage Dockerfile)
- **Single Dockerfile** with multiple build targets
- Images: `megabob70/crypto-<service>:latest`
- Size: 154.8GB total (12.9GB per image)
- All images included unnecessary ML libraries

### New System (Tiered Requirements)
- **Individual Dockerfiles** per service (12 total)
- Images: `crypto-enhanced-<service>:latest`
- Size: 22.5GB total (85.5% reduction)
- 4 requirement tiers:
  1. **Ultra-minimal** (214MB): schedule, requests, fastapi - 7 collectors
  2. **With-data** (259MB): ultra-minimal + pandas + numpy - 1 collector
  3. **Financial** (259MB): ultra-minimal + pandas + yfinance - 3 collectors
  4. **ML** (4.4GB): ultra-minimal + torch + transformers - 1 collector

## GitHub Actions Workflow Updates

### Modified Workflows

#### 1. `complete-ci-cd.yml` (Main CI/CD Pipeline)
**Changes Made:**
- Replaced multi-stage Docker build with `scripts/build-docker-images.sh`
- Updated image tagging to use `crypto-enhanced-*` → `megabob70/crypto-*` mapping
- Added image push step after build
- Preserved disk space optimization strategies

**Build Process:**
```bash
# Old (multi-stage):
docker build --target news-collector -t megabob70/crypto-news-collector:latest .

# New (individual Dockerfiles):
./scripts/build-docker-images.sh  # Builds all 12 images
docker tag crypto-enhanced-news-collector:latest megabob70/crypto-news-collector:latest
docker push megabob70/crypto-news-collector:latest
```

**Key Steps:**
1. Run `scripts/build-docker-images.sh` to build all 12 optimized images
2. Tag each `crypto-enhanced-*` image as `megabob70/crypto-*` for Docker Hub
3. Push all images to Docker Hub
4. Clean up to save disk space

#### 2. `k3d-deploy.yml` (NEW - Local K3d Deployment)
**Purpose:** Optimized workflow for local K3d deployments

**Features:**
- Uses `scripts/build-docker-images.sh` for builds
- Imports images directly to K3d (no Docker Hub push needed)
- Triggers on service code changes
- Manual workflow dispatch with rebuild options
- Comprehensive health checks and status reporting

**Workflow Inputs:**
- `rebuild_all`: Force rebuild without cache
- `deploy_only`: Skip build, deploy existing images

### Image Name Mapping

| Local K3d | Docker Hub | Service |
|-----------|------------|---------|
| crypto-enhanced-news-collector | megabob70/crypto-news-collector | News Collection |
| crypto-enhanced-sentiment-ml | megabob70/crypto-sentiment-ml | Sentiment ML |
| crypto-enhanced-technical-calculator | megabob70/crypto-technical-calculator | Technical Analysis |
| crypto-enhanced-ohlc-collector | megabob70/crypto-ohlc-collector | OHLC Data |
| crypto-enhanced-macro-collector-v2 | megabob70/crypto-macro-collector-v2 | Macro Indicators |
| crypto-enhanced-onchain-collector | megabob70/crypto-onchain-collector | On-chain Data |
| crypto-enhanced-derivatives-collector | megabob70/crypto-derivatives-collector | Derivatives |
| crypto-enhanced-ml-market-collector | megabob70/crypto-ml-market-collector | ML Market Analysis |
| crypto-enhanced-news-collector-sub | megabob70/crypto-news-collector-sub | News Subscriber |
| crypto-enhanced-crypto-prices-service | megabob70/crypto-prices-service | Price Service |
| crypto-enhanced-technical-indicators | megabob70/crypto-technical-indicators | Technical Indicators |
| crypto-enhanced-materialized-updater | megabob70/crypto-materialized-updater | Materialized Views |

## Deployment Configuration Updates

### K8s Manifests
The deployment manifests in `k8s/k3s-production/` already use the correct `crypto-enhanced-*` image names:

```yaml
# k8s/k3s-production/services-deployment-updated.yaml
spec:
  containers:
  - name: news-collector
    image: crypto-enhanced-news-collector:latest  # ✅ Correct
```

### Local K3d Deployment
For local K3d deployments, images stay local:
1. Build with `scripts/build-docker-images.sh`
2. Import to K3d: `k3d image import crypto-enhanced-*:latest -c crypto-k3s`
3. Deploy: `kubectl apply -f k8s/k3s-production/services-deployment-updated.yaml`

### Docker Hub Deployment (via GitHub Actions)
For GitHub Actions CI/CD:
1. Build with `scripts/build-docker-images.sh`
2. Tag for Docker Hub: `crypto-enhanced-* → megabob70/crypto-*`
3. Push to Docker Hub
4. Update deployment YAMLs to use `megabob70/crypto-*:latest` OR
5. Pull from Docker Hub to K3d before deployment

## Verification Steps

### 1. Local Build Test
```bash
# Test build script
cd /mnt/e/git/crypto-data-collection
chmod +x scripts/build-docker-images.sh
./scripts/build-docker-images.sh

# Verify images
docker images | grep crypto-enhanced

# Check total size (should be ~22.5GB)
docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | grep crypto-enhanced
```

### 2. GitHub Actions Test
```bash
# Trigger workflow manually
gh workflow run k3d-deploy.yml

# Monitor progress
gh run watch

# Check logs
gh run view --log
```

### 3. K3d Deployment Test
```bash
# Import images
k3d image import crypto-enhanced-*:latest -c crypto-k3s

# Deploy
kubectl apply -f k8s/k3s-production/services-deployment-updated.yaml

# Verify pods
kubectl get pods -n crypto-core-production
```

## Disk Space Management

### Workflow Optimizations
Both workflows include aggressive disk space management:

1. **Pre-build cleanup:**
   - Remove pre-installed software
   - Clean Docker system
   - Clear temporary files

2. **During build:**
   - Check available space before each image
   - Remove intermediate layers
   - Prune build cache

3. **Post-build:**
   - Remove local images after push
   - Final system prune

### Minimum Requirements
- **Local K3d build:** 25GB free (all images kept locally)
- **GitHub Actions build:** 15GB free (images pushed and removed)
- **Minimal build:** 8GB free (core services only)

## Troubleshooting

### Issue: Workflow fails with "insufficient disk space"
**Solution:**
```bash
# Manual cleanup
docker system prune -af --volumes

# Check available space
df -h
```

### Issue: Images not found in K3d
**Solution:**
```bash
# Import images manually
k3d image import crypto-enhanced-news-collector:latest -c crypto-k3s

# Verify import
docker exec k3d-crypto-k3s-server-0 crictl images | grep crypto-enhanced
```

### Issue: Pods in CrashLoopBackOff after deployment
**Solution:**
```bash
# Check logs
kubectl logs -f deployment/enhanced-news-collector -n crypto-core-production

# Verify image names match
kubectl get deployment enhanced-news-collector -n crypto-core-production -o yaml | grep image:

# Restart deployment
kubectl rollout restart deployment/enhanced-news-collector -n crypto-core-production
```

### Issue: GitHub Actions workflow uses old image names
**Solution:**
Update deployment YAMLs to pull from Docker Hub:
```yaml
spec:
  containers:
  - name: news-collector
    image: megabob70/crypto-news-collector:latest
    imagePullPolicy: Always
```

## Next Steps

### Option 1: Use Local K3d Images (Current)
- ✅ No Docker Hub required
- ✅ Faster deployments (no pull)
- ❌ Manual image builds required
- ❌ Not scalable to multiple machines

**Best for:** Local development, single-node K3d

### Option 2: Use Docker Hub Registry
- ✅ Centralized image storage
- ✅ Automated via GitHub Actions
- ✅ Scalable to multiple nodes
- ❌ Requires Docker Hub credentials
- ❌ Slower initial pulls

**Best for:** Production K3s, team collaboration

### Option 3: Use K3d Private Registry
- ✅ Local registry performance
- ✅ No external dependencies
- ✅ Automated registry-to-cluster flow
- ❌ Additional setup complexity

**Best for:** Advanced local development, air-gapped environments

## Recommended Configuration

### For GitHub Actions → K3d Workflow:
```yaml
# .github/workflows/k3d-deploy.yml
- Build images with scripts/build-docker-images.sh
- Import directly to K3d (no push)
- Deploy with crypto-enhanced-* image names
```

### For GitHub Actions → Production K3s:
```yaml
# .github/workflows/complete-ci-cd.yml
- Build images with scripts/build-docker-images.sh
- Tag as megabob70/crypto-* 
- Push to Docker Hub
- Pull from Docker Hub in K3s deployment
- Deploy with megabob70/crypto-* image names
```

## Summary of Changes

### Files Modified:
1. `.github/workflows/complete-ci-cd.yml`
   - Updated build step to use `scripts/build-docker-images.sh`
   - Added image tagging and push steps
   - Preserved disk space optimizations

2. `.github/workflows/k3d-deploy.yml` (NEW)
   - Optimized workflow for local K3d
   - Direct image import (no Docker Hub)
   - Comprehensive health checks

### Files Not Modified (Already Compatible):
- `k8s/k3s-production/services-deployment-updated.yaml` (uses crypto-enhanced-*)
- `scripts/build-docker-images.sh` (already creates optimized images)
- All `requirements-*.txt` files (already optimized)
- Individual Dockerfiles (already fixed with correct paths)

## Testing Checklist

- [ ] Local build script runs successfully
- [ ] All 12 images build without errors
- [ ] Total image size ~22.5GB (85.5% reduction achieved)
- [ ] K3d import completes successfully
- [ ] All pods restart and reach Running state
- [ ] GitHub Actions workflow runs without errors
- [ ] Images pushed to Docker Hub successfully
- [ ] K3s deployment pulls and uses correct images
- [ ] No CrashLoopBackOff after deployment
- [ ] All collectors functioning with minimal dependencies
