# CI/CD Architecture - Native K3s Deployment

## Architecture Overview

This project uses a **hybrid CI/CD approach** that separates build and deployment concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Push (master)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           GitHub Actions Workflow Triggers                   │
│         (.github/workflows/complete-ci-cd.yml)              │
└─────────────┬───────────────────────────────┬───────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────┐
│   BUILD PHASE                │   │   DEPLOY PHASE          │
│   runs-on: ubuntu-latest     │   │   runs-on: self-hosted  │
│   (GitHub's servers)         │   │   (Your WSL2 machine)   │
│                              │   │                         │
│ ✓ Docker pre-installed       │   │ ✓ K3s cluster access    │
│ ✓ Build 12 containers        │   │ ✓ kubectl configured    │
│ ✓ Push to Docker Hub         │   │ ✓ Local network access  │
│   megabob70/crypto-*:latest  │   │                         │
└──────────────┬───────────────┘   └────────┬────────────────┘
               │                            │
               │ Images ready on Docker Hub │
               └──────────────┬─────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │   Native K3s Pulls   │
                   │   from Docker Hub    │
                   │                      │
                   │ No Docker Desktop    │
                   │ needed on local      │
                   └──────────────────────┘
```

## Key Principles

### 1. **GitHub-Hosted Runners for Builds**
- **Why:** GitHub's `ubuntu-latest` runners have Docker pre-installed
- **What:** Builds all container images from Dockerfiles
- **Benefit:** You don't need Docker Desktop running locally
- **Cost:** Free (2000 minutes/month on free tier)

### 2. **Self-Hosted Runner for Deployment**
- **Why:** Needs direct access to your local K3s cluster
- **What:** Runs kubectl commands to deploy/update services
- **Requirement:** Runner must have kubectl and K3s kubeconfig
- **Location:** Your WSL2 Ubuntu instance

### 3. **Native K3s (Not K3d)**
- **Runtime:** Native K3s service (systemd)
- **Container Engine:** containerd (built into K3s)
- **Docker Desktop:** NOT required, NOT used
- **Image Source:** Pulls from Docker Hub registry

## Workflow Jobs Breakdown

### Job 1: Core Pipeline (GitHub-hosted)
```yaml
core-pipeline:
  runs-on: ubuntu-latest  # ← GitHub's infrastructure
```
- Linting, testing, validation
- Docker image builds (12 collectors)
- Push to Docker Hub as `megabob70/crypto-*:latest`

### Job 2: Database Integration Tests (GitHub-hosted)
```yaml
database-integration:
  runs-on: ubuntu-latest  # ← GitHub's infrastructure
```
- Spins up MySQL/Redis containers
- Runs integration tests
- Validates database operations

### Job 3: K3s Deployment (Self-hosted)
```yaml
k3s-production-deployment:
  runs-on: self-hosted    # ← YOUR machine
```
- Connects to local K3s cluster
- Applies Kubernetes manifests
- K3s pulls images from Docker Hub
- Services start running

## Docker Hub Integration

### Image Naming Convention
- **Local builds:** `crypto-enhanced-<service>:latest`
- **Docker Hub:** `megabob70/<service>:latest`
- **K3s deployments:** Pull from `megabob70/<service>:latest`

### Authentication
- GitHub Actions uses secrets:
  - `DOCKER_USERNAME`: Your Docker Hub username
  - `DOCKER_PASSWORD`: Your Docker Hub access token
  - `DOCKER_REGISTRY`: docker.io

## Local Machine Requirements

### What You NEED:
✅ Native K3s installed and running (`systemctl status k3s`)
✅ Self-hosted GitHub Actions runner
✅ kubectl configured with K3s kubeconfig
✅ Passwordless sudo (for kubectl operations)

### What You DON'T NEED:
❌ Docker Desktop
❌ Docker Engine in WSL2
❌ K3d (K3s in Docker)
❌ Local image builds

## Self-Hosted Runner Setup

### Runner Location
```bash
~/actions-runner/
```

### Runner Service
```bash
# Check status
systemctl --user status actions.runner.*

# View logs
journalctl --user -u actions.runner.* -f
```

### Passwordless Sudo Configuration
Required for kubectl operations:
```bash
# Already configured at:
/etc/sudoers.d/dad-nopasswd
```

## K3s Configuration

### Service Management
```bash
# Check K3s status
sudo systemctl status k3s

# View K3s logs
sudo journalctl -u k3s -f

# K3s configuration
/etc/rancher/k3s/k3s.yaml
```

### Kubeconfig for Runner
The self-hosted runner accesses K3s via the `K3S_KUBECONFIG` GitHub secret, which contains the base64-encoded kubeconfig.

## Deployment Flow

1. **Developer pushes to master**
   ```bash
   git push origin master
   ```

2. **GitHub Actions triggers** (automatically)
   - Workflow: `.github/workflows/complete-ci-cd.yml`

3. **Build phase** (GitHub's servers, ~20-30 min)
   - Checkout code
   - Build 12 Docker images with tiered requirements
   - Push to Docker Hub

4. **Deploy phase** (Your machine, ~2-3 min)
   - Self-hosted runner picks up job
   - Applies K8s manifests to K3s
   - K3s pulls images from Docker Hub
   - Pods start running

5. **Services running** (Native K3s)
   - 12 data collectors active
   - No Docker Desktop needed
   - Images cached in K3s containerd

## Troubleshooting

### Workflow fails with "Docker not found"
**Cause:** Build job is using self-hosted runner instead of GitHub-hosted
**Fix:** Ensure `runs-on: ubuntu-latest` for build jobs

### Deployment fails with "Unable to connect to server"
**Cause:** Self-hosted runner can't access K3s
**Fix:** Verify K3s is running: `sudo systemctl status k3s`

### Images not pulling
**Cause:** Images not pushed to Docker Hub
**Fix:** Check build job logs, verify Docker Hub credentials

### Sudo password prompts in workflow
**Cause:** Passwordless sudo not configured
**Fix:** Already configured in `/etc/sudoers.d/dad-nopasswd`

## Why This Architecture?

### Separation of Concerns
- **Builds** = Heavy, need Docker → GitHub's infrastructure
- **Deploys** = Light, need K3s access → Your infrastructure

### Resource Efficiency
- Don't waste local resources building images
- GitHub provides free compute for builds
- Local runner only for lightweight kubectl operations

### Simplicity
- No Docker Desktop maintenance on local machine
- K3s handles all container runtime needs
- Single source of truth: Docker Hub registry

## Related Documentation

- [K3s Deployment Guide](K3S_DEPLOYMENT_GUIDE.md)
- [GitHub Actions Workflow](.github/workflows/complete-ci-cd.yml)
- [Service Inventory](docs/SERVICE_INVENTORY.md)
- [Build Scripts](scripts/build-docker-images.sh)

## Quick Reference Commands

```bash
# Check workflow status
# Visit: https://github.com/mikeepley2/crypto-data-collection/actions

# Check K3s pods
sudo kubectl get pods -n crypto-core-production

# Check runner status
ps aux | grep actions.runner

# View K3s service logs
sudo journalctl -u k3s -f

# View runner logs
tail -f ~/actions-runner/_diag/Runner_*.log

# Restart a deployment (after new image push)
sudo kubectl rollout restart deployment/<name> -n crypto-core-production
```

---

**Last Updated:** December 5, 2025
**Architecture Status:** ✅ Production-ready with native K3s deployment
