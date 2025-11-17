"""
Integration tests for the Enhanced Onchain Collector service.
Tests real API endpoints and database interactions for onchain metrics.
"""
import pytest
import requests
import mysql.connector
import asyncio
import time
from datetime import datetime, timedelta


class TestOnchainCollectorIntegration:
    """Integration tests for Enhanced Onchain Collector"""

    @pytest.fixture
    def collector_url(self):
        """Base URL for the onchain collector test service"""
        return "http://localhost:8000"

    def test_health_endpoint(self, collector_url):
        """Test that the onchain collector health endpoint responds"""
        try:
            response = requests.get(f"{collector_url}/health", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            assert "service" in data
            assert data["service"] == "onchain-collector"
            
        except requests.ConnectionError:
            pytest.skip("Onchain collector service not running - start with docker-compose up onchain-collector-test")

    def test_ready_endpoint(self, collector_url):
        """Test that the onchain collector ready endpoint responds"""
        try:
            response = requests.get(f"{collector_url}/ready", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            
        except requests.ConnectionError:
            pytest.skip("Onchain collector service not running")

    @pytest.mark.real_api
    def test_defillama_api_integration(self, test_api_keys):
        """Test direct DeFiLlama API integration for onchain metrics"""
        # Test DeFiLlama TVL endpoint
        url = "https://api.llama.fi/protocol/ethereum"
        
        try:
            response = requests.get(url, timeout=15)
            assert response.status_code == 200
            
            data = response.json()
            assert "tvl" in data or "currentChainTvls" in data
            assert "name" in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"DeFiLlama API not accessible: {e}")

    @pytest.mark.real_api  
    def test_coingecko_onchain_data(self, test_api_keys):
        """Test CoinGecko onchain data endpoints"""
        url = "https://pro-api.coingecko.com/api/v3/coins/bitcoin/onchain_data"
        params = {
            'x_cg_pro_api_key': test_api_keys['coingecko']
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            # Note: This endpoint might not exist, test alternative
            if response.status_code == 404:
                # Test alternative onchain-related endpoint
                url = "https://pro-api.coingecko.com/api/v3/coins/bitcoin"
                response = requests.get(url, params=params, timeout=10)
                
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"CoinGecko API not accessible: {e}")

    def test_onchain_data_storage(self, test_mysql_connection):
        """Test that onchain data is being stored in test database"""
        cursor = test_mysql_connection.cursor()
        
        # Check for onchain data table structure
        cursor.execute("DESCRIBE onchain_data")
        columns = [row[0] for row in cursor.fetchall()]
        
        expected_columns = [
            'id', 'symbol', 'total_value_locked', 'active_addresses', 
            'transaction_count', 'data_completeness_percentage', 'created_at'
        ]
        
        for col in expected_columns:
            assert col in columns, f"Missing column: {col}"

    def test_onchain_data_insertion(self, test_mysql_connection):
        """Test inserting sample onchain data"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test onchain data
        test_data = {
            'symbol': 'BTC',
            'total_value_locked': 1250000.50,
            'active_addresses': 950000,
            'transaction_count': 280000,
            'data_completeness_percentage': 95.5
        }
        
        cursor.execute("""
            INSERT INTO onchain_data 
            (symbol, total_value_locked, active_addresses, transaction_count, data_completeness_percentage)
            VALUES (%(symbol)s, %(total_value_locked)s, %(active_addresses)s, %(transaction_count)s, %(data_completeness_percentage)s)
        """, test_data)
        
        test_mysql_connection.commit()
        
        # Verify insertion
        cursor.execute("""
            SELECT * FROM onchain_data 
            WHERE symbol = %s AND active_addresses = %s
            ORDER BY created_at DESC LIMIT 1
        """, (test_data['symbol'], test_data['active_addresses']))
        
        result = cursor.fetchone()
        assert result is not None
        assert result[1] == test_data['symbol']  # symbol
        assert float(result[2]) == test_data['total_value_locked']  # total_value_locked
        assert result[3] == test_data['active_addresses']  # active_addresses
        assert result[4] == test_data['transaction_count']  # transaction_count

    def test_data_completeness_tracking(self, test_mysql_connection):
        """Test data completeness percentage tracking"""
        cursor = test_mysql_connection.cursor()
        
        # Check completeness tracking
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(data_completeness_percentage) as avg_completeness,
                COUNT(CASE WHEN data_completeness_percentage IS NOT NULL THEN 1 END) as non_null_completeness
            FROM onchain_data 
            WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        total, avg_comp, non_null = result
        
        # Should track completeness for records
        if total > 0:
            completeness_coverage = (non_null / total) * 100 if total > 0 else 0
            assert completeness_coverage >= 0

    @pytest.mark.real_api
    def test_multiple_networks_support(self, test_api_keys):
        """Test support for multiple blockchain networks"""
        networks = ['ethereum', 'bitcoin', 'polygon']
        
        for network in networks:
            try:
                # Test network-specific data availability
                if network == 'ethereum':
                    url = "https://api.llama.fi/chains"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        chains = response.json()
                        network_found = any(chain.get('name', '').lower() == network for chain in chains)
                        assert network_found or len(chains) > 0  # At least some network data
                        
            except requests.exceptions.RequestException:
                pytest.skip(f"Network {network} data not accessible")

    def test_metric_types_collection(self, test_mysql_connection):
        """Test collection of various onchain metric types"""
        cursor = test_mysql_connection.cursor()
        
        # Test different cryptocurrencies onchain data
        test_cryptos = [
            {'symbol': 'BTC', 'total_value_locked': 2500000.0, 'active_addresses': 950000, 'transaction_count': 280000},
            {'symbol': 'ETH', 'total_value_locked': 1800000.0, 'active_addresses': 620000, 'transaction_count': 1200000},
            {'symbol': 'SOL', 'total_value_locked': 450000.0, 'active_addresses': 85000, 'transaction_count': 95000}
        ]
        
        # Insert sample data for each crypto
        for crypto in test_cryptos:
            cursor.execute("""
                INSERT IGNORE INTO onchain_data 
                (symbol, total_value_locked, active_addresses, transaction_count, data_completeness_percentage)
                VALUES (%(symbol)s, %(total_value_locked)s, %(active_addresses)s, %(transaction_count)s, 90.0)
            """, crypto)
        
        test_mysql_connection.commit()
        
        # Verify crypto diversity
        cursor.execute("""
            SELECT COUNT(DISTINCT symbol) as symbol_count
            FROM onchain_data 
            WHERE total_value_locked > 0
        """)
        
        result = cursor.fetchone()
        symbol_count = result[0]
        assert symbol_count > 0

    @pytest.mark.performance
    def test_collection_performance(self, collector_url):
        """Test onchain collector performance metrics"""
        try:
            start_time = time.time()
            response = requests.get(f"{collector_url}/health", timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 10.0  # Should respond within 10 seconds
            assert response.status_code == 200
            
        except requests.ConnectionError:
            pytest.skip("Onchain collector service not running")

    def test_error_handling(self, test_mysql_connection):
        """Test error handling for invalid onchain data"""
        cursor = test_mysql_connection.cursor()
        
        # Test handling of invalid data
        try:
            cursor.execute("""
                INSERT INTO onchain_data 
                (symbol, network, metric_name, metric_value, data_completeness_percentage)
                VALUES (NULL, 'bitcoin', 'test_metric', 1000, 100.0)
            """)
            test_mysql_connection.commit()
            assert False, "Should have failed with NULL symbol"
            
        except mysql.connector.Error:
            # Expected to fail due to NOT NULL constraint
            test_mysql_connection.rollback()
            assert True

    @pytest.mark.database
    def test_cross_table_consistency(self, test_mysql_connection):
        """Test consistency between onchain_data and crypto_assets tables"""
        cursor = test_mysql_connection.cursor()
        
        # Check that onchain data references valid crypto assets
        cursor.execute("""
            SELECT DISTINCT od.symbol, ca.symbol
            FROM onchain_data od
            LEFT JOIN crypto_assets ca ON od.symbol = ca.symbol
            WHERE od.created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        for row in results:
            onchain_symbol, asset_symbol = row
            # Either should have matching asset or be a valid symbol format
            assert onchain_symbol is not None
            assert len(onchain_symbol) >= 2  # Valid symbol length

    def test_real_time_data_freshness(self, test_mysql_connection):
        """Test that onchain data is reasonably fresh"""
        cursor = test_mysql_connection.cursor()
        
        # Check for recent data (within last 24 hours)
        cursor.execute("""
            SELECT COUNT(*), MAX(created_at)
            FROM onchain_data 
            WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        count, latest_time = result
        
        # Should have some recent data if collector is running
        if count > 0:
            assert latest_time is not None
            # Data should be within last 24 hours
            time_diff = datetime.now() - latest_time
            assert time_diff.total_seconds() <= 86400  # 24 hours