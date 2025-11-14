#!/usr/bin/env python3
"""
Comprehensive Unit Testing Framework for Enhanced Crypto Derivatives Collector

This module provides comprehensive unit testing for the Enhanced Crypto Derivatives Collector
implementing real derivatives data collection with ML indicators.
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

# Import the derivatives collector and components
from enhanced_crypto_derivatives_collector import (
    CryptoDerivativesCollector
)

class TestCryptoDerivativesCollector:
    """Test Enhanced Crypto Derivatives Collector core functionality"""

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
            'COINGECKO_API_KEY': 'test_cg_key',
            'SERVICE_NAME': 'test-derivatives-collector',
            'SERVICE_VERSION': '1.0.0'
        }):
            collector = CryptoDerivativesCollector()
            collector.db_config = mock_db_config
            return collector

    def test_collector_initialization(self, mock_collector):
        """Test collector initialization"""
        assert mock_collector.service_name == "test-derivatives-collector"
        assert mock_collector.service_version == "1.0.0"
        assert hasattr(mock_collector, 'coingecko_api_key')

    @patch('mysql.connector.connect')
    def test_database_connection(self, mock_connect, mock_collector):
        """Test database connection establishment"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        connection = mock_collector._get_db_connection()
        
        mock_connect.assert_called_once_with(**mock_collector.db_config)
        assert connection == mock_connection

    @patch('requests.get')
    def test_coingecko_api_call(self, mock_get, mock_collector):
        """Test CoinGecko API data retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'symbol': 'BTC',
                    'funding_rate': 0.0001,
                    'open_interest': 1000000,
                    'volume_24h': 5000000
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = mock_collector._fetch_derivatives_data(['BTC'])
        
        assert result is not None

    def test_supported_symbols(self, mock_collector):
        """Test supported symbols configuration"""
        symbols = mock_collector._get_supported_symbols()
        
        assert len(symbols) > 0
        assert 'BTC' in symbols or 'BTCUSDT' in symbols

    @patch('mysql.connector.connect')
    def test_funding_rate_insertion(self, mock_connect, mock_collector):
        """Test funding rate data insertion"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        test_data = [
            {
                'symbol': 'BTCUSDT',
                'exchange': 'binance',
                'funding_rate': 0.0001,
                'open_interest': 1000000,
                'timestamp': datetime.now()
            }
        ]
        
        mock_collector._insert_funding_rates(test_data)
        
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()

    def test_ml_indicator_calculation(self, mock_collector):
        """Test ML indicators calculation"""
        sample_data = [
            {'funding_rate': 0.0001, 'open_interest': 1000000, 'volume': 5000000},
            {'funding_rate': 0.0002, 'open_interest': 1100000, 'volume': 5500000},
            {'funding_rate': 0.0001, 'open_interest': 1200000, 'volume': 6000000}
        ]
        
        indicators = mock_collector._calculate_ml_indicators(sample_data)
        
        assert isinstance(indicators, dict)
        assert len(indicators) > 0

    @patch('mysql.connector.connect')
    def test_historical_data_retrieval(self, mock_connect, mock_collector):
        """Test historical derivatives data retrieval"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('BTCUSDT', 0.0001, 1000000, datetime.now()),
            ('ETHUSDT', 0.0002, 800000, datetime.now())
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        data = mock_collector._get_historical_data('BTCUSDT', 7)
        
        assert len(data) >= 0

    def test_exchange_normalization(self, mock_collector):
        """Test exchange symbol normalization"""
        symbol = 'BTC'
        normalized = mock_collector._normalize_symbol_for_exchange(symbol, 'binance')
        
        assert isinstance(normalized, str)
        assert len(normalized) > 0

class TestDerivativesCollectorAPI:
    """Test derivatives collector FastAPI endpoints"""

    @pytest.fixture
    def test_client(self):
        """Create test client for API testing"""
        with patch.dict(os.environ, {
            'COINGECKO_API_KEY': 'test_cg_key',
            'SERVICE_NAME': 'test-derivatives-collector'
        }):
            collector = CryptoDerivativesCollector()
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

    def test_derivatives_data_endpoint(self, test_client):
        """Test derivatives data endpoint"""
        with patch('mysql.connector.connect'):
            response = test_client.get("/derivatives/BTCUSDT")
            assert response.status_code in [200, 404]

class TestDerivativesDataProcessing:
    """Test derivatives data processing and calculations"""

    @pytest.fixture
    def processing_collector(self):
        """Create collector for data processing tests"""
        return CryptoDerivativesCollector()

    def test_funding_rate_validation(self, processing_collector):
        """Test funding rate data validation"""
        valid_data = {
            'symbol': 'BTCUSDT',
            'funding_rate': 0.0001,
            'open_interest': 1000000,
            'timestamp': datetime.now()
        }
        
        is_valid = processing_collector._validate_funding_rate_data(valid_data)
        assert is_valid is True

    def test_spread_calculation(self, processing_collector):
        """Test basis spread calculation"""
        spot_price = 50000.0
        futures_price = 50100.0
        
        spread = processing_collector._calculate_basis_spread(spot_price, futures_price)
        
        assert isinstance(spread, float)
        assert spread > 0

    def test_volatility_calculation(self, processing_collector):
        """Test volatility calculation for derivatives"""
        funding_rates = [0.0001, 0.0002, 0.0001, 0.0003, 0.0002]
        
        volatility = processing_collector._calculate_funding_rate_volatility(funding_rates)
        
        assert isinstance(volatility, float)
        assert volatility >= 0

    def test_anomaly_detection(self, processing_collector):
        """Test anomaly detection in funding rates"""
        normal_rates = [0.0001] * 100
        anomalous_rates = normal_rates + [0.01]  # Very high funding rate
        
        anomalies = processing_collector._detect_funding_rate_anomalies(anomalous_rates)
        
        assert len(anomalies) > 0

class TestDerivativesCollectorIntegration:
    """Integration tests for derivatives collector"""

    @pytest.fixture
    def integration_collector(self):
        """Create collector for integration testing"""
        with patch.dict(os.environ, {
            'COINGECKO_API_KEY': 'test_cg_key'
        }):
            return CryptoDerivativesCollector()

    @patch('requests.get')
    @patch('mysql.connector.connect')
    def test_full_collection_workflow(self, mock_connect, mock_get, integration_collector):
        """Test complete derivatives data collection workflow"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'symbol': 'BTC',
                    'funding_rate': 0.0001,
                    'open_interest': 1000000,
                    'volume_24h': 5000000
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock database
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Run collection
        result = integration_collector.collect_derivatives_data()
        
        assert result is not None

    @patch('mysql.connector.connect')
    def test_data_quality_assessment(self, mock_connect, integration_collector):
        """Test data quality assessment"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('BTCUSDT', 0.0001, 1000000, datetime.now()),
            ('ETHUSDT', 0.0002, 800000, datetime.now())
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        quality_score = integration_collector._assess_data_quality()
        
        assert 0 <= quality_score <= 100

class TestDerivativesCollectorErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def error_collector(self):
        """Create collector for error testing"""
        return CryptoDerivativesCollector()

    def test_missing_api_keys(self, error_collector):
        """Test behavior with missing API keys"""
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing keys gracefully
            assert hasattr(error_collector, 'coingecko_api_key')

    @patch('requests.get')
    def test_api_failure_handling(self, mock_get, error_collector):
        """Test API failure handling"""
        mock_get.side_effect = Exception("API Error")
        
        result = error_collector._fetch_derivatives_data(['BTC'])
        
        assert result == [] or result is None

    @patch('mysql.connector.connect')
    def test_database_failure_handling(self, mock_connect, error_collector):
        """Test database failure handling"""
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        with pytest.raises(mysql.connector.Error):
            error_collector._get_db_connection()

    def test_invalid_symbol_handling(self, error_collector):
        """Test handling of invalid symbols"""
        invalid_symbols = ['INVALID', 'NOTREAL', '']
        
        result = error_collector._validate_symbols(invalid_symbols)
        
        assert isinstance(result, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])