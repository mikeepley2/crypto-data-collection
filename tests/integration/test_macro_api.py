"""
Macro collector API and database integration tests.
Tests macro economic data collection APIs and database operations.
"""

import pytest
import requests
import mysql.connector
import time
from datetime import datetime, timezone


class TestMacroCollectorAPI:
    """API and database tests for macro economic data collection"""

    @pytest.mark.real_api
    def test_fred_api_integration(self):
        """Test FRED (Federal Reserve Economic Data) API integration"""
        api_key = "35478996c5e061d0fc99fc73f5ce348d"
        
        # Test FRED API for unemployment rate
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key={api_key}&file_type=json&limit=10"
        
        response = requests.get(url, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "observations" in data
        
        observations = data["observations"]
        assert len(observations) > 0
        
        # Validate data structure
        obs = observations[0]
        assert "date" in obs
        assert "value" in obs
        assert obs["value"] != "."  # FRED uses "." for missing values

    @pytest.mark.real_api
    def test_fred_gdp_data(self):
        """Test FRED GDP data collection"""
        api_key = "35478996c5e061d0fc99fc73f5ce348d"
        
        # Test GDP data
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key={api_key}&file_type=json&limit=5"
        
        response = requests.get(url, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "observations" in data
        
        observations = data["observations"]
        assert len(observations) > 0
        
        # Validate GDP values
        for obs in observations:
            if obs["value"] != ".":
                gdp_value = float(obs["value"])
                assert gdp_value > 0, "GDP should be positive"

    @pytest.mark.real_api  
    def test_fred_inflation_data(self):
        """Test FRED inflation data (CPI) collection"""
        api_key = "35478996c5e061d0fc99fc73f5ce348d"
        
        # Test Consumer Price Index
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key={api_key}&file_type=json&limit=5"
        
        response = requests.get(url, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "observations" in data
        
        observations = data["observations"]
        assert len(observations) > 0
        
        # Validate CPI values
        for obs in observations:
            if obs["value"] != ".":
                cpi_value = float(obs["value"])
                assert cpi_value > 0, "CPI should be positive"

    @pytest.mark.database
    def test_macro_indicators_storage(self, test_mysql_connection):
        """Test macro indicators table structure"""
        cursor = test_mysql_connection.cursor()
        
        # Verify macro_indicators table exists and has correct structure
        cursor.execute("DESCRIBE macro_indicators")
        columns = cursor.fetchall()
        
        column_names = [col[0] for col in columns]
        expected_columns = ['id', 'indicator_name', 'value', 'date', 'source']
        
        for expected_col in expected_columns:
            assert expected_col in column_names, f"Missing column: {expected_col}"
        
        cursor.close()

    @pytest.mark.database
    def test_macro_data_insertion(self, test_mysql_connection):
        """Test inserting macro economic data into database"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test macro data
        test_data = {
            'indicator_name': 'GDP',
            'value': 25000.5,
            'date': datetime(2023, 12, 31).date(),
            'source': 'FRED'
        }
        
        cursor.execute("""
            INSERT INTO macro_indicators (indicator_name, value, date, source)
            VALUES (%(indicator_name)s, %(value)s, %(date)s, %(source)s)
        """, test_data)
        
        test_mysql_connection.commit()
        
        # Verify insertion
        cursor.execute("SELECT * FROM macro_indicators WHERE indicator_name = 'GDP' ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'GDP'  # indicator_name
        assert abs(float(result[2]) - 25000.5) < 0.01  # value
        assert result[4] == 'FRED'  # source
        
        cursor.close()

    @pytest.mark.database
    def test_multiple_indicators_support(self, test_mysql_connection):
        """Test storing multiple macro indicators"""
        cursor = test_mysql_connection.cursor()
        
        indicators = [
            {'name': 'UNEMPLOYMENT', 'value': 3.5, 'source': 'FRED'},
            {'name': 'INFLATION', 'value': 2.1, 'source': 'FRED'},
            {'name': 'INTEREST_RATE', 'value': 5.25, 'source': 'FRED'},
        ]
        
        test_date = datetime(2023, 12, 31).date()
        
        for indicator in indicators:
            cursor.execute("""
                INSERT INTO macro_indicators (indicator_name, value, date, source)
                VALUES (%s, %s, %s, %s)
            """, (indicator['name'], indicator['value'], test_date, indicator['source']))
        
        test_mysql_connection.commit()
        
        # Verify all indicators were stored
        cursor.execute("SELECT DISTINCT indicator_name FROM macro_indicators WHERE indicator_name IN ('UNEMPLOYMENT', 'INFLATION', 'INTEREST_RATE')")
        results = cursor.fetchall()
        stored_indicators = [row[0] for row in results]
        
        for indicator in indicators:
            assert indicator['name'] in stored_indicators, f"Indicator {indicator['name']} not found"
        
        cursor.close()

    @pytest.mark.database
    def test_data_quality_tracking(self, test_mysql_connection):
        """Test tracking data quality for macro indicators"""
        cursor = test_mysql_connection.cursor()
        
        # Insert indicators with different quality levels
        test_cases = [
            {'name': 'COMPLETE_DATA', 'value': 100.0, 'completeness': 100.00},
            {'name': 'PARTIAL_DATA', 'value': 200.0, 'completeness': 75.50},
            {'name': 'MINIMAL_DATA', 'value': 300.0, 'completeness': 25.25},
        ]
        
        test_date = datetime(2023, 12, 31).date()
        
        for case in test_cases:
            cursor.execute("""
                INSERT INTO macro_indicators (indicator_name, value, date, source, data_completeness_percentage)
                VALUES (%s, %s, %s, %s, %s)
            """, (case['name'], case['value'], test_date, 'FRED', case['completeness']))
        
        test_mysql_connection.commit()
        
        # Verify completeness tracking
        cursor.execute("""
            SELECT indicator_name, data_completeness_percentage 
            FROM macro_indicators 
            WHERE indicator_name LIKE '%_DATA'
            ORDER BY indicator_name
        """)
        
        results = cursor.fetchall()
        assert len(results) == 3
        
        for result in results:
            name, completeness = result
            if name == 'COMPLETE_DATA':
                assert float(completeness) == 100.00
            elif name == 'MINIMAL_DATA':
                assert float(completeness) == 25.25
            elif name == 'PARTIAL_DATA':
                assert float(completeness) == 75.50
        
        cursor.close()

    @pytest.mark.real_api
    def test_fred_api_rate_limiting(self):
        """Test FRED API rate limiting compliance"""
        api_key = "35478996c5e061d0fc99fc73f5ce348d"
        
        start_time = time.time()
        
        # Make multiple requests with delays
        urls = [
            f"https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key={api_key}&file_type=json&limit=1",
            f"https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key={api_key}&file_type=json&limit=1"
        ]
        
        responses = []
        for url in urls:
            response = requests.get(url, timeout=30)
            responses.append(response)
            time.sleep(0.2)  # Small delay between requests
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should have taken at least 0.2 seconds due to delay
        assert duration >= 0.2
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

    @pytest.mark.database
    def test_historical_data_consistency(self, test_mysql_connection):
        """Test consistency of historical macro data"""
        cursor = test_mysql_connection.cursor()
        
        # Insert historical GDP data
        gdp_data = [
            {'date': datetime(2022, 12, 31).date(), 'value': 24000.0},
            {'date': datetime(2023, 3, 31).date(), 'value': 24250.0},
            {'date': datetime(2023, 6, 30).date(), 'value': 24500.0},
            {'date': datetime(2023, 9, 30).date(), 'value': 24750.0},
        ]
        
        for data in gdp_data:
            cursor.execute("""
                INSERT INTO macro_indicators (indicator_name, value, date, source)
                VALUES (%s, %s, %s, %s)
            """, ('GDP', data['value'], data['date'], 'FRED'))
        
        test_mysql_connection.commit()
        
        # Verify historical consistency (GDP should generally increase over time)
        cursor.execute("""
            SELECT value, date 
            FROM macro_indicators 
            WHERE indicator_name = 'GDP' 
            ORDER BY date ASC
        """)
        
        results = cursor.fetchall()
        assert len(results) >= 4
        
        # Check that values generally increase
        values = [float(row[0]) for row in results[-4:]]
        for i in range(1, len(values)):
            # Allow for occasional decreases but overall trend should be positive
            assert values[i] >= values[0] * 0.9, "GDP should not decrease drastically"
        
        cursor.close()

    @pytest.mark.real_api
    def test_data_freshness(self):
        """Test that macro economic data is reasonably fresh"""
        api_key = "35478996c5e061d0fc99fc73f5ce348d"
        
        # Get recent unemployment data
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key={api_key}&file_type=json&limit=1&sort_order=desc"
        
        response = requests.get(url, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        observations = data["observations"]
        
        if len(observations) > 0:
            latest_obs = observations[0]
            obs_date = datetime.strptime(latest_obs["date"], "%Y-%m-%d").date()
            current_date = datetime.now().date()
            
            # Data should be within the last 2 years
            days_diff = (current_date - obs_date).days
            assert days_diff < 730, f"Data is too old: {days_diff} days"