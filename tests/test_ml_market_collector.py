#!/usr/bin/env python3
"""
Comprehensive Unit Testing Framework for ML Market Collector

This module provides comprehensive unit testing for the ML Market Collector
implementing traditional market data collection for crypto ML trading.
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

# Import the ML market collector and components
from ml_market_collector import (
    MLMarketDataCollector
)

class TestMLMarketCollector:
    """Test ML Market Collector core functionality"""

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
            'ALPHA_VANTAGE_API_KEY': 'test_av_key',
            'YF_API_KEY': 'test_yf_key',
            'SERVICE_NAME': 'test-ml-market-collector',
            'SERVICE_VERSION': '1.0.0'
        }):
            collector = MLMarketDataCollector()
            collector.db_config = mock_db_config
            return collector

    def test_collector_initialization(self, mock_collector):
        """Test collector initialization"""
        assert mock_collector.service_name == "test-ml-market-collector"
        assert mock_collector.service_version == "1.0.0"
        assert hasattr(mock_collector, 'traditional_markets')

    @patch('mysql.connector.connect')
    def test_database_connection(self, mock_connect, mock_collector):
        """Test database connection establishment"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        connection = mock_collector._get_db_connection()
        
        mock_connect.assert_called_once_with(**mock_collector.db_config)
        assert connection == mock_connection

    @patch('yfinance.download')
    def test_yfinance_data_retrieval(self, mock_download, mock_collector):
        """Test Yahoo Finance data retrieval"""
        mock_data = Mock()
        mock_data.reset_index.return_value.to_dict.return_value = {
            'Date': {0: datetime(2024, 1, 1)},
            'Open': {0: 100.0},
            'High': {0: 105.0},
            'Low': {0: 95.0},
            'Close': {0: 102.0},
            'Volume': {0: 1000000}
        }
        mock_download.return_value = mock_data
        
        result = mock_collector._fetch_yahoo_finance_data(['SPY'], '1d', 30)
        
        assert result is not None

    @patch('requests.get')
    def test_alpha_vantage_api_call(self, mock_get, mock_collector):
        """Test Alpha Vantage API data retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Time Series (Daily)': {
                '2024-01-01': {
                    '1. open': '100.0',
                    '2. high': '105.0',
                    '3. low': '95.0',
                    '4. close': '102.0',
                    '5. volume': '1000000'
                }
            }
        }
        mock_get.return_value = mock_response
        
        result = mock_collector._fetch_alpha_vantage_data('SPY')
        
        assert result is not None

    def test_supported_symbols(self, mock_collector):
        """Test supported traditional market symbols"""
        symbols = mock_collector._get_traditional_market_symbols()
        
        assert len(symbols) > 0
        assert 'SPY' in symbols or 'QQQ' in symbols

    @patch('mysql.connector.connect')
    def test_market_data_insertion(self, mock_connect, mock_collector):
        """Test traditional market data insertion"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        test_data = [
            {
                'symbol': 'SPY',
                'date': datetime(2024, 1, 1),
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 1000000,
                'source': 'yahoo_finance'
            }
        ]
        
        mock_collector._insert_market_data(test_data)
        
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()

    def test_correlation_calculation(self, mock_collector):
        """Test correlation calculation between traditional and crypto markets"""
        traditional_data = [100, 102, 101, 105, 103]
        crypto_data = [50000, 51000, 50500, 52500, 51500]
        
        correlation = mock_collector._calculate_correlation(traditional_data, crypto_data)
        
        assert isinstance(correlation, float)
        assert -1 <= correlation <= 1

    @patch('mysql.connector.connect')
    def test_ml_feature_extraction(self, mock_connect, mock_collector):
        """Test ML feature extraction from market data"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('SPY', datetime(2024, 1, 1), 100.0, 105.0, 95.0, 102.0, 1000000),
            ('SPY', datetime(2024, 1, 2), 102.0, 106.0, 100.0, 104.0, 1100000)
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        features = mock_collector._extract_ml_features('SPY', 30)
        
        assert isinstance(features, dict)
        assert len(features) > 0

class TestMLMarketCollectorAPI:
    """Test ML market collector FastAPI endpoints"""

    @pytest.fixture
    def test_client(self):
        """Create test client for API testing"""
        with patch.dict(os.environ, {
            'ALPHA_VANTAGE_API_KEY': 'test_av_key',
            'SERVICE_NAME': 'test-ml-market-collector'
        }):
            collector = MLMarketDataCollector()
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

    def test_correlations_endpoint(self, test_client):
        """Test correlations data endpoint"""
        with patch('mysql.connector.connect'):
            response = test_client.get("/correlations")
            assert response.status_code in [200, 404]

class TestMLFeatureEngineering:
    """Test ML feature engineering capabilities"""

    @pytest.fixture
    def feature_collector(self):
        """Create collector for feature engineering tests"""
        return MLMarketDataCollector()

    def test_technical_indicators_calculation(self, feature_collector):
        """Test technical indicators calculation"""
        price_data = [100, 102, 101, 105, 103, 107, 106, 110, 108, 112]
        
        indicators = feature_collector._calculate_technical_indicators(price_data)
        
        assert isinstance(indicators, dict)
        assert 'sma' in indicators
        assert 'rsi' in indicators

    def test_volatility_features(self, feature_collector):
        """Test volatility feature calculation"""
        price_data = [100, 102, 98, 105, 95, 107, 92, 110, 88, 112]
        
        volatility_features = feature_collector._calculate_volatility_features(price_data)
        
        assert isinstance(volatility_features, dict)
        assert 'historical_volatility' in volatility_features

    def test_momentum_features(self, feature_collector):
        """Test momentum feature calculation"""
        price_data = [100, 102, 101, 105, 103, 107, 106, 110, 108, 112]
        
        momentum_features = feature_collector._calculate_momentum_features(price_data)
        
        assert isinstance(momentum_features, dict)
        assert 'roc' in momentum_features  # Rate of change

    def test_market_regime_detection(self, feature_collector):
        """Test market regime detection"""
        price_data = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]  # Trending up
        
        regime = feature_collector._detect_market_regime(price_data)
        
        assert isinstance(regime, str)
        assert regime in ['trending', 'sideways', 'volatile']

class TestMLMarketCollectorIntegration:
    """Integration tests for ML market collector"""

    @pytest.fixture
    def integration_collector(self):
        """Create collector for integration testing"""
        with patch.dict(os.environ, {
            'ALPHA_VANTAGE_API_KEY': 'test_av_key'
        }):
            return MLMarketDataCollector()

    @patch('yfinance.download')
    @patch('mysql.connector.connect')
    def test_full_collection_workflow(self, mock_connect, mock_download, integration_collector):
        """Test complete market data collection workflow"""
        # Mock Yahoo Finance data
        mock_data = Mock()
        mock_data.reset_index.return_value.to_dict.return_value = {
            'Date': {0: datetime(2024, 1, 1)},
            'Open': {0: 100.0},
            'High': {0: 105.0},
            'Low': {0: 95.0},
            'Close': {0: 102.0},
            'Volume': {0: 1000000}
        }
        mock_download.return_value = mock_data
        
        # Mock database
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Run collection
        result = integration_collector.collect_market_data()
        
        assert result is not None

    @patch('mysql.connector.connect')
    def test_correlation_analysis_pipeline(self, mock_connect, integration_collector):
        """Test correlation analysis pipeline"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('SPY', 100.0, 102.0),
            ('QQQ', 300.0, 305.0),
            ('BTC', 50000.0, 51000.0)
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        correlations = integration_collector._calculate_market_correlations()
        
        assert isinstance(correlations, dict)

class TestMLMarketCollectorErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def error_collector(self):
        """Create collector for error testing"""
        return MLMarketDataCollector()

    def test_missing_api_keys(self, error_collector):
        """Test behavior with missing API keys"""
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing keys gracefully
            assert hasattr(error_collector, 'traditional_markets')

    @patch('yfinance.download')
    def test_yahoo_finance_failure_handling(self, mock_download, error_collector):
        """Test Yahoo Finance API failure handling"""
        mock_download.side_effect = Exception("Yahoo Finance Error")
        
        result = error_collector._fetch_yahoo_finance_data(['SPY'], '1d', 30)
        
        assert result == [] or result is None

    @patch('requests.get')
    def test_alpha_vantage_failure_handling(self, mock_get, error_collector):
        """Test Alpha Vantage API failure handling"""
        mock_get.side_effect = Exception("Alpha Vantage Error")
        
        result = error_collector._fetch_alpha_vantage_data('SPY')
        
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

    def test_data_quality_validation(self, error_collector):
        """Test data quality validation"""
        # Test with invalid data (negative prices)
        invalid_data = {
            'open': -100.0,  # Invalid negative price
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000000
        }
        
        is_valid = error_collector._validate_market_data(invalid_data)
        assert is_valid is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])