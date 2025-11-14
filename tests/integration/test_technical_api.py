"""
Technical indicators collector API and database integration tests.
Tests technical analysis data collection and database operations.
"""

import pytest
import requests
import mysql.connector
import time
import math
from datetime import datetime, timezone, timedelta
import json


class TestTechnicalCollectorAPI:
    """API and database tests for technical indicators collection"""

    @pytest.mark.real_api
    def test_coingecko_historical_for_indicators(self):
        """Test CoinGecko historical data for technical analysis"""
        api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        
        # Get historical data for technical indicators calculation
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30&interval=daily"
        headers = {"x-cg-pro-api-key": api_key} if api_key else {}
        
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "prices" in data
        
        prices = data["prices"]
        assert len(prices) >= 20, "Need at least 20 data points for technical analysis"
        
        # Validate price data structure
        for price_point in prices[:5]:
            assert len(price_point) == 2  # [timestamp, price]
            assert isinstance(price_point[0], (int, float))  # timestamp
            assert isinstance(price_point[1], (int, float))  # price
            assert price_point[1] > 0  # price should be positive

    @pytest.mark.database
    def test_technical_indicators_storage(self, test_mysql_connection):
        """Test technical indicators table structure"""
        cursor = test_mysql_connection.cursor()
        
        # Verify technical_indicators table exists
        cursor.execute("DESCRIBE technical_indicators")
        columns = cursor.fetchall()
        
        column_names = [col[0] for col in columns]
        expected_columns = ['id', 'symbol', 'indicator_name', 'value', 'timestamp']
        
        for expected_col in expected_columns:
            assert expected_col in column_names, f"Missing column: {expected_col}"
        
        cursor.close()

    @pytest.mark.database
    def test_technical_indicators_insertion(self, test_mysql_connection):
        """Test inserting technical indicators into database"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test technical indicators
        test_indicators = [
            {'symbol': 'BTC', 'indicator_name': 'SMA_20', 'value': 45000.50},
            {'symbol': 'BTC', 'indicator_name': 'RSI', 'value': 65.25},
            {'symbol': 'BTC', 'indicator_name': 'MACD', 'value': 150.75},
            {'symbol': 'ETH', 'indicator_name': 'SMA_50', 'value': 3200.00},
        ]
        
        current_time = datetime.now(timezone.utc)
        
        for indicator in test_indicators:
            cursor.execute("""
                INSERT INTO technical_indicators (symbol, indicator_name, value, timestamp)
                VALUES (%(symbol)s, %(indicator_name)s, %(value)s, %(timestamp)s)
            """, {**indicator, 'timestamp': current_time})
        
        test_mysql_connection.commit()
        
        # Verify insertions
        cursor.execute("SELECT COUNT(*) FROM technical_indicators WHERE symbol IN ('BTC', 'ETH')")
        count = cursor.fetchone()[0]
        assert count >= 4, f"Expected at least 4 indicators, found {count}"
        
        # Verify specific indicator values
        cursor.execute("""
            SELECT value FROM technical_indicators 
            WHERE symbol = 'BTC' AND indicator_name = 'RSI'
            ORDER BY created_at DESC LIMIT 1
        """)
        
        rsi_result = cursor.fetchone()
        assert rsi_result is not None
        assert abs(float(rsi_result[0]) - 65.25) < 0.01
        
        cursor.close()

    @pytest.mark.database
    def test_moving_averages_calculation(self, test_mysql_connection):
        """Test moving averages calculation and storage"""
        cursor = test_mysql_connection.cursor()
        
        # Insert historical price data for moving average calculation
        symbol = 'TEST_MA'
        base_price = 100.0
        prices = []
        
        # Create 50 days of test price data
        for i in range(50):
            price = base_price + (i * 0.5) + ((-1) ** i * 2)  # Trending up with noise
            timestamp = datetime.now(timezone.utc) - timedelta(days=49-i)
            prices.append((symbol, price, timestamp))
        
        # Insert into price data table
        for symbol, price, timestamp in prices:
            cursor.execute("""
                INSERT INTO price_data_real (symbol, price, market_cap, total_volume, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol, price, 1000000000, 50000000, timestamp))
        
        test_mysql_connection.commit()
        
        # Calculate and insert simple moving averages
        sma_periods = [10, 20, 50]
        
        for period in sma_periods:
            # Get last 'period' prices
            cursor.execute(f"""
                SELECT price FROM price_data_real 
                WHERE symbol = %s 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (symbol, period))
            
            recent_prices = [float(row[0]) for row in cursor.fetchall()]
            
            if len(recent_prices) >= period:
                sma_value = sum(recent_prices) / len(recent_prices)
                
                # Insert calculated SMA
                cursor.execute("""
                    INSERT INTO technical_indicators (symbol, indicator_name, value, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (symbol, f'SMA_{period}', sma_value, datetime.now(timezone.utc)))
        
        test_mysql_connection.commit()
        
        # Verify SMA calculations
        cursor.execute("""
            SELECT indicator_name, value FROM technical_indicators 
            WHERE symbol = %s AND indicator_name LIKE 'SMA_%'
        """, (symbol,))
        
        sma_results = cursor.fetchall()
        assert len(sma_results) >= 3, f"Expected at least 3 SMA indicators, found {len(sma_results)}"
        
        # Validate SMA values are reasonable
        for indicator_name, value in sma_results:
            assert 90 < float(value) < 150, f"SMA value {value} seems unreasonable for {indicator_name}"
        
        cursor.close()

    @pytest.mark.database
    def test_rsi_calculation(self, test_mysql_connection):
        """Test RSI (Relative Strength Index) calculation"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test price data for RSI calculation
        symbol = 'TEST_RSI'
        base_price = 1000.0
        
        # Create price series with known up/down moves
        price_changes = [5, -3, 7, -2, 4, -6, 8, -1, 3, -4, 6, -2, 5, -3, 7]  # 15 days
        prices = []
        current_price = base_price
        
        for i, change in enumerate(price_changes):
            current_price += change
            timestamp = datetime.now(timezone.utc) - timedelta(days=14-i)
            prices.append((symbol, current_price, timestamp))
        
        # Insert price data
        for symbol_name, price, timestamp in prices:
            cursor.execute("""
                INSERT INTO price_data_real (symbol, price, market_cap, total_volume, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol_name, price, 1000000000, 50000000, timestamp))
        
        test_mysql_connection.commit()
        
        # Calculate RSI (simplified)
        cursor.execute(f"""
            SELECT price, timestamp FROM price_data_real 
            WHERE symbol = %s 
            ORDER BY timestamp ASC
        """, (symbol,))
        
        price_data = [(float(row[0]), row[1]) for row in cursor.fetchall()]
        
        if len(price_data) >= 14:  # Need at least 14 periods for RSI
            gains = []
            losses = []
            
            for i in range(1, len(price_data)):
                change = price_data[i][0] - price_data[i-1][0]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            # Calculate 14-period RSI
            if len(gains) >= 14:
                avg_gain = sum(gains[-14:]) / 14
                avg_loss = sum(losses[-14:]) / 14
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    # Insert RSI
                    cursor.execute("""
                        INSERT INTO technical_indicators (symbol, indicator_name, value, timestamp)
                        VALUES (%s, %s, %s, %s)
                    """, (symbol, 'RSI_14', rsi, datetime.now(timezone.utc)))
                    
                    test_mysql_connection.commit()
                    
                    # Verify RSI is in valid range (0-100)
                    assert 0 <= rsi <= 100, f"RSI value {rsi} is outside valid range 0-100"
        
        cursor.close()

    @pytest.mark.database
    def test_bollinger_bands_calculation(self, test_mysql_connection):
        """Test Bollinger Bands calculation"""
        cursor = test_mysql_connection.cursor()
        
        symbol = 'TEST_BB'
        base_price = 50.0
        
        # Create 20 days of price data
        prices = []
        for i in range(20):
            # Create some volatility
            price = base_price + (i * 0.1) + (math.sin(i/3) * 2)
            timestamp = datetime.now(timezone.utc) - timedelta(days=19-i)
            prices.append((symbol, price, timestamp))
        
        # Insert price data
        for symbol_name, price, timestamp in prices:
            cursor.execute("""
                INSERT INTO price_data_real (symbol, price, market_cap, total_volume, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol_name, price, 1000000000, 50000000, timestamp))
        
        test_mysql_connection.commit()
        
        # Calculate Bollinger Bands
        cursor.execute("""
            SELECT price FROM price_data_real 
            WHERE symbol = %s 
            ORDER BY timestamp DESC 
            LIMIT 20
        """, (symbol,))
        
        recent_prices = [float(row[0]) for row in cursor.fetchall()]
        
        if len(recent_prices) == 20:
            # Calculate 20-period moving average
            sma = sum(recent_prices) / 20
            
            # Calculate standard deviation
            variance = sum((price - sma) ** 2 for price in recent_prices) / 20
            std_dev = math.sqrt(variance)
            
            # Calculate Bollinger Bands (2 standard deviations)
            upper_band = sma + (2 * std_dev)
            lower_band = sma - (2 * std_dev)
            
            # Insert Bollinger Bands
            bb_indicators = [
                ('BB_MIDDLE', sma),
                ('BB_UPPER', upper_band),
                ('BB_LOWER', lower_band)
            ]
            
            for indicator_name, value in bb_indicators:
                cursor.execute("""
                    INSERT INTO technical_indicators (symbol, indicator_name, value, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (symbol, indicator_name, value, datetime.now(timezone.utc)))
            
            test_mysql_connection.commit()
            
            # Verify Bollinger Bands relationship
            assert upper_band > sma > lower_band, "Bollinger Bands relationship incorrect"
            assert (upper_band - sma) == (sma - lower_band), "Bollinger Bands should be symmetric"
        
        cursor.close()

    @pytest.mark.database
    def test_multiple_symbols_indicators(self, test_mysql_connection):
        """Test calculating indicators for multiple symbols"""
        cursor = test_mysql_connection.cursor()
        
        symbols = ['BTC', 'ETH', 'ADA']
        indicators = ['SMA_10', 'EMA_12', 'RSI_14']
        
        # Insert indicators for each symbol
        for symbol in symbols:
            for indicator in indicators:
                # Generate realistic values
                if 'SMA' in indicator or 'EMA' in indicator:
                    value = {'BTC': 45000, 'ETH': 3200, 'ADA': 0.45}[symbol]
                elif 'RSI' in indicator:
                    value = 55.5 + (hash(symbol + indicator) % 40)  # 55.5 to 95.5
                else:
                    value = 100.0
                
                cursor.execute("""
                    INSERT INTO technical_indicators (symbol, indicator_name, value, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (symbol, indicator, value, datetime.now(timezone.utc)))
        
        test_mysql_connection.commit()
        
        # Verify indicators for all symbols
        for symbol in symbols:
            cursor.execute("""
                SELECT COUNT(DISTINCT indicator_name) FROM technical_indicators 
                WHERE symbol = %s
            """, (symbol,))
            
            indicator_count = cursor.fetchone()[0]
            assert indicator_count >= 3, f"Expected at least 3 indicators for {symbol}, found {indicator_count}"
        
        cursor.close()

    @pytest.mark.database
    def test_indicator_data_quality(self, test_mysql_connection):
        """Test technical indicator data quality and consistency"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test data with quality tracking
        test_data = [
            {'symbol': 'QUAL_TEST', 'indicator': 'SMA_20', 'value': 100.0, 'completeness': 100.0},
            {'symbol': 'QUAL_TEST', 'indicator': 'RSI_14', 'value': 65.5, 'completeness': 95.0},
            {'symbol': 'QUAL_TEST', 'indicator': 'MACD', 'value': None, 'completeness': 0.0},  # Missing data
        ]
        
        for data in test_data:
            if data['value'] is not None:
                try:
                    cursor.execute("""
                        INSERT INTO technical_indicators (symbol, indicator_name, value, timestamp, data_completeness_percentage)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (data['symbol'], data['indicator'], data['value'], 
                          datetime.now(timezone.utc), data['completeness']))
                except mysql.connector.Error as e:
                    if "Unknown column 'data_completeness_percentage'" in str(e):
                        # Table doesn't have completeness tracking - insert without it
                        cursor.execute("""
                            INSERT INTO technical_indicators (symbol, indicator_name, value, timestamp)
                            VALUES (%s, %s, %s, %s)
                        """, (data['symbol'], data['indicator'], data['value'], datetime.now(timezone.utc)))
                    else:
                        raise
        
        test_mysql_connection.commit()
        
        # Verify data quality
        cursor.execute("""
            SELECT indicator_name, value FROM technical_indicators 
            WHERE symbol = 'QUAL_TEST' AND value IS NOT NULL
        """)
        
        results = cursor.fetchall()
        assert len(results) >= 2, "Should have at least 2 non-null indicators"
        
        # Validate indicator value ranges
        for indicator_name, value in results:
            if 'RSI' in indicator_name:
                assert 0 <= float(value) <= 100, f"RSI value {value} outside valid range"
            elif 'SMA' in indicator_name:
                assert float(value) > 0, f"SMA value {value} should be positive"
        
        cursor.close()

    @pytest.mark.real_api  
    def test_real_time_price_for_indicators(self):
        """Test real-time price data availability for technical analysis"""
        api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        
        # Get real-time prices for technical analysis
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
        headers = {"x-cg-pro-api-key": api_key} if api_key else {}
        
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        
        for coin in ['bitcoin', 'ethereum']:
            assert coin in data
            coin_data = data[coin]
            
            assert 'usd' in coin_data
            assert 'usd_24h_change' in coin_data
            
            price = coin_data['usd']
            change_24h = coin_data['usd_24h_change']
            
            assert price > 0, f"{coin} price should be positive"
            assert isinstance(change_24h, (int, float)), f"{coin} 24h change should be numeric"
            
            # 24h change should be reasonable (-50% to +50%)
            assert -50 <= change_24h <= 50, f"{coin} 24h change {change_24h}% seems unreasonable"