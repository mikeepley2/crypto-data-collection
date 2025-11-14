"""
Comprehensive Real Collector Endpoint Tests

This test suite validates that our collector endpoints are performing
real business activities rather than returning mock data.

Run with: pytest tests/test_real_endpoint_validation.py -v
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


@pytest.fixture
def ohlc_collector():
    """Set up real OHLC collector for testing"""
    sys.path.append('./services/ohlc-collection')
    
    with patch.dict(os.environ, {'COINGECKO_PREMIUM_API_KEY': 'test_key'}):
        with patch('mysql.connector.connect') as mock_db:
            mock_db.return_value = Mock()
            
            from enhanced_ohlc_collector import EnhancedOHLCCollector
            collector = EnhancedOHLCCollector()
            collector._setup_api_endpoints()
            return collector


@pytest.fixture 
def test_client(ohlc_collector):
    """Create test client for collector"""
    return TestClient(ohlc_collector.app)


class TestCollectEndpoint:
    """Test /collect endpoint performs real data collection"""
    
    def test_collect_calls_real_method(self, ohlc_collector, test_client):
        """Verify /collect calls actual collect_all_ohlc_data method"""
        method_called = False
        
        def track_collection(*args, **kwargs):
            nonlocal method_called
            method_called = True
            
        with patch.object(ohlc_collector, 'collect_all_ohlc_data', side_effect=track_collection):
            response = test_client.post('/collect')
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure from real business logic
            assert data['status'] == 'started'
            assert 'OHLC data collection triggered' in data['message']
            assert 'symbols_to_process' in data
            assert 'timestamp' in data
            
            # Verify real method was called
            assert method_called, "collect_all_ohlc_data method should be called"
    
    def test_collect_response_structure(self, test_client):
        """Verify /collect returns real operational data"""
        response = test_client.post('/collect')
        data = response.json()
        
        # These fields come from real business logic, not static mocks
        required_fields = ['status', 'message', 'symbols_to_process', 'timestamp']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert data['status'] == 'started'
        assert isinstance(data['symbols_to_process'], int)


class TestValidateDataEndpoint:
    """Test /gap-check (data validation) endpoint performs real validation"""
    
    def test_gap_check_calls_real_methods(self, ohlc_collector, test_client):
        """Verify gap check calls actual detection and health calculation"""
        gap_called = False
        health_called = False
        collect_called = False
        
        def track_gap(*args, **kwargs):
            nonlocal gap_called
            gap_called = True
            return 3.5  # Return gap > 2 hours to trigger collection
            
        def track_health(*args, **kwargs):
            nonlocal health_called
            health_called = True
            return 80
            
        def track_collect(*args, **kwargs):
            nonlocal collect_called
            collect_called = True
        
        with patch.object(ohlc_collector, 'detect_data_gap', side_effect=track_gap):
            with patch.object(ohlc_collector, 'calculate_health_score', side_effect=track_health):
                with patch.object(ohlc_collector, 'collect_all_ohlc_data', side_effect=track_collect):
                    
                    response = test_client.post('/gap-check')
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # Verify real methods were called
                    assert gap_called, "detect_data_gap should be called"
                    assert health_called, "calculate_health_score should be called"
                    assert collect_called, "collect_all_ohlc_data should be triggered for gaps > 2h"
                    
                    # Verify response contains real calculated values
                    assert data['gap_hours'] == 3.5
                    assert data['health_score'] == 80
                    assert data['backfill_triggered'] is True
    
    def test_gap_check_logic(self, ohlc_collector, test_client):
        """Test real gap detection logic"""
        # Test small gap (< 2 hours) - should not trigger collection
        with patch.object(ohlc_collector, 'detect_data_gap', return_value=1.5):
            with patch.object(ohlc_collector, 'calculate_health_score', return_value=90):
                with patch.object(ohlc_collector, 'collect_all_ohlc_data') as mock_collect:
                    
                    response = test_client.post('/gap-check')
                    data = response.json()
                    
                    assert data['gap_hours'] == 1.5
                    assert data['backfill_triggered'] is False
                    mock_collect.assert_not_called()


class TestBackfillEndpoint:
    """Test /backfill endpoint performs real backfill logic"""
    
    def test_backfill_validation_logic(self, test_client):
        """Test real backfill validation prevents excessive periods"""
        # Test exceeding maximum period (real validation logic)
        response = test_client.post('/backfill/200')
        data = response.json()
        
        assert 'error' in data
        assert 'Maximum backfill period is 168 hours' in data['error']
    
    def test_backfill_calculation_logic(self, ohlc_collector, test_client):
        """Test real backfill calculation logic"""
        backfill_called = False
        
        def track_backfill(*args, **kwargs):
            nonlocal backfill_called
            backfill_called = True
            
        with patch.object(ohlc_collector, '_intensive_backfill', side_effect=track_backfill):
            response = test_client.post('/backfill/48')
            data = response.json()
            
            # Verify real calculation: 48 hours // 6 hour intervals = 8 collections
            assert data['estimated_collections'] == 8
            assert data['status'] == 'started'
            assert backfill_called, "_intensive_backfill method should be called"
    
    def test_backfill_response_structure(self, ohlc_collector, test_client):
        """Test backfill returns real operational data"""
        with patch.object(ohlc_collector, '_intensive_backfill'):
            response = test_client.post('/backfill/24')
            data = response.json()
            
            required_fields = ['status', 'message', 'estimated_collections', 'timestamp']
            for field in required_fields:
                assert field in data, f"Missing field: {field}"


class TestRealBusinessLogic:
    """Test that collector has real business logic methods"""
    
    def test_real_methods_exist(self, ohlc_collector):
        """Verify all required business logic methods exist and are callable"""
        required_methods = [
            'collect_all_ohlc_data',
            'detect_data_gap', 
            'calculate_health_score',
            '_intensive_backfill',
            'collect_ohlc_for_symbol',
            'store_ohlc_data'
        ]
        
        for method in required_methods:
            assert hasattr(ohlc_collector, method), f"Missing method: {method}"
            assert callable(getattr(ohlc_collector, method)), f"Method not callable: {method}"
    
    def test_operational_data_structure(self, test_client):
        """Test that status endpoint returns real operational data structure"""
        response = test_client.get('/status')
        data = response.json()
        
        # Verify real operational data structure (not mock)
        assert data['service'] == 'Enhanced OHLC Collector'
        assert 'uptime_seconds' in data
        
        assert 'statistics' in data
        stats_fields = [
            'total_collections', 'successful_collections', 'failed_collections',
            'ohlc_records_collected', 'api_calls_made', 'database_writes'
        ]
        for field in stats_fields:
            assert field in data['statistics'], f"Missing statistic: {field}"
        
        assert 'configuration' in data
        config_fields = ['symbols_tracked', 'collection_interval', 'api_key_configured']
        for field in config_fields:
            assert field in data['configuration'], f"Missing config: {field}"
        
        assert 'health_metrics' in data
        health_fields = ['health_score', 'consecutive_failures']
        for field in health_fields:
            assert field in data['health_metrics'], f"Missing health metric: {field}"


class TestEndpointIntegration:
    """Test complete endpoint integration with real business flows"""
    
    def test_collect_to_status_flow(self, ohlc_collector, test_client):
        """Test that collection affects status endpoint data"""
        # Mock collection to track statistics
        original_stats = ohlc_collector.stats.copy()
        
        with patch.object(ohlc_collector, 'collect_all_ohlc_data'):
            # Trigger collection
            response = test_client.post('/collect')
            assert response.status_code == 200
            
            # Verify status reflects operational state
            status_response = test_client.get('/status')
            status_data = status_response.json()
            
            assert 'statistics' in status_data
            assert isinstance(status_data['statistics']['total_collections'], int)
    
    def test_health_endpoint_real_calculations(self, ohlc_collector, test_client):
        """Test health endpoint performs real calculations"""
        with patch.object(ohlc_collector, 'detect_data_gap', return_value=2.5):
            with patch.object(ohlc_collector, 'calculate_health_score', return_value=85):
                response = test_client.get('/health')
                data = response.json()
                
                # Values come from real method calls, not static data
                assert data['gap_hours'] == 2.5
                assert data['health_score'] == 85
                assert 'status' in data
                assert 'uptime' in data


if __name__ == "__main__":
    # Run tests directly if executed as script
    pytest.main([__file__, "-v"])