"""
Simple price collector API and database integration tests.
Tests price data collection APIs and database operations without service endpoints.
"""

import pytest
import requests
import mysql.connector
import time
from datetime import datetime, timezone


class TestPriceCollectorAPI:
    """API and database tests for price data collection"""

    @pytest.mark.real_api
    def test_coingecko_price_api_integration(self):
        """Test CoinGecko price API integration"""
        # Test CoinGecko API for price data
        api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        
        # Test simple price endpoint
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        headers = {"x-cg-pro-api-key": api_key} if api_key else {}
        
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "bitcoin" in data
        assert "ethereum" in data
        assert "usd" in data["bitcoin"]
        assert "usd" in data["ethereum"]
        
        # Validate price data
        btc_price = data["bitcoin"]["usd"]
        eth_price = data["ethereum"]["usd"]
        assert isinstance(btc_price, (int, float))
        assert isinstance(eth_price, (int, float))
        assert btc_price > 0
        assert eth_price > 0

    @pytest.mark.real_api
    def test_coingecko_historical_data(self):
        """Test CoinGecko historical price data API"""
        api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        
        # Test historical price data for Bitcoin
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1"
        headers = {"x-cg-pro-api-key": api_key} if api_key else {}
        
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "prices" in data
        assert "market_caps" in data
        assert "total_volumes" in data
        
        # Validate data structure
        prices = data["prices"]
        assert len(prices) > 0
        assert len(prices[0]) == 2  # [timestamp, price]
        assert isinstance(prices[0][0], (int, float))  # timestamp
        assert isinstance(prices[0][1], (int, float))  # price

    @pytest.mark.database
    def test_price_data_storage(self, test_mysql_connection):
        """Test price data table structure and basic operations"""
        cursor = test_mysql_connection.cursor()
        
        # Verify price_data_real table exists and has correct structure
        cursor.execute("DESCRIBE price_data_real")
        columns = cursor.fetchall()
        
        column_names = [col[0] for col in columns]
        expected_columns = ['id', 'symbol', 'price', 'market_cap', 'volume_24h', 'timestamp']
        
        for expected_col in expected_columns:
            assert expected_col in column_names, f"Missing column: {expected_col}"
        
        cursor.close()

    @pytest.mark.database
    def test_price_data_insertion(self, test_mysql_connection):
        """Test inserting price data into database"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test price data
        test_data = {
            'symbol': 'BTC',
            'price': 45000.50,
            'market_cap': 850000000000,
            'volume_24h': 25000000000,
            'timestamp': datetime.now(timezone.utc)
        }
        
        cursor.execute("""
            INSERT INTO price_data_real (symbol, price, market_cap, volume_24h, timestamp)
            VALUES (%(symbol)s, %(price)s, %(market_cap)s, %(volume_24h)s, %(timestamp)s)
        """, test_data)
        
        test_mysql_connection.commit()
        
        # Verify insertion
        cursor.execute("SELECT * FROM price_data_real WHERE symbol = 'BTC' ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'BTC'  # symbol
        assert abs(result[2] - 45000.50) < 0.01  # price
        assert result[3] == 850000000000  # market_cap
        assert result[4] == 25000000000  # volume_24h
        
        cursor.close()

    @pytest.mark.database
    def test_ohlc_data_storage(self, test_mysql_connection):
        """Test OHLC data table structure"""
        cursor = test_mysql_connection.cursor()
        
        # Verify ohlc_data table exists and has correct structure
        cursor.execute("DESCRIBE ohlc_data")
        columns = cursor.fetchall()
        
        column_names = [col[0] for col in columns]
        expected_columns = ['id', 'symbol', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'timestamp']
        
        for expected_col in expected_columns:
            assert expected_col in column_names, f"Missing column: {expected_col}"
        
        cursor.close()

    @pytest.mark.database
    def test_ohlc_data_insertion(self, test_mysql_connection):
        """Test inserting OHLC data into database"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test OHLC data
        test_data = {
            'symbol': 'ETH',
            'open_price': 3200.00,
            'high_price': 3250.00,
            'low_price': 3180.00,
            'close_price': 3225.50,
            'volume': 150000000,
            'timestamp': datetime.now(timezone.utc)
        }
        
        cursor.execute("""
            INSERT INTO ohlc_data (symbol, open_price, high_price, low_price, close_price, volume, timestamp)
            VALUES (%(symbol)s, %(open_price)s, %(high_price)s, %(low_price)s, %(close_price)s, %(volume)s, %(timestamp)s)
        """, test_data)
        
        test_mysql_connection.commit()
        
        # Verify insertion
        cursor.execute("SELECT * FROM ohlc_data WHERE symbol = 'ETH' ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'ETH'  # symbol
        assert abs(result[2] - 3200.00) < 0.01  # open_price
        assert abs(result[3] - 3250.00) < 0.01  # high_price
        assert abs(result[4] - 3180.00) < 0.01  # low_price
        assert abs(result[5] - 3225.50) < 0.01  # close_price
        
        cursor.close()

    @pytest.mark.database
    def test_multiple_symbols_support(self, test_mysql_connection):
        """Test collecting and storing data for multiple symbols"""
        cursor = test_mysql_connection.cursor()
        
        symbols = ['BTC', 'ETH', 'ADA', 'DOT']
        test_prices = [45000, 3200, 0.85, 25.50]
        
        for symbol, price in zip(symbols, test_prices):
            cursor.execute("""
                INSERT INTO price_data_real (symbol, price, market_cap, volume_24h, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol, price, price * 20000000, price * 500000, datetime.now(timezone.utc)))
        
        test_mysql_connection.commit()
        
        # Verify all symbols were stored
        cursor.execute("SELECT DISTINCT symbol FROM price_data_real WHERE symbol IN ('BTC', 'ETH', 'ADA', 'DOT')")
        results = cursor.fetchall()
        stored_symbols = [row[0] for row in results]
        
        for symbol in symbols:
            assert symbol in stored_symbols, f"Symbol {symbol} not found in database"
        
        cursor.close()

    @pytest.mark.database
    def test_data_quality_tracking(self, test_mysql_connection):
        """Test data quality and completeness tracking"""
        cursor = test_mysql_connection.cursor()
        
        # Insert price data with different completeness levels
        test_cases = [
            {'symbol': 'QUAL1', 'price': 100.0, 'market_cap': 1000000, 'volume_24h': 50000},
            {'symbol': 'QUAL2', 'price': 200.0, 'market_cap': None, 'volume_24h': 75000},
            {'symbol': 'QUAL3', 'price': 300.0, 'market_cap': 3000000, 'volume_24h': None},
        ]
        
        for case in test_cases:
            cursor.execute("""
                INSERT INTO price_data_real (symbol, price, market_cap, volume_24h, timestamp)
                VALUES (%(symbol)s, %(price)s, %(market_cap)s, %(volume_24h)s, %(timestamp)s)
            """, {**case, 'timestamp': datetime.now(timezone.utc)})
        
        test_mysql_connection.commit()
        
        # Calculate completeness metrics
        cursor.execute("""
            SELECT symbol,
                   CASE WHEN price IS NOT NULL THEN 1 ELSE 0 END as has_price,
                   CASE WHEN market_cap IS NOT NULL THEN 1 ELSE 0 END as has_market_cap,
                   CASE WHEN volume_24h IS NOT NULL THEN 1 ELSE 0 END as has_volume
            FROM price_data_real 
            WHERE symbol LIKE 'QUAL%'
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        assert len(results) == 3
        
        # Verify data quality tracking
        for i, result in enumerate(results):
            symbol, has_price, has_market_cap, has_volume = result
            assert has_price == 1  # All should have price
            
            if symbol == 'QUAL1':
                assert has_market_cap == 1 and has_volume == 1
            elif symbol == 'QUAL2':
                assert has_market_cap == 0 and has_volume == 1
            elif symbol == 'QUAL3':
                assert has_market_cap == 1 and has_volume == 0
        
        cursor.close()

    @pytest.mark.real_api
    def test_real_time_data_freshness(self):
        """Test that real-time price data is fresh and recent"""
        api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        
        # Get current price data
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_last_updated_at=true"
        headers = {"x-cg-pro-api-key": api_key} if api_key else {}
        
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        btc_data = data["bitcoin"]
        
        # Check that data includes timestamp
        assert "last_updated_at" in btc_data
        last_updated = btc_data["last_updated_at"]
        
        # Data should be relatively fresh (within last hour)
        current_time = datetime.now(timezone.utc).timestamp()
        time_diff = current_time - last_updated
        
        assert time_diff < 3600, f"Data is too old: {time_diff/60:.1f} minutes"
        assert time_diff >= 0, "Data timestamp is in the future"

    @pytest.mark.database
    def test_cross_table_consistency(self, test_mysql_connection):
        """Test consistency between price tables and crypto_assets"""
        cursor = test_mysql_connection.cursor()
        
        # Ensure we have a crypto asset
        cursor.execute("""
            INSERT IGNORE INTO crypto_assets (symbol, name, market_cap, price)
            VALUES ('PRICE_TEST', 'Price Test Coin', 5000000, 50.0)
        """)
        
        # Insert corresponding price data
        cursor.execute("""
            INSERT INTO price_data_real (symbol, price, market_cap, volume_24h, timestamp)
            VALUES ('PRICE_TEST', 50.25, 5050000, 250000, %s)
        """, (datetime.now(timezone.utc),))
        
        test_mysql_connection.commit()
        
        # Verify cross-table consistency
        cursor.execute("""
            SELECT pd.symbol, pd.price, ca.price as asset_price
            FROM price_data_real pd
            JOIN crypto_assets ca ON pd.symbol = ca.symbol
            WHERE pd.symbol = 'PRICE_TEST'
            ORDER BY pd.created_at DESC
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        assert result is not None, "Failed to find consistent data across tables"
        
        symbol, current_price, asset_price = result
        assert symbol == 'PRICE_TEST'
        
        # Prices should be reasonably close (within 10%)
        price_diff = abs(current_price - asset_price) / asset_price
        assert price_diff < 0.1, f"Price discrepancy too large: {price_diff*100:.1f}%"
        
        cursor.close()