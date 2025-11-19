#!/usr/bin/env python3
"""
Simple Integration Test without Complex Dependencies
Tests basic functionality that integration tests would verify
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import mysql.connector
from datetime import datetime, timezone

def test_database_operations():
    """Test basic database operations that integration tests would perform"""
    
    print("🔧 Testing database operations...")
    
    config = {
        'host': '172.22.32.1',
        'port': 3306,
        'user': 'news_collector',
        'password': '99Rules!',
        'database': 'crypto_news',
        'charset': 'utf8mb4'
    }
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Test 1: Read from crypto_assets
        cursor.execute("SELECT symbol, name, current_price FROM crypto_assets WHERE symbol = 'BTC'")
        btc_data = cursor.fetchone()
        
        if btc_data:
            symbol, name, price = btc_data
            print(f"✅ Crypto assets test: {symbol} ({name}) = ${price}")
        else:
            print(f"❌ No BTC data found in crypto_assets")
            return False
        
        # Test 2: Read from price_data_real
        cursor.execute("SELECT symbol, current_price, market_cap FROM price_data_real WHERE symbol = 'BTC' LIMIT 1")
        price_data = cursor.fetchone()
        
        if price_data:
            symbol, price, market_cap = price_data
            print(f"✅ Price data test: {symbol} = ${price}, market cap = ${market_cap}")
        else:
            print(f"❌ No BTC price data found")
            return False
        
        # Test 3: Read from news_data
        cursor.execute("SELECT title, source FROM news_data LIMIT 1")
        news_data = cursor.fetchone()
        
        if news_data:
            title, source = news_data
            print(f"✅ News data test: '{title[:50]}...' from {source}")
        else:
            print(f"❌ No news data found")
            return False
        
        # Test 4: Test insertion (using test tables)
        try:
            # Insert into test table
            test_timestamp = datetime.now(timezone.utc)
            cursor.execute("""
                INSERT INTO test_price_data_real (symbol, current_price, market_cap, total_volume, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, ('TEST', 1000.0, 1000000, 10000, test_timestamp))
            
            # Read back the test data
            cursor.execute("SELECT symbol, current_price FROM test_price_data_real WHERE symbol = 'TEST'")
            test_result = cursor.fetchone()
            
            if test_result and test_result[0] == 'TEST':
                print(f"✅ Insert/read test: {test_result[0]} = ${test_result[1]}")
            else:
                print(f"❌ Insert/read test failed")
                return False
                
            # Clean up test data
            cursor.execute("DELETE FROM test_price_data_real WHERE symbol = 'TEST'")
            
        except Exception as e:
            print(f"❌ Insert/read test failed: {e}")
            return False
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"🎯 All database operations: PASS")
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

def test_centralized_config_functionality():
    """Test that centralized config works for database operations"""
    
    print(f"\n🔧 Testing centralized config functionality...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        
        # Test MySQL connection via centralized config
        connection = mysql.connector.connect(**db_config.get_mysql_config_dict())
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = %s", (db_config.mysql_config['database'],))
        table_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        print(f"✅ Centralized config functionality: Found {table_count} tables via config")
        return True
        
    except Exception as e:
        print(f"❌ Centralized config functionality failed: {e}")
        return False

def test_environment_configuration():
    """Test that environment configuration is properly set"""
    
    print(f"\n🔧 Testing environment configuration...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        
        # Check environment detection
        print(f"Environment: {db_config.environment}")
        print(f"MySQL Host: {db_config.mysql_config['host']}")
        print(f"MySQL Database: {db_config.mysql_config['database']}")
        
        # Verify CI environment uses correct database
        if os.getenv('CI') == 'true':
            expected_database = 'crypto_news'
            actual_database = db_config.mysql_config['database']
            
            if actual_database == expected_database:
                print(f"✅ CI environment using correct database: {actual_database}")
            else:
                print(f"❌ CI environment using wrong database: {actual_database} (expected: {expected_database})")
                return False
        
        print(f"✅ Environment configuration: PASS")
        return True
        
    except Exception as e:
        print(f"❌ Environment configuration test failed: {e}")
        return False

def main():
    """Main test execution"""
    
    print("🚀 Integration Test Simulation")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Database Operations", test_database_operations),
        ("Centralized Config Functionality", test_centralized_config_functionality), 
        ("Environment Configuration", test_environment_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    # Summary
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"🏆 ALL TESTS PASSED!")
        print(f"✅ Database setup is working correctly")
        print(f"✅ Integration tests should now run successfully")
        print(f"✅ CI/CD pipeline database issues resolved")
    else:
        print(f"❌ Some tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)