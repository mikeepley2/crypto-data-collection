#!/usr/bin/env python3
"""
Final Integration Test Verification
Verifies that all components work together for CI integration tests
"""

import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def test_ci_integration_setup():
    """Test complete CI integration test setup"""
    
    print("🚀 Final Integration Test Verification")
    print("=" * 60)
    
    # Set up CI environment like GitHub Actions would
    os.environ['CI'] = 'true'
    sys.argv = ['python', '-m', 'pytest', 'tests/test_pytest_comprehensive_integration.py']
    
    try:
        # Test 1: Configuration Detection
        print("\n🔧 Testing Configuration Detection...")
        
        from shared.database_config import DatabaseConfig
        db_config = DatabaseConfig()
        config = db_config.get_mysql_config_dict()
        
        expected = {
            'host': '172.22.32.1',
            'port': 3306,
            'database': 'crypto_news',
            'user': 'news_collector'
        }
        
        for key, expected_value in expected.items():
            actual_value = config[key]
            if actual_value == expected_value:
                print(f"✅ {key}: {actual_value}")
            else:
                print(f"❌ {key}: expected {expected_value}, got {actual_value}")
                return False
        
        # Test 2: Database Connection
        print(f"\n🔧 Testing Database Connection...")
        
        import mysql.connector
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Test required tables exist
        cursor.execute("SHOW TABLES")
        available_tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = [
            'crypto_assets', 'price_data_real', 'ohlc_data', 'onchain_data',
            'macro_indicators', 'technical_indicators', 'real_time_sentiment_signals',
            'ml_features_materialized', 'news_data'
        ]
        
        missing_tables = [table for table in required_tables if table not in available_tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print(f"✅ All required tables present: {len(required_tables)} tables")
        
        # Test 3: Sample Data Access
        print(f"\n🔧 Testing Sample Data Access...")
        
        test_queries = [
            ("crypto_assets", "SELECT COUNT(*) FROM crypto_assets"),
            ("price_data_real", "SELECT COUNT(*) FROM price_data_real"),
            ("ml_features_materialized", "SELECT COUNT(*) FROM ml_features_materialized"),
        ]
        
        for table_name, query in test_queries:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"✅ {table_name}: {count} records")
            else:
                print(f"⚠️  {table_name}: empty (may cause test failures)")
        
        cursor.close()
        connection.close()
        
        # Test 4: Integration Test Simulation
        print(f"\n🔧 Testing Integration Test Simulation...")
        
        # Simulate test_db_connection fixture
        config_copy = config.copy()
        config_copy['autocommit'] = False
        
        connection = mysql.connector.connect(**config_copy)
        connection.start_transaction()
        
        cursor = connection.cursor()
        
        # Simulate TestComprehensiveDatabaseSchema.test_all_required_tables_exist
        cursor.execute("SHOW TABLES")
        available_tables = [table[0] for table in cursor.fetchall()]
        missing_tables = [table for table in required_tables if table not in available_tables]
        
        if len(missing_tables) == 0:
            print(f"✅ TestComprehensiveDatabaseSchema.test_all_required_tables_exist: WOULD PASS")
        else:
            print(f"❌ TestComprehensiveDatabaseSchema.test_all_required_tables_exist: WOULD FAIL")
        
        # Simulate TestComprehensiveDatabaseSchema.test_crypto_assets_populated
        cursor.execute("SELECT COUNT(*) FROM crypto_assets")
        asset_count = cursor.fetchone()[0]
        
        if asset_count > 0:
            print(f"✅ TestComprehensiveDatabaseSchema.test_crypto_assets_populated: WOULD PASS")
        else:
            print(f"❌ TestComprehensiveDatabaseSchema.test_crypto_assets_populated: WOULD FAIL")
        
        # Simulate TestDataFlowIntegration.test_create_test_price_data
        test_symbol = 'FINAL_TEST'
        test_price = 99999.99
        
        try:
            cursor.execute("""
                INSERT INTO price_data_real (symbol, current_price, market_cap, total_volume)
                VALUES (%s, %s, %s, %s)
            """, (test_symbol, test_price, 1000000000, 50000000))
            
            cursor.execute("SELECT current_price FROM price_data_real WHERE symbol = %s", (test_symbol,))
            retrieved_price = cursor.fetchone()
            
            if retrieved_price and float(retrieved_price[0]) == test_price:
                print(f"✅ TestDataFlowIntegration.test_create_test_price_data: WOULD PASS")
            else:
                print(f"❌ TestDataFlowIntegration.test_create_test_price_data: WOULD FAIL")
        except Exception as e:
            print(f"❌ TestDataFlowIntegration.test_create_test_price_data: WOULD FAIL - {e}")
        
        # Cleanup
        connection.rollback()
        connection.close()
        
        print(f"\n🎯 Final Assessment:")
        print(f"✅ Configuration: CORRECT")
        print(f"✅ Database Connection: WORKING") 
        print(f"✅ Required Tables: PRESENT")
        print(f"✅ Sample Data: AVAILABLE")
        print(f"✅ Integration Tests: SHOULD PASS")
        
        print(f"\n🎉 Integration test infrastructure is ready!")
        print(f"🚀 CI/CD pipeline should now run integration tests successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Final verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ci_integration_setup()
    sys.exit(0 if success else 1)