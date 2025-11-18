#!/usr/bin/env python3
"""
Comprehensive Test Configuration and Fixtures

This module provides shared fixtures for all crypto data collector tests,
including Docker container management, API key validation, and database setup.
Extended with endpoint testing configurations.
"""

import pytest
import asyncio
import os
import time
import docker
import mysql.connector
import redis
import requests
from typing import Dict, Any, Generator, Optional
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
import json
import sys
import logging
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to use centralized database configuration
try:
    from shared.database_config import db_config, get_db_connection, get_redis_connection
    CENTRALIZED_CONFIG_AVAILABLE = True
    logger.info("✅ Using centralized database configuration")
except ImportError:
    CENTRALIZED_CONFIG_AVAILABLE = False
    logger.warning("⚠️ Centralized config not available, using local config")

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration with environment variable support and centralized config fallback
if CENTRALIZED_CONFIG_AVAILABLE:
    # Use centralized configuration
    TEST_CONFIG = {
        'mysql': db_config.get_mysql_config_dict(),
        'redis': db_config.get_redis_config_dict(),
        'api_timeouts': {
            'coingecko': 10,
            'fred': 15,
            'guardian': 12
        },
        'rate_limits': {
            'coingecko': 0.2,  # 5 requests per second for testing
            'fred': 0.5,       # 2 requests per second for testing
            'guardian': 0.3    # ~3 requests per second for testing
        },
        'endpoint_testing': {
            'api_gateway_url': 'http://localhost:8000',
            'collectors': {
                'price': 'http://localhost:8001',
                'news': 'http://localhost:8002', 
                'sentiment': 'http://localhost:8003',
                'technical': 'http://localhost:8004',
                'macro': 'http://localhost:8005'
            },
            'auth': {
                'master_key': 'master-key',
                'readonly_key': 'readonly-key',
                'trading_key': 'trading-key'
            },
            'timeouts': {
                'default': 30,
                'websocket': 10
            }
        }
    }
else:
    # Fallback to local configuration
    TEST_CONFIG = {
        'mysql': {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_data_test'),
            'charset': 'utf8mb4'
        },
        'redis': {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': 0
        },
        'api_timeouts': {
            'coingecko': 10,
            'fred': 15,
            'guardian': 12
        },
        'rate_limits': {
            'coingecko': 0.2,  # 5 requests per second for testing
            'fred': 0.5,       # 2 requests per second for testing
            'guardian': 0.3    # ~3 requests per second for testing
        },
        'endpoint_testing': {
            'api_gateway_url': 'http://localhost:8000',
            'collectors': {
                'price': 'http://localhost:8001',
                'news': 'http://localhost:8002', 
                'sentiment': 'http://localhost:8003',
                'technical': 'http://localhost:8004',
                'macro': 'http://localhost:8005'
            },
            'auth': {
                'master_key': 'master-key',
                'readonly_key': 'readonly-key',
                'trading_key': 'trading-key'
            },
            'timeouts': {
                'default': 30,
                'websocket': 10
            }
        }
    }


# Pytest Configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test requiring running services"
    )
    config.addinivalue_line(
        "markers", 
        "unit: mark test as unit test with mocked dependencies"
    )
    config.addinivalue_line(
        "markers", 
        "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", 
        "auth: mark test as authentication/authorization test"
    )
    config.addinivalue_line(
        "markers", 
        "websocket: mark test as WebSocket functionality test"
    )
    config.addinivalue_line(
        "markers", 
        "slow: mark test as slow running test"
    )
    config.addinivalue_line(
        "markers", 
        "endpoint: mark test as endpoint testing"
    )


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests (requires running services)"
    )
    parser.addoption(
        "--performance",
        action="store_true", 
        default=False,
        help="run performance tests"
    )
    parser.addoption(
        "--endpoint",
        action="store_true",
        default=False,
        help="run endpoint tests (requires running API services)"
    )
    parser.addoption(
        "--api-key",
        action="store",
        default="master-key",
        help="API key for integration tests"
    )
    parser.addoption(
        "--api-host",
        action="store",
        default="localhost:8000",
        help="API host for integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    if not config.getoption("--performance"):
        skip_performance = pytest.mark.skip(reason="need --performance option to run")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_performance)
    
    if not config.getoption("--endpoint"):
        skip_endpoint = pytest.mark.skip(reason="need --endpoint option to run")
        for item in items:
            if "endpoint" in item.keywords:
                item.add_marker(skip_endpoint)

@pytest.fixture(scope="session")
def docker_client():
    """Docker client for managing test containers"""
    client = docker.from_env()
    return client

@pytest.fixture(scope="session")
def test_api_keys():
    """Provide API keys for testing with real APIs using production keys"""
    keys = {
        'coingecko': 'CG-94NCcVD2euxaGTZe94bS2oYz',
        'fred': '35478996c5e061d0fc99fc73f5ce348d', 
        'guardian': os.getenv('GUARDIAN_TEST_KEY', 'test_guardian_key'),  # Fallback if needed
    }
    
    print(f"\n🔑 Using API keys for testing:")
    print(f"   CoinGecko Premium: {keys['coingecko'][:8]}...")
    print(f"   FRED: {keys['fred'][:8]}...")
    print(f"   Guardian: {keys['guardian'][:8]}...")
    
    return keys


@pytest.fixture(scope="session")
def api_key(request):
    """API key for integration tests"""
    return request.config.getoption("--api-key")


@pytest.fixture(scope="session")
def api_host(request):
    """API host for integration tests"""
    return request.config.getoption("--api-host")


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "database": {
            "host": os.getenv("TEST_DB_HOST", "localhost"),
            "port": int(os.getenv("TEST_DB_PORT", "3306")),
            "user": os.getenv("TEST_DB_USER", "test_user"),
            "password": os.getenv("TEST_DB_PASSWORD", "test_password"),
            "database": os.getenv("TEST_DB_NAME", "test_crypto_data")
        },
        "redis": {
            "host": os.getenv("TEST_REDIS_HOST", "localhost"),
            "port": int(os.getenv("TEST_REDIS_PORT", "6379")),
            "db": int(os.getenv("TEST_REDIS_DB", "1"))
        },
        "api": {
            "timeout": 30,
            "retry_attempts": 3
        }
    }


# Session-scoped fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    yield loop
    
    # Clean up
    try:
        loop.close()
    except RuntimeError:
        pass


# Database fixtures
@pytest.fixture
def mock_mysql_pool():
    """Mock MySQL connection pool"""
    pool = Mock()
    connection = AsyncMock()
    cursor = AsyncMock()
    
    # Configure cursor methods
    cursor.execute = AsyncMock()
    cursor.fetchone = AsyncMock()
    cursor.fetchall = AsyncMock()
    cursor.fetchmany = AsyncMock()
    cursor.close = AsyncMock()
    
    # Configure connection methods
    connection.cursor = AsyncMock(return_value=cursor)
    connection.commit = AsyncMock()
    connection.rollback = AsyncMock()
    connection.close = AsyncMock()
    
    # Configure pool methods
    pool.acquire = AsyncMock(return_value=connection)
    pool.release = AsyncMock()
    
    return pool, connection, cursor


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    redis_client = AsyncMock()
    
    # Configure Redis methods
    redis_client.get = AsyncMock(return_value=None)
    redis_client.set = AsyncMock(return_value=True)
    redis_client.setex = AsyncMock(return_value=True)
    redis_client.delete = AsyncMock(return_value=1)
    redis_client.exists = AsyncMock(return_value=False)
    redis_client.ping = AsyncMock(return_value=True)
    redis_client.flushdb = AsyncMock(return_value=True)
    
    return redis_client


# HTTP client fixtures
@pytest.fixture
async def async_client():
    """Async HTTP client for testing"""
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def auth_headers(api_key):
    """Authentication headers for API requests"""
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture
def test_data():
    """Test data fixtures"""
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    
    return {
        "price_data": {
            "symbol": "BTC",
            "current_price": 45000.0,
            "price_change_24h": 1000.0,
            "price_change_percentage_24h": 2.27,
            "market_cap": 900000000000,
            "total_volume": 25000000000,
            "timestamp": now
        },
        "sentiment_data": {
            "symbol": "BTC",
            "sentiment_score": 0.75,
            "sentiment_label": "positive",
            "confidence": 0.85,
            "source": "news_analysis",
            "timestamp": now
        },
        "news_data": {
            "title": "Bitcoin Reaches New High",
            "content": "Bitcoin has reached a new all-time high of $45,000...",
            "source": "CryptoNews",
            "url": "https://example.com/news/bitcoin-high",
            "published_at": now,
            "symbols": ["BTC"],
            "sentiment_score": 0.8,
            "relevance_score": 0.9
        },
        "technical_data": {
            "symbol": "BTC",
            "rsi": 65.5,
            "macd": 120.5,
            "macd_signal": 115.0,
            "bb_upper": 46000.0,
            "bb_middle": 45000.0,
            "bb_lower": 44000.0,
            "sma_20": 44500.0,
            "sma_50": 43000.0,
            "ema_12": 45100.0,
            "ema_26": 44800.0,
            "timestamp": now
        },
        "ml_features": {
            "symbol": "BTC",
            "features": {
                "price_momentum": 0.15,
                "volatility": 0.25,
                "volume_trend": 0.8,
                "sentiment_composite": 0.7,
                "technical_strength": 0.6
            },
            "timestamp": now
        }
    }


# Test utilities
@pytest.fixture
def test_symbols():
    """Common test symbols"""
    return ["BTC", "ETH", "ADA", "SOL", "DOT", "LINK"]


@pytest.fixture
def test_stock_symbols():
    """Common stock symbols for testing"""
    return ["TSLA", "AAPL", "GOOGL", "MSFT", "AMZN"]


# Mock FastAPI app fixture
@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application for testing"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI(title="Test API")
    
    # Add basic endpoints
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
    
    @app.get("/ready") 
    async def ready():
        return {"status": "ready", "timestamp": "2024-01-01T00:00:00Z"}
    
    return app


@pytest.fixture
def test_client(mock_fastapi_app):
    """Test client for FastAPI app"""
    from fastapi.testclient import TestClient
    return TestClient(mock_fastapi_app)


# Database test data fixtures
@pytest.fixture
def sample_price_records():
    """Sample price records for testing"""
    from datetime import datetime, timedelta
    
    base_time = datetime.utcnow()
    
    return [
        {
            'symbol': 'BTC',
            'current_price': 45000.0 + i * 100,
            'price_change_24h': 1000.0 + i * 10,
            'price_change_percentage_24h': 2.3 + i * 0.1,
            'market_cap': 900000000000 + i * 1000000000,
            'total_volume': 25000000000 + i * 100000000,
            'timestamp': base_time - timedelta(minutes=i * 5)
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_sentiment_records():
    """Sample sentiment records for testing"""
    from datetime import datetime, timedelta
    
    base_time = datetime.utcnow()
    
    return [
        {
            'symbol': 'BTC',
            'sentiment_score': 0.1 * (i % 11) - 0.5,  # Range from -0.5 to 0.5
            'sentiment_label': 'positive' if i % 3 == 0 else 'negative' if i % 3 == 1 else 'neutral',
            'confidence': 0.5 + 0.04 * i,  # Range from 0.5 to 0.9
            'source': f'source_{i % 3}',
            'timestamp': base_time - timedelta(hours=i)
        }
        for i in range(10)
    ]


# Error simulation fixtures
@pytest.fixture
def simulate_db_error():
    """Fixture to simulate database errors"""
    def _simulate_error(error_type="connection"):
        if error_type == "connection":
            return Exception("Database connection failed")
        elif error_type == "timeout":
            return Exception("Database timeout")
        elif error_type == "permission":
            return Exception("Permission denied")
        else:
            return Exception("Unknown database error")
    
    return _simulate_error


@pytest.fixture
def simulate_api_error():
    """Fixture to simulate API errors"""
    def _simulate_error(status_code=500, message="Internal server error"):
        from fastapi import HTTPException
        return HTTPException(status_code=status_code, detail=message)
    
    return _simulate_error


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Performance monitoring utility"""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self):
            self.end_time = time.time()
            
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
            
        def assert_under_threshold(self, threshold_seconds=1.0):
            assert self.duration is not None, "Timer not stopped"
            assert self.duration < threshold_seconds, \
                f"Operation took {self.duration:.2f}s, expected < {threshold_seconds}s"
    
    return PerformanceMonitor


# WebSocket testing fixtures
@pytest.fixture
def websocket_test_client():
    """WebSocket test client"""
    def _create_websocket_client(app):
        from fastapi.testclient import TestClient
        client = TestClient(app)
        return client
    
    return _create_websocket_client


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("DATABASE_URL", "mysql://test:test@localhost/test_db")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
    
    yield
    
    # Cleanup if needed
    test_vars = ["ENVIRONMENT", "LOG_LEVEL", "DATABASE_URL", "REDIS_URL"]
    for var in test_vars:
        if var in os.environ and os.environ[var].startswith(("test", "Test")):
            del os.environ[var]


# Custom assertions
class TestAssertions:
    """Custom assertions for testing"""
    
    @staticmethod
    def assert_valid_timestamp(timestamp_str):
        """Assert timestamp string is valid ISO format"""
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            # Check that timestamp is recent (within 24 hours)
            now = datetime.utcnow().replace(tzinfo=dt.tzinfo)
            diff = abs((now - dt).total_seconds())
            assert diff < 86400, f"Timestamp {timestamp_str} is not recent"
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp_str}")
    
    @staticmethod
    def assert_valid_price_data(price_data):
        """Assert price data structure is valid"""
        required_fields = ["symbol", "current_price", "timestamp"]
        for field in required_fields:
            assert field in price_data, f"Missing required field: {field}"
        
        assert isinstance(price_data["current_price"], (int, float))
        assert price_data["current_price"] > 0
        TestAssertions.assert_valid_timestamp(price_data["timestamp"])
    
    @staticmethod
    def assert_valid_sentiment_data(sentiment_data):
        """Assert sentiment data structure is valid"""
        required_fields = ["sentiment_score", "sentiment_label", "timestamp"]
        for field in required_fields:
            assert field in sentiment_data, f"Missing required field: {field}"
        
        assert -1 <= sentiment_data["sentiment_score"] <= 1
        assert sentiment_data["sentiment_label"] in ["positive", "negative", "neutral"]
        TestAssertions.assert_valid_timestamp(sentiment_data["timestamp"])
    
    @staticmethod
    def assert_valid_news_data(news_data):
        """Assert news data structure is valid"""
        required_fields = ["title", "content", "source", "url", "published_at"]
        for field in required_fields:
            assert field in news_data, f"Missing required field: {field}"
        
        assert news_data["url"].startswith(("http://", "https://"))
        TestAssertions.assert_valid_timestamp(news_data["published_at"])


@pytest.fixture
def test_assertions():
    """Test assertions utility"""
    return TestAssertions


# Pytest plugins and hooks
def pytest_runtest_setup(item):
    """Set up before each test"""
    # Clear any existing patches
    patch.stopall()


def pytest_runtest_teardown(item):
    """Clean up after each test"""
    # Stop all patches
    patch.stopall()


# Test discovery configuration
def pytest_ignore_collect(collection_path, config):
    """Ignore certain files during test collection"""
    ignore_patterns = [
        "__pycache__",
        "*.pyc",
        ".git",
        "node_modules",
        "venv",
        ".env"
    ]
    
    for pattern in ignore_patterns:
        if pattern in str(collection_path):
            return True
    return False

@pytest.fixture(scope="session")
def test_mysql_connection():
    """MySQL database connection for test database with improved retry logic"""
    # Enhanced retry logic with better error handling
    max_retries = 60  # Increased retries for CI/CD environments
    retry_count = 0
    connection = None
    
    logger.info(f"🔍 Attempting to connect to MySQL at {TEST_CONFIG['mysql']['host']}:{TEST_CONFIG['mysql']['port']}")
    
    while retry_count < max_retries:
        try:
            # Test basic connectivity first
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((TEST_CONFIG['mysql']['host'], TEST_CONFIG['mysql']['port']))
            sock.close()
            
            if result != 0:
                raise Exception(f"Cannot reach MySQL port {TEST_CONFIG['mysql']['port']}")
            
            # Now try MySQL connection
            connection = mysql.connector.connect(**TEST_CONFIG['mysql'])
            connection.ping(reconnect=True)
            
            logger.info(f"✅ Successfully connected to MySQL on attempt {retry_count + 1}")
            yield connection
            break
            
        except Exception as e:
            retry_count += 1
            logger.warning(f"❌ MySQL connection attempt {retry_count}/{max_retries} failed: {e}")
            
            if retry_count >= max_retries:
                # Provide detailed diagnostic information
                error_msg = f"""
                Could not connect to test MySQL after {max_retries} attempts.
                
                Configuration:
                - Host: {TEST_CONFIG['mysql']['host']}
                - Port: {TEST_CONFIG['mysql']['port']}
                - User: {TEST_CONFIG['mysql']['user']}
                - Database: {TEST_CONFIG['mysql']['database']}
                
                Last error: {e}
                
                Possible causes:
                1. MySQL service not started in CI/CD
                2. Port mapping mismatch 
                3. Service health check not ready
                4. Network connectivity issues
                
                Environment variables:
                - MYSQL_HOST: {os.getenv('MYSQL_HOST', 'not set')}
                - MYSQL_PORT: {os.getenv('MYSQL_PORT', 'not set')}
                - MYSQL_USER: {os.getenv('MYSQL_USER', 'not set')}
                - MYSQL_DATABASE: {os.getenv('MYSQL_DATABASE', 'not set')}
                """
                raise Exception(error_msg)
            
            # Exponential backoff with jitter
            sleep_time = min(2 ** (retry_count // 5), 10) + (retry_count % 3)
            time.sleep(sleep_time)
    
    # Cleanup
    try:
        if connection and connection.is_connected():
            connection.close()
    except Exception as e:
        logger.warning(f"Error closing MySQL connection: {e}")

@pytest.fixture(scope="session")
def test_redis_connection():
    """Redis connection for test cache with improved retry logic"""
    # Enhanced retry logic similar to MySQL
    max_retries = 30
    retry_count = 0
    connection = None
    
    logger.info(f"🔍 Attempting to connect to Redis at {TEST_CONFIG['redis']['host']}:{TEST_CONFIG['redis']['port']}")
    
    while retry_count < max_retries:
        try:
            # Test basic connectivity first
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((TEST_CONFIG['redis']['host'], TEST_CONFIG['redis']['port']))
            sock.close()
            
            if result != 0:
                raise Exception(f"Cannot reach Redis port {TEST_CONFIG['redis']['port']}")
            
            # Now try Redis connection
            connection = redis.Redis(**TEST_CONFIG['redis'])
            connection.ping()
            
            logger.info(f"✅ Successfully connected to Redis on attempt {retry_count + 1}")
            yield connection
            break
            
        except Exception as e:
            retry_count += 1
            logger.warning(f"❌ Redis connection attempt {retry_count}/{max_retries} failed: {e}")
            
            if retry_count >= max_retries:
                error_msg = f"""
                Could not connect to test Redis after {max_retries} attempts.
                
                Configuration:
                - Host: {TEST_CONFIG['redis']['host']}
                - Port: {TEST_CONFIG['redis']['port']}
                
                Last error: {e}
                
                Environment variables:
                - REDIS_HOST: {os.getenv('REDIS_HOST', 'not set')}
                - REDIS_PORT: {os.getenv('REDIS_PORT', 'not set')}
                """
                raise Exception(error_msg)
            
            # Progressive backoff
            sleep_time = min(1 + (retry_count // 5), 5)
            time.sleep(sleep_time)
    
    # Cleanup
    try:
        if connection:
            connection.close()
    except Exception as e:
        logger.warning(f"Error closing Redis connection: {e}")

@pytest.fixture
def clean_test_database(test_mysql_connection):
    """Clean test database before each test"""
    cursor = test_mysql_connection.cursor()
    
    # List of tables to clean
    tables_to_clean = [
        'price_data_real',
        'technical_indicators',
        'onchain_data',
        'macro_indicators',
        'crypto_news.news_data',
        'real_time_sentiment_signals',
        'ohlc_data',
        'ml_features_materialized',
        'trading_signals',
        'crypto_assets'
    ]
    
    # Clean each table
    for table in tables_to_clean:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)")
        except mysql.connector.Error:
            # Table might not exist, continue
            pass
    
    test_mysql_connection.commit()
    cursor.close()

@pytest.fixture
def clean_test_redis(test_redis_connection):
    """Clean test Redis cache before each test"""
    # Flush test database
    test_redis_connection.flushdb()

@pytest.fixture
def rate_limiter():
    """Rate limiter for API calls during testing"""
    last_call_times = {}
    
    def limit_rate(api_name: str, delay: float = None):
        if delay is None:
            delay = TEST_CONFIG['rate_limits'].get(api_name, 0.5)
        
        if api_name in last_call_times:
            time_since_last = time.time() - last_call_times[api_name]
            if time_since_last < delay:
                time.sleep(delay - time_since_last)
        
        last_call_times[api_name] = time.time()
    
    return limit_rate

@pytest.fixture
def test_symbols():
    """Standard test symbols for consistent testing"""
    return {
        'primary': ['bitcoin', 'ethereum', 'solana'],
        'secondary': ['cardano', 'polkadot', 'chainlink'],
        'test_only': ['dogecoin']  # For destructive tests
    }

@pytest.fixture
def mock_api_responses():
    """Mock API responses for fallback when real APIs are not available"""
    return {
        'coingecko': {
            'bitcoin': {
                'id': 'bitcoin',
                'symbol': 'btc',
                'name': 'Bitcoin',
                'current_price': 45000.0,
                'market_cap': 850000000000,
                'total_volume': 25000000000,
                'price_change_percentage_24h': 2.5
            }
        },
        'fred': {
            'GDP': {
                'observations': [
                    {'date': '2024-01-01', 'value': '25000.0'},
                    {'date': '2024-04-01', 'value': '25500.0'}
                ]
            }
        },
        'guardian': {
            'response': {
                'status': 'ok',
                'results': [
                    {
                        'webTitle': 'Test Bitcoin News',
                        'webPublicationDate': '2024-01-01T10:00:00Z',
                        'fields': {
                            'bodyText': 'Bitcoin reaches new heights in test scenario'
                        }
                    }
                ]
            }
        }
    }

@pytest.fixture(scope="session")
def docker_services_ready(docker_client):
    """Wait for all Docker services to be ready"""
    services_to_check = [
        ('test-mysql', 3307),
        ('test-redis', 6380),
        ('onchain-collector-test', 8000),
        ('price-collector-test', 8001),
        ('macro-collector-test', 8002)
    ]
    
    def check_service(host, port, timeout=60):
        import socket
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    # Check each service
    for service_name, port in services_to_check:
        if not check_service('localhost', port):
            pytest.skip(f"Service {service_name} not ready on port {port}")
    
    return True

@pytest.fixture
def collector_endpoints():
    """Collector service endpoints for testing"""
    return {
        'onchain': 'http://localhost:8000',
        'price': 'http://localhost:8001', 
        'macro': 'http://localhost:8002',
        'news': 'http://localhost:8003',
        'technical': 'http://localhost:8004',
        'sentiment': 'http://localhost:8005'
    }

@pytest.fixture
def test_data_factory():
    """Factory for creating test data"""
    class TestDataFactory:
        @staticmethod
        def price_record(symbol='bitcoin', price=45000.0):
            return {
                'symbol': symbol,
                'price': price,
                'volume': 1000000.0,
                'market_cap': price * 21000000,
                'timestamp': datetime.now(timezone.utc),
                'data_completeness_percentage': 95.0
            }
        
        @staticmethod
        def technical_indicator(symbol='bitcoin', indicator_type='sma'):
            return {
                'symbol': symbol,
                'indicator_type': indicator_type,
                'value': 44500.0,
                'period': 20,
                'timestamp': datetime.now(timezone.utc),
                'data_completeness_percentage': 100.0
            }
        
        @staticmethod
        def macro_indicator(indicator='GDP', value=25000.0):
            return {
                'indicator': indicator,
                'value': value,
                'unit': 'billions',
                'timestamp': datetime.now(timezone.utc),
                'data_completeness_percentage': 100.0
            }
    
    return TestDataFactory()

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test(clean_test_database, clean_test_redis):
    """Automatic cleanup after each test"""
    yield
    # Cleanup happens automatically via the clean_* fixtures

# Performance monitoring fixture
@pytest.fixture
def performance_monitor():
    """Monitor test performance"""
    import time
    import psutil
    
    start_time = time.time()
    start_memory = psutil.virtual_memory().used
    
    yield
    
    end_time = time.time()
    end_memory = psutil.virtual_memory().used
    
    duration = end_time - start_time
    memory_used = end_memory - start_memory
    
    if duration > 30:  # Log slow tests
        print(f"\nSLOW TEST: Duration: {duration:.2f}s, Memory: {memory_used / 1024 / 1024:.2f}MB")