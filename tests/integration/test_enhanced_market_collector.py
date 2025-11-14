#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Enhanced Market Collector

Tests the market collector with real API calls and database validation.
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
class TestEnhancedMarketCollectorIntegration:
    """Integration tests for traditional market data collector"""
    
    def test_collector_health_endpoint(self):
        """Test market collector health endpoint"""
        # Market collector typically runs on port 8007
        response = requests.get("http://localhost:8007/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data
        assert 'market_data_sources' in health_data
    
    def test_collector_readiness_endpoint(self):
        """Test market collector readiness endpoint"""
        response = requests.get("http://localhost:8007/ready")
        assert response.status_code == 200
        
        ready_data = response.json()
        assert ready_data['ready'] is True
        assert 'data_providers_connected' in ready_data
    
    @pytest.mark.slow
    def test_stock_market_data_collection(self, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting traditional stock market data"""
        rate_limiter('market_data')
        
        response = requests.post(
            "http://localhost:8007/api/v1/collect/stocks",
            json={
                "symbols": ["AAPL", "GOOGL", "MSFT"],
                "data_types": ["price", "volume", "market_cap"]
            },
            headers={"X-API-Key": test_api_keys.get('alpha_vantage', 'demo_key')}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'stock_data' in result
        
        # Validate stock data structure
        stock_data = result['stock_data']
        for symbol in ['AAPL', 'GOOGL', 'MSFT']:
            if symbol in stock_data:
                symbol_data = stock_data[symbol]
                assert 'price' in symbol_data
                assert 'volume' in symbol_data
                assert symbol_data['price'] > 0
                assert symbol_data['volume'] >= 0
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM market_data WHERE asset_type = 'stock' ORDER BY created_at DESC LIMIT 10"
        )
        records = cursor.fetchall()
        assert len(records) > 0
        
        for record in records:
            assert record['asset_type'] == 'stock'
            assert record['symbol'] in ['AAPL', 'GOOGL', 'MSFT']
            assert record['data_completeness_percentage'] >= 80.0
        
        cursor.close()
    
    @pytest.mark.slow
    def test_forex_data_collection(self, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting forex market data"""
        rate_limiter('market_data')
        
        response = requests.post(
            "http://localhost:8007/api/v1/collect/forex",
            json={
                "currency_pairs": ["EUR/USD", "GBP/USD", "USD/JPY"],
                "timeframe": "1h"
            },
            headers={"X-API-Key": test_api_keys.get('forex', 'demo_key')}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'forex_data' in result
        
        # Validate forex data
        forex_data = result['forex_data']
        for pair in ['EUR/USD', 'GBP/USD', 'USD/JPY']:
            if pair in forex_data:
                pair_data = forex_data[pair]
                assert 'bid' in pair_data
                assert 'ask' in pair_data
                assert 'spread' in pair_data
                assert pair_data['bid'] > 0
                assert pair_data['ask'] > pair_data['bid']
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM market_data WHERE asset_type = 'forex' ORDER BY created_at DESC LIMIT 5"
        )
        records = cursor.fetchall()
        
        if len(records) > 0:
            for record in records:
                assert record['asset_type'] == 'forex'
                assert '/' in record['symbol']  # Currency pair format
                assert record['data_completeness_percentage'] >= 85.0
        
        cursor.close()
    
    def test_commodities_data_collection(self, test_api_keys, rate_limiter):
        """Test collecting commodities market data"""
        rate_limiter('market_data')
        
        response = requests.post(
            "http://localhost:8007/api/v1/collect/commodities",
            json={
                "commodities": ["GOLD", "SILVER", "OIL", "COPPER"],
                "include_futures": True
            },
            headers={"X-API-Key": test_api_keys.get('commodities', 'demo_key')}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'commodities_data' in result
        
        # Validate commodities data
        commodities_data = result['commodities_data']
        for commodity in ['GOLD', 'SILVER', 'OIL', 'COPPER']:
            if commodity in commodities_data:
                commodity_data = commodities_data[commodity]
                assert 'spot_price' in commodity_data
                assert 'futures_price' in commodity_data
                assert commodity_data['spot_price'] > 0
    
    def test_market_indices_collection(self, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting market indices data"""
        rate_limiter('market_data')
        
        response = requests.post(
            "http://localhost:8007/api/v1/collect/indices",
            json={
                "indices": ["SPX", "NDX", "DJI", "VIX"],
                "include_components": False
            },
            headers={"X-API-Key": test_api_keys.get('market_indices', 'demo_key')}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'indices_data' in result
        
        # Validate indices data
        indices_data = result['indices_data']
        for index in ['SPX', 'NDX', 'DJI', 'VIX']:
            if index in indices_data:
                index_data = indices_data[index]
                assert 'value' in index_data
                assert 'change' in index_data
                assert 'change_percent' in index_data
                assert index_data['value'] > 0
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM market_data WHERE asset_type = 'index' ORDER BY created_at DESC LIMIT 5"
        )
        records = cursor.fetchall()
        
        if len(records) > 0:
            for record in records:
                assert record['asset_type'] == 'index'
                assert record['symbol'] in ['SPX', 'NDX', 'DJI', 'VIX']
                assert record['data_completeness_percentage'] >= 90.0
        
        cursor.close()
    
    def test_correlation_analysis(self, test_api_keys):
        """Test market correlation analysis functionality"""
        response = requests.get(
            "http://localhost:8007/api/v1/analytics/correlation",
            params={
                "asset1": "SPX",
                "asset2": "BTC",
                "timeframe": "30d"
            },
            headers={"X-API-Key": test_api_keys.get('analytics', 'demo_key')}
        )
        
        assert response.status_code == 200
        correlation = response.json()
        
        assert 'correlation_coefficient' in correlation
        assert 'p_value' in correlation
        assert 'sample_size' in correlation
        
        # Validate correlation coefficient range
        corr_coeff = correlation['correlation_coefficient']
        assert -1 <= corr_coeff <= 1
    
    def test_volatility_analysis(self, test_api_keys):
        """Test volatility analysis for market instruments"""
        response = requests.get(
            "http://localhost:8007/api/v1/analytics/volatility",
            params={
                "symbol": "SPX",
                "period": "30",
                "method": "historical"
            },
            headers={"X-API-Key": test_api_keys.get('analytics', 'demo_key')}
        )
        
        assert response.status_code == 200
        volatility = response.json()
        
        assert 'historical_volatility' in volatility
        assert 'volatility_percentile' in volatility
        assert 'volatility_trend' in volatility
        
        # Validate volatility values
        hist_vol = volatility['historical_volatility']
        assert 0 <= hist_vol <= 200  # Reasonable volatility range (0-200%)
    
    def test_economic_calendar_integration(self, test_api_keys):
        """Test economic calendar data integration"""
        response = requests.get(
            "http://localhost:8007/api/v1/calendar/events",
            params={
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "importance": "high"
            },
            headers={"X-API-Key": test_api_keys.get('economic_calendar', 'demo_key')}
        )
        
        assert response.status_code == 200
        events = response.json()
        
        assert 'economic_events' in events
        
        if events['economic_events']:
            event = events['economic_events'][0]
            assert 'event_name' in event
            assert 'scheduled_time' in event
            assert 'importance' in event
            assert 'currency' in event
    
    def test_market_sentiment_indicators(self, test_api_keys, test_mysql_connection):
        """Test market sentiment indicators collection"""
        response = requests.get(
            "http://localhost:8007/api/v1/sentiment/indicators",
            headers={"X-API-Key": test_api_keys.get('sentiment', 'demo_key')}
        )
        
        assert response.status_code == 200
        sentiment = response.json()
        
        expected_indicators = ['vix', 'put_call_ratio', 'fear_greed_index', 'aaii_sentiment']
        for indicator in expected_indicators:
            if indicator in sentiment:
                indicator_data = sentiment[indicator]
                assert 'value' in indicator_data
                assert 'timestamp' in indicator_data
                
                # Validate indicator ranges
                value = indicator_data['value']
                if indicator == 'vix':
                    assert 0 <= value <= 100
                elif indicator == 'fear_greed_index':
                    assert 0 <= value <= 100
    
    def test_cross_asset_analysis(self, test_api_keys):
        """Test cross-asset analysis functionality"""
        response = requests.post(
            "http://localhost:8007/api/v1/analytics/cross_asset",
            json={
                "primary_asset": "SPX",
                "comparison_assets": ["GOLD", "USD/EUR", "BTC"],
                "analysis_type": "correlation_matrix",
                "timeframe": "90d"
            },
            headers={"X-API-Key": test_api_keys.get('analytics', 'demo_key')}
        )
        
        assert response.status_code == 200
        analysis = response.json()
        
        assert 'correlation_matrix' in analysis
        assert 'asset_performance' in analysis
        assert 'diversification_metrics' in analysis
        
        # Validate correlation matrix structure
        correlation_matrix = analysis['correlation_matrix']
        for asset in ['SPX', 'GOLD', 'USD/EUR', 'BTC']:
            if asset in correlation_matrix:
                assert isinstance(correlation_matrix[asset], dict)
    
    def test_market_data_quality_validation(self, test_mysql_connection):
        """Test market data quality and completeness validation"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM market_data WHERE data_completeness_percentage IS NOT NULL ORDER BY created_at DESC LIMIT 20"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            completeness = record['data_completeness_percentage']
            assert completeness is not None
            assert 0 <= completeness <= 100
            
            # Market data should generally have high completeness
            assert completeness >= 75.0
            
            # Validate required fields are present
            assert record['symbol'] is not None
            assert record['asset_type'] is not None
            assert record['price'] is not None
            assert record['timestamp'] is not None
        
        cursor.close()