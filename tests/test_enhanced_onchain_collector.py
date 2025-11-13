"""
Unit tests for Enhanced Onchain Data Collector
"""

import pytest
import asyncio
import mysql.connector
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, date, timedelta
import json
import os
import sys
import aiohttp

# Add the project root to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the collector - need to handle the hyphenated directory name
import importlib.util
collector_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'onchain-collection', 'enhanced_onchain_collector.py')
spec = importlib.util.spec_from_file_location("enhanced_onchain_collector", collector_path)
onchain_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(onchain_module)
EnhancedOnchainCollector = onchain_module.EnhancedOnchainCollector


class TestEnhancedOnchainCollector:
    """Test Enhanced Onchain Data Collector functionality"""

    @pytest.fixture
    def onchain_collector(self):
        """Create a test instance of EnhancedOnchainCollector"""
        with patch.dict(os.environ, {
            'MYSQL_HOST': 'localhost',
            'MYSQL_USER': 'test_user',
            'MYSQL_PASSWORD': 'test_password',
            'MYSQL_DATABASE': 'test_crypto_prices'
        }):
            return EnhancedOnchainCollector()

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'symbol': 'BTC'}, 
            {'symbol': 'ETH'}, 
            {'symbol': 'ADA'}
        ]
        mock_cursor.fetchone.return_value = [1]
        return mock_conn, mock_cursor

    @pytest.fixture
    def sample_onchain_data(self):
        """Sample onchain data for testing"""
        return [
            {
                'symbol': 'BTC',
                'coin_id': 'bitcoin',
                'timestamp_iso': datetime.now(),
                'active_addresses': 1000000,
                'transaction_count': 300000,
                'transaction_volume': 50000.5,
                'circulating_supply': 19500000.0,
                'market_cap': 850000000000.0,
                'data_source': 'coingecko'
            },
            {
                'symbol': 'ETH',
                'coin_id': 'ethereum',
                'timestamp_iso': datetime.now(),
                'active_addresses': 750000,
                'transaction_count': 1200000,
                'transaction_volume': 25000.2,
                'circulating_supply': 120000000.0,
                'market_cap': 300000000000.0,
                'data_source': 'coingecko'
            }
        ]

    def test_collector_initialization(self, onchain_collector):
        """Test that collector initializes with correct configuration"""
        assert onchain_collector.db_config['host'] == 'localhost'
        assert onchain_collector.db_config['user'] == 'test_user'
        assert onchain_collector.db_config['database'] == 'test_crypto_prices'
        assert 'messari' in onchain_collector.api_endpoints
        assert 'coingecko' in onchain_collector.api_endpoints
        assert onchain_collector.min_delay == 1.0

    @patch('services.onchain_collection.enhanced_onchain_collector.mysql.connector.connect')
    def test_get_db_connection(self, mock_connect, onchain_collector):
        """Test database connection creation"""
        mock_connect.return_value = Mock()
        
        connection = onchain_collector.get_db_connection()
        
        mock_connect.assert_called_once_with(**onchain_collector.db_config)
        assert connection is not None

    @patch('services.onchain_collection.enhanced_onchain_collector.mysql.connector.connect')
    def test_get_symbols_fallback(self, mock_connect, onchain_collector, mock_db_connection):
        """Test getting symbols from database fallback"""
        mock_conn, mock_cursor = mock_db_connection
        mock_connect.return_value = mock_conn
        
        symbols = onchain_collector.get_symbols()
        
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert all(isinstance(symbol, str) for symbol in symbols)

    @patch('services.onchain_collection.enhanced_onchain_collector.mysql.connector.connect')
    def test_get_symbols_error_handling(self, mock_connect, onchain_collector):
        """Test error handling when getting symbols"""
        mock_connect.side_effect = mysql.connector.Error("Database error")
        
        symbols = onchain_collector.get_symbols()
        
        # Should return hardcoded fallback symbols
        assert symbols == ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']

    @patch('services.onchain_collection.enhanced_onchain_collector.mysql.connector.connect')
    def test_ensure_table_exists(self, mock_connect, onchain_collector, mock_db_connection):
        """Test table creation"""
        mock_conn, mock_cursor = mock_db_connection
        mock_connect.return_value = mock_conn
        
        onchain_collector.ensure_table_exists()
        
        # Verify that cursor.execute was called with CREATE TABLE statement
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0][0]
        assert 'CREATE TABLE IF NOT EXISTS' in call_args
        assert 'onchain_data' in call_args

    @pytest.mark.asyncio
    async def test_rate_limiting(self, onchain_collector):
        """Test API rate limiting functionality"""
        endpoint = 'test_endpoint'
        
        # Test rate limiting delay
        await onchain_collector.rate_limit(endpoint)
        
        # Should track the last call time
        assert endpoint in onchain_collector.last_api_call



    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_coingecko_data_success(self, mock_get, onchain_collector):
        """Test successful CoinGecko data fetching"""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'id': 'bitcoin',
            'symbol': 'btc',
            'market_data': {
                'circulating_supply': 19500000.0,
                'market_cap': {'usd': 850000000000.0}
            },
            'developer_data': {
                'commit_count_4_weeks': 50
            }
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with aiohttp.ClientSession() as session:
            result = await onchain_collector.get_coingecko_data(session, 'bitcoin')
            
            assert result is not None
            assert 'id' in result

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_coingecko_data_api_error(self, mock_get, onchain_collector):
        """Test API error handling"""
        # Mock API error response
        mock_response = AsyncMock()
        mock_response.status = 429  # Rate limited
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with aiohttp.ClientSession() as session:
            result = await onchain_collector.get_coingecko_data(session, 'bitcoin')
            
            # Should handle error gracefully
            assert result is None

    @patch('services.onchain_collection.enhanced_onchain_collector.mysql.connector.connect')
    def test_store_onchain_data(self, mock_connect, onchain_collector, mock_db_connection, sample_onchain_data):
        """Test storing onchain data in database"""
        mock_conn, mock_cursor = mock_db_connection
        mock_connect.return_value = mock_conn
        
        target_date = date.today()
        
        result = onchain_collector.store_onchain_data(sample_onchain_data, target_date)
        
        # Verify database operations
        assert mock_cursor.execute.called
        assert mock_conn.commit.called
        assert result['success'] is True

    @patch('services.onchain_collection.enhanced_onchain_collector.mysql.connector.connect')
    def test_store_onchain_data_error_handling(self, mock_connect, onchain_collector):
        """Test error handling during data storage"""
        mock_connect.side_effect = mysql.connector.Error("Database error")
        
        result = onchain_collector.store_onchain_data({}, date.today())
        
        assert result['success'] is False
        assert 'error' in result



    @pytest.mark.asyncio
    async def test_run_backfill_integration(self, onchain_collector):
        """Test backfill functionality"""
        start_date = date.today() - timedelta(days=2)
        end_date = date.today() - timedelta(days=1)
        
        with patch.object(onchain_collector, 'get_symbols', return_value=['BTC']), \
             patch.object(onchain_collector, 'ensure_table_exists'), \
             patch.object(onchain_collector, 'fetch_onchain_data', return_value={'BTC': {'active_addresses': 1000}}), \
             patch.object(onchain_collector, 'store_onchain_data', return_value={'success': True, 'records_stored': 1}):
            
            result = await onchain_collector.run_backfill(start_date, end_date)
            
            assert result['success'] is True
            assert result['dates_processed'] == 2







# Integration test that can be run separately
class TestOnchainCollectorIntegration:
    """Integration tests requiring database connection"""
    
    @pytest.mark.integration
    def test_real_database_connection(self):
        """Test real database connection (requires test database)"""
        # Only run if TEST_DATABASE environment variable is set
        if not os.getenv('TEST_DATABASE'):
            pytest.skip("Integration test requires TEST_DATABASE environment variable")
        
        collector = EnhancedOnchainCollector()
        
        try:
            conn = collector.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            conn.close()
        except mysql.connector.Error as e:
            pytest.fail(f"Database connection failed: {e}")

    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test real API call (requires internet connection)"""
        if not os.getenv('TEST_API_CALLS'):
            pytest.skip("API test requires TEST_API_CALLS environment variable")
            
        collector = EnhancedOnchainCollector()
        
        # Test with a single symbol to avoid rate limiting
        symbols = ['BTC']
        target_date = date.today() - timedelta(days=1)
        
        result = await collector.fetch_onchain_data(symbols, target_date)
        
        assert isinstance(result, dict)
        # Don't assert specific data since APIs can fail or return different structures


if __name__ == "__main__":
    # Run basic unit tests
    pytest.main([__file__, "-v"])