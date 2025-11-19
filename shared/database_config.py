#!/usr/bin/env python3
"""
Centralized Database Configuration Module
This module provides a single source of truth for database connections
that works in CI/CD, Kubernetes (using ConfigMaps/Secrets), local development,
and Windows/WSL environments.
"""
import os
import sys
import mysql.connector
from typing import Dict, Optional, Any
import logging
import socket

# Try to import redis, make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

def get_wsl_windows_host() -> str:
    """
    Get the Windows host IP when running in WSL.
    Falls back to localhost if not in WSL or can't detect.
    """
    try:
        # Check if we're in WSL
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower():
                # We're in WSL, get Windows host IP
                with open('/etc/resolv.conf', 'r') as resolv:
                    for line in resolv:
                        if 'nameserver' in line:
                            host_ip = line.split()[1].strip()
                            logger.debug(f"🐧 WSL detected, Windows host IP: {host_ip}")
                            return host_ip
    except (FileNotFoundError, IndexError):
        pass
    
    # Not in WSL or couldn't detect, use localhost
    return 'localhost'

def detect_environment() -> str:
    """Detect the current environment: ci, docker, wsl, or local"""
    if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
        return 'ci'
    elif os.path.exists('/.dockerenv'):
        return 'docker'
    elif get_wsl_windows_host() != 'localhost':
        return 'wsl'
    else:
        return 'local'

class DatabaseConfig:
    """Centralized database configuration manager"""
    
    def __init__(self):
        """Initialize database configuration from environment variables"""
        self.environment = detect_environment()
        self.mysql_config = self._load_mysql_config()
        self.redis_config = self._load_redis_config()
        
        logger.info(f"🌍 Environment detected: {self.environment}")
        logger.info(f"🔧 MySQL config: {self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']}")
        logger.info(f"🔧 Redis config: {self.redis_config['host']}:{self.redis_config['port']}")
        
    def _get_default_host(self) -> str:
        """Get default database host based on environment"""
        if self.environment == 'ci':
            return '127.0.0.1'  # CI/CD services
        elif self.environment == 'docker':
            return 'mysql'  # Docker compose service name
        elif self.environment == 'wsl':
            return get_wsl_windows_host()  # Windows host IP
        else:
            return 'localhost'  # Local development
            
    def _is_test_environment(self) -> bool:
        """Check if we're in a test environment"""
        return (
            'test' in os.getenv('PYTEST_CURRENT_TEST', '').lower() or
            os.getenv('TESTING') == 'true' or
            'pytest' in ' '.join(sys.argv).lower() or
            any('test' in arg.lower() for arg in sys.argv) or
            # Check if running from pytest process
            any('pytest' in part for part in os.getenv('_', '').split('/')) or
            # Check command line for pytest
            'pytest' in os.getenv('PS1', '') or
            # Check process name
            'pytest' in str(sys.argv[0]).lower()
        )
        
    def _load_mysql_config(self) -> Dict[str, Any]:
        """Load MySQL configuration from environment variables with smart defaults"""
        is_testing = self._is_test_environment()
        default_host = self._get_default_host()
        
        # Use test-specific settings if in test environment
        if is_testing:
            # In CI environment, use existing database with test tables
            if os.getenv('CI') == 'true':
                default_database = 'crypto_news'
                # CI environment needs specific host override - force use of correct MySQL instance
                ci_host = os.getenv('MYSQL_HOST')
                if ci_host:
                    default_host = ci_host
                else:
                    # Fallback to known working CI MySQL host
                    default_host = '172.22.32.1'
            else:
                default_database = 'crypto_data_test'
        else:
            default_database = 'crypto_prices'
        
        # CI environment overrides for integration tests
        if os.getenv('CI') == 'true' and is_testing:
            # Force specific CI configuration to use existing database with test tables
            config = {
                'host': '172.22.32.1',  # Known working MySQL host in CI
                'port': 3306,
                'user': 'news_collector',
                'password': '99Rules!',
                'database': 'crypto_news',  # Database with test tables
                'connect_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
                'autocommit': True,
                'charset': 'utf8mb4',
                'use_unicode': True,
                'pool_name': f'pool_{os.getpid()}_{self.environment}',
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'pool_reset_session': True,
            }
            logger.info(f"🎯 CI Test Override: Using {config['host']}:{config['port']}/{config['database']}")
        else:
            # Standard configuration logic
            config = {
                'host': os.getenv('MYSQL_HOST') or os.getenv('DB_HOST', default_host),
                'port': int(os.getenv('MYSQL_PORT') or os.getenv('DB_PORT', '3306')),
                'user': os.getenv('MYSQL_USER') or os.getenv('DB_USER', 'news_collector'),
                'password': os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD', '99Rules!'),
                'database': os.getenv('MYSQL_DATABASE') or os.getenv('DB_NAME', default_database),
                'connect_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
                'autocommit': True,
                'charset': 'utf8mb4',
                'use_unicode': True,
                'pool_name': f'pool_{os.getpid()}_{self.environment}',
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'pool_reset_session': True,
            }
        
        return config
        
    def _load_redis_config(self) -> Dict[str, Any]:
        """Load Redis configuration from environment variables with smart defaults"""
        default_host = self._get_default_host()
        
        # Use docker service name for Redis in docker environment
        if self.environment == 'docker':
            default_host = 'redis'
            
        config = {
            'host': os.getenv('REDIS_HOST', default_host),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'decode_responses': True,
            'socket_connect_timeout': int(os.getenv('REDIS_TIMEOUT', '10')),
            'socket_timeout': int(os.getenv('REDIS_TIMEOUT', '10')),
        }
        
        return config
    
    def get_connection(self) -> mysql.connector.MySQLConnection:
        """Get a MySQL database connection"""
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            logger.debug("✅ MySQL connection established")
            return connection
        except mysql.connector.Error as e:
            logger.error(f"❌ MySQL connection failed: {e}")
            logger.error(f"   Config: {self.get_connection_info()}")
            raise
    
    def get_redis_connection(self) -> 'redis.Redis':
        """Get a Redis connection"""
        if not REDIS_AVAILABLE:
            raise ImportError("Redis package not installed. Install with: pip install redis")
            
        try:
            client = redis.Redis(**self.redis_config)
            # Test the connection
            client.ping()
            logger.debug("✅ Redis connection established")
            return client
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.error(f"   Config: {self.redis_config['host']}:{self.redis_config['port']}")
            raise
    
    def get_mysql_config_dict(self) -> Dict[str, Any]:
        """Get MySQL configuration dictionary for manual connection"""
        return self.mysql_config.copy()
        
    def get_redis_config_dict(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary for manual connection"""
        return self.redis_config.copy()
    
    def test_mysql_connection(self) -> bool:
        """Test MySQL database connectivity"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if result and result[0] == 1:
                logger.info("✅ MySQL connectivity test passed")
                return True
            else:
                logger.error("❌ MySQL connectivity test failed: Invalid response")
                return False
                
        except Exception as e:
            logger.error(f"❌ MySQL connectivity test failed: {e}")
            return False
            
    def test_redis_connection(self) -> bool:
        """Test Redis connectivity"""
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis package not available, skipping Redis test")
            return False
            
        try:
            client = self.get_redis_connection()
            response = client.ping()
            client.close()
            
            if response:
                logger.info("✅ Redis connectivity test passed")
                return True
            else:
                logger.error("❌ Redis connectivity test failed: No response")
                return False
                
        except Exception as e:
            logger.error(f"❌ Redis connectivity test failed: {e}")
            return False
    
    def get_connection_info(self) -> str:
        """Get MySQL connection info string for logging"""
        return f"{self.mysql_config['user']}@{self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']}"
        
    def get_redis_info(self) -> str:
        """Get Redis connection info string for logging"""
        return f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}"
        
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all database connections"""
        results = {
            'mysql': self.test_mysql_connection(),
            'redis': self.test_redis_connection()
        }
        
        if all(results.values()):
            logger.info("✅ All database connections working")
        else:
            failed = [db for db, status in results.items() if not status]
            logger.error(f"❌ Failed connections: {failed}")
            
        return results

# Global instance for easy import
db_config = DatabaseConfig()

# Convenience functions for backward compatibility
def get_db_connection() -> mysql.connector.MySQLConnection:
    """Get a MySQL database connection - convenience function"""
    return db_config.get_connection()

def get_redis_connection() -> 'redis.Redis':
    """Get a Redis connection - convenience function"""
    return db_config.get_redis_connection()

def test_db_connection() -> bool:
    """Test MySQL database connection - convenience function"""
    return db_config.test_mysql_connection()

def test_redis_connection() -> bool:
    """Test Redis connection - convenience function"""
    return db_config.test_redis_connection()

def get_db_config() -> Dict[str, Any]:
    """Get MySQL database configuration - convenience function"""
    return db_config.get_mysql_config_dict()

def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration - convenience function"""
    return db_config.get_redis_config_dict()

if __name__ == "__main__":
    # Test the configuration when run directly
    print("🔧 Testing centralized database configuration...")
    print(f"🌍 Environment: {db_config.environment}")
    print(f"📊 MySQL: {db_config.get_connection_info()}")
    print(f"📊 Redis: {db_config.get_redis_info()}")
    
    # Test connections
    results = db_config.test_all_connections()
    
    if all(results.values()):
        print("✅ All database configurations are working correctly!")
        
        # Show configuration (without sensitive data)
        mysql_config = get_db_config()
        safe_mysql_config = {k: v for k, v in mysql_config.items() if 'password' not in k.lower()}
        print(f"⚙️  MySQL Configuration: {safe_mysql_config}")
        
        redis_config = get_redis_config()
        print(f"⚙️  Redis Configuration: {redis_config}")
    else:
        failed = [db for db, status in results.items() if not status]
        print(f"❌ Database configuration test failed for: {failed}")
        print("\n💡 Troubleshooting:")
        if not results['mysql']:
            print("   MySQL: Check credentials, database exists, and service is running")
        if not results['redis']:
            print("   Redis: Check service is running and accessible")
        exit(1)