#!/usr/bin/env python3
"""
Centralized Database Configuration Module
This module provides a single source of truth for database connections
that works both in Kubernetes (using ConfigMaps/Secrets) and local development.
"""
import os
import mysql.connector
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Centralized database configuration manager"""
    
    def __init__(self):
        """Initialize database configuration from environment variables"""
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, str]:
        """Load database configuration from environment variables"""
        config = {
            'host': os.getenv('DB_HOST', '172.22.32.1'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'news_collector'),
            'password': os.getenv('DB_PASSWORD', '99Rules!'),
            'database': os.getenv('DB_NAME', 'crypto_prices'),
            'connection_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            'autocommit': True,
            'charset': 'utf8mb4',
            'use_unicode': True,
            'pool_name': f'pool_{os.getpid()}',
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
            'pool_reset_session': True,
        }
        
        logger.info(f"🔧 Database config loaded: {config['host']}:{config['port']}/{config['database']}")
        return config
    
    def get_connection(self) -> mysql.connector.MySQLConnection:
        """Get a database connection"""
        try:
            connection = mysql.connector.connect(**self.config)
            logger.debug("✅ Database connection established")
            return connection
        except mysql.connector.Error as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def get_config_dict(self) -> Dict[str, str]:
        """Get configuration dictionary for manual connection"""
        return self.config.copy()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if result and result[0] == 1:
                logger.info("✅ Database connectivity test passed")
                return True
            else:
                logger.error("❌ Database connectivity test failed: Invalid response")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database connectivity test failed: {e}")
            return False
    
    def get_connection_info(self) -> str:
        """Get connection info string for logging"""
        return f"{self.config['user']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"

# Global instance for easy import
db_config = DatabaseConfig()

# Convenience functions
def get_db_connection() -> mysql.connector.MySQLConnection:
    """Get a database connection - convenience function"""
    return db_config.get_connection()

def test_db_connection() -> bool:
    """Test database connection - convenience function"""
    return db_config.test_connection()

def get_db_config() -> Dict[str, str]:
    """Get database configuration - convenience function"""
    return db_config.get_config_dict()

if __name__ == "__main__":
    # Test the configuration when run directly
    print("🔧 Testing centralized database configuration...")
    
    # Test connection
    if test_db_connection():
        print("✅ Database configuration is working correctly!")
        print(f"📊 Connection: {db_config.get_connection_info()}")
        
        # Show configuration (without password)
        config = get_db_config()
        safe_config = {k: v for k, v in config.items() if 'password' not in k.lower()}
        print(f"⚙️  Configuration: {safe_config}")
    else:
        print("❌ Database configuration test failed!")
        exit(1)