# 🏗️ External Model Storage Architecture

## 🎯 **Multi-Tier External Storage Strategy**

### **🌐 Tier 1: GitHub Releases (Primary)**
```
github.com/mikeepley2/crypto-data-collection/releases/
├── ml-models-v1.0.0.tar.gz           (FinBERT + CryptoBERT)
├── finbert-model-v1.0.0.tar.gz       (FinBERT only)  
├── cryptobert-model-v1.0.0.tar.gz    (CryptoBERT only)
└── twitter-roberta-v1.0.0.tar.gz     (Twitter sentiment)
```

**Benefits:**
- ✅ **Free unlimited storage** for public repos
- ✅ **Version control** for models (v1.0.0, v1.1.0, etc.)
- ✅ **Global CDN** (fast downloads worldwide)  
- ✅ **Release automation** via GitHub Actions
- ✅ **Direct download URLs** for containers

### **🐳 Tier 2: Docker Hub (Secondary)**
```
docker.io/megabob70/
├── crypto-ml-models:finbert-latest
├── crypto-ml-models:cryptobert-latest  
├── crypto-ml-models:all-models-latest
└── crypto-ml-models:twitter-roberta-latest
```

**Benefits:**
- ✅ **Container-native** storage
- ✅ **Layer caching** and deduplication
- ✅ **Init container** pattern support
- ✅ **Kubernetes native** mounting

### **☁️ Tier 3: Cloud Storage (Enterprise)**
```
# S3-Compatible Storage
s3://crypto-data-models/
├── finbert/
│   ├── pytorch_model.bin
│   ├── tokenizer.json
│   └── config.json
├── cryptobert/
└── twitter-roberta/
```

## 🏗️ **Recommended Architecture: GitHub Releases + Docker Hub**

### **📦 GitHub Releases Implementation**

#### **1. Model Release Workflow**
```yaml
# .github/workflows/release-models.yml
name: 📦 Release ML Models

on:
  push:
    paths:
      - 'archive/models/**'
    tags:
      - 'models-v*'
  workflow_dispatch:

jobs:
  release-models:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: 📦 Package Models
      run: |
        # Create separate archives for each model
        cd archive/models
        tar -czf ../../finbert-model-${{ github.ref_name }}.tar.gz finbert/
        tar -czf ../../cryptobert-model-${{ github.ref_name }}.tar.gz cryptobert/
        tar -czf ../../all-models-${{ github.ref_name }}.tar.gz .
        
    - name: 🚀 Create Release
      uses: actions/create-release@v1
      with:
        tag_name: ${{ github.ref_name }}
        release_name: ML Models ${{ github.ref_name }}
        body: |
          ML Models Release ${{ github.ref_name }}
          
          📊 **Model Sizes:**
          - FinBERT: ~1.2GB
          - CryptoBERT: ~1.2GB  
          - All models: ~2.5GB
          
          📋 **Download URLs:**
          - FinBERT only: [finbert-model-${{ github.ref_name }}.tar.gz]
          - CryptoBERT only: [cryptobert-model-${{ github.ref_name }}.tar.gz]
          - All models: [all-models-${{ github.ref_name }}.tar.gz]
          
    - name: ⬆️ Upload Model Assets
      uses: actions/upload-release-asset@v1
      with:
        asset_path: finbert-model-${{ github.ref_name }}.tar.gz
        asset_name: finbert-model-${{ github.ref_name }}.tar.gz
        asset_content_type: application/gzip
```

#### **2. Container Model Downloader**
```dockerfile
# Slim sentiment analyzer with external models
FROM base AS sentiment-analyzer
COPY shared/ ./shared/
COPY services/enhanced_sentiment_ml_analysis.py ./services/
COPY *.py ./

# Model download script
COPY scripts/download-models.sh /app/scripts/
RUN chmod +x /app/scripts/download-models.sh

# Environment for model management
ENV MODEL_CACHE_DIR=/app/models
ENV MODEL_VERSION=v1.0.0
ENV GITHUB_REPO=mikeepley2/crypto-data-collection
ENV MODEL_DOWNLOAD_URL=https://github.com/${GITHUB_REPO}/releases/download

# Create model directory
RUN mkdir -p $MODEL_CACHE_DIR

# Download script (runs on container start)
COPY scripts/ensure-models.py /app/scripts/
RUN chmod +x /app/scripts/ensure-models.py

USER appuser
EXPOSE 8008
CMD ["/app/scripts/ensure-models.py", "&&", "python", "services/enhanced_sentiment_ml_analysis.py"]
```

### **🐳 Docker Hub Model Images**

#### **1. Model-Only Container**
```dockerfile
# Dockerfile.models
FROM alpine:latest AS model-base
RUN apk add --no-cache curl tar

# Download and extract models
WORKDIR /models
ARG MODEL_VERSION=v1.0.0
RUN curl -L https://github.com/mikeepley2/crypto-data-collection/releases/download/${MODEL_VERSION}/all-models-${MODEL_VERSION}.tar.gz | tar xz

FROM scratch
COPY --from=model-base /models /models
```

#### **2. Build Model Images**
```yaml
# In CI/CD after model release
- name: 🐳 Build Model Containers
  run: |
    # Build model-only containers
    docker build -f Dockerfile.models \
      --build-arg MODEL_VERSION=${{ github.ref_name }} \
      -t ${{ secrets.DOCKER_USERNAME }}/crypto-ml-models:${{ github.ref_name }} \
      -t ${{ secrets.DOCKER_USERNAME }}/crypto-ml-models:latest .
    
    # Push model containers
    docker push ${{ secrets.DOCKER_USERNAME }}/crypto-ml-models:${{ github.ref_name }}
    docker push ${{ secrets.DOCKER_USERNAME }}/crypto-ml-models:latest
```

## 🚀 **Container Integration Patterns**

### **Pattern 1: Init Container (Kubernetes)**
```yaml
# K3s deployment with model init container
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-analyzer
spec:
  template:
    spec:
      initContainers:
      - name: model-loader
        image: megabob70/crypto-ml-models:latest
        command: ['cp', '-r', '/models', '/shared-models/']
        volumeMounts:
        - name: models-volume
          mountPath: /shared-models
      
      containers:
      - name: sentiment-analyzer
        image: megabob70/crypto-sentiment-analyzer:latest
        volumeMounts:
        - name: models-volume
          mountPath: /app/models
          readOnly: true
      
      volumes:
      - name: models-volume
        emptyDir: {}
```

### **Pattern 2: Runtime Download (Docker Compose)**
```yaml
# docker-compose.yml
services:
  sentiment-analyzer:
    image: megabob70/crypto-sentiment-analyzer:latest
    environment:
      - MODEL_DOWNLOAD_ON_START=true
      - MODEL_VERSION=v1.0.0
      - MODEL_CACHE_DIR=/app/models
    volumes:
      - model-cache:/app/models
    healthcheck:
      test: ["CMD", "python", "/app/scripts/check-models.py"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  model-cache:
    driver: local
```

### **Pattern 3: Shared Volume (K3s Production)**
```yaml
# Persistent model storage in K3s
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ml-models-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadOnlyMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  hostPath:
    path: /var/lib/k3s/ml-models

---
apiVersion: v1  
kind: PersistentVolumeClaim
metadata:
  name: ml-models-pvc
  namespace: crypto-data-collection
spec:
  accessModes:
    - ReadOnlyMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: local-storage

---
# Model initialization job (runs once)
apiVersion: batch/v1
kind: Job
metadata:
  name: model-downloader
  namespace: crypto-data-collection
spec:
  template:
    spec:
      containers:
      - name: downloader
        image: megabob70/crypto-ml-models:latest
        command: ['cp', '-r', '/models/*', '/shared/']
        volumeMounts:
        - name: ml-models
          mountPath: /shared
      volumes:
      - name: ml-models
        persistentVolumeClaim:
          claimName: ml-models-pvc
      restartPolicy: Never
```

## 🛠️ **Implementation Scripts**

### **Model Download Script**
```bash
#!/bin/bash
# scripts/download-models.sh

set -e

MODEL_VERSION=${MODEL_VERSION:-"v1.0.0"}
GITHUB_REPO=${GITHUB_REPO:-"mikeepley2/crypto-data-collection"}
MODEL_CACHE_DIR=${MODEL_CACHE_DIR:-"/app/models"}
BASE_URL="https://github.com/${GITHUB_REPO}/releases/download"

echo "🔍 Checking for models in ${MODEL_CACHE_DIR}..."

download_model() {
    local model_name=$1
    local model_file="${model_name}-model-${MODEL_VERSION}.tar.gz"
    local download_url="${BASE_URL}/${MODEL_VERSION}/${model_file}"
    local model_dir="${MODEL_CACHE_DIR}/${model_name}"
    
    if [ -d "$model_dir" ] && [ -f "$model_dir/pytorch_model.bin" ]; then
        echo "✅ Model $model_name already exists"
        return 0
    fi
    
    echo "📥 Downloading $model_name from $download_url..."
    mkdir -p "$MODEL_CACHE_DIR"
    
    if curl -L "$download_url" | tar xz -C "$MODEL_CACHE_DIR"; then
        echo "✅ Successfully downloaded $model_name"
    else
        echo "❌ Failed to download $model_name"
        return 1
    fi
}

# Download required models
download_model "finbert"
download_model "cryptobert"

echo "🎉 All models ready!"
```

### **Model Verification Script**
```python
#!/usr/bin/env python3
# scripts/ensure-models.py

import os
import sys
import subprocess
from pathlib import Path

def check_model_exists(model_name, model_dir):
    """Check if model files exist and are valid"""
    model_path = Path(model_dir) / model_name
    required_files = ['pytorch_model.bin', 'config.json', 'tokenizer.json']
    
    if not model_path.exists():
        return False
        
    for file_name in required_files:
        if not (model_path / file_name).exists():
            return False
            
    return True

def main():
    model_cache_dir = os.getenv('MODEL_CACHE_DIR', '/app/models')
    required_models = ['finbert', 'cryptobert']
    
    print("🔍 Verifying ML models...")
    
    missing_models = []
    for model in required_models:
        if not check_model_exists(model, model_cache_dir):
            missing_models.append(model)
            
    if missing_models:
        print(f"📥 Downloading missing models: {missing_models}")
        result = subprocess.run(['/app/scripts/download-models.sh'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to download models: {result.stderr}")
            sys.exit(1)
    else:
        print("✅ All models verified and ready!")

if __name__ == "__main__":
    main()
```

## 📊 **Storage Cost & Performance Analysis**

| Storage Method | Cost/Month | Download Speed | Reliability | Maintenance |
|----------------|------------|----------------|-------------|-------------|
| **GitHub Releases** | Free | Fast (CDN) | ✅ High | ✅ Low |
| **Docker Hub** | Free (public) | Fast | ✅ High | ✅ Low |
| **AWS S3** | ~$2-5 | Very Fast | ✅ Very High | ⚠️ Medium |
| **Bundle in Container** | Free | N/A | ✅ High | ❌ High |

## 🎯 **Recommended Implementation Order**

1. **Phase 1**: GitHub Releases setup (1-2 hours)
2. **Phase 2**: Update containers for external models (1 hour)  
3. **Phase 3**: Docker Hub model containers (30 minutes)
4. **Phase 4**: K3s persistent volume setup (1 hour)

**Total implementation time: ~4-5 hours for complete setup**

Would you like me to implement Phase 1 (GitHub Releases) right now?