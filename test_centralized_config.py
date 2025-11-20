#!/usr/bin/env python3
"""
Centralized Configuration Test and Summary
This script demonstrates how the centralized config automatically handles different environments.
"""

import os
import sys

# Add project root to path
sys.path.append('.')

def test_environment_detection():
    """Test the environment detection in different scenarios"""
    print("🌍 Testing Environment Detection")
    print("=" * 40)
    
    from shared.database_config import DatabaseConfig
    
    # Test 1: Normal WSL environment
    print("\n1️⃣ Normal WSL Environment:")
    config = DatabaseConfig()
    print(f"   Environment: {config.environment}")
    print(f"   MySQL Host: {config.mysql_config['host']}")
    print(f"   MySQL Database: {config.mysql_config['database']}")
    
    # Test 2: Test environment
    print("\n2️⃣ Test Environment (TESTING=true):")
    os.environ['TESTING'] = 'true'
    config_test = DatabaseConfig()
    print(f"   Environment: {config_test.environment}")
    print(f"   MySQL Host: {config_test.mysql_config['host']}")
    print(f"   MySQL Database: {config_test.mysql_config['database']}")
    
    # Test 3: CI environment simulation
    print("\n3️⃣ CI/CD Environment (CI=true):")
    os.environ['CI'] = 'true'
    os.environ.pop('TESTING', None)
    config_ci = DatabaseConfig()
    print(f"   Environment: {config_ci.environment}")
    print(f"   MySQL Host: {config_ci.mysql_config['host']}")
    print(f"   MySQL Database: {config_ci.mysql_config['database']}")
    
    # Cleanup
    os.environ.pop('CI', None)
    os.environ.pop('TESTING', None)

def test_environment_variables():
    """Test how environment variables override defaults"""
    print("\n🔧 Testing Environment Variable Overrides")
    print("=" * 50)
    
    # Set custom environment variables
    os.environ['MYSQL_HOST'] = '192.168.1.100'
    os.environ['MYSQL_PORT'] = '3307'
    os.environ['MYSQL_DATABASE'] = 'custom_db'
    
    from shared.database_config import DatabaseConfig
    config = DatabaseConfig()
    
    print(f"   Custom Host: {config.mysql_config['host']}")
    print(f"   Custom Port: {config.mysql_config['port']}")
    print(f"   Custom Database: {config.mysql_config['database']}")
    
    # Cleanup
    os.environ.pop('MYSQL_HOST', None)
    os.environ.pop('MYSQL_PORT', None)
    os.environ.pop('MYSQL_DATABASE', None)

def show_configuration_summary():
    """Show the complete configuration summary"""
    print("\n📋 Configuration Summary")
    print("=" * 30)
    
    from shared.database_config import db_config
    
    mysql_config = db_config.get_mysql_config_dict()
    redis_config = db_config.get_redis_config_dict()
    
    print(f"🌍 Environment: {db_config.environment}")
    print(f"📊 MySQL Connection: {db_config.get_connection_info()}")
    print(f"📊 Redis Connection: {db_config.get_redis_info()}")
    
    print("\n⚙️ MySQL Configuration:")
    for key, value in mysql_config.items():
        if 'password' in key.lower():
            value = '[REDACTED]'
        print(f"   {key}: {value}")
    
    print("\n⚙️ Redis Configuration:")
    for key, value in redis_config.items():
        print(f"   {key}: {value}")

def show_usage_examples():
    """Show how to use the centralized configuration in your code"""
    print("\n💡 Usage Examples")
    print("=" * 20)
    
    examples = [
        ("Simple MySQL Connection", 
         "from shared.database_config import get_db_connection\nconn = get_db_connection()"),
        
        ("Redis Connection", 
         "from shared.database_config import get_redis_connection\nredis_client = get_redis_connection()"),
        
        ("Test Connection", 
         "from shared.database_config import db_config\nif db_config.test_mysql_connection():\n    print('MySQL is ready!')"),
        
        ("Get Raw Config", 
         "from shared.database_config import get_db_config\nconfig = get_db_config()\nmysql.connector.connect(**config)")
    ]
    
    for title, code in examples:
        print(f"\n🔹 {title}:")
        for line in code.split('\n'):
            print(f"   {line}")

def main():
    print("🚀 Centralized Database Configuration Demo")
    print("=" * 50)
    
    # Run all tests
    test_environment_detection()
    test_environment_variables()
    show_configuration_summary()
    show_usage_examples()
    
    print(f"\n✅ Configuration Demo Complete!")
    print(f"\n💡 Key Benefits:")
    print(f"   - Automatic environment detection (WSL/CI/Docker/Local)")
    print(f"   - Windows host IP detection for WSL")
    print(f"   - Test database switching")
    print(f"   - Environment variable overrides")
    print(f"   - Centralized connection management")
    print(f"   - Redis and MySQL support")

if __name__ == "__main__":
    main()