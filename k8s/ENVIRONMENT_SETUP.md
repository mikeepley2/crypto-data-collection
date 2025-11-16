# Environment Configuration Documentation
# This file documents all environment variables needed for the CI/CD pipeline

## GitHub Secrets Configuration

### Required Secrets for CI/CD Pipeline:

#### Container Registry
- `DOCKER_REGISTRY`: Container registry URL (e.g., ghcr.io, docker.io)
- `DOCKER_USERNAME`: Registry username
- `DOCKER_PASSWORD`: Registry password/token

#### Kubernetes Access
- `KUBECONFIG_STAGING`: Base64 encoded kubeconfig for staging cluster
- `KUBECONFIG_PRODUCTION`: Base64 encoded kubeconfig for production cluster

#### Database Credentials (Staging)
- `STAGING_MYSQL_ROOT_PASSWORD`: MySQL root password for staging
- `STAGING_MYSQL_USER`: MySQL user for staging
- `STAGING_MYSQL_PASSWORD`: MySQL user password for staging
- `STAGING_MYSQL_DATABASE`: MySQL database name for staging
- `STAGING_REDIS_PASSWORD`: Redis password for staging

#### Database Credentials (Production)
- `PROD_MYSQL_ROOT_PASSWORD`: MySQL root password for production
- `PROD_MYSQL_USER`: MySQL user for production
- `PROD_MYSQL_PASSWORD`: MySQL user password for production
- `PROD_MYSQL_DATABASE`: MySQL database name for production
- `PROD_REDIS_PASSWORD`: Redis password for production

#### API Keys (Staging)
- `STAGING_COINBASE_API_KEY`: Coinbase API key for staging
- `STAGING_COINBASE_API_SECRET`: Coinbase API secret for staging
- `STAGING_NEWSAPI_KEY`: NewsAPI key for staging
- `STAGING_ALPHA_VANTAGE_KEY`: Alpha Vantage API key for staging
- `STAGING_BINANCE_API_KEY`: Binance API key for staging
- `STAGING_BINANCE_API_SECRET`: Binance API secret for staging

#### API Keys (Production)
- `PROD_COINBASE_API_KEY`: Coinbase API key for production
- `PROD_COINBASE_API_SECRET`: Coinbase API secret for production
- `PROD_NEWSAPI_KEY`: NewsAPI key for production
- `PROD_ALPHA_VANTAGE_KEY`: Alpha Vantage API key for production
- `PROD_BINANCE_API_KEY`: Binance API key for production
- `PROD_BINANCE_API_SECRET`: Binance API secret for production

#### Monitoring
- `STAGING_GRAFANA_ADMIN_PASSWORD`: Grafana admin password for staging
- `PROD_GRAFANA_ADMIN_PASSWORD`: Grafana admin password for production

#### Notifications
- `SLACK_WEBHOOK_URL`: Slack webhook for deployment notifications
- `DISCORD_WEBHOOK_URL`: Discord webhook for deployment notifications (optional)

## Environment Variable Substitution

The CI/CD pipeline uses `envsubst` to replace environment variables in Kubernetes templates.

### Template Variable Format:
```yaml
stringData:
  mysql-password: "${MYSQL_PASSWORD}"
```

### Pipeline Substitution:
```bash
envsubst < k8s/staging/namespace-and-secrets.yaml | kubectl apply -f -
```

## Setup Instructions

### 1. Configure GitHub Secrets
Go to your GitHub repository → Settings → Secrets and variables → Actions

Add all the secrets listed above with appropriate values.

### 2. Prepare Kubeconfig Files
```bash
# For staging cluster
kubectl config view --flatten --minify > staging-kubeconfig.yaml
base64 -i staging-kubeconfig.yaml

# For production cluster
kubectl config view --flatten --minify > production-kubeconfig.yaml
base64 -i production-kubeconfig.yaml
```

Add the base64 output as `KUBECONFIG_STAGING` and `KUBECONFIG_PRODUCTION` secrets.

### 3. Container Registry Setup

#### Using GitHub Container Registry (recommended):
```bash
# Create a Personal Access Token with package permissions
# Set as DOCKER_PASSWORD secret
DOCKER_REGISTRY=ghcr.io
DOCKER_USERNAME=your-github-username
DOCKER_PASSWORD=your-personal-access-token
```

#### Using Docker Hub:
```bash
DOCKER_REGISTRY=docker.io
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password
```

### 4. API Keys Configuration

Obtain API keys from:
- **Coinbase Pro**: https://pro.coinbase.com/profile/api
- **NewsAPI**: https://newsapi.org/register
- **Alpha Vantage**: https://www.alphavantage.co/support/#api-key
- **Binance**: https://www.binance.com/en/my/settings/api-management

### 5. Database Credentials

Generate strong passwords:
```bash
# Generate random passwords
openssl rand -base64 32  # For MySQL passwords
openssl rand -base64 24  # For Redis passwords
```

## Security Best Practices

1. **Rotate Secrets Regularly**: Set up a schedule to rotate API keys and passwords
2. **Least Privilege**: Use service accounts with minimal required permissions
3. **Environment Separation**: Use different API keys and credentials for staging/production
4. **Monitoring**: Set up alerts for failed authentication attempts
5. **Audit**: Regularly review access logs and secret usage

## Troubleshooting

### Common Issues:

#### 1. Template Substitution Failures
```bash
# Check if all variables are set
envsubst --variables < k8s/staging/namespace-and-secrets.yaml
```

#### 2. Kubernetes Authentication
```bash
# Test kubeconfig
echo "$KUBECONFIG_STAGING" | base64 -d > /tmp/kubeconfig
kubectl --kubeconfig=/tmp/kubeconfig get nodes
```

#### 3. Container Registry Access
```bash
# Test docker login
echo "$DOCKER_PASSWORD" | docker login $DOCKER_REGISTRY -u $DOCKER_USERNAME --password-stdin
```

## Pipeline Validation

Before deploying to production, validate all configurations:

1. **Staging Deployment**: Ensure staging environment works correctly
2. **Health Checks**: Verify all services pass health checks
3. **Integration Tests**: Run the full test suite (72 tests)
4. **Performance Tests**: Validate system performance under load
5. **Security Scan**: Ensure no vulnerabilities in deployed images