# 🧪 Multi-Environment Testing Guide

## 📋 **Testing Commands for Different Environments**

### **1. Local Development (Fast Unit Tests with Mocks)**
```bash
# Run only unit tests with mock models (fastest)
pytest -m "unit and not real_models" -x

# Run unit tests with coverage
pytest -m unit --cov=services --cov=shared

# Run specific ML sentiment tests
pytest tests/test_enhanced_sentiment_ml_multi_env.py -v

# Test with different model environments
MODEL_CACHE_DIR=./dev_models pytest tests/test_enhanced_sentiment_ml_multi_env.py
```

### **2. Local Integration Testing (Real Models)**
```bash
# Run integration tests with real model downloads (slower)
export MODEL_CACHE_DIR=./integration_models
export RUN_INTEGRATION_TESTS=true
pytest -m "integration and ml_models" --timeout=900

# Test with real models but skip API calls
pytest -m "integration and not real_api and ml_models"

# Full local integration test
pytest -m "integration" -x --tb=short
```

### **3. CI/CD Pipeline Testing**
```bash
# GitHub Actions - unit tests only (fast CI)
pytest -m "unit and not slow" --timeout=300

# GitHub Actions - integration with model downloads
export GITHUB_ACTIONS=true
export MODEL_CACHE_DIR=/tmp/ci_models
pytest -m "integration and ml_models" --timeout=900

# CI smoke tests
pytest -m smoke --tb=line
```

### **4. K3s Production Validation**
```bash
# Production health checks
kubectl exec deployment/sentiment-analyzer -n crypto-data-collection -- \
  python -c "
from shared.smart_model_manager import get_model_manager
manager = get_model_manager()
print(f'Environment: {manager.environment.value}')
print(f'Models loaded: {list(manager.models.keys())}')
"

# Test model access in production
kubectl exec deployment/sentiment-analyzer -n crypto-data-collection -- \
  python scripts/validate-models.py --quiet

# Production integration test
kubectl port-forward deployment/sentiment-analyzer 8008:8008 &
pytest tests/test_production_endpoints.py
```

## 🔧 **Environment-Specific Test Configuration**

### **pytest.ini Sections by Environment**
```ini
# For local development
[testenv:dev]
deps = 
    pytest
    pytest-asyncio
    pytest-mock
setenv =
    TESTING = true
    MODEL_CACHE_DIR = ./dev_models
commands = pytest -m "unit" {posargs}

# For integration testing  
[testenv:integration]
deps = 
    pytest
    pytest-asyncio 
    transformers
    torch
setenv =
    MODEL_CACHE_DIR = ./integration_models
    RUN_INTEGRATION_TESTS = true
commands = pytest -m "integration" {posargs}

# For CI/CD
[testenv:ci]
deps = 
    pytest
    pytest-asyncio
    pytest-timeout
setenv =
    GITHUB_ACTIONS = true
    MODEL_CACHE_DIR = /tmp/ci_models
    TESTING = ""
commands = pytest -m "unit and integration" --timeout=600 {posargs}
```

## 📊 **Test Matrix by Environment**

| Environment | Model Source | Test Types | Duration | Use Cases |
|-------------|--------------|------------|----------|-----------|
| **Unit Tests** | Mock Models | unit, mock_models | <30s | Development, PR checks |
| **Local Integration** | Local Cache | integration, real_models | 2-5min | Full local testing |
| **CI/CD** | Download On-Demand | unit, integration | 3-8min | Automated testing |
| **Production** | Persistent Volume | smoke, health | <1min | Production validation |

## 🚀 **GitHub Actions Workflow Examples**

### **Fast Unit Tests (Pull Requests)**
```yaml
name: Fast Unit Tests
on: [pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-asyncio pytest-mock
        pip install -e .
    
    - name: Run unit tests with mocks
      env:
        TESTING: true
      run: |
        pytest -m "unit and not slow" --timeout=300 -v
```

### **Integration Tests (Main Branch)**
```yaml
name: Integration Tests
on: 
  push:
    branches: [main, dev]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: [unit, integration]
        
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-asyncio transformers torch
        pip install -e .
    
    - name: Run unit tests
      if: matrix.test-group == 'unit'
      env:
        TESTING: true
      run: |
        pytest -m unit -v
    
    - name: Run integration tests with model downloads
      if: matrix.test-group == 'integration'
      env:
        GITHUB_ACTIONS: true
        MODEL_CACHE_DIR: /tmp/ci_models
        RUN_INTEGRATION_TESTS: true
      run: |
        pytest -m "integration and ml_models" --timeout=900 -v
```

### **Production Deployment Tests**
```yaml
name: Production Tests
on:
  workflow_run:
    workflows: ["Deploy to K3s"]
    types: [completed]

jobs:
  production-validation:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure kubectl
      run: |
        # Configure kubectl for K3s cluster
        
    - name: Validate persistent model storage
      run: |
        ./scripts/k3s-models.sh status
        ./scripts/k3s-models.sh validate
    
    - name: Run production health checks
      run: |
        kubectl wait --for=condition=ready pod -l app=sentiment-analyzer --timeout=300s
        kubectl exec deployment/sentiment-analyzer -- python scripts/validate-models.py
    
    - name: Run smoke tests against production
      run: |
        kubectl port-forward deployment/sentiment-analyzer 8008:8008 &
        sleep 10
        pytest -m smoke --timeout=60
```

## 💡 **Testing Best Practices by Environment**

### **Development (Local)**
```bash
# Quick feedback loop
pytest tests/test_enhanced_sentiment_ml_multi_env.py::TestSmartModelManager -v

# Test specific functionality
pytest -k "test_mock_sentiment" -v

# Watch mode for TDD
pytest -f tests/test_enhanced_sentiment_ml_multi_env.py
```

### **CI/CD Optimization**
```bash
# Parallel test execution
pytest -n auto -m "unit"

# Selective test running based on changes
pytest --lf --ff -x  # Last failed, fail fast

# Test result caching
pytest --cache-show
```

### **Production Monitoring**
```bash
# Continuous production validation
while true; do
  ./scripts/k3s-models.sh validate
  sleep 300  # Every 5 minutes
done

# Model performance monitoring
kubectl exec deployment/sentiment-analyzer -- python -c "
from shared.smart_model_manager import get_model_manager
manager = get_model_manager()
print('Model loading history:')
for entry in manager.loading_history[-10:]:
    print(f'{entry[\"model\"]}: {entry[\"load_time\"]:.2f}s - {entry[\"success\"]}')
"
```

## 🎯 **Environment Selection Strategy**

### **When to Use Each Environment:**

1. **Mock Models (Unit Tests)**
   - ✅ During development
   - ✅ PR validation  
   - ✅ Fast feedback
   - ❌ Model accuracy validation

2. **Local Cache (Integration)**
   - ✅ Full feature testing
   - ✅ Model accuracy validation
   - ✅ Development debugging
   - ❌ CI/CD (cache not shared)

3. **Download On-Demand (CI/CD)**
   - ✅ Automated testing
   - ✅ Clean environment
   - ✅ Reproducible results
   - ❌ Slow first run

4. **Persistent Volume (Production)**
   - ✅ Maximum performance
   - ✅ Production validation
   - ✅ Consistent environment
   - ❌ Only available in K3s

This multi-environment testing strategy ensures your ML services work reliably across all deployment scenarios while maintaining fast development cycles! 🚀