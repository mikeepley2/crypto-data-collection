# Unit Testing Documentation

## Overview

The crypto-data-collection project includes a comprehensive unit testing suite covering all major components of the data collection system. This document provides guidance on running tests individually or collectively.

## Test Suite Structure

### 📁 Unit Test Files (11 total)

1. **`test_base_collector.py`** - Base collector functionality and template compliance
2. **`test_database_validation.py`** - Database schema validation and integrity checks
3. **`test_enhanced_news_collector.py`** - News collection and RSS feed processing
4. **`test_enhanced_sentiment_ml.py`** - ML sentiment analysis and NLP processing
5. **`test_enhanced_technical_calculator.py`** - Technical indicator calculations
6. **`test_enhanced_materialized_updater.py`** - ML materialized view updates
7. **`test_onchain_collector_unit.py`** - Onchain data collection and validation
8. **`test_macro_collector_unit.py`** - Macroeconomic indicators collection
9. **`test_derivatives_collector_unit.py`** - Crypto derivatives data collection
10. **`test_ohlc_collector_unit.py`** - OHLC price data collection and validation
11. **`test_ml_market_collector.py`** - ML market correlation and feature engineering

## Test Infrastructure

### Dependencies
- **pytest** - Primary testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **unittest.mock** - Mocking and patching
- **fastapi.testclient** - API endpoint testing

### Mock Dependencies
- **mock_transformers.py** - Lightweight ML transformers mock
- **table_config.py** - Mock shared configuration module

## Running Tests

### Prerequisites
```bash
# Activate the test environment
cd /mnt/e/git/crypto-data-collection
source test-env/bin/activate
```

### Running All Unit Tests
```bash
# Run all unit tests (excludes integration tests)
python -m pytest tests/ -k "not integration" -v

# Run with coverage report
python -m pytest tests/ -k "not integration" --cov=. --cov-report=term-missing

# Run with HTML coverage report
python -m pytest tests/ -k "not integration" --cov=. --cov-report=html:test-results/coverage
```

### Running Individual Test Files

#### Core Collector Tests
```bash
# Base collector template functionality
python -m pytest tests/test_base_collector.py -v

# Database validation and schema checks
python -m pytest tests/test_database_validation.py -v
```

#### Data Collection Tests
```bash
# News collection and RSS processing
python -m pytest tests/test_enhanced_news_collector.py -v

# Onchain data collection
python -m pytest tests/test_onchain_collector_unit.py -v

# OHLC price data collection
python -m pytest tests/test_ohlc_collector_unit.py -v

# Macroeconomic data collection
python -m pytest tests/test_macro_collector_unit.py -v

# Crypto derivatives collection
python -m pytest tests/test_derivatives_collector_unit.py -v
```

#### ML and Analytics Tests
```bash
# ML sentiment analysis
python -m pytest tests/test_enhanced_sentiment_ml.py -v

# Technical indicator calculations
python -m pytest tests/test_enhanced_technical_calculator.py -v

# ML materialized view updates
python -m pytest tests/test_enhanced_materialized_updater.py -v

# ML market correlation analysis
python -m pytest tests/test_ml_market_collector.py -v
```

### Running Specific Test Classes or Methods

#### By Test Class
```bash
# Run specific test class
python -m pytest tests/test_base_collector.py::TestBaseCollectorCore -v

# Run specific test method
python -m pytest tests/test_base_collector.py::TestBaseCollectorCore::test_collector_initialization -v
```

#### By Pattern Matching
```bash
# Run tests matching a pattern
python -m pytest tests/ -k "test_config" -v

# Run tests for specific functionality
python -m pytest tests/ -k "validation" -v

# Run async tests only
python -m pytest tests/ -k "asyncio" -v
```

### Test Output and Reporting

#### Verbose Output
```bash
# Maximum verbosity
python -m pytest tests/ -k "not integration" -vv

# Show test durations
python -m pytest tests/ -k "not integration" --durations=10
```

#### Stopping on Failures
```bash
# Stop on first failure
python -m pytest tests/ -k "not integration" -x

# Stop after N failures
python -m pytest tests/ -k "not integration" --maxfail=3
```

#### Quiet Mode
```bash
# Minimal output
python -m pytest tests/ -k "not integration" -q

# Only show test summary
python -m pytest tests/ -k "not integration" --tb=no
```

## Test Categories and Markers

### Available Pytest Markers
- `@pytest.mark.unit` - Unit tests with mocked dependencies
- `@pytest.mark.integration` - Integration tests requiring real services
- `@pytest.mark.asyncio` - Asynchronous tests
- `@pytest.mark.database` - Tests requiring database connections
- `@pytest.mark.real_api` - Tests making actual API calls
- `@pytest.mark.slow` - Tests taking more than 30 seconds
- `@pytest.mark.performance` - Performance and load testing

### Running by Markers
```bash
# Run only unit tests
python -m pytest tests/ -m "unit" -v

# Run async tests
python -m pytest tests/ -m "asyncio" -v

# Exclude slow tests
python -m pytest tests/ -m "not slow" -v
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Check Python path
export PYTHONPATH=/mnt/e/git/crypto-data-collection:$PYTHONPATH

# Verify test environment
python -c "import sys; print(sys.path)"
```

#### Missing Dependencies
```bash
# Install missing packages
pip install pytest pytest-asyncio pytest-cov fastapi httpx

# Check installed packages
pip list | grep pytest
```

#### Mock Dependencies Not Found
```bash
# Verify mock modules exist
ls -la mock_transformers.py table_config.py

# Test mock imports
python -c "from mock_transformers import pipeline; print('Mock transformers working')"
```

### Test Environment Validation
```bash
# Verify test environment setup
python -c "
import pytest
from tests.test_base_collector import TestBaseCollectorCore
print('✅ Test environment is operational')
"
```

## Test Development Guidelines

### Writing New Unit Tests
1. **Follow naming convention**: `test_*.py` files, `test_*` functions
2. **Use appropriate fixtures**: Database, API mocks, test data
3. **Mock external dependencies**: APIs, databases, file systems
4. **Test error conditions**: Invalid inputs, network failures, timeouts
5. **Validate outputs**: Return values, side effects, state changes

### Test Organization
```python
class TestMyCollector:
    """Test MyCollector functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {...}
    
    def test_initialization(self, mock_config):
        """Test collector initialization"""
        pass
    
    @pytest.mark.asyncio
    async def test_async_operation(self, mock_config):
        """Test async operations"""
        pass
```

### Best Practices
- **Isolate tests**: Each test should be independent
- **Use descriptive names**: Test names should explain what is being tested
- **Mock external services**: Don't rely on external APIs or databases
- **Test edge cases**: Boundary conditions, error states, empty inputs
- **Maintain test data**: Use factories or fixtures for consistent test data

## Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/tests.yml
name: Unit Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run unit tests
        run: python -m pytest tests/ -k "not integration" --cov=. --cov-report=xml
```

### Local Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Performance and Coverage

### Coverage Analysis
```bash
# Generate detailed coverage report
python -m pytest tests/ -k "not integration" --cov=. --cov-report=term-missing --cov-report=html

# View HTML coverage report
open test-results/coverage/index.html
```

### Performance Profiling
```bash
# Profile test execution
python -m pytest tests/ -k "not integration" --profile --profile-svg

# Time individual tests
python -m pytest tests/ -k "not integration" --durations=0
```

This documentation provides comprehensive guidance for running and maintaining the unit test suite. The tests are designed to be fast, reliable, and comprehensive, providing confidence in code quality and functionality.