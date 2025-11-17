# Crypto Data Collection - Testing & CI/CD Setup

## Overview

This document outlines the comprehensive testing framework and CI/CD pipeline for the crypto data collection system.

## Testing Framework

### Test Structure

```
tests/
├── test_base_collector.py           # Base collector functionality and framework
├── test_enhanced_news_collector.py  # RSS news collection tests
├── test_enhanced_sentiment_ml.py    # ML sentiment analysis tests
├── test_enhanced_technical_calculator.py  # Technical indicators tests
├── test_enhanced_materialized_updater.py  # Materialized view tests
├── conftest.py                      # Shared pytest fixtures
└── integration/                     # Integration tests
    ├── test_end_to_end.py          # Full pipeline tests
    └── test_database_integration.py # Database integration tests
```

### Test Categories

#### Unit Tests
- **Base Collector Tests**: Core functionality, API endpoints, health checks, circuit breaker, rate limiting
- **News Collector Tests**: RSS feed parsing, crypto mention detection, article processing
- **Sentiment ML Tests**: Model loading, sentiment analysis, confidence scoring, market type detection
- **Technical Calculator Tests**: Indicator calculations (SMA, EMA, RSI, MACD, Bollinger Bands), mathematical correctness
- **Materialized Updater Tests**: View refresh, dependency resolution, performance monitoring

#### Integration Tests
- Database connectivity and operations
- End-to-end data flow validation
- Service communication testing
- External API integration

#### Performance Tests
- Load testing with high data volumes
- Memory usage optimization
- Database query performance
- ML model inference speed

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_base_collector.py -v
pytest tests/ -m "unit" -v
pytest tests/ -m "integration" -v
pytest tests/ -m "performance" -v

# Run with coverage
pytest tests/ --cov=services --cov=templates --cov-report=html

# Run tests in parallel
pytest tests/ -n auto

# Run performance benchmarks
pytest tests/ --benchmark-only
```

### Test Configuration

#### Environment Variables for Testing
```bash
# Database
DB_HOST=localhost
DB_USER=test
DB_PASSWORD=test
DB_NAME=test_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Test environment
ENVIRONMENT=test
```

#### Mocking Strategy
- Database connections and queries
- External API calls (RSS feeds, ML models)
- Time-dependent operations
- File system operations

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline is defined in `.github/workflows/ci-cd.yml` and includes:

#### 1. Code Quality & Security
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **bandit**: Security vulnerability scanning
- **safety**: Dependency vulnerability checking
- **mypy**: Type checking

#### 2. Testing Stages
- **Unit Tests**: Run on Python 3.9, 3.10, 3.11
- **Integration Tests**: Full database and service integration
- **Performance Tests**: Benchmarking and load testing

#### 3. Build & Deploy
- **Docker Build**: Multi-platform images (amd64, arm64)
- **Security Scanning**: Trivy vulnerability scanning
- **Staging Deployment**: Automatic deploy on `develop` branch
- **Production Deployment**: Automatic deploy on `main` branch

#### 4. Monitoring & Alerts
- Slack notifications for deployment status
- Test result artifacts
- Coverage reports

### Pipeline Triggers

```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

### Required Secrets

```bash
# Docker Hub
DOCKER_USERNAME
DOCKER_PASSWORD

# Kubernetes
KUBE_CONFIG_STAGING
KUBE_CONFIG_PRODUCTION

# Notifications
SLACK_WEBHOOK
```

## Docker Configuration

### Multi-Service Dockerfiles

Each collector service has its own optimized Dockerfile:

```dockerfile
# docker/Dockerfile.enhanced-news-collector
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/enhanced_news_collector_template.py ./services/
COPY templates/collector-template/ ./templates/

EXPOSE 8080

CMD ["python", "-m", "services.enhanced_news_collector_template"]
```

### Build Commands

```bash
# Build all services
docker build -f docker/Dockerfile.enhanced-news-collector -t crypto-news-collector .
docker build -f docker/Dockerfile.enhanced-sentiment-ml -t crypto-sentiment-ml .
docker build -f docker/Dockerfile.enhanced-technical-calculator -t crypto-technical-calculator .
docker build -f docker/Dockerfile.enhanced-materialized-updater -t crypto-materialized-updater .
```

## Kubernetes Deployment

### Service Manifests

Each service is deployed with:
- Deployment with health/readiness probes
- Service for internal communication
- ConfigMap for configuration
- Secret for sensitive data

```yaml
# k8s/production/news-collector.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-news-collector
spec:
  replicas: 2
  selector:
    matchLabels:
      app: enhanced-news-collector
  template:
    spec:
      containers:
      - name: collector
        image: crypto-enhanced-news-collector:latest
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
```

### Deployment Strategy

1. **Blue-Green Deployment**: Zero-downtime deployments
2. **Rolling Updates**: Gradual service updates
3. **Health Checks**: Ensure services are ready before routing traffic
4. **Resource Limits**: CPU and memory constraints

## Monitoring & Observability

### Metrics Collection
- Prometheus metrics endpoint (`/metrics`)
- Custom business metrics
- Performance counters

### Logging
- Structured logging (JSON format)
- Log aggregation with ELK stack
- Error tracking and alerting

### Health Monitoring
- `/health` - Service liveness
- `/ready` - Service readiness
- `/status` - Detailed service status

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-collector

# Run tests locally
pytest tests/

# Code quality checks
black .
isort .
flake8 .

# Commit and push
git commit -m "Add new collector functionality"
git push origin feature/new-collector
```

### 2. Pull Request Process
- Automated tests run on PR
- Code review required
- Security and quality checks pass
- Integration tests validate changes

### 3. Deployment Process
- Merge to `develop` → Deploy to staging
- Merge to `main` → Deploy to production
- Automatic rollback on health check failure

## Performance Optimization

### Test Performance Targets
- Unit tests: < 5 minutes
- Integration tests: < 15 minutes
- Full pipeline: < 30 minutes

### Database Testing
- Use test-specific database
- Parallel test execution
- Transaction rollback between tests

### ML Model Testing
- Mock heavy model operations
- Use smaller test models
- Cached model loading

## Troubleshooting

### Common Issues

1. **Test Database Connection**
   ```bash
   # Check database connectivity
   pg_isready -h localhost -p 5432 -U test
   ```

2. **Docker Build Failures**
   ```bash
   # Check Docker daemon
   docker system info
   
   # Clear build cache
   docker builder prune
   ```

3. **Kubernetes Deployment Issues**
   ```bash
   # Check pod status
   kubectl get pods -n crypto-production
   
   # View logs
   kubectl logs -f deployment/enhanced-news-collector -n crypto-production
   ```

### Debug Commands

```bash
# Run tests with debugging
pytest tests/ -vvv --tb=long

# Profile test performance
pytest tests/ --profile

# Run single test with debugging
pytest tests/test_enhanced_news_collector.py::TestEnhancedNewsCollector::test_collect_data -vvv -s
```

## Best Practices

### Testing Best Practices
1. **Test Isolation**: Each test should be independent
2. **Comprehensive Mocking**: Mock external dependencies
3. **Clear Test Names**: Describe what is being tested
4. **Fast Execution**: Optimize for quick feedback
5. **Realistic Data**: Use representative test data

### CI/CD Best Practices
1. **Fail Fast**: Run quick tests first
2. **Parallel Execution**: Maximize pipeline efficiency
3. **Artifact Preservation**: Save test results and logs
4. **Security First**: Scan for vulnerabilities early
5. **Monitoring**: Track pipeline performance

### Deployment Best Practices
1. **Gradual Rollout**: Deploy to staging first
2. **Health Checks**: Verify service health before promotion
3. **Quick Rollback**: Ability to revert quickly
4. **Configuration Management**: Environment-specific configs
5. **Monitoring**: Real-time deployment monitoring

## Conclusion

This comprehensive testing and CI/CD setup ensures:
- **Quality**: Automated testing catches issues early
- **Security**: Vulnerability scanning and security checks
- **Reliability**: Consistent deployments with health checks
- **Speed**: Efficient pipeline with parallel execution
- **Visibility**: Comprehensive monitoring and alerting

The system supports rapid development while maintaining high quality and reliability standards for the crypto data collection infrastructure.