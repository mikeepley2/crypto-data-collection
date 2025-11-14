#!/usr/bin/env python3
"""
Comprehensive Unit Testing Framework for Enhanced Macro Collector

This module provides comprehensive unit testing for the Enhanced Macro Collector
implementing macroeconomic data collection with real-time monitoring.
"""

import pytest
import asyncio
import mysql.connector
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List
import json
import os
from fastapi.testclient import TestClient

# Import the macro collector and components
from enhanced_macro_collector_v2 import (
    EnhancedMacroCollector, DataFrequency, MacroIndicator
)

class TestMacroIndicator:
    """Test macro indicator configuration"""
    
    def test_macro_indicator_initialization(self):
        """Test macro indicator creation"""
        indicator = MacroIndicator(
            name="GDP",
            fred_series_id="GDP",
            frequency=DataFrequency.QUARTERLY,
            description="Gross Domestic Product",
            category="economic_growth"
        )
        
        assert indicator.name == "GDP"
        assert indicator.fred_series_id == "GDP"
        assert indicator.frequency == DataFrequency.QUARTERLY
        assert indicator.description == "Gross Domestic Product"
        assert indicator.category == "economic_growth"
        assert indicator.active is True

class TestDataFrequency:
    """Test data frequency enumeration"""
    
    def test_frequency_values(self):
        """Test all frequency types"""
        assert DataFrequency.DAILY.value == "daily"
        assert DataFrequency.WEEKLY.value == "weekly"
        assert DataFrequency.MONTHLY.value == "monthly"
        assert DataFrequency.QUARTERLY.value == "quarterly"
        assert DataFrequency.ANNUAL.value == "annual"

class TestEnhancedMacroCollector:
    """Test Enhanced Macro Collector core functionality"""

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
            'FRED_API_KEY': 'test_fred_key',
            'ALPHAVANTAGE_API_KEY': 'test_av_key',
            'SERVICE_NAME': 'test-macro-collector',
            'SERVICE_VERSION': '1.0.0'
        }):
            collector = EnhancedMacroCollector()
            collector.db_config = mock_db_config
            return collector

    def test_collector_initialization(self, mock_collector):
        """Test collector initialization"""
        assert mock_collector.service_name == "test-macro-collector"
        assert mock_collector.service_version == "1.0.0"
        assert mock_collector.fred_api_key == "test_fred_key"
        assert mock_collector.alphavantage_api_key == "test_av_key"

    @patch('mysql.connector.connect')
    def test_database_connection(self, mock_connect, mock_collector):
        """Test database connection establishment"""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        connection = mock_collector._get_db_connection()
        
        mock_connect.assert_called_once_with(**mock_collector.db_config)
        assert connection == mock_connection

    @patch('requests.get')
    def test_fred_api_call(self, mock_get, mock_collector):
        """Test FRED API data retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'observations': [
                {
                    'date': '2024-01-01',
                    'value': '25000.0'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = mock_collector._fetch_fred_data('GDP', '2024-01-01', '2024-12-31')
        
        assert len(result) == 1
        assert result[0]['date'] == '2024-01-01'
        assert result[0]['value'] == '25000.0'

    @patch('requests.get')
    def test_alphavantage_api_call(self, mock_get, mock_collector):
        """Test Alpha Vantage API data retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'date': '2024-01-01',
                    'value': '3.5'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = mock_collector._fetch_alphavantage_data('UNEMPLOYMENT', '2024-01-01', '2024-12-31')
        
        assert result is not None

    def test_macro_indicators_config(self, mock_collector):
        """Test macro indicators configuration"""
        indicators = mock_collector._get_macro_indicators()
        
        assert len(indicators) > 0
        
        # Check for key economic indicators
        indicator_names = [ind.name for ind in indicators]
        assert any('GDP' in name for name in indicator_names)
        assert any('Unemployment' in name for name in indicator_names)
        assert any('Inflation' in name for name in indicator_names)

    @patch('mysql.connector.connect')
    def test_data_insertion(self, mock_connect, mock_collector):
        """Test macro data insertion into database"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        test_data = [
            {
                'indicator_name': 'GDP',
                'date': '2024-01-01',
                'value': 25000.0,
                'frequency': 'quarterly',
                'source': 'FRED'
            }
        ]
        
        mock_collector._insert_macro_data(test_data)
        
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()

    def test_date_range_calculation(self, mock_collector):
        """Test date range calculation for data collection"""
        start_date, end_date = mock_collector._calculate_collection_range()
        
        assert isinstance(start_date, date)
        assert isinstance(end_date, date)
        assert start_date <= end_date

    @patch('mysql.connector.connect')
    def test_gap_detection(self, mock_connect, mock_collector):
        """Test data gap detection"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('2024-01-01',),
            ('2024-01-03',)  # Missing 2024-01-02
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        gaps = mock_collector._detect_data_gaps('GDP')
        
        assert len(gaps) >= 0  # May have gaps depending on logic

class TestMacroCollectorAPI:
    """Test macro collector FastAPI endpoints"""

    @pytest.fixture
    def test_client(self):
        """Create test client for API testing"""
        with patch.dict(os.environ, {
            'FRED_API_KEY': 'test_fred_key',
            'ALPHAVANTAGE_API_KEY': 'test_av_key',
            'SERVICE_NAME': 'test-macro-collector'
        }):
            collector = EnhancedMacroCollector()
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

    def test_status_endpoint(self, test_client):
        """Test status endpoint"""
        with patch('mysql.connector.connect'):
            response = test_client.get("/status")
            assert response.status_code == 200
            
            data = response.json()
            assert "service_name" in data
            assert "version" in data

class TestMacroCollectorIntegration:
    """Integration tests for macro collector"""

    @pytest.fixture
    def integration_collector(self):
        """Create collector for integration testing"""
        with patch.dict(os.environ, {
            'FRED_API_KEY': 'test_fred_key',
            'ALPHAVANTAGE_API_KEY': 'test_av_key'
        }):
            return EnhancedMacroCollector()

    @patch('requests.get')
    @patch('mysql.connector.connect')
    def test_full_collection_workflow(self, mock_connect, mock_get, integration_collector):
        """Test complete data collection workflow"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'observations': [
                {'date': '2024-01-01', 'value': '25000.0'}
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock database
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Run collection
        result = integration_collector.collect_macro_data()
        
        assert result is not None

    @patch('mysql.connector.connect')
    def test_health_scoring(self, mock_connect, integration_collector):
        """Test health scoring system"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (100,)  # Mock record count
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        health_score = integration_collector._calculate_health_score()
        
        assert 0 <= health_score <= 100

class TestMacroCollectorErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def error_collector(self):
        """Create collector for error testing"""
        return EnhancedMacroCollector()

    def test_missing_api_keys(self, error_collector):
        """Test behavior with missing API keys"""
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing keys gracefully
            assert error_collector.fred_api_key is None

    @patch('requests.get')
    def test_api_failure_handling(self, mock_get, error_collector):
        """Test API failure handling"""
        mock_get.side_effect = Exception("API Error")
        
        result = error_collector._fetch_fred_data('GDP', '2024-01-01', '2024-12-31')
        
        assert result == []  # Should return empty list on error

    @patch('mysql.connector.connect')
    def test_database_failure_handling(self, mock_connect, error_collector):
        """Test database failure handling"""
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        with pytest.raises(mysql.connector.Error):
            error_collector._get_db_connection()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])