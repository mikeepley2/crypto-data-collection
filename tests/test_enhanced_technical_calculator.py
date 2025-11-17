#!/usr/bin/env python3
"""
Unit tests for Enhanced Technical Calculator Collector
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from enhanced_technical_calculator_template import (
    EnhancedTechnicalCalculator,
    TechnicalCalculatorConfig
)
from tests.test_base_collector import BaseCollectorTestCase

class TestTechnicalCalculatorConfig:
    """Test technical calculator configuration"""
    
    def test_config_initialization(self):
        """Test configuration defaults"""
        config = TechnicalCalculatorConfig.from_env()
        
        assert config.service_name == "enhanced-technical-calculator"
        assert config.calculation_interval == 900  # 15 minutes
        assert config.batch_size == 50
        assert config.lookback_periods == 200
        assert config.parallel_workers == 4
    
    def test_technical_indicators_config(self):
        """Test technical indicators configuration"""
        config = TechnicalCalculatorConfig()
        
        # Bollinger Bands
        assert config.bollinger_period == 20
        assert config.bollinger_std == 2
        
        # RSI
        assert config.rsi_period == 14
        
        # MACD
        assert config.macd_fast == 12
        assert config.macd_slow == 26
        assert config.macd_signal == 9
        
        # Moving Averages
        assert config.sma_periods == [10, 20, 50, 200]
        assert config.ema_periods == [12, 26]

class TestEnhancedTechnicalCalculator(BaseCollectorTestCase):
    """Test Enhanced Technical Calculator Collector functionality"""
    
    @pytest.fixture
    def tech_collector(self):
        """Create technical calculator instance for testing"""
        with patch.dict('os.environ', {
            'DB_HOST': 'localhost',
            'DB_USER': 'test',
            'DB_PASSWORD': 'test',
            'DB_NAME': 'test_db',
            'SERVICE_NAME': 'enhanced-technical-calculator'
        }):
            return EnhancedTechnicalCalculator()
    
    @pytest.fixture
    def sample_price_data(self):
        """Sample OHLCV price data for testing"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        data = {
            'timestamp': dates,
            'open': np.random.uniform(40000, 50000, 100),
            'high': np.random.uniform(50000, 55000, 100),
            'low': np.random.uniform(35000, 40000, 100),
            'close': np.random.uniform(40000, 50000, 100),
            'volume': np.random.uniform(1000000, 5000000, 100)
        }
        df = pd.DataFrame(data)
        # Ensure high >= open, close and low <= open, close
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
        return df
    
    def test_collector_initialization(self, tech_collector):
        """Test technical calculator initialization"""
        assert tech_collector.config.service_name == "enhanced-technical-calculator"
        assert isinstance(tech_collector.config.sma_periods, list)
        assert isinstance(tech_collector.config.ema_periods, list)
    
    def test_calculate_sma(self, tech_collector, sample_price_data):
        """Test Simple Moving Average calculation"""
        period = 20
        sma_values = tech_collector._calculate_sma(sample_price_data['close'], period)
        
        assert isinstance(sma_values, pd.Series)
        assert len(sma_values) == len(sample_price_data)
        # First period-1 values should be NaN
        assert pd.isna(sma_values.iloc[:period-1]).all()
        # Values after should be calculated
        assert not pd.isna(sma_values.iloc[period:]).any()
    
    def test_calculate_ema(self, tech_collector, sample_price_data):
        """Test Exponential Moving Average calculation"""
        period = 12
        ema_values = tech_collector._calculate_ema(sample_price_data['close'], period)
        
        assert isinstance(ema_values, pd.Series)
        assert len(ema_values) == len(sample_price_data)
        # EMA should start from first valid value
        assert not pd.isna(ema_values.iloc[period-1:]).any()
    
    def test_calculate_bollinger_bands(self, tech_collector, sample_price_data):
        """Test Bollinger Bands calculation"""
        period = 20
        std_dev = 2
        
        upper, middle, lower = tech_collector._calculate_bollinger_bands(
            sample_price_data['close'], period, std_dev
        )
        
        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert len(upper) == len(sample_price_data)
        
        # Upper should be >= middle >= lower (where not NaN)
        valid_idx = ~pd.isna(upper)
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()
    
    def test_calculate_rsi(self, tech_collector, sample_price_data):
        """Test RSI (Relative Strength Index) calculation"""
        period = 14
        rsi_values = tech_collector._calculate_rsi(sample_price_data['close'], period)
        
        assert isinstance(rsi_values, pd.Series)
        assert len(rsi_values) == len(sample_price_data)
        
        # RSI should be between 0 and 100
        valid_rsi = rsi_values.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_calculate_macd(self, tech_collector, sample_price_data):
        """Test MACD calculation"""
        fast = 12
        slow = 26
        signal = 9
        
        macd_line, signal_line, histogram = tech_collector._calculate_macd(
            sample_price_data['close'], fast, slow, signal
        )
        
        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)
        assert len(macd_line) == len(sample_price_data)
        
        # Histogram should equal MACD - Signal (where both exist)
        valid_idx = ~(pd.isna(macd_line) | pd.isna(signal_line))
        np.testing.assert_array_almost_equal(
            histogram[valid_idx], 
            macd_line[valid_idx] - signal_line[valid_idx],
            decimal=5
        )
    
    def test_calculate_volatility(self, tech_collector, sample_price_data):
        """Test volatility calculation"""
        period = 20
        volatility = tech_collector._calculate_volatility(
            sample_price_data['close'], period
        )
        
        assert isinstance(volatility, pd.Series)
        assert len(volatility) == len(sample_price_data)
        # Volatility should be non-negative
        valid_vol = volatility.dropna()
        assert (valid_vol >= 0).all()
    
    def test_calculate_volume_indicators(self, tech_collector, sample_price_data):
        """Test volume-based indicators"""
        vma = tech_collector._calculate_volume_moving_average(
            sample_price_data['volume'], period=20
        )
        
        assert isinstance(vma, pd.Series)
        assert len(vma) == len(sample_price_data)
        
        # Volume indicators should be non-negative
        valid_vma = vma.dropna()
        assert (valid_vma >= 0).all()
    
    @pytest.mark.asyncio
    async def test_get_pending_calculations(self, tech_collector, mock_database):
        """Test retrieving pending price records for calculation"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            ('BTC', datetime(2024, 1, 1)),
            ('ETH', datetime(2024, 1, 1)),
            ('BTC', datetime(2024, 1, 2))
        ]
        
        pending = await tech_collector._get_pending_calculations()
        
        assert isinstance(pending, list)
        assert len(pending) == 3
        mock_cursor.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_historical_price_data(self, tech_collector, mock_database):
        """Test retrieving historical price data for calculations"""
        mock_conn, mock_cursor = mock_database
        
        # Mock historical price data
        historical_data = [
            (datetime(2024, 1, 1), 45000.0, 46000.0, 44000.0, 45500.0, 1000000.0),
            (datetime(2024, 1, 2), 45500.0, 47000.0, 45000.0, 46500.0, 1200000.0),
            (datetime(2024, 1, 3), 46500.0, 47500.0, 46000.0, 47000.0, 900000.0)
        ]
        mock_cursor.fetchall.return_value = historical_data
        
        symbol = 'BTC'
        end_date = datetime(2024, 1, 3)
        lookback_periods = 100
        
        df = await tech_collector._get_historical_price_data(
            symbol, end_date, lookback_periods
        )
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'timestamp' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
    
    @pytest.mark.asyncio
    async def test_calculate_all_indicators(self, tech_collector, sample_price_data):
        """Test calculating all technical indicators for price data"""
        indicators = tech_collector._calculate_all_indicators(sample_price_data)
        
        assert isinstance(indicators, dict)
        
        # Check required indicators exist
        assert 'sma_20' in indicators
        assert 'ema_12' in indicators
        assert 'rsi_14' in indicators
        assert 'bollinger_upper' in indicators
        assert 'bollinger_middle' in indicators
        assert 'bollinger_lower' in indicators
        assert 'macd_line' in indicators
        assert 'macd_signal' in indicators
        assert 'macd_histogram' in indicators
        assert 'volatility_20' in indicators
        
        # All indicators should be same length as input data
        for indicator_name, values in indicators.items():
            assert len(values) == len(sample_price_data)
    
    @pytest.mark.asyncio
    async def test_store_technical_indicators(self, tech_collector, mock_database):
        """Test storing calculated indicators to database"""
        mock_conn, mock_cursor = mock_database
        
        symbol = 'BTC'
        timestamp = datetime(2024, 1, 1)
        indicators = {
            'sma_20': 45000.0,
            'ema_12': 45100.0,
            'rsi_14': 65.5,
            'bollinger_upper': 47000.0,
            'bollinger_middle': 45000.0,
            'bollinger_lower': 43000.0,
            'macd_line': 150.0,
            'macd_signal': 120.0,
            'macd_histogram': 30.0,
            'volatility_20': 0.025
        }
        
        await tech_collector._store_technical_indicators(symbol, timestamp, indicators)
        
        # Should call database insert/update
        assert mock_cursor.execute.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_process_single_calculation(self, tech_collector, mock_database):
        """Test processing calculation for single symbol/timestamp"""
        mock_conn, mock_cursor = mock_database
        
        # Mock historical data retrieval
        with patch.object(tech_collector, '_get_historical_price_data') as mock_history:
            with patch.object(tech_collector, '_store_technical_indicators') as mock_store:
                
                # Setup mock data
                sample_df = pd.DataFrame({
                    'timestamp': pd.date_range('2024-01-01', periods=50, freq='H'),
                    'open': np.random.uniform(40000, 50000, 50),
                    'high': np.random.uniform(50000, 55000, 50),
                    'low': np.random.uniform(35000, 40000, 50),
                    'close': np.random.uniform(40000, 50000, 50),
                    'volume': np.random.uniform(1000000, 5000000, 50)
                })
                mock_history.return_value = sample_df
                
                result = await tech_collector._process_single_calculation(
                    'BTC', datetime(2024, 1, 1)
                )
                
                assert result == True
                mock_history.assert_called_once()
                mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_data(self, tech_collector):
        """Test main data collection method"""
        with patch.object(tech_collector, '_get_pending_calculations', return_value=[
            ('BTC', datetime(2024, 1, 1)),
            ('ETH', datetime(2024, 1, 1))
        ]) as mock_pending:
            with patch.object(tech_collector, '_process_single_calculation', return_value=True) as mock_process:
                
                result = await tech_collector.collect_data()
                
                assert result == 2
                mock_pending.assert_called_once()
                assert mock_process.call_count == 2
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self, tech_collector):
        """Test parallel processing of calculations"""
        # Test with multiple pending calculations
        pending_calculations = [
            ('BTC', datetime(2024, 1, 1)),
            ('ETH', datetime(2024, 1, 1)),
            ('ADA', datetime(2024, 1, 1)),
            ('SOL', datetime(2024, 1, 1))
        ]
        
        with patch.object(tech_collector, '_get_pending_calculations', return_value=pending_calculations):
            with patch.object(tech_collector, '_process_single_calculation', return_value=True) as mock_process:
                
                result = await tech_collector.collect_data()
                
                assert result == 4
                assert mock_process.call_count == 4
    
    @pytest.mark.asyncio
    async def test_backfill_data(self, tech_collector):
        """Test backfill functionality for missing calculations"""
        missing_periods = [
            {
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 1, 2),
                "symbol": "BTC"
            }
        ]
        
        with patch.object(tech_collector, '_process_single_calculation', return_value=True) as mock_process:
            with patch.object(tech_collector, 'get_database_connection') as mock_db:
                mock_cursor = Mock()
                mock_cursor.fetchall.return_value = [
                    ('BTC', datetime(2024, 1, 1)),
                    ('BTC', datetime(2024, 1, 2))
                ]
                mock_db.return_value.__enter__.return_value.cursor.return_value = mock_cursor
                
                result = await tech_collector.backfill_data(missing_periods)
                
                assert result >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_missing_data(self, tech_collector, mock_database):
        """Test analysis of missing technical indicators"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            (datetime(2024, 1, 1).date(), 'BTC', 100, 20),  # 20 missing
            (datetime(2024, 1, 2).date(), 'ETH', 80, 15)    # 15 missing
        ]
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        missing_periods = await tech_collector._analyze_missing_data(start_date, end_date)
        
        assert isinstance(missing_periods, list)
        assert len(missing_periods) == 2
        for period in missing_periods:
            assert "missing_technical" in period
            assert period["missing_technical"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_data_quality_report(self, tech_collector, mock_database):
        """Test data quality report generation"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.side_effect = [
            (1000,),  # total_price_records
            (800,),   # calculated_indicators
            (50,)     # invalid_calculations
        ]
        
        report = await tech_collector._generate_data_quality_report()
        
        assert report.total_records == 1000
        assert report.valid_records == 750  # 800 - 50
        assert report.invalid_records == 250  # 1000 - 750
        assert 0 <= report.data_quality_score <= 100

class TestTechnicalIndicatorMath:
    """Test mathematical correctness of technical indicators"""
    
    def test_sma_mathematical_correctness(self):
        """Test SMA calculation mathematical correctness"""
        # Simple test case with known values
        prices = pd.Series([10, 12, 14, 16, 18])
        period = 3
        
        collector = EnhancedTechnicalCalculator()
        sma = collector._calculate_sma(prices, period)
        
        # Manual calculation for period 3
        expected_sma_3 = (10 + 12 + 14) / 3  # 12
        expected_sma_4 = (12 + 14 + 16) / 3  # 14
        expected_sma_5 = (14 + 16 + 18) / 3  # 16
        
        assert abs(sma.iloc[2] - expected_sma_3) < 0.001
        assert abs(sma.iloc[3] - expected_sma_4) < 0.001
        assert abs(sma.iloc[4] - expected_sma_5) < 0.001
    
    def test_rsi_boundary_conditions(self):
        """Test RSI boundary conditions"""
        collector = EnhancedTechnicalCalculator()
        
        # All prices increasing (should approach 100)
        increasing_prices = pd.Series(range(1, 101))  # 1 to 100
        rsi_up = collector._calculate_rsi(increasing_prices, 14)
        
        # All prices decreasing (should approach 0)
        decreasing_prices = pd.Series(range(100, 0, -1))  # 100 to 1
        rsi_down = collector._calculate_rsi(decreasing_prices, 14)
        
        # RSI should be in valid range
        valid_rsi_up = rsi_up.dropna()
        valid_rsi_down = rsi_down.dropna()
        
        assert (valid_rsi_up >= 0).all() and (valid_rsi_up <= 100).all()
        assert (valid_rsi_down >= 0).all() and (valid_rsi_down <= 100).all()
    
    def test_bollinger_bands_properties(self):
        """Test Bollinger Bands mathematical properties"""
        collector = EnhancedTechnicalCalculator()
        
        # Create sample data
        np.random.seed(42)  # For reproducible results
        prices = pd.Series(np.random.normal(100, 10, 100))  # Normal distribution
        
        upper, middle, lower = collector._calculate_bollinger_bands(prices, 20, 2)
        
        # Middle band should equal SMA
        sma = collector._calculate_sma(prices, 20)
        valid_idx = ~pd.isna(middle)
        pd.testing.assert_series_equal(middle[valid_idx], sma[valid_idx])

class TestPerformanceOptimizations:
    """Test performance optimizations and edge cases"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        collector = EnhancedTechnicalCalculator()
        
        # Large dataset
        large_df = pd.DataFrame({
            'timestamp': pd.date_range('2020-01-01', periods=10000, freq='H'),
            'open': np.random.uniform(40000, 50000, 10000),
            'high': np.random.uniform(50000, 55000, 10000),
            'low': np.random.uniform(35000, 40000, 10000),
            'close': np.random.uniform(40000, 50000, 10000),
            'volume': np.random.uniform(1000000, 5000000, 10000)
        })
        
        # Should complete without memory issues
        indicators = collector._calculate_all_indicators(large_df)
        
        assert isinstance(indicators, dict)
        assert len(indicators) > 0
    
    def test_edge_case_insufficient_data(self):
        """Test edge case with insufficient data"""
        collector = EnhancedTechnicalCalculator()
        
        # Very small dataset
        small_df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
            'close': [100, 101, 102, 103, 104],
            'volume': [1000, 1100, 900, 1200, 1050]
        })
        
        # Should handle gracefully without errors
        indicators = collector._calculate_all_indicators(small_df)
        
        assert isinstance(indicators, dict)
        # Most indicators should be NaN due to insufficient data
        for indicator_name, values in indicators.items():
            assert isinstance(values, (pd.Series, type(None)))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])