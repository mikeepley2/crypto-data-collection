#!/usr/bin/env python3
"""
CI Database Test Script
Tests the database connectivity and schema setup in the CI environment.
"""

import mysql.connector
import os
import sys
import time
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connectivity():
    """Test database connectivity with CI environment variables"""
    logger.info("🔍 Testing database connectivity...")
    
    # Get MySQL configuration from environment variables with CI defaults
    mysql_host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
    mysql_user = os.environ.get('MYSQL_USER', 'news_collector')
    mysql_password = os.environ.get('MYSQL_PASSWORD', '99Rules!')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'crypto_data_test')
    
    logger.info(f"📊 Connecting to: {mysql_user}@{mysql_host}:{mysql_port}/{mysql_database}")
    
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connect_timeout=10,
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        if result[0] == 1:
            logger.info("✅ Basic database connectivity test passed")
        else:
            logger.error("❌ Basic database connectivity test failed")
            return False
        
        # Test table existence
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        expected_tables = [
            'crypto_assets', 'price_data_real', 'onchain_data', 'macro_indicators',
            'technical_indicators', 'real_time_sentiment_signals', 
            'ml_features_materialized', 'ohlc_data', 'news_data'
        ]
        
        logger.info(f"📋 Found {len(tables)} tables: {tables}")
        
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            logger.info("✅ All expected tables exist")
        
        # Test sample data
        cursor.execute("SELECT COUNT(*) FROM crypto_assets")
        asset_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM price_data_real") 
        price_count = cursor.fetchone()[0]
        
        logger.info(f"📊 Sample data counts:")
        logger.info(f"   crypto_assets: {asset_count} rows")
        logger.info(f"   price_data_real: {price_count} rows")
        
        if asset_count > 0 and price_count > 0:
            logger.info("✅ Sample data verification passed")
        else:
            logger.warning("⚠️ Sample data may be missing")
        
        cursor.close()
        connection.close()
        
        logger.info("✅ Database connectivity and schema test completed successfully")
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"❌ Database connectivity test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during database test: {e}")
        return False

def test_schema_structure():
    """Test specific schema structure against integration test expectations"""
    logger.info("🔍 Testing schema structure...")
    
    # Get database configuration
    mysql_host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
    mysql_user = os.environ.get('MYSQL_USER', 'news_collector')
    mysql_password = os.environ.get('MYSQL_PASSWORD', '99Rules!')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'crypto_data_test')
    
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connect_timeout=10,
            autocommit=True
        )
        cursor = connection.cursor()
        
        # Test price_data_real schema
        cursor.execute("DESCRIBE price_data_real")
        price_columns = [row[0] for row in cursor.fetchall()]
        
        required_price_fields = ['symbol', 'current_price', 'market_cap', 'volume_usd_24h', 'timestamp_iso']
        missing_price_fields = [field for field in required_price_fields if field not in price_columns]
        
        if missing_price_fields:
            logger.error(f"❌ price_data_real missing fields: {missing_price_fields}")
            return False
        else:
            logger.info("✅ price_data_real schema validation passed")
        
        # Test onchain_data schema
        cursor.execute("DESCRIBE onchain_data")
        onchain_columns = [row[0] for row in cursor.fetchall()]
        
        required_onchain_fields = ['symbol', 'active_addresses', 'transaction_count', 'transaction_volume', 'timestamp_iso']
        missing_onchain_fields = [field for field in required_onchain_fields if field not in onchain_columns]
        
        if missing_onchain_fields:
            logger.error(f"❌ onchain_data missing fields: {missing_onchain_fields}")
            return False
        else:
            logger.info("✅ onchain_data schema validation passed")
        
        # Test technical_indicators schema
        cursor.execute("DESCRIBE technical_indicators")
        tech_columns = [row[0] for row in cursor.fetchall()]
        
        required_tech_fields = ['symbol', 'rsi', 'sma_20', 'macd', 'timestamp_iso']
        missing_tech_fields = [field for field in required_tech_fields if field not in tech_columns]
        
        if missing_tech_fields:
            logger.error(f"❌ technical_indicators missing fields: {missing_tech_fields}")
            return False
        else:
            logger.info("✅ technical_indicators schema validation passed")
        
        cursor.close()
        connection.close()
        
        logger.info("✅ Schema structure validation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema structure test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 CI Database Test")
    logger.info("=" * 50)
    
    # Test 1: Basic connectivity
    if not test_database_connectivity():
        logger.error("❌ Database connectivity test failed")
        return False
    
    # Test 2: Schema structure
    if not test_schema_structure():
        logger.error("❌ Schema structure test failed") 
        return False
    
    logger.info("🎉 All database tests passed!")
    logger.info("✅ Database is ready for integration tests")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)