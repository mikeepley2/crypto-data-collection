#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Enhanced OHLC Collector

Tests the OHLC collector with real API calls and database validation.
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
@pytest.mark.coingecko
class TestEnhancedOHLCCollectorIntegration:
    """Integration tests for OHLC collector with real API calls"""
    
    def test_collector_health_endpoint(self):
        """Test OHLC collector health endpoint"""
        # OHLC collector typically runs on port 8008
        response = requests.get("http://localhost:8008/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data
        assert 'ohlc_intervals' in health_data
    
    def test_collector_readiness_endpoint(self):
        """Test OHLC collector readiness endpoint"""
        response = requests.get("http://localhost:8008/ready")
        assert response.status_code == 200
        
        ready_data = response.json()
        assert ready_data['ready'] is True
        assert 'data_sources_connected' in ready_data
    
    @pytest.mark.slow
    def test_hourly_ohlc_collection(self, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting hourly OHLC data"""
        rate_limiter('coingecko')
        
        response = requests.post(
            "http://localhost:8008/api/v1/collect/ohlc",
            json={
                "symbols": ["bitcoin", "ethereum"],
                "timeframe": "1h",
                "lookback_hours": 24
            },
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'ohlc_data' in result
        
        # Validate OHLC data structure
        ohlc_data = result['ohlc_data']
        for symbol in ['bitcoin', 'ethereum']:
            if symbol in ohlc_data:
                symbol_ohlc = ohlc_data[symbol]
                assert len(symbol_ohlc) > 0
                
                for candle in symbol_ohlc:
                    assert 'timestamp' in candle
                    assert 'open' in candle
                    assert 'high' in candle
                    assert 'low' in candle
                    assert 'close' in candle
                    assert 'volume' in candle
                    
                    # Validate OHLC price relationships
                    assert candle['high'] >= candle['open']
                    assert candle['high'] >= candle['close']
                    assert candle['low'] <= candle['open']
                    assert candle['low'] <= candle['close']
                    assert candle['volume'] >= 0
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM ohlc_data WHERE timeframe = '1h' ORDER BY timestamp DESC LIMIT 10"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            assert record['timeframe'] == '1h'
            assert record['high_price'] >= record['open_price']
            assert record['high_price'] >= record['close_price']
            assert record['low_price'] <= record['open_price']
            assert record['low_price'] <= record['close_price']
            assert record['data_completeness_percentage'] >= 95.0
        
        cursor.close()
    
    @pytest.mark.slow
    def test_daily_ohlc_collection(self, test_api_keys, rate_limiter, test_mysql_connection):
        """Test collecting daily OHLC data"""
        rate_limiter('coingecko')
        
        response = requests.post(
            "http://localhost:8008/api/v1/collect/ohlc",
            json={
                "symbols": ["bitcoin", "ethereum", "solana"],
                "timeframe": "1d",
                "lookback_days": 7
            },
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        
        # Verify database storage
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM ohlc_data WHERE timeframe = '1d' ORDER BY timestamp DESC LIMIT 15"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        
        # Validate daily candles have proper time spacing
        if len(records) >= 2:
            time_diff = records[0]['timestamp'] - records[1]['timestamp']
            # Should be approximately 24 hours (86400 seconds)
            assert 21600 <= time_diff.total_seconds() <= 100800  # 6-28 hours tolerance
        
        cursor.close()
    
    def test_multiple_timeframes_collection(self, test_api_keys, rate_limiter):
        """Test collecting multiple timeframes simultaneously"""
        timeframes = ['5m', '15m', '1h', '4h', '1d']
        
        for timeframe in timeframes:
            rate_limiter('coingecko')
            time.sleep(0.3)  # Additional delay between timeframes
        
        response = requests.post(
            "http://localhost:8008/api/v1/collect/multi_timeframe",
            json={
                "symbol": "bitcoin",
                "timeframes": timeframes,
                "lookback_periods": {
                    "5m": 12,   # Last hour
                    "15m": 16,  # Last 4 hours
                    "1h": 24,   # Last day
                    "4h": 24,   # Last 4 days
                    "1d": 7     # Last week
                }
            },
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'multi_timeframe_data' in result
        
        multi_data = result['multi_timeframe_data']
        for timeframe in timeframes:
            if timeframe in multi_data:
                timeframe_data = multi_data[timeframe]
                assert len(timeframe_data) > 0
                
                # Validate timeframe-specific properties
                for candle in timeframe_data:
                    assert candle['open'] > 0
                    assert candle['high'] > 0
                    assert candle['low'] > 0
                    assert candle['close'] > 0
    
    def test_ohlc_data_validation_and_cleaning(self, test_api_keys, rate_limiter):
        """Test OHLC data validation and cleaning processes"""
        rate_limiter('coingecko')
        
        response = requests.post(
            "http://localhost:8008/api/v1/validate/ohlc",
            json={
                "symbol": "bitcoin",
                "timeframe": "1h",
                "validation_rules": {
                    "check_price_continuity": True,
                    "detect_anomalies": True,
                    "validate_volume": True,
                    "check_gaps": True
                }
            },
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        validation = response.json()
        
        assert 'validation_summary' in validation
        assert 'anomalies_detected' in validation
        assert 'data_quality_score' in validation
        
        # Validate quality score
        quality_score = validation['data_quality_score']
        assert 0 <= quality_score <= 100
        
        # Check validation summary
        summary = validation['validation_summary']
        assert 'total_candles_checked' in summary
        assert 'valid_candles' in summary
        assert 'invalid_candles' in summary
    
    def test_ohlc_gap_detection(self, test_mysql_connection):
        """Test detection of gaps in OHLC data"""
        response = requests.get(
            "http://localhost:8008/api/v1/gaps/detect",
            params={
                "symbol": "bitcoin",
                "timeframe": "1h",
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "end_date": datetime.now().isoformat()
            }
        )
        
        assert response.status_code == 200
        gaps = response.json()
        
        assert 'gaps_detected' in gaps
        assert 'total_expected_candles' in gaps
        assert 'actual_candles' in gaps
        assert 'gap_percentage' in gaps
        
        gap_percentage = gaps['gap_percentage']
        assert 0 <= gap_percentage <= 100
        
        # If gaps are detected, validate gap information
        if gaps['gaps_detected'] and len(gaps['gaps_detected']) > 0:
            gap = gaps['gaps_detected'][0]
            assert 'start_time' in gap
            assert 'end_time' in gap
            assert 'duration_minutes' in gap
    
    def test_ohlc_aggregation_from_trades(self, test_api_keys, rate_limiter):
        """Test OHLC aggregation from raw trade data"""
        rate_limiter('coingecko')
        
        response = requests.post(
            "http://localhost:8008/api/v1/aggregate/from_trades",
            json={
                "symbol": "bitcoin",
                "timeframe": "1m",
                "aggregation_period": "1h",
                "source": "websocket_trades"
            },
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        aggregation = response.json()
        
        assert 'aggregated_candles' in aggregation
        assert 'source_trades_count' in aggregation
        assert 'aggregation_quality' in aggregation
        
        # Validate aggregated candles
        if aggregation['aggregated_candles']:
            candle = aggregation['aggregated_candles'][0]
            assert 'volume_weighted_average' in candle
            assert 'trade_count' in candle
            assert candle['trade_count'] > 0
    
    def test_volume_profile_analysis(self, test_api_keys):
        """Test volume profile analysis for OHLC data"""
        response = requests.get(
            "http://localhost:8008/api/v1/analysis/volume_profile",
            params={
                "symbol": "bitcoin",
                "timeframe": "1h",
                "lookback_hours": 168  # 1 week
            },
            headers={"X-API-Key": test_api_keys['coingecko']}
        )
        
        assert response.status_code == 200
        volume_profile = response.json()
        
        assert 'volume_by_price_levels' in volume_profile
        assert 'point_of_control' in volume_profile
        assert 'value_area_high' in volume_profile
        assert 'value_area_low' in volume_profile
        
        # Validate volume profile structure
        volume_levels = volume_profile['volume_by_price_levels']
        assert len(volume_levels) > 0
        
        for level in volume_levels:
            assert 'price_level' in level
            assert 'volume' in level
            assert 'percentage_of_total' in level
            assert level['volume'] >= 0
            assert 0 <= level['percentage_of_total'] <= 100
    
    def test_ohlc_synchronization_across_symbols(self, test_mysql_connection):
        """Test that OHLC data is properly synchronized across symbols"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Check timestamp alignment for multiple symbols
        cursor.execute(
            """
            SELECT timestamp, COUNT(DISTINCT symbol) as symbol_count
            FROM ohlc_data 
            WHERE timeframe = '1h' 
            AND timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY timestamp
            HAVING symbol_count > 1
            ORDER BY timestamp DESC
            LIMIT 10
            """
        )
        sync_records = cursor.fetchall()
        
        # Should have synchronized timestamps across symbols
        assert len(sync_records) > 0
        
        for record in sync_records:
            assert record['symbol_count'] >= 2
        
        cursor.close()
    
    def test_ohlc_data_completeness_tracking(self, test_mysql_connection):
        """Test OHLC data completeness percentage tracking"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM ohlc_data WHERE data_completeness_percentage IS NOT NULL ORDER BY created_at DESC LIMIT 15"
        )
        records = cursor.fetchall()
        
        assert len(records) > 0
        for record in records:
            completeness = record['data_completeness_percentage']
            assert completeness is not None
            assert 0 <= completeness <= 100
            
            # OHLC data should generally have very high completeness
            # since it's structured price data
            assert completeness >= 90.0
            
            # Validate required OHLC fields are present
            assert record['open_price'] is not None
            assert record['high_price'] is not None
            assert record['low_price'] is not None
            assert record['close_price'] is not None
            assert record['volume'] is not None
        
        cursor.close()
    
    def test_performance_metrics_collection(self, performance_monitor, test_mysql_connection):
        """Test OHLC collection performance metrics"""
        cursor = test_mysql_connection.cursor()
        
        # Test bulk OHLC insertion performance
        start_time = time.time()
        
        # Insert 100 test OHLC records
        for i in range(100):
            cursor.execute(
                """
                INSERT INTO ohlc_data 
                (symbol, open_price, high_price, low_price, close_price, volume, timeframe, data_completeness_percentage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (f'TEST_PERF_{i}', 100.0, 105.0, 95.0, 102.0, 1000000, '1h', 100.0)
            )
        
        test_mysql_connection.commit()
        end_time = time.time()
        
        insertion_time = end_time - start_time
        assert insertion_time < 3.0  # Should complete in under 3 seconds
        
        # Cleanup
        cursor.execute("DELETE FROM ohlc_data WHERE symbol LIKE 'TEST_PERF_%'")
        test_mysql_connection.commit()
        cursor.close()