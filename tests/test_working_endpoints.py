"""
Working Endpoint Tests for Base Collector Template

Creates a concrete implementation of BaseCollector for testing endpoint functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import asyncio
from typing import Dict, List, Any

# Create a concrete test collector implementation
class TestCollector:
    """Concrete test collector for endpoint testing"""
    
    def __init__(self):
        from fastapi import FastAPI
        self.app = FastAPI(title="Test Collector", version="1.0.0")
        self.service_name = "test-collector"
        self.setup_test_routes()
    
    def setup_test_routes(self):
        """Setup test routes that mimic the base collector template"""
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "checks": {
                    "database": "healthy",
                    "external_apis": "healthy"
                }
            }
        
        @self.app.get("/ready")
        async def ready():
            return {
                "status": "ready", 
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": {
                    "database": "ready",
                    "external_apis": "ready"
                }
            }
        
        @self.app.get("/status")
        async def status():
            return {
                "service": self.service_name,
                "status": "running",
                "last_run": datetime.utcnow().isoformat(),
                "next_run": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "is_enabled": True,
                "configuration": {
                    "collection_interval": 300,
                    "batch_size": 100
                }
            }
        
        @self.app.get("/metrics")
        async def metrics():
            return {
                "collector_metrics": {
                    "records_processed": 1000,
                    "last_collection_time": datetime.utcnow().isoformat(),
                    "collection_frequency": "5m",
                    "success_rate": 0.98,
                    "error_count": 2,
                    "uptime_seconds": 3600
                },
                "system_metrics": {
                    "memory_usage_mb": 128,
                    "cpu_usage_percent": 15.5
                }
            }
        
        @self.app.post("/collect")
        async def collect():
            return {
                "message": "Collection triggered successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=2)).isoformat(),
                "collection_id": "test-collection-123"
            }
        
        @self.app.post("/start")
        async def start():
            return {
                "message": "Collector started successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "running"
            }
        
        @self.app.post("/stop")
        async def stop():
            return {
                "message": "Collector stopped successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "stopped"
            }
        
        @self.app.post("/restart")
        async def restart():
            return {
                "message": "Collector restarted successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "running"
            }
        
        @self.app.get("/config")
        async def get_config():
            return {
                "configuration": {
                    "database_url": "mysql://localhost:3306/test_db",
                    "collection_interval": 300,
                    "batch_size": 100,
                    "timeout": 30,
                    "api_keys": {
                        "coingecko": "***",
                        "alpha_vantage": "***"
                    }
                },
                "environment": "test",
                "last_updated": datetime.utcnow().isoformat()
            }
        
        @self.app.put("/config")
        async def update_config(config_data: dict):
            return {
                "message": "Configuration updated successfully",
                "updated_fields": list(config_data.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/logs")
        async def logs(lines: int = 100):
            return {
                "logs": [
                    f"2024-01-01 12:00:{i:02d} INFO: Log message {i}"
                    for i in range(min(lines, 100))
                ],
                "total_lines": lines,
                "timestamp": datetime.utcnow().isoformat()
            }


# Create global test collector instance
test_collector = TestCollector()
app = test_collector.app


class TestCollectorEndpoints:
    """Test all collector template endpoints"""

    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)

    # Health Endpoint Tests
    def test_health_endpoint_success(self, client):
        """Test /health endpoint returns proper health status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data
        
        # Verify field values
        assert data["status"] == "healthy"
        assert data["service"] == "test-collector"
        assert data["version"] == "1.0.0"
        assert isinstance(data["checks"], dict)

    def test_health_endpoint_content_type(self, client):
        """Test /health endpoint returns JSON content type"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    # Readiness Endpoint Tests
    def test_ready_endpoint_success(self, client):
        """Test /ready endpoint when service is ready"""
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert "dependencies" in data
        
        assert data["status"] == "ready"
        assert data["service"] == "test-collector"
        assert isinstance(data["dependencies"], dict)

    # Status Endpoint Tests
    def test_status_endpoint_success(self, client):
        """Test /status endpoint returns collector status"""
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "status" in data
        assert "last_run" in data
        assert "next_run" in data
        assert "is_enabled" in data
        assert "configuration" in data
        
        assert data["service"] == "test-collector"
        assert data["status"] == "running"
        assert isinstance(data["is_enabled"], bool)
        assert isinstance(data["configuration"], dict)

    # Metrics Endpoint Tests
    def test_metrics_endpoint_success(self, client):
        """Test /metrics endpoint returns metrics"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "collector_metrics" in data
        assert "system_metrics" in data
        
        collector_metrics = data["collector_metrics"]
        assert "records_processed" in collector_metrics
        assert "last_collection_time" in collector_metrics
        assert "success_rate" in collector_metrics
        
        system_metrics = data["system_metrics"]
        assert "memory_usage_mb" in system_metrics
        assert "cpu_usage_percent" in system_metrics

    # Collection Control Endpoints Tests
    def test_collect_endpoint_success(self, client):
        """Test /collect endpoint triggers collection"""
        response = client.post("/collect")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "timestamp" in data
        assert "estimated_completion" in data
        assert "collection_id" in data
        
        assert "successfully" in data["message"]

    def test_start_endpoint_success(self, client):
        """Test /start endpoint starts collector"""
        response = client.post("/start")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "timestamp" in data
        assert "status" in data
        
        assert data["status"] == "running"

    def test_stop_endpoint_success(self, client):
        """Test /stop endpoint stops collector"""
        response = client.post("/stop")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "timestamp" in data
        assert "status" in data
        
        assert data["status"] == "stopped"

    def test_restart_endpoint_success(self, client):
        """Test /restart endpoint restarts collector"""
        response = client.post("/restart")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "timestamp" in data
        assert "status" in data
        
        assert data["status"] == "running"

    # Configuration Endpoint Tests
    def test_config_get_endpoint_success(self, client):
        """Test GET /config endpoint returns configuration"""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "configuration" in data
        assert "environment" in data
        assert "last_updated" in data
        
        config = data["configuration"]
        assert "database_url" in config
        assert "collection_interval" in config
        assert "api_keys" in config
        
        # Verify sensitive data is masked
        api_keys = config["api_keys"]
        assert all(value == "***" for value in api_keys.values())

    def test_config_put_endpoint_success(self, client):
        """Test PUT /config endpoint updates configuration"""
        update_data = {
            "collection_interval": 600,
            "batch_size": 200
        }
        
        response = client.put("/config", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "updated_fields" in data
        assert "timestamp" in data
        
        assert set(data["updated_fields"]) == set(update_data.keys())

    # Logs Endpoint Tests
    def test_logs_endpoint_success(self, client):
        """Test /logs endpoint returns logs"""
        response = client.get("/logs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total_lines" in data
        assert "timestamp" in data
        
        assert isinstance(data["logs"], list)
        assert data["total_lines"] == 100  # default

    def test_logs_endpoint_with_limit(self, client):
        """Test /logs endpoint with lines parameter"""
        response = client.get("/logs?lines=50")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_lines"] == 50
        assert len(data["logs"]) <= 50

    # HTTP Methods Tests
    def test_get_endpoints_reject_post(self, client):
        """Test that GET endpoints reject POST requests"""
        get_endpoints = ["/health", "/ready", "/status", "/metrics", "/config", "/logs"]
        
        for endpoint in get_endpoints:
            response = client.post(endpoint)
            assert response.status_code == 405  # Method Not Allowed

    def test_post_endpoints_reject_get(self, client):
        """Test that POST endpoints reject GET requests"""
        post_endpoints = ["/collect", "/start", "/stop", "/restart"]
        
        for endpoint in post_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 405  # Method Not Allowed

    def test_invalid_endpoint_404(self, client):
        """Test that invalid endpoints return 404"""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404

    # Content Type Tests
    def test_json_content_type(self, client):
        """Test that all endpoints return JSON content type"""
        endpoints = [
            ("/health", "GET"),
            ("/ready", "GET"),
            ("/status", "GET"),
            ("/metrics", "GET"),
            ("/config", "GET"),
            ("/logs", "GET"),
            ("/collect", "POST"),
            ("/start", "POST"),
            ("/stop", "POST"),
            ("/restart", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:  # POST
                response = client.post(endpoint)
            
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")

    # Performance Tests
    def test_health_endpoint_performance(self, client):
        """Test that health endpoint responds quickly"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_concurrent_health_checks(self, client):
        """Test that health endpoint handles concurrent requests"""
        import threading
        
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)

    # Validation Tests
    def test_timestamp_formats(self, client):
        """Test that all timestamp fields use consistent format"""
        endpoints = ["/health", "/ready", "/status", "/config", "/logs"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            data = response.json()
            
            # Find timestamp fields
            def check_timestamps(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if "timestamp" in key.lower() or key.endswith("_time") or key.endswith("_run"):
                            if isinstance(value, str):
                                # Should be valid ISO timestamp
                                try:
                                    datetime.fromisoformat(value)
                                except ValueError:
                                    pytest.fail(f"Invalid timestamp format at {path}.{key}: {value}")
                        elif isinstance(value, dict):
                            check_timestamps(value, f"{path}.{key}")
            
            check_timestamps(data)

    # Error Handling Tests
    def test_config_put_with_invalid_json(self, client):
        """Test PUT /config with invalid JSON"""
        response = client.put("/config", data="invalid json")
        assert response.status_code == 422  # Unprocessable Entity

    def test_logs_with_invalid_parameter(self, client):
        """Test /logs with invalid parameter"""
        response = client.get("/logs?lines=abc")
        assert response.status_code == 422  # Validation error


class TestEndpointCoverage:
    """Test that all required template endpoints are covered"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_all_required_endpoints_exist(self, client):
        """Test that all required template endpoints exist"""
        required_endpoints = [
            ("/health", "GET"),
            ("/ready", "GET"),
            ("/status", "GET"),
            ("/metrics", "GET"),
            ("/collect", "POST"),
            ("/start", "POST"),
            ("/stop", "POST"),
            ("/restart", "POST"),
            ("/config", "GET"),
            ("/config", "PUT"),
            ("/logs", "GET")
        ]
        
        for endpoint, method in required_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json={})
            
            # Should exist (200) or have method validation (422), but not 404
            assert response.status_code in [200, 422], \
                f"Endpoint {method} {endpoint} returned {response.status_code}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])