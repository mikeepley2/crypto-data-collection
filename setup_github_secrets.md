# GitHub Secrets Setup Guide

## 🔗 Direct Link to Add Secrets
Go to: https://github.com/mikeepley2/crypto-data-collection/settings/secrets/actions

## 📋 Copy-Paste Ready Secrets

### Container Registry (Docker Hub)
```
Name: DOCKER_REGISTRY
Value: docker.io

Name: DOCKER_USERNAME  
Value: megabob70

Name: DOCKER_PASSWORD
Value: 99988Anchove!
```

### Staging Database
```
Name: STAGING_MYSQL_ROOT_PASSWORD
Value: dNXhRCdvh60C4rNMtFYAiLOC4dcbKH73FK2HsYnMINs=

Name: STAGING_MYSQL_USER
Value: crypto_user

Name: STAGING_MYSQL_PASSWORD
Value: GPPluPuZm4LmEYyTJzH2JSQ1MEWrWazXXniNOexgUeU=

Name: STAGING_MYSQL_DATABASE
Value: crypto_data_staging

Name: STAGING_REDIS_PASSWORD
Value: 7haza+3rSXxNQ/wtDTZUNnJn8raylbMG
```

### Production Database
```
Name: PROD_MYSQL_ROOT_PASSWORD
Value: Hmzqqor/7Kni3lomGrBAVUVTXa+hVzuzBhD2Oj+XTLk=

Name: PROD_MYSQL_USER
Value: crypto_user

Name: PROD_MYSQL_PASSWORD
Value: yZy8WNIW51om49FnPu2fePDhCTILGh7q4VnMEFM1FhQ=

Name: PROD_MYSQL_DATABASE
Value: crypto_data_production

Name: PROD_REDIS_PASSWORD
Value: 1XZeVJNBvo3eNA3bVTCESYsGp8miydeH
```

### API Keys (Placeholders)
```
Name: STAGING_COINBASE_API_KEY
Value: placeholder

Name: STAGING_COINBASE_API_SECRET
Value: placeholder

Name: STAGING_NEWSAPI_KEY
Value: placeholder

Name: STAGING_ALPHA_VANTAGE_KEY
Value: placeholder

Name: STAGING_BINANCE_API_KEY
Value: placeholder

Name: STAGING_BINANCE_API_SECRET
Value: placeholder

Name: PROD_COINBASE_API_KEY
Value: placeholder

Name: PROD_COINBASE_API_SECRET
Value: placeholder

Name: PROD_NEWSAPI_KEY
Value: placeholder

Name: PROD_ALPHA_VANTAGE_KEY
Value: placeholder

Name: PROD_BINANCE_API_KEY
Value: placeholder

Name: PROD_BINANCE_API_SECRET
Value: placeholder
```

## 🚀 Quick Setup Steps

1. Click the link above
2. Click "New repository secret" for each entry
3. Copy the Name and Value from above
4. Click "Add secret"
5. Repeat for all secrets

## ✅ After Setup
- Check your pipeline: https://github.com/mikeepley2/crypto-data-collection/actions
- Your 72 tests should run automatically
- Container builds will push to docker.io/megabob70/crypto-data-collection

## 🔧 Priority Order (if you want to add gradually)
1. Docker credentials (for container builds)
2. Database credentials (for integration tests)  
3. API keys (can be placeholders initially)