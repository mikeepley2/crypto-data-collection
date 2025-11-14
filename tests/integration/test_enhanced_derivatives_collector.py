#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Enhanced Derivatives Collector

Tests the derivatives collector with real API calls and database validation.
"""

import pytest
import asyncio
import requests
import mysql.connector
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import time
import json


@pytest.mark.integration
@pytest.mark.real_api
class TestEnhancedDerivativesCollectorIntegration:
    """Integration tests for derivatives collector with real API calls"""
    
    def test_collector_health_endpoint(self):
        """Test derivatives collector health endpoint"""
        # Derivatives collector typically runs on port 8006
        response = requests.get("http://localhost:8006/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data
        assert 'uptime' in health_data
    
    def test_collector_readiness_endpoint(self):
        """Test derivatives collector readiness endpoint"""
        response = requests.get("http://localhost:8006/ready")
        assert response.status_code == 200
        
        ready_data = response.json()
        assert ready_data['ready'] is True
        assert 'exchange_connections' in ready_data
    
    @pytest.mark.slow
    def test_options_data_collection(self, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting options data from multiple exchanges"""
        rate_limiter('derivatives')
        
        response = requests.post(
            "http://localhost:8006/api/v1/collect/options",
            json={
                "symbols": ["BTC", "ETH"],
                "exchanges": ["deribit", "okex"],
                "expiry_days": 30
            },
            headers={"X-API-Key": test_api_keys.get('derivatives', 'demo_key')}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'options_data' in result
        
        # Verify data structure
        options_data = result['options_data']
        for symbol in ['BTC', 'ETH']:
            assert symbol in options_data
            symbol_options = options_data[symbol]
            assert 'calls' in symbol_options
            assert 'puts' in symbol_options
            
            # Validate option data fields
            for option_type in ['calls', 'puts']:
                if symbol_options[option_type]:
                    option = symbol_options[option_type][0]  # First option
                    assert 'strike' in option
                    assert 'premium' in option
                    assert 'volume' in option
                    assert 'open_interest' in option
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM derivatives_data WHERE instrument_type = 'option' ORDER BY created_at DESC LIMIT 10"
        )
        records = cursor.fetchall()
        assert len(records) > 0
        
        for record in records:
            assert record['symbol'] in ['BTC', 'ETH']
            assert record['instrument_type'] == 'option'
            assert record['data_completeness_percentage'] >= 80.0
        
        cursor.close()
    
    @pytest.mark.slow 
    def test_futures_data_collection(self, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting futures data from multiple exchanges"""
        rate_limiter('derivatives')
        
        response = requests.post(
            "http://localhost:8006/api/v1/collect/futures",
            json={
                "symbols": ["BTC", "ETH"],
                "exchanges": ["binance", "bybit"],
                "contract_types": ["perpetual", "quarterly"]
            },
            headers={"X-API-Key": test_api_keys.get('derivatives', 'demo_key')}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'futures_data' in result
        
        # Verify futures data structure
        futures_data = result['futures_data']
        for symbol in ['BTC', 'ETH']:
            if symbol in futures_data:
                symbol_futures = futures_data[symbol]
                for contract in symbol_futures:
                    assert 'contract_type' in contract
                    assert 'price' in contract
                    assert 'volume' in contract
                    assert 'open_interest' in contract
                    assert 'funding_rate' in contract
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM derivatives_data WHERE instrument_type = 'future' ORDER BY created_at DESC LIMIT 10"
        )
        records = cursor.fetchall()
        assert len(records) > 0
        
        cursor.close()
    
    def test_derivatives_analytics_endpoint(self, test_api_keys):
        """Test derivatives analytics computation"""
        response = requests.get(
            "http://localhost:8006/api/v1/analytics/derivatives",
            params={
                "symbol": "BTC",
                "timeframe": "24h"
            },
            headers={"X-API-Key": test_api_keys.get('derivatives', 'demo_key')}
        )
        
        assert response.status_code == 200
        analytics = response.json()
        
        assert 'put_call_ratio' in analytics
        assert 'total_open_interest' in analytics
        assert 'volume_weighted_iv' in analytics
        assert 'max_pain' in analytics
        
        # Validate analytics values
        assert analytics['put_call_ratio'] >= 0
        assert analytics['total_open_interest'] >= 0
        if analytics['volume_weighted_iv']:
            assert 0 <= analytics['volume_weighted_iv'] <= 500  # IV in percentage
    
    def test_multi_exchange_data_aggregation(self, test_api_keys, rate_limiter):
        """Test aggregating data from multiple exchanges"""
        rate_limiter('derivatives')
        
        response = requests.post(
            "http://localhost:8006/api/v1/aggregate",
            json={
                "symbol": "BTC",
                "instrument_type": "option",
                "exchanges": ["deribit", "okex", "binance"],
                "aggregation_method": "volume_weighted"
            },
            headers={"X-API-Key": test_api_keys.get('derivatives', 'demo_key')}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'aggregated_data' in result
        
        aggregated = result['aggregated_data']
        assert 'volume_weighted_premium' in aggregated
        assert 'total_volume' in aggregated
        assert 'exchange_breakdown' in aggregated
        
        # Validate exchange breakdown
        exchange_breakdown = aggregated['exchange_breakdown']
        for exchange in ['deribit', 'okex', 'binance']:
            if exchange in exchange_breakdown:
                exchange_data = exchange_breakdown[exchange]
                assert 'volume_share' in exchange_data
                assert 'premium_contribution' in exchange_data
    
    def test_real_time_derivatives_streaming(self, test_api_keys):
        """Test real-time derivatives data streaming"""
        # Note: This would typically use WebSocket connections
        response = requests.get(
            "http://localhost:8006/api/v1/stream/status",
            headers={"X-API-Key": test_api_keys.get('derivatives', 'demo_key')}
        )
        
        assert response.status_code == 200
        stream_status = response.json()
        
        assert 'active_streams' in stream_status
        assert 'total_symbols' in stream_status
        assert 'exchanges_connected' in stream_status
        
        # Verify at least some streams are active
        if stream_status['active_streams'] > 0:
            assert stream_status['exchanges_connected'] > 0
    
    def test_derivatives_risk_metrics(self, test_api_keys, test_mysql_connection):
        """Test derivatives risk metrics calculation"""
        response = requests.get(
            "http://localhost:8006/api/v1/risk/metrics",
            params={"symbol": "BTC"},
            headers={"X-API-Key": test_api_keys.get('derivatives', 'demo_key')}
        )
        
        assert response.status_code == 200
        risk_metrics = response.json()
        
        expected_metrics = ['gamma_exposure', 'delta_exposure', 'vanna_exposure', 'charm_exposure']
        for metric in expected_metrics:
            assert metric in risk_metrics
            if risk_metrics[metric] is not None:
                assert isinstance(risk_metrics[metric], (int, float))
        
        # Verify risk metrics are stored in database
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM derivatives_risk_metrics WHERE symbol = 'BTC' ORDER BY created_at DESC LIMIT 1"
        )
        record = cursor.fetchone()
        
        if record:
            assert record['symbol'] == 'BTC'
            assert record['data_completeness_percentage'] >= 70.0
        
        cursor.close()
    
    def test_error_handling_exchange_downtime(self, test_api_keys):
        """Test error handling when exchanges are down"""
        response = requests.post(
            "http://localhost:8006/api/v1/collect/options",
            json={
                "symbols": ["BTC"],
                "exchanges": ["fake_exchange"],  # Non-existent exchange
                "timeout": 5
            },
            headers={"X-API-Key": test_api_keys.get('derivatives', 'demo_key')}
        )
        
        assert response.status_code == 200  # Should handle gracefully
        result = response.json()
        
        assert 'errors' in result
        assert any('fake_exchange' in error for error in result['errors'])
        assert 'fallback_used' in result
    
    def test_database_schema_validation(self, test_mysql_connection):
        """Test that derivatives database schema includes completeness tracking"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Check if derivatives_data table exists with proper schema
        cursor.execute("DESCRIBE derivatives_data")
        columns = cursor.fetchall()
        column_names = [col['Field'] for col in columns]
        
        required_columns = [
            'symbol', 'instrument_type', 'exchange', 'strike_price',
            'premium', 'volume', 'open_interest', 'data_completeness_percentage',
            'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in column_names, f"Missing required column: {col}"
        
        # Verify data_completeness_percentage column is properly typed
        completeness_col = next(col for col in columns if col['Field'] == 'data_completeness_percentage')
        assert 'decimal' in completeness_col['Type'].lower()
        
        cursor.close()