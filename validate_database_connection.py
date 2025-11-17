#!/usr/bin/env python3
"""
🔍 Database Connectivity Validation for CI/CD Pipeline

This script validates database connectivity using the actual production credentials
provided by the user (news_collector / 99Rules!).

Usage:
    python validate_database_connection.py
    python validate_database_connection.py --host localhost --user news_collector --password 99Rules!
"""

import argparse
import sys
import os
import time
from typing import Optional, Dict, Any

# Database connectivity testing
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("⚠️  MySQL connector not available. Install with: pip install mysql-connector-python")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available. Install with: pip install redis")

def test_mysql_connection(host: str, port: int, user: str, password: str, database: Optional[str] = None) -> Dict[str, Any]:
    """Test MySQL database connectivity."""
    if not MYSQL_AVAILABLE:
        return {
            "success": False,
            "error": "MySQL connector not installed",
            "suggestion": "pip install mysql-connector-python"
        }
    
    try:
        print(f"🔍 Testing MySQL connection to {host}:{port}")
        print(f"   User: {user}")
        print(f"   Database: {database or 'default'}")
        
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connection_timeout=10,
            autocommit=True
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            # Get server info
            cursor.execute("SELECT VERSION() as version")
            version = cursor.fetchone()[0]
            
            # Test database access
            cursor.execute("SELECT DATABASE() as current_db")
            current_db = cursor.fetchone()[0]
            
            # Test table creation permission
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ci_test_table (
                        id INT PRIMARY KEY,
                        test_data VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                table_creation = True
                
                # Test data insertion
                cursor.execute("INSERT IGNORE INTO ci_test_table (id, test_data) VALUES (1, 'CI/CD Test')")
                
                # Test data retrieval
                cursor.execute("SELECT COUNT(*) FROM ci_test_table")
                row_count = cursor.fetchone()[0]
                
                # Clean up test table
                cursor.execute("DROP TABLE IF EXISTS ci_test_table")
                
            except Error as e:
                table_creation = False
                print(f"⚠️  Table operations limited: {e}")
            
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "server_version": version,
                "current_database": current_db,
                "table_operations": table_creation,
                "test_result": result[0] if result else None,
                "connection_time": "< 10s"
            }
            
    except Error as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": getattr(e, 'errno', None),
            "suggestion": get_mysql_error_suggestion(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "suggestion": "Check network connectivity and credentials"
        }

def test_redis_connection(host: str, port: int, password: Optional[str] = None) -> Dict[str, Any]:
    """Test Redis connectivity."""
    if not REDIS_AVAILABLE:
        return {
            "success": False,
            "error": "Redis not installed",
            "suggestion": "pip install redis"
        }
    
    try:
        print(f"🔍 Testing Redis connection to {host}:{port}")
        
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            socket_timeout=10,
            socket_connect_timeout=10,
            decode_responses=True
        )
        
        # Test basic connectivity
        ping_result = r.ping()
        
        # Test data operations
        test_key = "ci_test_key"
        r.set(test_key, "CI/CD Test", ex=60)  # Expires in 60 seconds
        test_value = r.get(test_key)
        r.delete(test_key)
        
        # Get server info
        info = r.info()
        
        return {
            "success": True,
            "ping_result": ping_result,
            "test_data": test_value,
            "redis_version": info.get('redis_version', 'Unknown'),
            "memory_usage": info.get('used_memory_human', 'Unknown'),
            "connected_clients": info.get('connected_clients', 'Unknown')
        }
        
    except redis.ConnectionError as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}",
            "suggestion": "Check Redis server is running and accessible"
        }
    except redis.AuthenticationError as e:
        return {
            "success": False,
            "error": f"Authentication error: {str(e)}",
            "suggestion": "Check Redis password or disable AUTH"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "suggestion": "Check network connectivity"
        }

def get_mysql_error_suggestion(error: Error) -> str:
    """Get helpful suggestions for MySQL errors."""
    error_code = getattr(error, 'errno', None)
    error_msg = str(error).lower()
    
    if error_code == 1045 or 'access denied' in error_msg:
        return "Check username and password. User: news_collector, Password: 99Rules!"
    elif error_code == 2003 or 'can\'t connect' in error_msg:
        return "Check host and port. Ensure MySQL server is running and accessible."
    elif error_code == 1049 or 'unknown database' in error_msg:
        return "Database doesn't exist. Create it or connect without specifying database."
    elif 'timeout' in error_msg:
        return "Connection timeout. Check network connectivity or increase timeout."
    else:
        return "Check MySQL server status and network connectivity."

def main():
    parser = argparse.ArgumentParser(description='Validate database connectivity for CI/CD pipeline')
    parser.add_argument('--mysql-host', default=os.getenv('MYSQL_HOST', '127.0.0.1'),
                       help='MySQL host (default: 127.0.0.1)')
    parser.add_argument('--mysql-port', type=int, default=int(os.getenv('MYSQL_PORT', '3306')),
                       help='MySQL port (default: 3306)')
    parser.add_argument('--mysql-user', default=os.getenv('MYSQL_USER', 'news_collector'),
                       help='MySQL user (default: news_collector)')
    parser.add_argument('--mysql-password', default=os.getenv('MYSQL_PASSWORD', '99Rules!'),
                       help='MySQL password (default: 99Rules!)')
    parser.add_argument('--mysql-database', default=os.getenv('MYSQL_DATABASE'),
                       help='MySQL database (optional)')
    
    parser.add_argument('--redis-host', default=os.getenv('REDIS_HOST', '127.0.0.1'),
                       help='Redis host (default: 127.0.0.1)')
    parser.add_argument('--redis-port', type=int, default=int(os.getenv('REDIS_PORT', '6379')),
                       help='Redis port (default: 6379)')
    parser.add_argument('--redis-password', default=os.getenv('REDIS_PASSWORD'),
                       help='Redis password (optional)')
    
    parser.add_argument('--skip-mysql', action='store_true',
                       help='Skip MySQL connectivity test')
    parser.add_argument('--skip-redis', action='store_true',
                       help='Skip Redis connectivity test')
    
    args = parser.parse_args()
    
    print("🚀 Database Connectivity Validation for CI/CD Pipeline")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Test MySQL
    if not args.skip_mysql:
        total_tests += 1
        print("\n📊 MySQL Database Testing")
        print("-" * 30)
        
        mysql_result = test_mysql_connection(
            args.mysql_host, args.mysql_port, args.mysql_user, 
            args.mysql_password, args.mysql_database
        )
        
        if mysql_result["success"]:
            success_count += 1
            print("✅ MySQL Connection: SUCCESS")
            print(f"   Server Version: {mysql_result['server_version']}")
            print(f"   Current Database: {mysql_result['current_database']}")
            print(f"   Table Operations: {'✅ Enabled' if mysql_result['table_operations'] else '⚠️  Limited'}")
            print(f"   Test Query Result: {mysql_result['test_result']}")
        else:
            print("❌ MySQL Connection: FAILED")
            print(f"   Error: {mysql_result['error']}")
            print(f"   Suggestion: {mysql_result['suggestion']}")
    
    # Test Redis  
    if not args.skip_redis:
        total_tests += 1
        print("\n🔄 Redis Cache Testing")
        print("-" * 30)
        
        redis_result = test_redis_connection(
            args.redis_host, args.redis_port, args.redis_password
        )
        
        if redis_result["success"]:
            success_count += 1
            print("✅ Redis Connection: SUCCESS")
            print(f"   Redis Version: {redis_result['redis_version']}")
            print(f"   Memory Usage: {redis_result['memory_usage']}")
            print(f"   Connected Clients: {redis_result['connected_clients']}")
            print(f"   Test Data: {redis_result['test_data']}")
        else:
            print("❌ Redis Connection: FAILED")
            print(f"   Error: {redis_result['error']}")
            print(f"   Suggestion: {redis_result['suggestion']}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🎯 Validation Summary: {success_count}/{total_tests} services connected")
    
    if success_count == total_tests:
        print("🏆 ALL SYSTEMS READY FOR CI/CD PIPELINE!")
        print("\n✅ Your database integration testing is ready to run.")
        print("✅ Set ENABLE_DATABASE_TESTS=true in GitHub repository variables.")
        print("✅ Add database secrets to GitHub repository secrets.")
        print("✅ Push code to trigger the complete CI/CD pipeline.")
        sys.exit(0)
    else:
        print("🚨 SOME SYSTEMS NEED ATTENTION")
        print(f"\n❌ {total_tests - success_count} service(s) failed connectivity test.")
        print("❌ Review error messages above and fix connectivity issues.")
        print("❌ Database integration tests may fail in CI/CD pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    main()