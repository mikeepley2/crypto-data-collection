#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Enhanced Macro Collector

Tests the macro collector with real FRED API calls and database validation.
"""

import pytest
import requests
import mysql.connector
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import time
import json


@pytest.mark.integration
@pytest.mark.real_api
@pytest.mark.fred
class TestEnhancedMacroCollectorIntegration:
    """Integration tests for macro collector with real FRED API calls"""
    
    def test_collector_health_endpoint(self, collector_endpoints):
        """Test macro collector health endpoint"""
        response = requests.get(f"{collector_endpoints['macro']}/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data
        assert 'fred_api_status' in health_data
    
    def test_collector_readiness_endpoint(self, collector_endpoints):
        """Test macro collector readiness endpoint"""
        response = requests.get(f"{collector_endpoints['macro']}/ready")
        assert response.status_code == 200
        
        ready_data = response.json()
        assert ready_data['ready'] is True
        assert 'fred_api_connected' in ready_data
        assert ready_data['fred_api_connected'] is True
    
    @pytest.mark.slow
    def test_gdp_data_collection(self, collector_endpoints, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting GDP data from FRED API"""
        rate_limiter('fred')
        
        response = requests.post(
            f"{collector_endpoints['macro']}/api/v1/collect/gdp",
            json={
                "series_id": "GDP",
                "start_date": "2023-01-01",
                "end_date": "2024-01-01"
            },
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'gdp_data' in result
        assert len(result['gdp_data']) > 0
        
        # Validate GDP data structure
        gdp_data = result['gdp_data']
        for data_point in gdp_data:
            assert 'date' in data_point
            assert 'value' in data_point
            assert data_point['value'] is not None
            assert float(data_point['value']) > 0
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM macro_indicators WHERE indicator = 'GDP' ORDER BY timestamp DESC LIMIT 5"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            assert record['indicator'] == 'GDP'
            assert record['value'] > 0
            assert record['unit'] == 'billions'
            assert record['data_completeness_percentage'] >= 95.0
        
        cursor.close()
    
    @pytest.mark.slow
    def test_inflation_data_collection(self, collector_endpoints, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting CPI inflation data from FRED API"""
        rate_limiter('fred')
        
        response = requests.post(
            f"{collector_endpoints['macro']}/api/v1/collect/inflation",
            json={
                "series_id": "CPIAUCSL",  # Consumer Price Index
                "start_date": "2023-01-01"
            },
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'cpi_data' in result
        
        # Validate CPI data
        cpi_data = result['cpi_data']
        assert len(cpi_data) > 0
        
        for data_point in cpi_data:
            assert 'date' in data_point
            assert 'value' in data_point
            assert float(data_point['value']) > 0
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM macro_indicators WHERE indicator = 'CPI' ORDER BY timestamp DESC LIMIT 3"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            assert record['indicator'] == 'CPI'
            assert record['frequency'] == 'monthly'
            assert record['data_completeness_percentage'] >= 90.0
        
        cursor.close()
    
    @pytest.mark.slow
    def test_unemployment_rate_collection(self, collector_endpoints, test_api_keys, rate_limiter):
        """Test collecting unemployment rate from FRED API"""
        rate_limiter('fred')
        
        response = requests.post(
            f"{collector_endpoints['macro']}/api/v1/collect/unemployment",
            json={"series_id": "UNRATE"},
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'unemployment_data' in result
        
        unemployment_data = result['unemployment_data']
        assert len(unemployment_data) > 0
        
        # Validate unemployment rate values
        for data_point in unemployment_data:
            rate = float(data_point['value'])
            assert 0 <= rate <= 25  # Reasonable unemployment rate range
    
    @pytest.mark.slow
    def test_federal_funds_rate_collection(self, collector_endpoints, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting Federal Funds Rate from FRED API"""
        rate_limiter('fred')
        
        response = requests.post(
            f"{collector_endpoints['macro']}/api/v1/collect/fed_rate",
            json={"series_id": "FEDFUNDS"},
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'fed_rate_data' in result
        
        # Verify data structure
        fed_rate_data = result['fed_rate_data']
        assert len(fed_rate_data) > 0
        
        for data_point in fed_rate_data:
            rate = float(data_point['value'])
            assert 0 <= rate <= 20  # Reasonable fed funds rate range
        
        # Check database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM macro_indicators WHERE indicator = 'FEDERAL_FUNDS_RATE' ORDER BY timestamp DESC LIMIT 3"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            assert record['indicator'] == 'FEDERAL_FUNDS_RATE'
            assert record['unit'] == 'percentage'
            assert 0 <= record['value'] <= 20
        
        cursor.close()
    
    def test_bulk_macro_indicators_collection(self, collector_endpoints, test_api_keys, rate_limiter):
        """Test collecting multiple macro indicators in bulk"""
        indicators = ['GDP', 'CPIAUCSL', 'UNRATE', 'FEDFUNDS']
        
        for indicator in indicators:
            rate_limiter('fred')
            time.sleep(1)  # Extra delay for bulk collection
        
        response = requests.post(
            f"{collector_endpoints['macro']}/api/v1/collect/bulk",
            json={
                "series_ids": indicators,
                "start_date": "2023-01-01"
            },
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'bulk_data' in result
        
        bulk_data = result['bulk_data']
        assert len(bulk_data) >= len(indicators)
        
        # Verify each indicator was collected
        collected_indicators = [item['series_id'] for item in bulk_data]
        for indicator in indicators:
            assert indicator in collected_indicators
    
    def test_macro_analytics_endpoint(self, collector_endpoints, test_api_keys):
        """Test macro analytics computation"""
        response = requests.get(
            f"{collector_endpoints['macro']}/api/v1/analytics/correlation",
            params={
                "primary_indicator": "GDP",
                "secondary_indicator": "CPI",
                "timeframe": "2y"
            },
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        assert response.status_code == 200
        analytics = response.json()
        
        assert 'correlation_coefficient' in analytics
        assert 'statistical_significance' in analytics
        assert 'data_points_used' in analytics
        
        # Validate correlation coefficient
        correlation = analytics['correlation_coefficient']
        assert -1 <= correlation <= 1
    
    def test_rate_limiting_fred_api(self, collector_endpoints, test_api_keys):
        """Test FRED API rate limiting compliance (120 requests/minute)"""
        start_time = time.time()
        
        # Make multiple requests quickly
        responses = []
        for i in range(3):
            response = requests.get(
                f"{collector_endpoints['macro']}/api/v1/status",
                headers={"X-API-Key": test_api_keys['fred']}
            )
            responses.append(response)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should respect 0.5s delay between FRED API calls
        assert duration >= 1.0  # 3 requests with 0.5s delays
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_error_handling_invalid_series_id(self, collector_endpoints, test_api_keys):
        """Test error handling for invalid FRED series IDs"""
        response = requests.post(
            f"{collector_endpoints['macro']}/api/v1/collect/gdp",
            json={"series_id": "INVALID_SERIES_ID_12345"},
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        # Should handle gracefully
        assert response.status_code == 200
        result = response.json()
        
        assert result['success'] is False
        assert 'errors' in result
        assert any('INVALID_SERIES_ID_12345' in error for error in result['errors'])
    
    def test_data_completeness_validation(self, test_mysql_connection):
        """Test macro data completeness percentage calculation"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM macro_indicators WHERE data_completeness_percentage IS NOT NULL ORDER BY created_at DESC LIMIT 10"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            completeness = record['data_completeness_percentage']
            assert completeness is not None
            assert 0 <= completeness <= 100
            
            # Macro data should generally have high completeness
            # since FRED provides structured, complete data
            assert completeness >= 85.0
        
        cursor.close()
    
    def test_historical_data_backfill(self, collector_endpoints, test_api_keys, rate_limiter):
        """Test historical macro data backfill functionality"""
        rate_limiter('fred')
        
        # Request backfill for last 2 years
        response = requests.post(
            f"{collector_endpoints['macro']}/api/v1/backfill",
            json={
                "indicators": ["GDP", "CPI"],
                "start_date": "2022-01-01",
                "end_date": "2024-01-01"
            },
            headers={"X-API-Key": test_api_keys['fred']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'backfill_summary' in result
        
        summary = result['backfill_summary']
        assert 'total_records_processed' in summary
        assert 'indicators_updated' in summary
        assert summary['total_records_processed'] > 0