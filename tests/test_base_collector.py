#!/usr/bin/env python3
"""
Comprehensive Unit Testing Framework for Crypto Data Collectors

This module provides a standardized testing framework for all collectors
implementing the BaseCollector template.
"""

import pytest
import asyncio
import aiohttp
import mysql.connector
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
import json
import os
from contextlib import asynccontextmanager

# Import the base collector and components
from base_collector_template import (
    BaseCollector, CollectorConfig, HealthResponse, ReadinessResponse, 
    DataQualityReport, PerformanceMetrics, CircuitBreaker, RateLimiter
)

class MockCollectorConfig(CollectorConfig):
    """Mock configuration for testing"""
    
    def __init__(self):
        super().__init__(
            service_name="test-collector",
            service_version="1.0.0-test",
            mysql_host="localhost",
            mysql_port=3306,
            mysql_user="test_user",
            mysql_password="test_password",
            mysql_database="test_db",
            collection_interval=60,
            enable_rate_limiting=True,
            enable_circuit_breaker=True,
            enable_data_validation=True,
            enable_alerting=True,
            enable_performance_monitoring=True
        )

class MockCollector(BaseCollector):
    """Mock collector implementation for testing"""
    
    def __init__(self, config: CollectorConfig = None):
        if config is None:
            config = MockCollectorConfig()
        super().__init__(config)
        self.collected_data = []
        self.backfilled_data = []
    
    async def collect_data(self) -> int:
        """Mock data collection"""
        await asyncio.sleep(0.1)  # Simulate work
        self.collected_data.append({
            "timestamp": datetime.now(timezone.utc),
            "data": "test_data",
            "count": 1
        })
        return 1
    
    async def backfill_data(self, missing_periods: List[Dict], force: bool = False) -> int:
        """Mock backfill implementation"""
        await asyncio.sleep(0.1)  # Simulate work
        for period in missing_periods:
            self.backfilled_data.append({
                "period": period,
                "timestamp": datetime.now(timezone.utc),
                "records": 10
            })
        return len(missing_periods) * 10
    
    async def _get_table_status(self, cursor) -> Dict[str, Any]:
        """Mock table status"""
        return {
            "test_table": {
                "total_records": 1000,
                "last_update": datetime.now(timezone.utc),
                "status": "healthy"
            }
        }
    
    async def _analyze_missing_data(self, start_date: datetime, end_date: datetime, symbols: List[str] = None) -> List[Dict]:
        """Mock missing data analysis"""
        return [
            {
                "date": start_date.date(),
                "reason": "missing_data",
                "count": 5
            }
        ]
    
    async def _estimate_backfill_records(self, start_date: datetime, end_date: datetime, symbols: List[str] = None) -> int:
        """Mock backfill estimation"""
        days = (end_date - start_date).days
        return days * 10
    
    async def _get_required_fields(self) -> List[str]:
        """Mock required fields"""
        return ["timestamp", "data", "count"]
    
    async def _generate_data_quality_report(self) -> DataQualityReport:
        """Mock data quality report"""
        return DataQualityReport(
            total_records=1000,
            valid_records=950,
            invalid_records=30,
            duplicate_records=20,
            validation_errors=["5 records missing timestamp", "10 records with invalid data"],
            data_quality_score=95.0
        )

class BaseCollectorTestCase:
    """Base test case class with common test utilities"""
    
    @pytest.fixture
    def mock_config(self):
        """Provide mock configuration"""
        return MockCollectorConfig()
    
    @pytest.fixture
    def mock_collector(self, mock_config):
        """Provide mock collector instance"""
        return MockCollector(mock_config)
    
    @pytest.fixture
    def client(self, mock_collector):
        """Provide FastAPI test client"""
        return TestClient(mock_collector.app)
    
    @pytest.fixture
    async def async_client(self, mock_collector):
        """Provide async test client"""
        async with AsyncMock() as mock:
            yield mock
    
    @pytest.fixture
    def mock_database(self):
        """Mock database connection"""
        with patch('mysql.connector.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            yield mock_conn, mock_cursor

class TestBaseCollectorCore(BaseCollectorTestCase):
    """Test core BaseCollector functionality"""
    
    def test_collector_initialization(self, mock_config):
        """Test collector initialization"""
        collector = MockCollector(mock_config)
        
        assert collector.config.service_name == "test-collector"
        assert collector.config.service_version == "1.0.0-test"
        assert collector.startup_complete == False
        assert collector.is_collecting == False
        assert collector.collection_errors == 0
        assert collector.session_id is not None
        
        # Test components initialization
        assert collector.rate_limiter is not None
        assert collector.circuit_breaker is not None
        assert collector.data_validator is not None
    
    def test_fastapi_app_creation(self, mock_collector):
        """Test FastAPI app is created with correct configuration"""
        app = mock_collector.app
        
        assert app.title == "Test Collector"
        assert app.version == "1.0.0-test"
        assert app.description == "Standardized data collector for test-collector"
    
    def test_logging_setup(self, mock_collector):
        """Test logging is properly configured"""
        assert mock_collector.logger is not None
        assert hasattr(mock_collector.logger, 'info')
        assert hasattr(mock_collector.logger, 'error')
        assert hasattr(mock_collector.logger, 'warning')
    
    def test_metrics_setup(self, mock_collector):
        """Test Prometheus metrics are properly initialized"""
        metrics = mock_collector.metrics
        
        required_metrics = [
            'collection_requests_total',
            'collection_duration_seconds',
            'records_processed_total',
            'database_operations_total',
            'api_requests_total',
            'backfill_operations_total',
            'active_collections'
        ]
        
        for metric in required_metrics:
            assert metric in metrics

class TestHealthAndReadinessEndpoints(BaseCollectorTestCase):
    """Test health and readiness endpoints"""
    
    def test_health_endpoint_healthy(self, client, mock_database):
        """Test health endpoint returns healthy status"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = (1,)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "test-collector"
        assert data["version"] == "1.0.0-test"
        assert data["database_connected"] == True
    
    def test_health_endpoint_unhealthy(self, client):
        """Test health endpoint returns unhealthy when database fails"""
        with patch('mysql.connector.connect', side_effect=mysql.connector.Error("Connection failed")):
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_connected"] == False
    
    def test_ready_endpoint_not_ready(self, client):
        """Test readiness endpoint when service is not ready"""
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] == False
        assert "checks" in data
        assert data["checks"]["startup_complete"] == False
    
    def test_ready_endpoint_ready(self, client, mock_collector, mock_database):
        """Test readiness endpoint when service is ready"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = (1,)
        
        # Mark as ready
        mock_collector.startup_complete = True
        
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] == True
        assert data["checks"]["startup_complete"] == True
        assert data["checks"]["database"] == True
        assert data["checks"]["configuration"] == True

class TestDataCollectionEndpoints(BaseCollectorTestCase):
    """Test data collection related endpoints"""
    
    def test_manual_collect_endpoint(self, client, mock_collector):
        """Test manual collection trigger"""
        response = client.post("/collect")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "task_id" in data
    
    def test_collect_already_running(self, client, mock_collector):
        """Test collection trigger when already running"""
        mock_collector.is_collecting = True
        
        response = client.post("/collect")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_collecting"
    
    def test_backfill_endpoint(self, client):
        """Test backfill endpoint"""
        backfill_request = {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-02T00:00:00Z",
            "symbols": ["BTC", "ETH"],
            "force": False
        }
        
        response = client.post("/backfill", json=backfill_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "task_id" in data
        assert "estimated_records" in data
    
    def test_data_quality_endpoint(self, client, mock_database):
        """Test data quality report endpoint"""
        mock_conn, mock_cursor = mock_database
        
        response = client.get("/data-quality")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data
        assert "valid_records" in data
        assert "data_quality_score" in data

class TestCircuitBreakerAndRateLimiting(BaseCollectorTestCase):
    """Test circuit breaker and rate limiting functionality"""
    
    def test_circuit_breaker_initialization(self, mock_collector):
        """Test circuit breaker is properly initialized"""
        cb = mock_collector.circuit_breaker
        assert cb.failure_threshold == 5
        assert cb.timeout == 60
        assert cb.state.value == "closed"
    
    def test_circuit_breaker_status_endpoint(self, client):
        """Test circuit breaker status endpoint"""
        response = client.get("/circuit-breaker-status")
        
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "failure_count" in data
    
    def test_rate_limiter_initialization(self, mock_collector):
        """Test rate limiter is properly initialized"""
        rl = mock_collector.rate_limiter
        assert rl is not None
        assert rl.max_tokens == 60  # From config
    
    @pytest.mark.asyncio
    async def test_rate_limiting_functionality(self, mock_collector):
        """Test rate limiting actually works"""
        rl = mock_collector.rate_limiter
        
        # Should be able to get tokens initially
        await rl.wait_for_token()
        await rl.wait_for_token()
        
        # Exhaust all tokens
        for _ in range(58):  # Already used 2
            await rl.wait_for_token()
        
        # Next request should be rate limited
        start_time = asyncio.get_event_loop().time()
        await rl.wait_for_token()
        end_time = asyncio.get_event_loop().time()
        
        # Should have waited for token refill
        assert end_time - start_time > 0.5

class TestDataValidation(BaseCollectorTestCase):
    """Test data validation functionality"""
    
    def test_validate_data_endpoint_enabled(self, client):
        """Test data validation endpoint when enabled"""
        test_data = {
            "timestamp": "2024-01-01T00:00:00Z",
            "data": "test_value",
            "count": 1
        }
        
        response = client.post("/validate-data", json=test_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
    
    def test_validate_data_endpoint_disabled(self, client, mock_collector):
        """Test data validation endpoint when disabled"""
        mock_collector.config.enable_data_validation = False
        
        response = client.post("/validate-data", json={"test": "data"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "validation_disabled"

class TestAlerting(BaseCollectorTestCase):
    """Test alerting functionality"""
    
    @patch('aiohttp.ClientSession.post')
    def test_alert_endpoint(self, mock_post, client):
        """Test alert sending endpoint"""
        mock_response = Mock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        alert_data = {
            "alert_type": "test_alert",
            "severity": "warning",
            "message": "Test alert message",
            "service": "test-collector"
        }
        
        response = client.post("/alert", json=alert_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alert_sent"
    
    def test_alert_endpoint_disabled(self, client, mock_collector):
        """Test alert endpoint when alerting is disabled"""
        mock_collector.config.enable_alerting = False
        
        alert_data = {
            "alert_type": "test_alert",
            "severity": "warning", 
            "message": "Test alert message",
            "service": "test-collector"
        }
        
        response = client.post("/alert", json=alert_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alerting_disabled"

class TestMetricsAndMonitoring(BaseCollectorTestCase):
    """Test metrics and monitoring functionality"""
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_status_endpoint(self, client, mock_database):
        """Test detailed status endpoint"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = ("8.0.0",)  # MySQL version
        
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "service_info" in data
        assert "database_status" in data
        assert "collection_status" in data
        assert "metrics" in data
        assert "configuration" in data
    
    def test_performance_endpoint(self, client):
        """Test performance metrics endpoint"""
        response = client.get("/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_collection_time" in data
        assert "success_rate" in data
        assert "memory_usage_mb" in data
        assert "cpu_usage_percent" in data

class TestCollectorSpecificTests:
    """Base class for collector-specific tests"""
    
    @pytest.fixture
    def collector_class(self):
        """Override in subclasses to specify collector class"""
        raise NotImplementedError("Must specify collector_class fixture")
    
    @pytest.fixture
    def collector_config(self):
        """Override in subclasses to provide specific configuration"""
        raise NotImplementedError("Must specify collector_config fixture")
    
    @pytest.fixture
    def collector_instance(self, collector_class, collector_config):
        """Create collector instance"""
        return collector_class(collector_config)

# Integration test utilities
class IntegrationTestCase:
    """Base class for integration tests"""
    
    @pytest.fixture(scope="session")
    def test_database(self):
        """Setup test database"""
        # This would setup a test MySQL instance
        # For now, mock it
        pass
    
    @pytest.fixture
    def real_database_config(self):
        """Real database configuration for integration tests"""
        return CollectorConfig(
            service_name="integration-test",
            mysql_host=os.getenv("TEST_MYSQL_HOST", "localhost"),
            mysql_port=int(os.getenv("TEST_MYSQL_PORT", "3306")),
            mysql_user=os.getenv("TEST_MYSQL_USER", "test"),
            mysql_password=os.getenv("TEST_MYSQL_PASSWORD", "test"),
            mysql_database=os.getenv("TEST_MYSQL_DATABASE", "test_crypto"),
        )

# Performance test utilities
class PerformanceTestCase:
    """Base class for performance tests"""
    
    @pytest.mark.benchmark(group="collection")
    def test_collection_performance(self, benchmark, mock_collector):
        """Benchmark collection performance"""
        async def run_collection():
            return await mock_collector.collect_data()
        
        # Run benchmark
        result = benchmark(asyncio.run, run_collection())
        assert result > 0
    
    @pytest.mark.load
    async def test_concurrent_collections(self, mock_collector):
        """Test concurrent collection handling"""
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(mock_collector.collect_data())
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all completed successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 10

# Test configuration utilities
def create_test_config(**overrides) -> CollectorConfig:
    """Create test configuration with overrides"""
    defaults = {
        'service_name': 'test-collector',
        'service_version': '1.0.0-test',
        'mysql_host': 'localhost',
        'mysql_port': 3306,
        'mysql_user': 'test',
        'mysql_password': 'test',
        'mysql_database': 'test_db',
        'collection_interval': 60,
        'enable_rate_limiting': True,
        'enable_circuit_breaker': True,
        'enable_data_validation': True,
        'enable_alerting': False,  # Disable by default in tests
        'enable_performance_monitoring': True
    }
    
    config_dict = {**defaults, **overrides}
    return CollectorConfig(**config_dict)

# Test data factories
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_health_response(**kwargs) -> Dict[str, Any]:
        """Create test health response"""
        defaults = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "test-collector",
            "version": "1.0.0-test",
            "uptime_seconds": 3600.0,
            "database_connected": True,
            "last_collection": None,
            "last_successful_collection": None,
            "collection_errors": 0
        }
        return {**defaults, **kwargs}
    
    @staticmethod
    def create_backfill_request(**kwargs) -> Dict[str, Any]:
        """Create test backfill request"""
        defaults = {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-02T00:00:00Z",
            "symbols": ["BTC", "ETH"],
            "force": False
        }
        return {**defaults, **kwargs}
    
    @staticmethod
    def create_alert_request(**kwargs) -> Dict[str, Any]:
        """Create test alert request"""
        defaults = {
            "alert_type": "test_alert",
            "severity": "warning",
            "message": "Test alert message", 
            "service": "test-collector",
            "additional_data": None
        }
        return {**defaults, **kwargs}

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])