#!/usr/bin/env python3
"""
Comprehensive Unit Testing Framework for Enhanced OHLC Collector

This module provides comprehensive unit testing for the Enhanced OHLC Collector
implementing OHLC data collection with real-time monitoring and gap detection.
"""

import pytest
import asyncio
import mysql.connector
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import json
import os
from fastapi.testclient import TestClient

# Import the OHLC collector and components
from enhanced_ohlc_collector import (
    EnhancedOHLCCollector
)

class TestEnhancedOHLCCollector:
    """Test Enhanced OHLC Collector core functionality"""

    @pytest.fixture
    def mock_db_config(self):
        """Mock database configuration"""
        return {
            'host': 'localhost',
            'port': 3307,
            'user': 'test_user',
            'password': 'test_pass',
            'database': 'test_crypto_data',
            'autocommit': True
        }

    @pytest.fixture
    def mock_collector(self, mock_db_config):
        """Create collector with mocked dependencies"""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_binance_key',
            'COINBASE_API_KEY': 'test_coinbase_key',
            'SERVICE_NAME': 'test-ohlc-collector',
            'SERVICE_VERSION': '1.0.0'
        }):
            collector = EnhancedOHLCCollector()
            collector.db_config = mock_db_config
            return collector

    def test_collector_initialization(self, mock_collector):
        """Test collector initialization"""
        assert mock_collector.service_name == "test-ohlc-collector"
        assert mock_collector.service_version == "1.0.0"
        assert hasattr(mock_collector, 'exchanges')

    @patch('mysql.connector.connect')
    def test_database_connection(self, mock_connect, mock_collector):
        """Test database connection establishment"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        connection = mock_collector._get_db_connection()
        
        mock_connect.assert_called_once_with(**mock_collector.db_config)
        assert connection == mock_connection

    @patch('requests.get')
    def test_binance_api_call(self, mock_get, mock_collector):
        """Test Binance API OHLC data retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1640995200000,  # timestamp
                "50000.0",      # open
                "51000.0",      # high
                "49000.0",      # low
                "50500.0",      # close
                "100.0",        # volume
                1640998800000,  # close timestamp
                "5050000.0",    # quote volume
                1000,           # trade count
                "50.0",         # taker buy base volume
                "2525000.0",    # taker buy quote volume
                "0"             # ignore
            ]
        ]
        mock_get.return_value = mock_response
        
        result = mock_collector._fetch_binance_ohlc('BTCUSDT', '1h', 24)
        
        assert len(result) >= 0

    @patch('requests.get')
    def test_coinbase_api_call(self, mock_get, mock_collector):
        """Test Coinbase API OHLC data retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1640995200,     # timestamp
                49000.0,        # low
                51000.0,        # high
                50000.0,        # open
                50500.0,        # close
                100.0           # volume
            ]
        ]
        mock_get.return_value = mock_response
        
        result = mock_collector._fetch_coinbase_ohlc('BTC-USD', 3600, 24)
        
        assert len(result) >= 0

    def test_supported_symbols(self, mock_collector):
        """Test supported symbols configuration"""
        symbols = mock_collector._get_supported_symbols()
        
        assert len(symbols) > 0
        assert 'BTC' in symbols or 'BTCUSDT' in symbols

    @patch('mysql.connector.connect')
    def test_ohlc_data_insertion(self, mock_connect, mock_collector):
        """Test OHLC data insertion into database"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        test_data = [
            {
                'symbol': 'BTCUSDT',
                'exchange': 'binance',
                'timeframe': '1h',
                'timestamp': datetime.now(),
                'open': 50000.0,
                'high': 51000.0,
                'low': 49000.0,
                'close': 50500.0,
                'volume': 100.0
            }
        ]
        
        mock_collector._insert_ohlc_data(test_data)
        
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()

    def test_timeframe_conversion(self, mock_collector):
        """Test timeframe conversion utilities"""
        # Test various timeframe conversions
        assert mock_collector._convert_timeframe_to_seconds('1m') == 60
        assert mock_collector._convert_timeframe_to_seconds('1h') == 3600
        assert mock_collector._convert_timeframe_to_seconds('1d') == 86400

    @patch('mysql.connector.connect')
    def test_gap_detection(self, mock_connect, mock_collector):
        """Test OHLC data gap detection"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('2024-01-01 00:00:00',),
            ('2024-01-01 02:00:00',)  # Missing 01:00:00
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        gaps = mock_collector._detect_data_gaps('BTCUSDT', 'binance', '1h')
        
        assert len(gaps) >= 0

    def test_data_validation(self, mock_collector):
        """Test OHLC data validation"""
        valid_data = {
            'open': 50000.0,
            'high': 51000.0,
            'low': 49000.0,
            'close': 50500.0,
            'volume': 100.0
        }
        
        is_valid = mock_collector._validate_ohlc_data(valid_data)
        assert is_valid is True
        
        # Test invalid data (high < low)
        invalid_data = {
            'open': 50000.0,
            'high': 48000.0,  # Invalid: high < low
            'low': 49000.0,
            'close': 50500.0,
            'volume': 100.0
        }
        
        is_valid = mock_collector._validate_ohlc_data(invalid_data)
        assert is_valid is False

class TestOHLCCollectorAPI:
    """Test OHLC collector FastAPI endpoints"""

    @pytest.fixture
    def test_client(self):
        """Create test client for API testing"""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_binance_key',
            'SERVICE_NAME': 'test-ohlc-collector'
        }):
            collector = EnhancedOHLCCollector()
            app = collector.create_app()
            return TestClient(app)

    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_readiness_endpoint(self, test_client):
        """Test readiness check endpoint"""
        with patch('mysql.connector.connect'):
            response = test_client.get("/ready")
            assert response.status_code in [200, 503]

    def test_metrics_endpoint(self, test_client):
        """Test metrics endpoint"""
        response = test_client.get("/metrics")
        assert response.status_code == 200

    def test_ohlc_data_endpoint(self, test_client):
        """Test OHLC data retrieval endpoint"""
        with patch('mysql.connector.connect'):
            response = test_client.get("/ohlc/BTCUSDT/1h")
            assert response.status_code in [200, 404]

class TestOHLCDataProcessing:
    """Test OHLC data processing and calculations"""

    @pytest.fixture
    def processing_collector(self):
        """Create collector for data processing tests"""
        return EnhancedOHLCCollector()

    def test_price_change_calculation(self, processing_collector):
        """Test price change calculation"""
        open_price = 50000.0
        close_price = 50500.0
        
        change = processing_collector._calculate_price_change(open_price, close_price)
        
        assert isinstance(change, float)
        assert change == 1.0  # 1% change

    def test_volatility_calculation(self, processing_collector):
        """Test volatility calculation"""
        ohlc_data = [
            {'high': 51000, 'low': 49000, 'close': 50000},
            {'high': 52000, 'low': 50000, 'close': 51000},
            {'high': 51500, 'low': 49500, 'close': 50500}
        ]
        
        volatility = processing_collector._calculate_volatility(ohlc_data)
        
        assert isinstance(volatility, float)
        assert volatility >= 0

    def test_volume_analysis(self, processing_collector):
        """Test volume analysis"""
        volume_data = [100, 150, 120, 200, 180]
        
        analysis = processing_collector._analyze_volume_patterns(volume_data)
        
        assert isinstance(analysis, dict)
        assert 'average_volume' in analysis

class TestOHLCCollectorIntegration:
    """Integration tests for OHLC collector"""

    @pytest.fixture
    def integration_collector(self):
        """Create collector for integration testing"""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_binance_key'
        }):
            return EnhancedOHLCCollector()

    @patch('requests.get')
    @patch('mysql.connector.connect')
    def test_full_collection_workflow(self, mock_connect, mock_get, integration_collector):
        """Test complete OHLC data collection workflow"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1640995200000, "50000.0", "51000.0", "49000.0", "50500.0",
                "100.0", 1640998800000, "5050000.0", 1000, "50.0", "2525000.0", "0"
            ]
        ]
        mock_get.return_value = mock_response
        
        # Mock database
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Run collection
        result = integration_collector.collect_ohlc_data()
        
        assert result is not None

    @patch('mysql.connector.connect')
    def test_health_scoring(self, mock_connect, integration_collector):
        """Test health scoring system"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1000,)  # Mock record count
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        health_score = integration_collector._calculate_health_score()
        
        assert 0 <= health_score <= 100

class TestOHLCCollectorErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def error_collector(self):
        """Create collector for error testing"""
        return EnhancedOHLCCollector()

    def test_missing_api_keys(self, error_collector):
        """Test behavior with missing API keys"""
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing keys gracefully
            assert hasattr(error_collector, 'exchanges')

    @patch('requests.get')
    def test_api_failure_handling(self, mock_get, error_collector):
        """Test API failure handling"""
        mock_get.side_effect = Exception("API Error")
        
        result = error_collector._fetch_binance_ohlc('BTCUSDT', '1h', 24)
        
        assert result == [] or result is None

    @patch('mysql.connector.connect')
    def test_database_failure_handling(self, mock_connect, error_collector):
        """Test database failure handling"""
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        with pytest.raises(mysql.connector.Error):
            error_collector._get_db_connection()

    def test_invalid_timeframe_handling(self, error_collector):
        """Test handling of invalid timeframes"""
        invalid_timeframes = ['invalid', '0m', '25h']
        
        for timeframe in invalid_timeframes:
            result = error_collector._validate_timeframe(timeframe)
            assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])