#!/usr/bin/env python3
"""
Local Windows MySQL Configuration Helper

This script helps you configure the correct MySQL settings for your local Windows MySQL server
when running tests from WSL.
"""

import os
import mysql.connector
from mysql.connector import Error
import sys

def get_windows_host_ip():
    """Get the Windows host IP from WSL resolv.conf"""
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if 'nameserver' in line:
                    return line.split()[1].strip()
    except:
        return '172.22.32.1'  # Default WSL2 gateway
    return 'localhost'

def test_mysql_connection(host, port, user, password, database=None):
    """Test MySQL connection with given parameters"""
    try:
        config = {
            'host': host,
            'port': int(port),
            'user': user,
            'password': password,
            'connect_timeout': 10
        }
        
        if database:
            config['database'] = database
            
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Test query
            if database:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print(f"✅ Successfully connected to database '{database}'")
            else:
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                print(f"✅ Successfully connected to MySQL server")
                print("📋 Available databases:")
                for db in databases:
                    print(f"   - {db[0]}")
                    
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🔧 Local Windows MySQL Configuration Helper")
    print("=" * 50)
    
    # Get Windows host IP
    windows_host = get_windows_host_ip()
    print(f"🌐 Windows host IP detected: {windows_host}")
    
    # Test current configuration first
    print(f"\n🧪 Testing current test configuration...")
    current_config = {
        'host': windows_host,
        'port': 3306,
        'user': 'news_collector',
        'password': '99Rules!',
        'database': 'crypto_data_test'
    }
    
    print(f"   Host: {current_config['host']}")
    print(f"   Port: {current_config['port']}")
    print(f"   User: {current_config['user']}")
    print(f"   Database: {current_config['database']}")
    
    if test_mysql_connection(**current_config):
        print("\n🎉 Current configuration works! No changes needed.")
        
        # Set environment variables
        print(f"\n📝 Setting environment variables for testing:")
        os.environ['MYSQL_HOST'] = current_config['host']
        os.environ['MYSQL_PORT'] = str(current_config['port'])
        os.environ['MYSQL_USER'] = current_config['user']
        os.environ['MYSQL_PASSWORD'] = current_config['password']
        os.environ['MYSQL_DATABASE'] = current_config['database']
        
        for key, value in [('MYSQL_HOST', current_config['host']),
                          ('MYSQL_PORT', str(current_config['port'])),
                          ('MYSQL_USER', current_config['user']),
                          ('MYSQL_PASSWORD', current_config['password']),
                          ('MYSQL_DATABASE', current_config['database'])]:
            print(f"   export {key}='{value}'")
        
        return True
    
    print("\n🔍 Testing common MySQL configurations...")
    
    # Common MySQL setups
    test_configs = [
        {'user': 'root', 'password': '', 'desc': 'root with no password'},
        {'user': 'root', 'password': 'root', 'desc': 'root:root'},
        {'user': 'root', 'password': 'password', 'desc': 'root:password'},
        {'user': 'mysql', 'password': 'mysql', 'desc': 'mysql:mysql'},
        {'user': 'admin', 'password': 'admin', 'desc': 'admin:admin'},
    ]
    
    for config in test_configs:
        print(f"\n   Testing {config['desc']}...")
        if test_mysql_connection(windows_host, 3306, config['user'], config['password']):
            
            # Found working connection, now check for the database
            print(f"\n✅ Found working MySQL connection: {config['user']}")
            
            # Try to create the database and user if needed
            try:
                connection = mysql.connector.connect(
                    host=windows_host,
                    port=3306,
                    user=config['user'],
                    password=config['password']
                )
                cursor = connection.cursor()
                
                # Check if database exists
                cursor.execute("SHOW DATABASES LIKE 'crypto_data_test'")
                if not cursor.fetchone():
                    print("   Creating database 'crypto_data_test'...")
                    cursor.execute("CREATE DATABASE crypto_data_test")
                
                # Check if user exists
                cursor.execute("SELECT User FROM mysql.user WHERE User = 'news_collector'")
                if not cursor.fetchone():
                    print("   Creating user 'news_collector'...")
                    cursor.execute("CREATE USER 'news_collector'@'%' IDENTIFIED BY '99Rules!'")
                    cursor.execute("GRANT ALL PRIVILEGES ON crypto_data_test.* TO 'news_collector'@'%'")
                    cursor.execute("FLUSH PRIVILEGES")
                
                cursor.close()
                connection.close()
                
                # Test the final configuration
                print(f"\n🧪 Testing final configuration...")
                if test_mysql_connection(windows_host, 3306, 'news_collector', '99Rules!', 'crypto_data_test'):
                    print(f"\n🎉 MySQL setup complete!")
                    print(f"\n📝 Use these environment variables:")
                    print(f"   export MYSQL_HOST='{windows_host}'")
                    print(f"   export MYSQL_PORT='3306'")
                    print(f"   export MYSQL_USER='news_collector'")
                    print(f"   export MYSQL_PASSWORD='99Rules!'")
                    print(f"   export MYSQL_DATABASE='crypto_data_test'")
                    return True
                    
            except Error as e:
                print(f"   ⚠️  Could not setup database/user: {e}")
                print(f"   💡 You may need to manually create:")
                print(f"      - Database: crypto_data_test")
                print(f"      - User: news_collector with password '99Rules!'")
                print(f"      - Permissions: GRANT ALL ON crypto_data_test.* TO 'news_collector'@'%'")
            
            break
    else:
        print("\n❌ Could not find working MySQL configuration")
        print("\n💡 Manual setup required:")
        print("   1. Open MySQL command line or MySQL Workbench")
        print("   2. Run these commands:")
        print("      CREATE DATABASE crypto_data_test;")
        print("      CREATE USER 'news_collector'@'%' IDENTIFIED BY '99Rules!';")
        print("      GRANT ALL PRIVILEGES ON crypto_data_test.* TO 'news_collector'@'%';")
        print("      FLUSH PRIVILEGES;")
        print(f"   3. Ensure MySQL is listening on 0.0.0.0:3306 (not just 127.0.0.1)")
        
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)