#!/usr/bin/env python3
"""
Simple Integration Test Runner
Tests integration functionality without complex dependencies
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import mysql.connector
from datetime import datetime, timezone

def test_database_configuration():
    """Test that database configuration works correctly"""
    print("🔧 Testing database configuration...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        config = db_config.get_mysql_config_dict()
        
        # Verify CI configuration
        expected_values = {
            'database': 'crypto_news',
            'host': '172.22.32.1',
            'port': 3306,
            'user': 'news_collector'
        }
        
        for key, expected in expected_values.items():
            actual = config[key]
            if actual == expected:
                print(f"✅ {key}: {actual}")
            else:
                print(f"❌ {key}: expected {expected}, got {actual}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_all_required_tables_exist():
    """Test that all required tables exist (mimics integration test)"""
    print(f"\\n🔧 Testing required tables exist...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig() 
        connection = mysql.connector.connect(**db_config.get_mysql_config_dict())
        cursor = connection.cursor()
        
        # Get all available tables
        cursor.execute("SHOW TABLES")
        available_tables = [table[0] for table in cursor.fetchall()]
        
        # Required tables from integration tests
        required_tables = [
            'crypto_assets',
            'price_data_real', 
            'ohlc_data',
            'onchain_data',
            'macro_indicators',
            'technical_indicators',
            'real_time_sentiment_signals',
            'ml_features_materialized',
            'news_data'
        ]
        
        missing_tables = [table for table in required_tables if table not in available_tables]
        
        if missing_tables:
            print(f"❌ Missing required tables: {missing_tables}")
            cursor.close()
            connection.close()
            return False
        else:
            print(f"✅ All required tables exist: {len(required_tables)} tables")
            cursor.close()
            connection.close()
            return True
            
    except Exception as e:
        print(f"❌ Table existence test failed: {e}")
        return False

def test_crypto_assets_populated():
    """Test that crypto_assets table is populated (mimics integration test)"""
    print(f"\\n🔧 Testing crypto_assets populated...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        connection = mysql.connector.connect(**db_config.get_mysql_config_dict())
        cursor = connection.cursor()
        
        # Test crypto_assets table
        cursor.execute("SELECT COUNT(*) FROM crypto_assets")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ crypto_assets has {count} records")
            
            # Test specific record
            cursor.execute("SELECT symbol, name FROM crypto_assets WHERE symbol = 'BTC'")
            btc_record = cursor.fetchone()
            
            if btc_record:
                symbol, name = btc_record
                print(f"✅ Found BTC record: {symbol} - {name}")
                cursor.close()
                connection.close()
                return True
            else:
                print(f"❌ No BTC record found")
                cursor.close()
                connection.close()
                return False
        else:
            print(f"❌ crypto_assets table is empty")
            cursor.close()
            connection.close()
            return False
            
    except Exception as e:
        print(f"❌ Crypto assets test failed: {e}")
        return False

def test_database_tables_exist():
    """Test database tables exist (mimics DataFlowIntegration test)"""
    print(f"\\n🔧 Testing database tables exist for data flow...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        connection = mysql.connector.connect(**db_config.get_mysql_config_dict())
        cursor = connection.cursor()
        
        # Tables needed for data flow tests
        required_tables = ['price_data_real', 'ml_features_materialized', 'news_data']
        
        cursor.execute("SHOW TABLES")
        available_tables = [table[0] for table in cursor.fetchall()]
        
        for table in required_tables:
            if table in available_tables:
                print(f"✅ Table {table} exists")
            else:
                print(f"❌ Required table {table} does not exist")
                cursor.close()
                connection.close()
                return False
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database tables test failed: {e}")
        return False

def test_create_test_price_data():
    """Test creating test price data (mimics integration test)"""
    print(f"\\n🔧 Testing test price data creation...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        connection = mysql.connector.connect(**db_config.get_mysql_config_dict())
        cursor = connection.cursor()
        
        # Test insert
        test_timestamp = datetime.now(timezone.utc)
        cursor.execute("""
            INSERT INTO price_data_real (symbol, current_price, market_cap, total_volume, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, ('TEST_INTEGRATION', 99999.99, 999999999999, 999999999, test_timestamp))
        
        # Verify insert
        cursor.execute("SELECT symbol, current_price FROM price_data_real WHERE symbol = 'TEST_INTEGRATION'")
        test_record = cursor.fetchone()
        
        if test_record and test_record[0] == 'TEST_INTEGRATION':
            print(f"✅ Test price data created: {test_record[0]} = ${test_record[1]}")
            
            # Clean up
            cursor.execute("DELETE FROM price_data_real WHERE symbol = 'TEST_INTEGRATION'")
            connection.commit()
            
            cursor.close()
            connection.close()
            return True
        else:
            print(f"❌ Test price data creation failed")
            cursor.close()
            connection.close()
            return False
            
    except Exception as e:
        print(f"❌ Test price data creation failed: {e}")
        return False

def test_sql_syntax_fixes():
    """Test that our SQL syntax fixes work"""
    print(f"\\n🔧 Testing SQL syntax fixes...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        connection = mysql.connector.connect(**db_config.get_mysql_config_dict())
        cursor = connection.cursor()
        
        # Test the fixed SQL syntax
        test_queries = [
            "SELECT COUNT(*) FROM ml_features_materialized WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 4 HOUR)",
            "SELECT COUNT(*) FROM price_data_real p JOIN ml_features_materialized ml ON p.symbol = ml.symbol WHERE p.timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR) AND ml.updated_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)",
            "SELECT COUNT(*) FROM ml_features_materialized WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 6 HOUR)"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                cursor.execute(query)
                result = cursor.fetchone()[0]
                print(f"✅ SQL syntax test {i}: {result} records")
            except Exception as e:
                print(f"❌ SQL syntax test {i} failed: {e}")
                cursor.close()
                connection.close()
                return False
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ SQL syntax test failed: {e}")
        return False

def main():
    """Main test execution"""
    
    print("🚀 Integration Test Verification")
    print("=" * 60)
    
    # Run tests in order
    tests = [
        ("Database Configuration", test_database_configuration),
        ("Required Tables Exist", test_all_required_tables_exist),
        ("Crypto Assets Populated", test_crypto_assets_populated),
        ("Database Tables for Data Flow", test_database_tables_exist),
        ("Test Price Data Creation", test_create_test_price_data),
        ("SQL Syntax Fixes", test_sql_syntax_fixes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"🟢 {test_name}: PASS")
            else:
                print(f"🔴 {test_name}: FAIL")
        except Exception as e:
            print(f"🔴 {test_name}: ERROR - {e}")
    
    # Summary
    print(f"\\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\\n🏆 ALL TESTS PASSED!")
        print(f"✅ Integration tests should now run successfully")
        print(f"✅ Database configuration is correct")
        print(f"✅ All required tables are available")
        print(f"✅ SQL syntax issues are fixed")
        print(f"🎉 CI/CD pipeline integration tests ready!")
    else:
        print(f"\\n❌ Some tests failed - check configuration")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)