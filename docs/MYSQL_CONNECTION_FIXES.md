# MySQL Connection Test Fixes

This document summarizes the fixes applied to resolve the MySQL connection issues in the CI/CD pipeline.

## Problem Analysis

The tests were failing with:
```
mysql.connector.errors.DatabaseError: 2003 (HY000): Can't connect to MySQL server on 'localhost:3307' (111)
```

**Root Causes:**
1. **Port mismatch**: Tests configured for port 3307, CI/CD services on port 3306
2. **Credential mismatch**: Different usernames/passwords between test config and CI/CD
3. **Insufficient retry logic**: Limited connection attempts and poor error handling
4. **Missing environment variables**: Tests not using CI/CD environment variables
5. **Poor health checks**: No comprehensive service verification

## Fixes Applied

### 1. **Test Configuration Updates** (`tests/conftest.py`)

**Before:**
```python
TEST_CONFIG = {
    'mysql': {
        'host': 'localhost',
        'port': 3307,  # Wrong port
        'user': 'test_user',  # Wrong user
        'password': 'test_password',  # Wrong password
        'database': 'crypto_prices_test',  # Wrong database
    }
}
```

**After:**
```python
TEST_CONFIG = {
    'mysql': {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),  # Correct CI/CD port
        'user': os.getenv('MYSQL_USER', 'news_collector'),  # Correct CI/CD user
        'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),  # Correct CI/CD password
        'database': os.getenv('MYSQL_DATABASE', 'crypto_data_test'),  # Correct CI/CD database
    }
}
```

### 2. **Enhanced Connection Retry Logic**

**Improvements:**
- Increased retry attempts from 30 to 60
- Added socket connectivity tests before MySQL connection attempts
- Exponential backoff with jitter
- Detailed diagnostic error messages
- Proper connection cleanup

**Key Features:**
```python
# Test basic connectivity first
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
result = sock.connect_ex((host, port))

# Enhanced error reporting with diagnostics
error_msg = f"""
Could not connect to test MySQL after {max_retries} attempts.
Configuration: {config}
Environment variables: {env_vars}
Possible causes and solutions...
"""
```

### 3. **CI/CD Pipeline Enhancements** (`.github/workflows/complete-ci-cd.yml`)

**Added comprehensive service setup:**
```yaml
- name: 🔄 Wait for Services and Setup Test Environment
  run: |
    # Set all required environment variables
    export MYSQL_HOST=127.0.0.1
    export MYSQL_PORT=3306
    export MYSQL_USER=${{ secrets.STAGING_MYSQL_USER || 'news_collector' }}
    # ... more environment setup
    
    # Enhanced health checks with diagnostics
    # Port connectivity tests
    # Database access verification
    # Service log collection on failure
```

### 4. **Environment Diagnostics Script** (`tests/test_environment_diagnostics.py`)

**Features:**
- Comprehensive environment variable validation
- Port connectivity testing
- MySQL connection and query testing
- Redis connection and ping testing
- Detailed troubleshooting guidance

**Usage:**
```bash
python tests/test_environment_diagnostics.py
```

### 5. **Docker Compose Consistency** (`docker-compose.test.yml`)

**Updated for consistency:**
- Unified MySQL credentials with CI/CD
- Consistent database names
- Environment variable alignment
- Port mapping documentation

## Configuration Matrix

| Environment | MySQL Port | MySQL User | MySQL Password | MySQL Database |
|-------------|------------|------------|----------------|----------------|
| CI/CD | 3306 | news_collector | 99Rules! | crypto_data_test |
| Local Docker | 3307→3306 | news_collector | 99Rules! | crypto_data_test |
| Local Direct | 3306 | news_collector | 99Rules! | crypto_data_test |

## Testing the Fixes

### Local Testing
```bash
# Test with environment variables
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=news_collector
export MYSQL_PASSWORD="99Rules!"
export MYSQL_DATABASE=crypto_data_test
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Run diagnostics
python tests/test_environment_diagnostics.py

# Run specific failing tests
pytest tests/test_macro_economic_service.py -v
```

### Docker Testing
```bash
# Start test services
docker-compose -f docker-compose.test.yml up test-mysql test-redis -d

# Wait for services
sleep 30

# Run diagnostics in container context
docker-compose -f docker-compose.test.yml run test-runner python tests/test_environment_diagnostics.py

# Run tests
docker-compose -f docker-compose.test.yml run test-integration
```

### CI/CD Testing
The fixes will automatically apply in GitHub Actions. Look for:
- ✅ Environment variable setup
- ✅ Service health checks passing
- ✅ Diagnostic script success
- ✅ Test execution without connection errors

## Expected Results

**Before fixes:**
```
E mysql.connector.errors.DatabaseError: 2003 (HY000): Can't connect to MySQL server on 'localhost:3307' (111)
```

**After fixes:**
```
✅ Successfully connected to MySQL on attempt 1
✅ Redis connection successful
✅ All diagnostics passed! Test environment is ready.
[Tests run successfully]
```

## Troubleshooting

If tests still fail:

1. **Check environment variables:**
   ```bash
   python tests/test_environment_diagnostics.py
   ```

2. **Verify service health:**
   ```bash
   mysqladmin ping -h 127.0.0.1 -u news_collector -p99Rules!
   redis-cli -h 127.0.0.1 ping
   ```

3. **Check port connectivity:**
   ```bash
   nc -z 127.0.0.1 3306  # MySQL
   nc -z 127.0.0.1 6379  # Redis
   ```

4. **Review CI/CD logs:**
   - Look for "Test Environment Diagnostics" step
   - Check MySQL/Redis service startup logs
   - Verify environment variable setup

## Files Modified

```
tests/conftest.py                          # Fixed MySQL/Redis config
tests/test_environment_diagnostics.py      # New diagnostic script
.github/workflows/complete-ci-cd.yml       # Enhanced service setup
docker-compose.test.yml                    # Unified credentials
docs/MYSQL_CONNECTION_FIXES.md            # This documentation
```

The fixes ensure robust, consistent database connectivity across all environments while providing comprehensive diagnostics for troubleshooting.