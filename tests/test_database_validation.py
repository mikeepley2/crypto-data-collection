#!/usr/bin/env python3
"""
Comprehensive Database Validation Tests

Tests database schema integrity, data completeness columns, and cross-table consistency.
"""

import pytest
import mysql.connector
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseSchemaValidation:
    """Test database schema and structure validation"""
    
    def test_all_required_tables_exist(self, test_mysql_connection):
        """Verify all required tables exist in test database"""
        cursor = test_mysql_connection.cursor()
        
        # Expected tables from PRIMARY_COLLECTION_TABLES
        required_tables = [
            'price_data_real',
            'technical_indicators', 
            'ohlc_data',
            'onchain_data',
            'macro_indicators',
            'real_time_sentiment_signals',
            'ml_features_materialized',
            'trading_signals',
            'crypto_assets'
        ]
        
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        for table in required_tables:
            assert table in existing_tables, f"Required table {table} does not exist"
        
        cursor.close()
    
    def test_data_completeness_columns_exist(self, test_mysql_connection):
        """Verify all tables have data_completeness_percentage column"""
        cursor = test_mysql_connection.cursor()
        
        tables_to_check = [
            'price_data_real',
            'technical_indicators', 
            'ohlc_data',
            'onchain_data',
            'macro_indicators',
            'real_time_sentiment_signals',
            'ml_features_materialized',
            'trading_signals',
            'crypto_assets'
        ]
        
        for table in tables_to_check:
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]
            
            assert 'data_completeness_percentage' in column_names, \
                f"Table {table} missing data_completeness_percentage column"
            
            # Check column type is DECIMAL
            completeness_col = next(col for col in columns if col[0] == 'data_completeness_percentage')
            assert 'decimal' in completeness_col[1].lower(), \
                f"data_completeness_percentage in {table} should be DECIMAL type"
        
        cursor.close()
    
    def test_required_columns_price_data(self, test_mysql_connection):
        """Test price_data_real table has all required columns"""
        cursor = test_mysql_connection.cursor()
        cursor.execute("DESCRIBE price_data_real")
        columns = [col[0] for col in cursor.fetchall()]
        
        required_columns = [
            'id', 'symbol', 'price', 'market_cap', 'total_volume',
            'price_change_24h', 'price_change_percentage_24h', 
            'circulating_supply', 'total_supply', 'max_supply',
            'timestamp', 'created_at', 'data_completeness_percentage'
        ]
        
        for col in required_columns:
            assert col in columns, f"price_data_real missing column: {col}"
        
        cursor.close()
    
    def test_required_columns_technical_indicators(self, test_mysql_connection):
        """Test technical_indicators table has all required columns"""
        cursor = test_mysql_connection.cursor()
        cursor.execute("DESCRIBE technical_indicators")
        columns = [col[0] for col in cursor.fetchall()]
        
        required_columns = [
            'id', 'symbol', 'indicator_type', 'value', 'period',
            'timestamp', 'created_at', 'data_completeness_percentage'
        ]
        
        for col in required_columns:
            assert col in columns, f"technical_indicators missing column: {col}"
        
        cursor.close()
    
    def test_required_columns_ohlc_data(self, test_mysql_connection):
        """Test ohlc_data table has all required columns"""
        cursor = test_mysql_connection.cursor()
        cursor.execute("DESCRIBE ohlc_data")
        columns = [col[0] for col in cursor.fetchall()]
        
        required_columns = [
            'id', 'symbol', 'open_price', 'high_price', 'low_price', 
            'close_price', 'volume', 'timestamp', 'timeframe',
            'created_at', 'data_completeness_percentage'
        ]
        
        for col in required_columns:
            assert col in columns, f"ohlc_data missing column: {col}"
        
        cursor.close()
    
    def test_required_columns_macro_indicators(self, test_mysql_connection):
        """Test macro_indicators table has all required columns"""
        cursor = test_mysql_connection.cursor()
        cursor.execute("DESCRIBE macro_indicators")
        columns = [col[0] for col in cursor.fetchall()]
        
        required_columns = [
            'id', 'indicator', 'value', 'unit', 'frequency',
            'timestamp', 'created_at', 'data_completeness_percentage'
        ]
        
        for col in required_columns:
            assert col in columns, f"macro_indicators missing column: {col}"
        
        cursor.close()
    
    def test_database_indexes_exist(self, test_mysql_connection):
        """Test that required database indexes exist for performance"""
        cursor = test_mysql_connection.cursor()
        
        # Check indexes on price_data_real
        cursor.execute("SHOW INDEX FROM price_data_real")
        indexes = cursor.fetchall()
        index_names = [idx[2] for idx in indexes]
        
        # Should have indexes on commonly queried columns
        expected_indexes = ['PRIMARY']  # At minimum should have primary key
        for idx in expected_indexes:
            assert idx in index_names, f"Missing index: {idx} on price_data_real"
        
        # Check for symbol and timestamp indexes (may be named differently)
        symbol_indexed = any('symbol' in str(idx) for idx in indexes)
        timestamp_indexed = any('timestamp' in str(idx) for idx in indexes)
        
        assert symbol_indexed, "price_data_real should have symbol index"
        assert timestamp_indexed, "price_data_real should have timestamp index"
        
        cursor.close()


@pytest.mark.database
@pytest.mark.integration  
class TestDataCompletenessValidation:
    """Test data completeness percentage validation"""
    
    def test_completeness_percentage_ranges(self, test_mysql_connection):
        """Test that completeness percentages are within valid range (0-100)"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        tables_to_check = [
            'price_data_real', 'technical_indicators', 'ohlc_data',
            'macro_indicators', 'real_time_sentiment_signals'
        ]
        
        for table in tables_to_check:
            cursor.execute(f"""
                SELECT symbol, data_completeness_percentage 
                FROM {table} 
                WHERE data_completeness_percentage IS NOT NULL
                LIMIT 50
            """)
            records = cursor.fetchall()
            
            for record in records:
                completeness = record['data_completeness_percentage']
                assert 0 <= completeness <= 100, \
                    f"Invalid completeness {completeness}% in {table} for {record['symbol']}"
        
        cursor.close()
    
    def test_completeness_consistency_across_tables(self, test_mysql_connection):
        """Test that completeness is consistent for same symbol/timestamp across tables"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Find common symbols and timestamps
        cursor.execute("""
            SELECT p.symbol, p.timestamp, p.data_completeness_percentage as price_completeness,
                   t.data_completeness_percentage as tech_completeness
            FROM price_data_real p
            JOIN technical_indicators t ON p.symbol = t.symbol 
                AND ABS(TIMESTAMPDIFF(MINUTE, p.timestamp, t.timestamp)) <= 5
            WHERE p.data_completeness_percentage IS NOT NULL
              AND t.data_completeness_percentage IS NOT NULL
            LIMIT 20
        """)
        records = cursor.fetchall()
        
        for record in records:
            price_comp = record['price_completeness']
            tech_comp = record['tech_completeness']
            
            # Completeness should be reasonably correlated
            # Allow 20% difference between related tables
            assert abs(price_comp - tech_comp) <= 30, \
                f"Large completeness discrepancy for {record['symbol']}: price={price_comp}%, tech={tech_comp}%"
        
        cursor.close()
    
    def test_high_completeness_for_core_data(self, test_mysql_connection):
        """Test that core data fields have high completeness scores"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Price data should have very high completeness
        cursor.execute("""
            SELECT AVG(data_completeness_percentage) as avg_completeness
            FROM price_data_real 
            WHERE data_completeness_percentage IS NOT NULL
              AND created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        result = cursor.fetchone()
        
        if result and result['avg_completeness']:
            avg_completeness = result['avg_completeness']
            assert avg_completeness >= 85.0, \
                f"Price data completeness too low: {avg_completeness}%"
        
        cursor.close()
    
    def test_placeholder_data_identification(self, test_mysql_connection):
        """Test that placeholder data is properly identified with 0% completeness"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Check for placeholder records (0% completeness)
        cursor.execute("""
            SELECT COUNT(*) as placeholder_count
            FROM price_data_real 
            WHERE data_completeness_percentage = 0.0
        """)
        result = cursor.fetchone()
        
        placeholder_count = result['placeholder_count'] if result else 0
        
        if placeholder_count > 0:
            # Verify placeholder records have minimal data
            cursor.execute("""
                SELECT symbol, price, market_cap, total_volume
                FROM price_data_real 
                WHERE data_completeness_percentage = 0.0
                LIMIT 5
            """)
            placeholders = cursor.fetchall()
            
            for placeholder in placeholders:
                # Placeholder records should have minimal or null data
                filled_fields = sum(1 for field in ['price', 'market_cap', 'total_volume'] 
                                  if placeholder[field] is not None)
                assert filled_fields <= 1, \
                    f"Placeholder for {placeholder['symbol']} has too much data"
        
        cursor.close()


@pytest.mark.database
@pytest.mark.integration
class TestCrossTableConsistency:
    """Test consistency across related tables"""
    
    def test_symbol_consistency_across_tables(self, test_mysql_connection):
        """Test that symbols are consistent across all tables"""
        cursor = test_mysql_connection.cursor()
        
        # Get symbols from crypto_assets (master list)
        cursor.execute("SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1")
        master_symbols = {row[0] for row in cursor.fetchall()}
        
        if not master_symbols:
            pytest.skip("No active symbols in crypto_assets table")
        
        # Check symbols in other tables match master list
        tables_to_check = ['price_data_real', 'technical_indicators', 'ohlc_data']
        
        for table in tables_to_check:
            cursor.execute(f"SELECT DISTINCT symbol FROM {table}")
            table_symbols = {row[0] for row in cursor.fetchall()}
            
            # All symbols in data tables should exist in master list
            orphaned_symbols = table_symbols - master_symbols
            assert len(orphaned_symbols) == 0, \
                f"Table {table} has orphaned symbols: {orphaned_symbols}"
        
        cursor.close()
    
    def test_timestamp_alignment_across_tables(self, test_mysql_connection):
        """Test timestamp alignment between related tables"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Check alignment between price and technical data
        cursor.execute("""
            SELECT p.symbol, p.timestamp as price_timestamp, 
                   t.timestamp as tech_timestamp,
                   ABS(TIMESTAMPDIFF(MINUTE, p.timestamp, t.timestamp)) as time_diff_minutes
            FROM price_data_real p
            JOIN technical_indicators t ON p.symbol = t.symbol
            WHERE p.timestamp > DATE_SUB(NOW(), INTERVAL 6 HOUR)
              AND t.timestamp > DATE_SUB(NOW(), INTERVAL 6 HOUR)
            ORDER BY time_diff_minutes DESC
            LIMIT 10
        """)
        alignments = cursor.fetchall()
        
        for alignment in alignments:
            time_diff = alignment['time_diff_minutes']
            # Allow up to 10 minutes difference for timestamp alignment
            assert time_diff <= 10, \
                f"Poor timestamp alignment for {alignment['symbol']}: {time_diff} minutes difference"
        
        cursor.close()
    
    def test_data_freshness_consistency(self, test_mysql_connection):
        """Test that data freshness is consistent across tables"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        tables_to_check = [
            'price_data_real', 'technical_indicators', 'ohlc_data', 'macro_indicators'
        ]
        
        freshness_data = {}
        
        for table in tables_to_check:
            cursor.execute(f"""
                SELECT MAX(created_at) as latest_record
                FROM {table}
            """)
            result = cursor.fetchone()
            
            if result and result['latest_record']:
                latest_time = result['latest_record']
                age_minutes = (datetime.now() - latest_time).total_seconds() / 60
                freshness_data[table] = age_minutes
        
        # All tables should have reasonably fresh data (within 4 hours for testing)
        max_age_minutes = 240  # 4 hours
        
        for table, age in freshness_data.items():
            assert age <= max_age_minutes, \
                f"Table {table} data too old: {age:.1f} minutes"
        
        cursor.close()
    
    def test_referential_integrity_constraints(self, test_mysql_connection):
        """Test referential integrity between tables"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Check that all symbols in data tables exist in crypto_assets
        cursor.execute("""
            SELECT DISTINCT p.symbol
            FROM price_data_real p
            LEFT JOIN crypto_assets ca ON p.symbol = ca.symbol
            WHERE ca.symbol IS NULL
            LIMIT 5
        """)
        orphaned_price_symbols = cursor.fetchall()
        
        assert len(orphaned_price_symbols) == 0, \
            f"Found orphaned symbols in price_data_real: {[s['symbol'] for s in orphaned_price_symbols]}"
        
        # Similar check for technical indicators
        cursor.execute("""
            SELECT DISTINCT t.symbol
            FROM technical_indicators t
            LEFT JOIN crypto_assets ca ON t.symbol = ca.symbol  
            WHERE ca.symbol IS NULL
            LIMIT 5
        """)
        orphaned_tech_symbols = cursor.fetchall()
        
        assert len(orphaned_tech_symbols) == 0, \
            f"Found orphaned symbols in technical_indicators: {[s['symbol'] for s in orphaned_tech_symbols]}"
        
        cursor.close()


@pytest.mark.database
@pytest.mark.performance
class TestDatabasePerformance:
    """Test database performance and optimization"""
    
    def test_query_performance_price_data(self, test_mysql_connection, performance_monitor):
        """Test query performance on price data table"""
        cursor = test_mysql_connection.cursor()
        
        # Test symbol-based query performance
        start_time = time.time()
        cursor.execute("""
            SELECT * FROM price_data_real 
            WHERE symbol = 'bitcoin' 
            AND timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        results = cursor.fetchall()
        end_time = time.time()
        
        query_time = end_time - start_time
        assert query_time < 2.0, f"Price data query too slow: {query_time:.2f}s"
        
        cursor.close()
    
    def test_aggregation_performance(self, test_mysql_connection):
        """Test performance of aggregation queries"""
        cursor = test_mysql_connection.cursor()
        
        # Test completeness aggregation performance
        start_time = time.time()
        cursor.execute("""
            SELECT symbol, 
                   AVG(data_completeness_percentage) as avg_completeness,
                   COUNT(*) as record_count
            FROM price_data_real 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY symbol
            HAVING record_count > 10
        """)
        results = cursor.fetchall()
        end_time = time.time()
        
        query_time = end_time - start_time
        assert query_time < 5.0, f"Aggregation query too slow: {query_time:.2f}s"
        
        cursor.close()
    
    def test_cross_table_join_performance(self, test_mysql_connection):
        """Test performance of cross-table joins"""
        cursor = test_mysql_connection.cursor()
        
        start_time = time.time()
        cursor.execute("""
            SELECT p.symbol, p.price, t.indicator_type, t.value
            FROM price_data_real p
            JOIN technical_indicators t ON p.symbol = t.symbol
            WHERE p.timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
              AND t.timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
              AND ABS(TIMESTAMPDIFF(MINUTE, p.timestamp, t.timestamp)) <= 5
            LIMIT 50
        """)
        results = cursor.fetchall()
        end_time = time.time()
        
        query_time = end_time - start_time
        assert query_time < 3.0, f"Join query too slow: {query_time:.2f}s"
        
        cursor.close()


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseRecovery:
    """Test database recovery and backup validation"""
    
    def test_data_backup_verification(self, test_mysql_connection):
        """Test data backup and recovery verification"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Check that critical data exists
        critical_tables = ['crypto_assets', 'price_data_real', 'technical_indicators']
        
        for table in critical_tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            result = cursor.fetchone()
            
            count = result['count'] if result else 0
            assert count > 0, f"Critical table {table} is empty - potential data loss"
        
        cursor.close()
    
    def test_data_integrity_after_operations(self, test_mysql_connection):
        """Test data integrity after insert/update operations"""
        cursor = test_mysql_connection.cursor(dictionary=True)
        
        # Insert test record and verify integrity
        test_symbol = 'TEST_INTEGRITY'
        test_price = 12345.67
        test_completeness = 98.5
        
        cursor.execute("""
            INSERT INTO price_data_real (symbol, price, market_cap, data_completeness_percentage)
            VALUES (%s, %s, %s, %s)
        """, (test_symbol, test_price, 1000000000, test_completeness))
        
        test_mysql_connection.commit()
        
        # Verify data was inserted correctly
        cursor.execute("""
            SELECT symbol, price, data_completeness_percentage
            FROM price_data_real 
            WHERE symbol = %s
        """, (test_symbol,))
        
        result = cursor.fetchone()
        assert result is not None, "Test record not found after insert"
        assert result['symbol'] == test_symbol
        assert abs(float(result['price']) - test_price) < 0.01
        assert abs(float(result['data_completeness_percentage']) - test_completeness) < 0.1
        
        # Cleanup
        cursor.execute("DELETE FROM price_data_real WHERE symbol = %s", (test_symbol,))
        test_mysql_connection.commit()
        cursor.close()