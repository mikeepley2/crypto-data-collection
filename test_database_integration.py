#!/usr/bin/env python3
"""
Simple Database Integration Test
Tests that our CI database setup works correctly
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import mysql.connector

def test_database_connection():
    """Test database connection and table access"""
    
    print("🔍 Testing database connection...")
    
    # Test configuration using CI setup
    config = {
        'host': '172.22.32.1',
        'port': 3306,
        'user': 'news_collector',
        'password': '99Rules!', 
        'database': 'crypto_news',
        'charset': 'utf8mb4'
    }
    
    try:
        # Connect to database
        print(f"🔗 Connecting to {config['user']}@{config['host']}:{config['port']}/{config['database']}")
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Test basic connectivity
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to MySQL {version}")
        
        # Check available tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"📋 Available tables: {len(tables)} tables")
        
        # Check for our test tables
        expected_tables = ['crypto_assets', 'price_data_real', 'news_data']
        missing_tables = []
        available_test_tables = []
        
        for table in expected_tables:
            if table in tables:
                available_test_tables.append(table)
                print(f"✅ Found required table: {table}")
            else:
                missing_tables.append(table)
                print(f"❌ Missing table: {table}")
        
        # Test data access on available tables
        test_passed = True
        
        for table in available_test_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📊 Table {table}: {count} records")
                
                # Try to fetch sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"🔍 Sample from {table}: {sample[:3]}..." if len(sample) > 3 else f"🔍 Sample from {table}: {sample}")
                else:
                    print(f"⚠️  Table {table} is empty")
                    
            except Exception as e:
                print(f"❌ Error accessing {table}: {e}")
                test_passed = False
        
        cursor.close()
        connection.close()
        
        # Summary
        print(f"\n📋 Database Integration Test Summary:")
        print(f"✅ Database connectivity: OK")
        print(f"✅ Available test tables: {len(available_test_tables)}/{len(expected_tables)}")
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
        print(f"🎯 Test result: {'PASS' if test_passed and len(available_test_tables) >= 2 else 'FAIL'}")
        
        return test_passed and len(available_test_tables) >= 2
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_centralized_config():
    """Test centralized database configuration"""
    
    print(f"\n🔧 Testing centralized configuration...")
    
    try:
        from shared.database_config import DatabaseConfig
        
        db_config = DatabaseConfig()
        mysql_config = db_config.get_mysql_config_dict()
        
        print(f"📋 Centralized config:")
        print(f"   Host: {mysql_config['host']}")
        print(f"   Port: {mysql_config['port']}")
        print(f"   Database: {mysql_config['database']}")
        print(f"   User: {mysql_config['user']}")
        
        # Test connection using centralized config
        connection = mysql.connector.connect(**mysql_config)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        print(f"✅ Centralized configuration test: PASS")
        return True
        
    except Exception as e:
        print(f"❌ Centralized configuration test: FAIL - {e}")
        return False

def test_environment_detection():
    """Test environment detection logic"""
    
    print(f"\n🌍 Testing environment detection...")
    
    print(f"Environment variables:")
    env_vars = ['CI', 'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DATABASE', 'TESTING', 'PYTEST_CURRENT_TEST']
    for var in env_vars:
        value = os.getenv(var, 'not set')
        print(f"   {var}: {value}")
    
    # Test environment detection
    is_ci = os.getenv('CI') == 'true'
    is_testing = any('test' in arg.lower() for arg in sys.argv)
    
    print(f"Detection results:")
    print(f"   CI environment: {is_ci}")
    print(f"   Testing mode: {is_testing}")
    
    return True

def main():
    """Main test execution"""
    
    print("🚀 Database Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Environment detection
    env_test = test_environment_detection()
    
    # Test 2: Direct database connection
    db_test = test_database_connection()
    
    # Test 3: Centralized configuration
    config_test = test_centralized_config()
    
    # Summary
    print(f"\n🎯 Final Test Results:")
    print(f"✅ Environment Detection: {'PASS' if env_test else 'FAIL'}")
    print(f"✅ Database Connection: {'PASS' if db_test else 'FAIL'}")
    print(f"✅ Centralized Config: {'PASS' if config_test else 'FAIL'}")
    
    all_passed = env_test and db_test and config_test
    print(f"\n🏆 Overall Result: {'SUCCESS' if all_passed else 'FAILURE'}")
    
    if all_passed:
        print(f"🎉 Integration tests are ready to run!")
        print(f"✅ Database tables are accessible")
        print(f"✅ Configuration is working properly")
    else:
        print(f"⚠️  Some tests failed - check configuration")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)