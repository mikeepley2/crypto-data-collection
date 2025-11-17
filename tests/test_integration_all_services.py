"""
Integration Tests for All API Services

Comprehensive integration tests for all FastAPI services to ensure
complete endpoint coverage and real system interactions.
"""

import pytest
import httpx
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time


class TestAPIServiceIntegration:
    """Integration tests for all API service endpoints"""
    
    # Service configurations - update these URLs based on your deployment
    SERVICES = {
        "api_gateway": "http://localhost:8000",
        "price_collector": "http://localhost:8001", 
        "news_collector": "http://localhost:8002",
        "sentiment_collector": "http://localhost:8003",
        "technical_collector": "http://localhost:8004",
        "macro_collector": "http://localhost:8005"
    }
    
    API_KEY = "master-key"  # Update with actual test API key
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for API requests"""
        return {"Authorization": f"Bearer {self.API_KEY}"}
    
    @pytest.fixture
    async def http_client(self):
        """Async HTTP client for testing"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    # Service Health and Readiness Tests
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_services_health_endpoints(self, http_client):
        """Test health endpoints for all services"""
        results = {}
        
        for service_name, base_url in self.SERVICES.items():
            try:
                response = await http_client.get(f"{base_url}/health")
                results[service_name] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "healthy": response.status_code == 200
                }
                
                if response.status_code == 200:
                    data = response.json()
                    assert "status" in data
                    assert "timestamp" in data
                    
            except httpx.ConnectError:
                results[service_name] = {
                    "status_code": None,
                    "response_time": None,
                    "healthy": False,
                    "error": "Service not available"
                }
        
        # Log results for debugging
        print("\nHealth Check Results:")
        for service, result in results.items():
            print(f"{service}: {result}")
        
        # At least API gateway should be healthy for tests
        assert results.get("api_gateway", {}).get("healthy", False), \
            "API Gateway must be healthy for integration tests"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_services_ready_endpoints(self, http_client):
        """Test readiness endpoints for all services"""
        results = {}
        
        for service_name, base_url in self.SERVICES.items():
            try:
                response = await http_client.get(f"{base_url}/ready")
                results[service_name] = {
                    "status_code": response.status_code,
                    "ready": response.status_code == 200
                }
                
            except httpx.ConnectError:
                results[service_name] = {
                    "status_code": None,
                    "ready": False,
                    "error": "Service not available"
                }
        
        print("\nReadiness Check Results:")
        for service, result in results.items():
            print(f"{service}: {result}")
    
    # API Gateway Endpoint Tests
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_current_price(self, http_client, auth_headers):
        """Test API Gateway current price endpoint"""
        base_url = self.SERVICES["api_gateway"]
        
        # Test with common crypto symbols
        symbols = ["BTC", "ETH", "ADA", "SOL"]
        
        for symbol in symbols:
            response = await http_client.get(
                f"{base_url}/api/v1/prices/current/{symbol}",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["symbol"] == symbol
                assert "current_price" in data
                assert "timestamp" in data
                assert isinstance(data["current_price"], (int, float))
                assert data["current_price"] > 0
                
                # Verify timestamp is recent (within last hour)
                timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                assert (datetime.utcnow().replace(tzinfo=timestamp.tzinfo) - timestamp).total_seconds() < 3600
                
            elif response.status_code == 404:
                # Acceptable if symbol doesn't exist in database
                print(f"No data found for symbol: {symbol}")
            else:
                pytest.fail(f"Unexpected status code {response.status_code} for symbol {symbol}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_historical_prices(self, http_client, auth_headers):
        """Test API Gateway historical prices endpoint"""
        base_url = self.SERVICES["api_gateway"]
        
        # Test with date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        start_str = start_date.isoformat() + "Z"
        end_str = end_date.isoformat() + "Z"
        
        response = await http_client.get(
            f"{base_url}/api/v1/prices/historical/BTC?start={start_str}&end={end_str}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            for price_point in data[:5]:  # Check first 5 records
                assert "timestamp" in price_point
                assert "current_price" in price_point
                assert isinstance(price_point["current_price"], (int, float))
        
        elif response.status_code == 404:
            print("No historical price data found")
        else:
            assert False, f"Unexpected status code: {response.status_code}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_sentiment(self, http_client, auth_headers):
        """Test API Gateway sentiment endpoints"""
        base_url = self.SERVICES["api_gateway"]
        
        # Test crypto sentiment
        response = await http_client.get(
            f"{base_url}/api/v1/sentiment/crypto/BTC",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            for sentiment in data[:3]:  # Check first 3 records
                assert "sentiment_score" in sentiment
                assert "sentiment_label" in sentiment
                assert "timestamp" in sentiment
                assert -1 <= sentiment["sentiment_score"] <= 1
                assert sentiment["sentiment_label"] in ["positive", "negative", "neutral"]
        
        # Test stock sentiment
        response = await http_client.get(
            f"{base_url}/api/v1/sentiment/stock/TSLA",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]  # 404 acceptable if no data
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_news(self, http_client, auth_headers):
        """Test API Gateway news endpoints"""
        base_url = self.SERVICES["api_gateway"]
        
        response = await http_client.get(
            f"{base_url}/api/v1/news/crypto/latest",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            for article in data[:3]:  # Check first 3 articles
                assert "title" in article
                assert "content" in article
                assert "source" in article
                assert "published_at" in article
                assert "url" in article
                
                # Verify URL format
                assert article["url"].startswith(("http://", "https://"))
                
                # Verify timestamp format
                datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
        
        elif response.status_code == 404:
            print("No news data found")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_technical_indicators(self, http_client, auth_headers):
        """Test API Gateway technical indicators endpoint"""
        base_url = self.SERVICES["api_gateway"]
        
        response = await http_client.get(
            f"{base_url}/api/v1/technical/BTC/indicators",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == "BTC"
            assert "timestamp" in data
            
            # Check for common technical indicators
            indicator_fields = ["rsi", "macd", "bb_upper", "bb_lower", "sma_20", "sma_50"]
            for field in indicator_fields:
                if field in data:
                    assert isinstance(data[field], (int, float))
        
        elif response.status_code == 404:
            print("No technical indicator data found for BTC")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_ml_features(self, http_client, auth_headers):
        """Test API Gateway ML features endpoints"""
        base_url = self.SERVICES["api_gateway"]
        
        # Test current ML features
        response = await http_client.get(
            f"{base_url}/api/v1/ml-features/BTC/current",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == "BTC"
            assert "features" in data
            assert "timestamp" in data
            assert isinstance(data["features"], dict)
        
        # Test bulk ML features
        response = await http_client.get(
            f"{base_url}/api/v1/ml-features/bulk?symbols=BTC,ETH",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_stats(self, http_client, auth_headers):
        """Test API Gateway stats endpoint"""
        base_url = self.SERVICES["api_gateway"]
        
        response = await http_client.get(
            f"{base_url}/api/v1/stats/collectors",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should contain stats for different data types
            expected_keys = ["price_data", "news_data", "sentiment_analysis"]
            for key in expected_keys:
                if key in data:
                    assert isinstance(data[key], dict)
    
    # Collector Service Integration Tests
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_collector_services_status(self, http_client):
        """Test status endpoints for all collector services"""
        collector_services = [
            "price_collector", "news_collector", "sentiment_collector",
            "technical_collector", "macro_collector"
        ]
        
        for service_name in collector_services:
            if service_name not in self.SERVICES:
                continue
                
            base_url = self.SERVICES[service_name]
            
            try:
                response = await http_client.get(f"{base_url}/status")
                
                if response.status_code == 200:
                    data = response.json()
                    assert "collector_name" in data
                    assert "status" in data
                    assert "last_run" in data
                    assert "is_enabled" in data
                    
            except httpx.ConnectError:
                print(f"Service {service_name} not available")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_collector_services_metrics(self, http_client):
        """Test metrics endpoints for all collector services"""
        collector_services = [
            "price_collector", "news_collector", "sentiment_collector",
            "technical_collector", "macro_collector"
        ]
        
        for service_name in collector_services:
            if service_name not in self.SERVICES:
                continue
                
            base_url = self.SERVICES[service_name]
            
            try:
                response = await http_client.get(f"{base_url}/metrics")
                
                if response.status_code == 200:
                    data = response.json()
                    assert "collector_metrics" in data
                    
                    metrics = data["collector_metrics"]
                    assert "records_processed" in metrics
                    assert "last_collection_time" in metrics
                    assert isinstance(metrics["records_processed"], int)
                    
            except httpx.ConnectError:
                print(f"Service {service_name} not available")
    
    # Authentication and Authorization Tests
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_authentication(self, http_client):
        """Test API Gateway authentication requirements"""
        base_url = self.SERVICES["api_gateway"]
        
        # Test without auth header
        response = await http_client.get(f"{base_url}/api/v1/prices/current/BTC")
        assert response.status_code == 401
        
        # Test with invalid auth header
        invalid_headers = {"Authorization": "Bearer invalid-key"}
        response = await http_client.get(
            f"{base_url}/api/v1/prices/current/BTC",
            headers=invalid_headers
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_collector_control_endpoints(self, http_client):
        """Test collector control endpoints (start/stop/restart)"""
        collector_services = ["price_collector", "news_collector"]
        
        for service_name in collector_services:
            if service_name not in self.SERVICES:
                continue
                
            base_url = self.SERVICES[service_name]
            
            try:
                # Test collect endpoint
                response = await http_client.post(f"{base_url}/collect")
                
                if response.status_code == 200:
                    data = response.json()
                    assert "message" in data
                    assert "timestamp" in data
                    
            except httpx.ConnectError:
                print(f"Service {service_name} not available for control testing")
    
    # Error Handling Integration Tests
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_error_handling(self, http_client, auth_headers):
        """Test API Gateway error handling"""
        base_url = self.SERVICES["api_gateway"]
        
        # Test with invalid symbol
        response = await http_client.get(
            f"{base_url}/api/v1/prices/current/INVALID_SYMBOL_12345",
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Test with invalid date format
        response = await http_client.get(
            f"{base_url}/api/v1/prices/historical/BTC?start=invalid&end=invalid",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test with invalid limit parameter
        response = await http_client.get(
            f"{base_url}/api/v1/news/crypto/latest?limit=999",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    # Performance Integration Tests
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_gateway_performance(self, http_client, auth_headers):
        """Test API Gateway response times"""
        base_url = self.SERVICES["api_gateway"]
        
        endpoints = [
            "/health",
            "/ready",
            "/api/v1/prices/current/BTC",
            "/api/v1/sentiment/crypto/BTC",
            "/api/v1/news/crypto/latest?limit=10"
        ]
        
        for endpoint in endpoints:
            headers = auth_headers if endpoint.startswith("/api/") else {}
            
            start_time = time.time()
            response = await http_client.get(f"{base_url}{endpoint}", headers=headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # All endpoints should respond within 5 seconds
            assert response_time < 5.0, f"Endpoint {endpoint} took {response_time:.2f}s"
            
            if response.status_code not in [200, 404]:
                print(f"Endpoint {endpoint} returned status {response.status_code}")
    
    # Data Consistency Integration Tests
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_data_consistency_across_endpoints(self, http_client, auth_headers):
        """Test data consistency across related endpoints"""
        base_url = self.SERVICES["api_gateway"]
        
        # Get current price
        price_response = await http_client.get(
            f"{base_url}/api/v1/prices/current/BTC",
            headers=auth_headers
        )
        
        if price_response.status_code == 200:
            price_data = price_response.json()
            price_timestamp = datetime.fromisoformat(price_data["timestamp"].replace("Z", "+00:00"))
            
            # Get technical indicators
            tech_response = await http_client.get(
                f"{base_url}/api/v1/technical/BTC/indicators",
                headers=auth_headers
            )
            
            if tech_response.status_code == 200:
                tech_data = tech_response.json()
                tech_timestamp = datetime.fromisoformat(tech_data["timestamp"].replace("Z", "+00:00"))
                
                # Timestamps should be reasonably close (within 1 hour)
                time_diff = abs((price_timestamp - tech_timestamp).total_seconds())
                assert time_diff < 3600, "Price and technical indicator timestamps too far apart"


class TestWebSocketIntegration:
    """Integration tests for WebSocket endpoints"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_price_stream(self):
        """Test WebSocket price streaming endpoint"""
        try:
            import websockets
            
            uri = "ws://localhost:8000/ws/prices"
            
            async with websockets.connect(uri) as websocket:
                # Send subscription message
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "symbols": ["BTC", "ETH"]
                }))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                
                assert "type" in data
                # Could be subscription confirmation or price data
                
        except ImportError:
            pytest.skip("websockets library not available")
        except (ConnectionRefusedError, OSError):
            pytest.skip("WebSocket server not available")


# Test Configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Custom markers for test organization
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration", "--tb=short"])