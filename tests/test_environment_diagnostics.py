#!/usr/bin/env python3
"""
Test Environment Diagnostic Script

This script validates that the test environment is properly configured
and all required services are accessible before running tests.
"""

import os
import sys
import time
import socket
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_port_connectivity(host: str, port: int, service_name: str) -> bool:
    """Test if a port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info(f"✅ {service_name} port {port} is accessible")
            return True
        else:
            logger.error(f"❌ {service_name} port {port} is not accessible")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing {service_name} connectivity: {e}")
        return False

def test_mysql_connection() -> bool:
    """Test MySQL database connection"""
    try:
        import mysql.connector
        
        config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_data_test'),
            'charset': 'utf8mb4'
        }
        
        logger.info(f"🔍 Testing MySQL connection to {config['host']}:{config['port']}")
        logger.info(f"   Database: {config['database']}, User: {config['user']}")
        
        # Test port first
        if not test_port_connectivity(config['host'], config['port'], 'MySQL'):
            return False
        
        # Test MySQL connection
        connection = mysql.connector.connect(**config)
        connection.ping(reconnect=True)
        
        # Test database access
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result == (1,):
            logger.info("✅ MySQL connection and database access successful")
            return True
        else:
            logger.error("❌ MySQL query test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ MySQL connection failed: {e}")
        return False

def test_redis_connection() -> bool:
    """Test Redis connection"""
    try:
        import redis
        
        config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': 0
        }
        
        logger.info(f"🔍 Testing Redis connection to {config['host']}:{config['port']}")
        
        # Test port first
        if not test_port_connectivity(config['host'], config['port'], 'Redis'):
            return False
        
        # Test Redis connection
        r = redis.Redis(**config)
        response = r.ping()
        r.close()
        
        if response:
            logger.info("✅ Redis connection successful")
            return True
        else:
            logger.error("❌ Redis ping failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

def check_environment_variables():
    """Check that required environment variables are set"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = [
        'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 
        'MYSQL_PASSWORD', 'MYSQL_DATABASE',
        'REDIS_HOST', 'REDIS_PORT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Don't log passwords
            if 'PASSWORD' in var:
                logger.info(f"  ✅ {var}: [REDACTED]")
            else:
                logger.info(f"  ✅ {var}: {value}")
        else:
            logger.warning(f"  ⚠️ {var}: Not set (using default)")
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Tests will use default values from conftest.py")
    
    return len(missing_vars) == 0

def main():
    """Run all diagnostic tests"""
    logger.info("🚀 Starting test environment diagnostics...")
    
    all_good = True
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Test service connectivity
    mysql_ok = test_mysql_connection()
    redis_ok = test_redis_connection()
    
    all_good = env_ok and mysql_ok and redis_ok
    
    logger.info("\n📊 Diagnostic Results Summary:")
    logger.info(f"  Environment Variables: {'✅ OK' if env_ok else '⚠️ MISSING'}")
    logger.info(f"  MySQL Connection: {'✅ OK' if mysql_ok else '❌ FAILED'}")
    logger.info(f"  Redis Connection: {'✅ OK' if redis_ok else '❌ FAILED'}")
    
    if all_good:
        logger.info("\n🎉 All diagnostics passed! Test environment is ready.")
        sys.exit(0)
    else:
        logger.error("\n🚨 Some diagnostics failed. Check service configuration.")
        logger.error("\nTroubleshooting steps:")
        if not mysql_ok:
            logger.error("  - Check if MySQL service is running")
            logger.error("  - Verify MySQL port mapping in CI/CD")
            logger.error("  - Check MySQL credentials and database name")
        if not redis_ok:
            logger.error("  - Check if Redis service is running")
            logger.error("  - Verify Redis port mapping in CI/CD")
        sys.exit(1)

if __name__ == "__main__":
    main()