#!/usr/bin/env python3
"""
Centralized Database Connection Pool
Shared connection pooling solution for all crypto data collection services
"""

import os
import logging
import time
import threading
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling, Error as MySQLError

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    """
    Centralized database connection pool manager
    Provides thread-safe connection pooling for all services
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure one pool per process"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnectionPool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the connection pool with configuration from environment"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._pool = None
        self._pool_lock = threading.Lock()
        
        # Database configuration from environment
        self.pool_config = {
            'pool_name': 'crypto_data_pool',
            'pool_size': int(os.getenv('DB_POOL_SIZE', '15')),
            'pool_reset_session': True,
            'host': os.getenv('MYSQL_HOST', 'host.docker.internal'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': False,  # Explicit transaction control
            'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO',
            'time_zone': '+00:00',
            'raise_on_warnings': True,
            'get_warnings': True,
            'connection_timeout': 30,
            'auth_plugin': 'mysql_native_password'
        }
        
        # Initialize pool
        self._create_pool()
    
    def _create_pool(self):
        """Create the MySQL connection pool"""
        try:
            with self._pool_lock:
                if self._pool is None:
                    self._pool = pooling.MySQLConnectionPool(**self.pool_config)
                    logger.info(f"✅ Database connection pool created: {self.pool_config['pool_name']} "
                              f"(size: {self.pool_config['pool_size']})")
        except MySQLError as e:
            logger.error(f"❌ Failed to create database connection pool: {e}")
            raise
    
    def get_connection(self, max_retries: int = 3) -> mysql.connector.MySQLConnection:
        """
        Get a connection from the pool with retry logic
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            MySQL connection from the pool
            
        Raises:
            MySQLError: If unable to get connection after retries
        """
        if self._pool is None:
            self._create_pool()
            
        for attempt in range(max_retries):
            try:
                connection = self._pool.get_connection()
                logger.debug(f"📊 Pool stats - Connections: {self._pool._cnx_queue.qsize()}")
                return connection
            except pooling.PoolError as e:
                if attempt == max_retries - 1:
                    logger.error(f"❌ Pool exhausted after {max_retries} attempts: {e}")
                    raise
                # Exponential backoff
                delay = 0.1 * (2 ** attempt)
                time.sleep(delay)
                logger.warning(f"⚠️  Pool busy, retrying in {delay}s (attempt {attempt + 1})")
        
        raise MySQLError("Failed to get connection from pool")
    
    @contextmanager
    def get_connection_context(self, max_retries: int = 3):
        """
        Context manager for database connections
        Automatically handles connection cleanup
        
        Usage:
            with pool.get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        connection = None
        try:
            connection = self.get_connection(max_retries)
            yield connection
        finally:
            if connection:
                try:
                    connection.close()  # Returns connection to pool
                except:
                    pass
    
    def execute_with_retry(self, query: str, params: tuple = None, 
                          max_retries: int = 3, fetch_results: bool = True) -> Optional[List]:
        """
        Execute a query with automatic retry on deadlocks
        
        Args:
            query: SQL query to execute
            params: Query parameters
            max_retries: Maximum retry attempts for deadlocks
            fetch_results: Whether to fetch and return results
            
        Returns:
            Query results if fetch_results=True, None otherwise
        """
        for attempt in range(max_retries):
            connection = None
            cursor = None
            
            try:
                connection = self.get_connection()
                cursor = connection.cursor()
                
                cursor.execute(query, params)
                
                if fetch_results:
                    results = cursor.fetchall()
                    connection.commit()
                    return results
                else:
                    connection.commit()
                    return None
                    
            except MySQLError as e:
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass
                
                # Handle deadlocks and lock timeouts with retry
                if e.errno in (1213, 1205):  # Deadlock or lock timeout
                    if attempt < max_retries - 1:
                        delay = 0.1 * (2 ** attempt) + (0.05 * attempt)
                        logger.warning(f"⚠️  Database lock issue (errno {e.errno}), "
                                     f"retrying in {delay:.2f}s (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Max retries exceeded for lock issue: {e}")
                        raise
                else:
                    logger.error(f"❌ Database error: {e}")
                    raise
                    
            except Exception as e:
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass
                logger.error(f"❌ Unexpected error: {e}")
                raise
                
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                if connection:
                    try:
                        connection.close()
                    except:
                        pass
        
        raise MySQLError("Failed to execute query after retries")
    
    def execute_batch_with_retry(self, query: str, batch_data: List[tuple], 
                                max_retries: int = 3) -> int:
        """
        Execute a batch operation with automatic retry on deadlocks
        
        Args:
            query: SQL query with placeholders
            batch_data: List of parameter tuples
            max_retries: Maximum retry attempts
            
        Returns:
            Number of affected rows
        """
        if not batch_data:
            return 0
        
        # Sort batch data for consistent lock ordering (prevent deadlocks)
        try:
            batch_data.sort()
        except TypeError:
            # If sorting fails, continue without sorting
            pass
        
        for attempt in range(max_retries):
            connection = None
            cursor = None
            
            try:
                connection = self.get_connection()
                cursor = connection.cursor()
                
                # Start explicit transaction
                connection.start_transaction()
                
                # Execute batch operation
                cursor.executemany(query, batch_data)
                
                # Commit transaction
                connection.commit()
                
                affected_rows = cursor.rowcount
                logger.info(f"✅ Batch operation completed: {affected_rows} rows affected")
                return affected_rows
                
            except MySQLError as e:
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass
                
                if e.errno in (1213, 1205):  # Deadlock or lock timeout
                    if attempt < max_retries - 1:
                        delay = 0.1 * (2 ** attempt) + (0.05 * attempt)
                        logger.warning(f"⚠️  Batch deadlock (errno {e.errno}), "
                                     f"retrying in {delay:.2f}s (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Batch operation failed after {max_retries} attempts: {e}")
                        raise
                else:
                    logger.error(f"❌ Batch database error: {e}")
                    raise
                    
            except Exception as e:
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass
                logger.error(f"❌ Unexpected batch error: {e}")
                raise
                
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                if connection:
                    try:
                        connection.close()
                    except:
                        pass
        
        return 0
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if self._pool is None:
            return {"status": "not_initialized"}
        
        try:
            return {
                "pool_name": self.pool_config['pool_name'],
                "pool_size": self.pool_config['pool_size'],
                "available_connections": self._pool._cnx_queue.qsize(),
                "host": self.pool_config['host'],
                "database": self.pool_config['database']
            }
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """Perform a health check on the connection pool"""
        try:
            with self.get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result[0] == 1
        except Exception as e:
            logger.error(f"❌ Pool health check failed: {e}")
            return False

# Global pool instance for easy import
database_pool = DatabaseConnectionPool()

# Convenience functions for common operations
def get_connection(max_retries: int = 3):
    """Get a database connection from the global pool"""
    return database_pool.get_connection(max_retries)

def get_connection_context(max_retries: int = 3):
    """Get a database connection context manager from the global pool"""
    return database_pool.get_connection_context(max_retries)

def execute_query(query: str, params: tuple = None, fetch_results: bool = True):
    """Execute a query using the global pool with automatic retry"""
    return database_pool.execute_with_retry(query, params, fetch_results=fetch_results)

def execute_batch(query: str, batch_data: List[tuple]):
    """Execute a batch operation using the global pool with automatic retry"""
    return database_pool.execute_batch_with_retry(query, batch_data)

def get_pool_stats():
    """Get statistics from the global pool"""
    return database_pool.get_pool_stats()

def health_check():
    """Perform a health check on the global pool"""
    return database_pool.health_check()

if __name__ == "__main__":
    # Test the connection pool
    print("🧪 Testing Database Connection Pool")
    print("=" * 40)
    
    try:
        # Test basic connection
        print("📡 Testing basic connection...")
        with get_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT NOW() as current_time, DATABASE() as db_name")
            result = cursor.fetchone()
            print(f"✅ Connected to database: {result[1]} at {result[0]}")
            cursor.close()
        
        # Test pool stats
        print("\n📊 Pool Statistics:")
        stats = get_pool_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test health check
        print(f"\n🏥 Health Check: {'✅ PASSED' if health_check() else '❌ FAILED'}")
        
    except Exception as e:
        print(f"❌ Connection pool test failed: {e}")