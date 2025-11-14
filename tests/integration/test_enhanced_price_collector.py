#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Enhanced Price Collector

Tests the price collector with real CoinGecko API calls and database validation.
"""

import pytest
import asyncio
import aiohttp
import mysql.connector
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import time
import json
import requests


@pytest.mark.integration
@pytest.mark.real_api
@pytest.mark.coingecko
class TestEnhancedPriceCollectorIntegration:
    """Integration tests for price collector with real API calls"""
    
    def test_collector_health_endpoint(self, collector_endpoints):
        """Test price collector health endpoint"""
        response = requests.get(f"{collector_endpoints['price']}/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data
        assert 'uptime' in health_data
    
    def test_collector_readiness_endpoint(self, collector_endpoints):
        """Test price collector readiness endpoint"""
        response = requests.get(f"{collector_endpoints['price']}/ready")
        assert response.status_code == 200
        
        ready_data = response.json()
        assert ready_data['ready'] is True
        assert 'database_connected' in ready_data
        assert ready_data['database_connected'] is True
    
    def test_collector_metrics_endpoint(self, collector_endpoints):
        """Test price collector Prometheus metrics endpoint"""
        response = requests.get(f"{collector_endpoints['price']}/metrics")
        assert response.status_code == 200
        
        metrics = response.text
        assert 'price_collection_requests_total' in metrics
        assert 'price_collection_duration_seconds' in metrics
        assert 'price_collection_errors_total' in metrics
    
    @pytest.mark.slow
    def test_real_api_bitcoin_price_collection(self, collector_endpoints, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting real Bitcoin price data from CoinGecko API"""
        rate_limiter('coingecko')
        
        # Trigger price collection for Bitcoin
        response = requests.post(
            f"{collector_endpoints['price']}/api/v1/collect",
            json={"symbols": ["bitcoin"]},
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['symbols_processed'] >= 1
        assert 'bitcoin' in result['collected_data']
        
        # Verify data was stored in database
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM price_data_real WHERE symbol = 'bitcoin' ORDER BY created_at DESC LIMIT 1"
        )
        record = cursor.fetchone()
        
        assert record is not None
        assert record['symbol'] == 'bitcoin'
        assert record['price'] > 0
        assert record['market_cap'] > 0
        assert record['data_completeness_percentage'] >= 90.0
        assert record['created_at'] is not None
        
        cursor.close()
    
    def test_multiple_symbols_collection(self, collector_endpoints, test_api_keys, rate_limiter, test_symbols):
        """Test collecting data for multiple symbols"""
        symbols = test_symbols['primary']  # [bitcoin, ethereum, solana]
        
        for symbol in symbols:
            rate_limiter('coingecko')
            time.sleep(0.5)  # Additional delay between symbols
        
        response = requests.post(
            f"{collector_endpoints['price']}/api/v1/collect",
            json={"symbols": symbols},
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['symbols_processed'] == len(symbols)
        
        # Check each symbol was processed
        for symbol in symbols:
            assert symbol in result['collected_data']
            symbol_data = result['collected_data'][symbol]
            assert 'price' in symbol_data
            assert 'market_cap' in symbol_data
            assert symbol_data['price'] > 0
    
    def test_price_data_completeness_validation(self, test_mysql_connection):
        """Test that price data includes completeness percentage"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM price_data_real WHERE data_completeness_percentage IS NOT NULL ORDER BY created_at DESC LIMIT 10"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            completeness = record['data_completeness_percentage']
            assert completeness is not None
            assert 0 <= completeness <= 100
            
            # Validate completeness calculation
            expected_fields = ['price', 'market_cap', 'total_volume']
            filled_fields = sum(1 for field in expected_fields if record.get(field) is not None)
            expected_completeness = (filled_fields / len(expected_fields)) * 100
            
            # Allow some tolerance for additional optional fields
            assert abs(completeness - expected_completeness) <= 20
        
        cursor.close()
    
    def test_error_handling_invalid_symbol(self, collector_endpoints, test_api_keys):
        """Test error handling for invalid symbols"""
        response = requests.post(
            f"{collector_endpoints['price']}/api/v1/collect",
            json={"symbols": ["invalid_symbol_12345"]},
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        # Should still return 200 but with error details
        assert response.status_code == 200
        result = response.json()
        
        assert 'errors' in result
        assert len(result['errors']) > 0
        assert any('invalid_symbol_12345' in error for error in result['errors'])
    
    def test_rate_limiting_compliance(self, collector_endpoints, test_api_keys, test_symbols):
        """Test that rate limiting is properly implemented"""
        start_time = time.time()
        
        # Make multiple rapid requests
        responses = []
        for i in range(3):
            response = requests.post(
                f"{collector_endpoints['price']}/api/v1/collect",
                json={"symbols": [test_symbols['test_only'][0]]},  # dogecoin
                headers={"X-API-Key": test_api_keys['coingecko']}
            )
            responses.append(response)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should take at least 0.4 seconds (0.2s delay between calls)
        assert duration >= 0.4
        
        # All requests should succeed (rate limiting should delay, not reject)
        for response in responses:
            assert response.status_code == 200
    
    @pytest.mark.slow
    def test_historical_data_collection(self, collector_endpoints, test_api_keys, rate_limiter):
        """Test collecting historical price data"""
        rate_limiter('coingecko')
        
        # Request historical data for the last 24 hours
        response = requests.post(
            f"{collector_endpoints['price']}/api/v1/collect/historical",
            json={
                "symbol": "bitcoin",
                "days": 1,
                "vs_currency": "usd"
            },
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'historical_data' in result
        assert len(result['historical_data']) > 0
        
        # Validate historical data structure
        for data_point in result['historical_data'][:5]:  # Check first 5 points
            assert 'timestamp' in data_point
            assert 'price' in data_point
            assert 'market_cap' in data_point
            assert data_point['price'] > 0
    
    def test_database_performance(self, test_mysql_connection, performance_monitor):
        """Test database insertion performance"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test data and measure performance
        test_data = {
            'symbol': 'TEST',
            'price': 100.50,
            'market_cap': 2000000000,
            'total_volume': 500000000,
            'data_completeness_percentage': 95.0
        }
        
        start_time = time.time()
        
        for i in range(100):
            cursor.execute(
                "INSERT INTO price_data_real (symbol, price, market_cap, total_volume, data_completeness_percentage) VALUES (%s, %s, %s, %s, %s)",
                (f"TEST_{i}", test_data['price'], test_data['market_cap'], test_data['total_volume'], test_data['data_completeness_percentage'])
            )
        
        test_mysql_connection.commit()
        end_time = time.time()
        
        insertion_time = end_time - start_time
        assert insertion_time < 5.0  # Should complete in under 5 seconds
        
        # Cleanup
        cursor.execute("DELETE FROM price_data_real WHERE symbol LIKE 'TEST_%'")
        test_mysql_connection.commit()
        cursor.close()