# Local Database Testing Guide

This guide helps you test the database initialization and CI fixes locally before running them in GitHub Actions.

## Overview

We've created several scripts to test the database setup locally:

1. **`scripts/test_local_database_setup.py`** - Full Docker-based test (recommended)
2. **`scripts/quick_local_test.py`** - Quick test with existing MySQL
3. **`scripts/test_ci_database.py`** - Database connectivity and schema validation
4. **`scripts/init_ci_database.py`** - Database initialization script

## Option 1: Docker-Based Testing (Recommended)

This is the closest to the GitHub Actions environment.

### Prerequisites
- Docker installed and running
- Python 3.7+

### Steps

1. **Run the full test suite:**
   ```bash
   cd /mnt/e/git/crypto-data-collection
   python3 scripts/test_local_database_setup.py
   ```

This will:
- ✅ Check Docker availability
- 🐳 Start a MySQL 8.0 container (port 3307 to avoid conflicts)
- 🏗️ Run database initialization
- 🧪 Test database connectivity and schema
- 🧪 Run sample integration tests
- 🧹 Clean up the test container

### What it tests:
- MySQL container startup with CI environment variables
- Database initialization with correct authentication
- Schema creation with production-matching structures
- Sample data insertion
- Integration test field name validation

## Option 2: Local MySQL Testing

If you have MySQL already installed locally.

### Prerequisites
- MySQL server running locally
- Python 3.7+
- mysql-connector-python package

### Steps

1. **Set environment variables:**
   ```bash
   export MYSQL_HOST=127.0.0.1
   export MYSQL_PORT=3306
   export MYSQL_USER=your_mysql_user
   export MYSQL_PASSWORD=your_mysql_password
   export MYSQL_DATABASE=crypto_data_test
   export MYSQL_ROOT_PASSWORD=your_root_password
   ```

2. **Run the quick test:**
   ```bash
   python3 scripts/quick_local_test.py
   ```

3. **Or run tests individually:**
   ```bash
   # Initialize database
   python3 scripts/init_ci_database.py
   
   # Test connectivity and schema
   python3 scripts/test_ci_database.py
   ```

## Option 3: Manual Testing

### Step-by-step verification:

1. **Check MySQL connectivity:**
   ```bash
   mysql -h 127.0.0.1 -u your_user -p
   ```

2. **Create test database:**
   ```sql
   CREATE DATABASE IF NOT EXISTS crypto_data_test;
   USE crypto_data_test;
   ```

3. **Run initialization script:**
   ```bash
   python3 scripts/init_ci_database.py
   ```

4. **Verify tables were created:**
   ```sql
   SHOW TABLES;
   DESCRIBE price_data_real;
   DESCRIBE onchain_data;
   DESCRIBE technical_indicators;
   ```

5. **Check sample data:**
   ```sql
   SELECT COUNT(*) FROM crypto_assets;
   SELECT COUNT(*) FROM price_data_real;
   ```

## What the Tests Validate

### Database Initialization (`init_ci_database.py`)
- ✅ Connects using environment variables (not hardcoded credentials)
- ✅ Creates all required tables with production schemas
- ✅ Inserts sample data for testing
- ✅ Handles MySQL 8.0 authentication properly

### Database Testing (`test_ci_database.py`)
- ✅ Tests connectivity with CI environment variables
- ✅ Validates all expected tables exist
- ✅ Checks schema fields match integration test expectations
- ✅ Verifies sample data was inserted correctly

### Integration Test Fields
Tests that these field mappings work correctly:
- `price_data_real`: price → current_price, total_volume → volume_usd_24h
- `technical_indicators`: indicator_type → rsi/sma_20/macd fields
- `onchain_data`: all fields present and properly named

## Troubleshooting

### Docker Issues
```bash
# Check if Docker is running
docker --version
docker ps

# If port conflicts
docker stop crypto-test-mysql
docker rm crypto-test-mysql
```

### MySQL Connection Issues
```bash
# Check MySQL is running
mysql -h 127.0.0.1 -u root -p

# Check environment variables
echo $MYSQL_USER
echo $MYSQL_DATABASE
```

### Python Module Issues
```bash
# Install required packages
pip install mysql-connector-python pytest
```

### Authentication Issues
If you see "Access denied for user", check:
- Environment variables are set correctly
- MySQL user has proper permissions
- Password is correct

## Expected Output

### Successful Docker Test:
```
🚀 Local Database Setup Test
============================================================
✅ Docker available: Docker version 20.10.x
🐳 Starting MySQL container for testing...
✅ MySQL container started
✅ MySQL is ready!
🏗️ Running database initialization...
✅ Database initialization completed successfully
🧪 Running database tests...
✅ Database tests completed successfully
🧪 Running sample integration tests...
✅ Sample integration tests passed
🎉 All local tests passed!
✅ Your changes are ready for GitHub Actions CI
```

### Successful Quick Test:
```
🚀 Quick Local Database Test
==================================================
✅ Environment variables found
🏗️ Testing database initialization...
✅ Database initialization successful
🧪 Testing database connectivity...
✅ Database tests passed
🎉 All tests passed! Ready for GitHub Actions.
```

## Next Steps

Once local testing passes:

1. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Fix CI database authentication and schema alignment"
   ```

2. **Push to trigger GitHub Actions:**
   ```bash
   git push origin your-branch
   ```

3. **Monitor GitHub Actions:**
   - Check that "🏗️ Setting up test database schema..." step succeeds
   - Verify integration tests pass
   - Confirm no more authentication errors

## Files Changed

The testing validates these recent fixes:
- `scripts/init_ci_database.py` - Environment variable authentication
- `tests/test_pytest_comprehensive_integration.py` - Field name corrections
- `scripts/test_ci_database.py` - Comprehensive validation
- `tests/test_environment_diagnostics.py` - Enhanced diagnostics

All changes ensure CI environment matches production database structure.