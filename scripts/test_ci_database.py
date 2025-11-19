#!/usr/bin/env python3
"""
CI Database Connectivity Test
Simple test to verify containerized MySQL is working properly
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connectivity():
    """Test basic database connectivity"""
    logger.info("🧪 Testing containerized MySQL connectivity...")
    
    # Use environment variables from CI
    config = {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', 'news_collector'),
        'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
        'database': os.getenv('MYSQL_DATABASE', 'crypto_data_test')
    }
    
    logger.info(f"🔗 Connecting to {config['host']}:{config['port']}/{config['database']} as {config['user']}")
    
    try:
        # Test connection
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        logger.info(f"✅ MySQL version: {version}")
        
        # Test database selection
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()[0]
        logger.info(f"✅ Current database: {current_db}")
        
        # Test table listing
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        logger.info(f"✅ Available tables ({len(tables)}): {', '.join(tables)}")
        
        # Test sample data query
        if 'crypto_assets' in tables:
            cursor.execute("SELECT COUNT(*) FROM crypto_assets")
            count = cursor.fetchone()[0]
            logger.info(f"✅ crypto_assets has {count} records")
        
        cursor.close()
        connection.close()
        
        logger.info("🎉 All database connectivity tests passed!")
        return True
        
    except Error as e:
        logger.error(f"❌ Database connectivity test failed: {e}")
        return False

def test_shared_config():
    """Test the shared database configuration module"""
    logger.info("🧪 Testing shared database configuration...")
    
    try:
        sys.path.append('.')
        from shared.database_config import DatabaseConfig
        
        # Create config instance
        config = DatabaseConfig()
        logger.info(f"✅ Environment detected: {config.environment}")
        logger.info(f"✅ MySQL config: {config.mysql_config}")
        
        # Test connection using shared config
        connection = mysql.connector.connect(**config.mysql_config)
        cursor = connection.cursor()
        
        cursor.execute("SELECT 1")
        result = cursor.fetchone()[0]
        logger.info(f"✅ Shared config connection test: {result}")
        
        cursor.close()
        connection.close()
        
        logger.info("🎉 Shared configuration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Shared configuration test failed: {e}")
        return False

def main():
    """Run all connectivity tests"""
    logger.info("🚀 Starting CI database connectivity tests")
    logger.info("=" * 60)
    
    success = True
    
    # Test 1: Direct connectivity
    if not test_database_connectivity():
        success = False
    
    # Test 2: Shared configuration
    if not test_shared_config():
        success = False
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 ALL TESTS PASSED - Database is ready for integration tests!")
    else:
        logger.error("💥 TESTS FAILED - Database setup needs attention")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())