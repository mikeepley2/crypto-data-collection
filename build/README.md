# Build and Deployment Infrastructure

This directory contains all the build, deployment, and configuration files for the crypto data collection system.

## Directory Structure

```
build/
├── config/                 # Environment-specific configuration files
│   ├── .env.development   # Development environment variables
│   ├── .env.staging       # Staging environment variables
│   ├── .env.production    # Production environment variables
│   └── .env.test          # Test environment variables
├── docker/                # Docker build configurations
│   ├── Dockerfile.enhanced-news-collector
│   ├── Dockerfile.enhanced-sentiment-ml
│   ├── Dockerfile.enhanced-technical-calculator
│   ├── Dockerfile.enhanced-materialized-updater
│   └── docker-compose.yml # Development environment
├── k8s/                   # Kubernetes deployment manifests
│   ├── base/              # Base Kubernetes resources
│   ├── staging/           # Staging environment overlays
│   └── production/        # Production environment overlays
└── scripts/               # Deployment and utility scripts
    ├── build-docker.sh    # Docker build and push script
    ├── deploy-k8s.sh      # Kubernetes deployment script
    ├── dev-environment.sh # Development environment setup
    └── run-tests.sh       # Test execution script
```

## Quick Start

### Development Environment

1. **Setup local development environment:**
   ```bash
   ./build/scripts/dev-environment.sh start
   ```

2. **View running services:**
   - News Collector: http://localhost:8080
   - Sentiment ML: http://localhost:8081
   - Technical Calculator: http://localhost:8082
   - Materialized Updater: http://localhost:8083
   - Grafana Dashboard: http://localhost:3000 (admin/admin123)

3. **Stop development environment:**
   ```bash
   ./build/scripts/dev-environment.sh stop
   ```

### Building Docker Images

```bash
# Build for development
./build/scripts/build-docker.sh development

# Build and push for staging
./build/scripts/build-docker.sh staging true

# Build and push for production with specific tag
IMAGE_TAG=v1.0.0 ./build/scripts/build-docker.sh production true
```

### Kubernetes Deployment

```bash
# Deploy to staging
./build/scripts/deploy-k8s.sh staging deploy

# Deploy to production
./build/scripts/deploy-k8s.sh production deploy

# Check deployment status
./build/scripts/deploy-k8s.sh staging status

# View logs
./build/scripts/deploy-k8s.sh staging logs

# Rollback deployment
./build/scripts/deploy-k8s.sh staging rollback
```

### Running Tests

```bash
# Run all tests
./build/scripts/run-tests.sh

# Run unit tests with coverage
./build/scripts/run-tests.sh -t unit -c

# Run tests in parallel
./build/scripts/run-tests.sh -p -c
```

## Configuration Management

### Environment Variables

Each environment has its own configuration file:

- **Development** (`.env.development`): Local development with relaxed settings
- **Staging** (`.env.staging`): Pre-production testing environment
- **Production** (`.env.production`): Production-optimized settings
- **Test** (`.env.test`): Test environment with mocked services

### Key Configuration Areas

1. **Database & Redis**: Connection settings for each environment
2. **Collection Intervals**: How often each collector runs
3. **Batch Sizes**: Number of items processed per batch
4. **Circuit Breaker**: Failure tolerance settings
5. **ML Models**: Model selection and device configuration
6. **Monitoring**: Health checks, metrics, and alerting
7. **Performance**: Parallel processing and connection limits

## Docker Images

### Multi-stage Builds

Each service uses multi-stage Docker builds:

- **Base stage**: Common dependencies and system setup
- **Development stage**: Includes all source code for development
- **Production stage**: Optimized image with security hardening

### Features

- **Security**: Non-root user, read-only filesystem where possible
- **Health Checks**: Built-in health check endpoints
- **Caching**: Optimized layer caching for faster builds
- **Multi-platform**: ARM64 and AMD64 support

## Kubernetes Deployment

### Architecture

- **Base**: Common Kubernetes resources shared across environments
- **Staging**: Lower resource limits, relaxed intervals
- **Production**: High availability, auto-scaling, stricter security

### Features

- **Kustomize**: Environment-specific overlays
- **Auto-scaling**: HPA for dynamic scaling based on CPU/memory
- **Security**: RBAC, Pod Disruption Budgets, Security Contexts
- **Monitoring**: Prometheus metrics, health/readiness probes
- **Secrets Management**: Kubernetes secrets for sensitive data

### Resource Allocation

#### Staging
- Reduced replicas (1 per service except ML which needs resources)
- Lower memory/CPU limits
- Relaxed collection intervals

#### Production
- Multiple replicas for high availability
- Optimized resource requests/limits
- Aggressive collection intervals
- Auto-scaling enabled

## Scripts

### `build-docker.sh`

Comprehensive Docker build script with:
- Multi-service build support
- Environment-specific targeting
- Automatic tagging with git commit SHA
- Push to registry capability
- Build caching optimization

### `deploy-k8s.sh`

Kubernetes deployment automation with:
- Environment validation
- Rollout status monitoring
- Health check verification
- Rollback capability
- Log aggregation

### `dev-environment.sh`

Development environment management:
- Docker Compose orchestration
- Database schema setup
- Service health monitoring
- Log streaming
- Environment cleanup

### `run-tests.sh`

Test execution framework:
- Multiple test type support (unit/integration/performance)
- Coverage reporting
- Parallel execution
- Test result aggregation
- CI/CD integration

## CI/CD Integration

### GitHub Actions Workflow

The build infrastructure integrates with the GitHub Actions workflow:

1. **Code Quality**: Linting, formatting, security scans
2. **Testing**: Unit, integration, and performance tests
3. **Building**: Docker images for all services
4. **Security**: Vulnerability scanning
5. **Deployment**: Automated staging and production deployments

### Secrets Required

```bash
# Docker Registry
DOCKER_USERNAME
DOCKER_PASSWORD

# Kubernetes
KUBE_CONFIG_STAGING
KUBE_CONFIG_PRODUCTION

# Notifications
SLACK_WEBHOOK

# Application
DB_PASSWORD
REDIS_PASSWORD
SECRET_KEY
JWT_SECRET
RSS_API_KEY
SENTIMENT_API_KEY
```

## Monitoring & Observability

### Metrics Collection

- **Prometheus**: Metrics scraping and storage
- **Grafana**: Visualization dashboards
- **Custom Metrics**: Business-specific metrics per collector

### Health Monitoring

- **Liveness Probes**: `/health` endpoint for basic service health
- **Readiness Probes**: `/ready` endpoint for traffic readiness
- **Metrics Endpoint**: `/metrics` for Prometheus scraping

### Logging

- **Structured Logging**: JSON format for log aggregation
- **Log Levels**: Environment-appropriate log levels
- **Centralized**: ELK stack integration ready

## Security

### Container Security

- Non-root user execution
- Read-only root filesystem
- Minimal base images
- Regular vulnerability scanning

### Kubernetes Security

- RBAC for service accounts
- Network policies (ready for implementation)
- Pod security contexts
- Secret management

### Configuration Security

- Secrets stored in Kubernetes secrets
- Environment-specific access controls
- No hardcoded credentials

## Best Practices

### Development

1. Use the development environment for local testing
2. Always run tests before committing
3. Follow the GitFlow branching model
4. Keep Docker images small and secure

### Deployment

1. Deploy to staging before production
2. Monitor deployment rollouts
3. Use blue-green or rolling deployments
4. Have rollback procedures ready

### Monitoring

1. Set up proper alerting thresholds
2. Monitor both infrastructure and application metrics
3. Use distributed tracing for complex debugging
4. Maintain runbooks for common issues

## Troubleshooting

### Common Issues

1. **Docker build failures**: Check Dockerfile syntax and base image availability
2. **Kubernetes deployment issues**: Verify resource limits and image availability
3. **Database connection errors**: Check network policies and credentials
4. **Health check failures**: Verify service startup time and dependencies

### Debug Commands

```bash
# View Docker logs
docker-compose logs -f [service]

# Check Kubernetes pod status
kubectl get pods -n crypto-staging

# Describe problematic pods
kubectl describe pod [pod-name] -n crypto-staging

# View application logs
kubectl logs -f deployment/staging-enhanced-news-collector -n crypto-staging

# Check resource usage
kubectl top pods -n crypto-production
```

## Contributing

When adding new services or modifying existing ones:

1. Update Docker configurations in `docker/`
2. Add Kubernetes manifests in `k8s/base/`
3. Update environment configurations in `config/`
4. Modify scripts as needed in `scripts/`
5. Test changes in development environment first
6. Update this README with any new features or changes

## Support

For issues with the build and deployment infrastructure:

1. Check the troubleshooting section
2. Review logs using the provided scripts
3. Verify configuration files for your environment
4. Ensure all prerequisites are installed and configured