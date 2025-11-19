#!/usr/bin/env python3
"""
Quick database connectivity test for CI environments
"""

import os
import subprocess

def check_mysql_service():
    """Check if MySQL service is running"""
    print("🔍 Checking MySQL service status...")
    
    # Check if we can reach the MySQL port
    try:
        result = subprocess.run(
            ['nc', '-z', '172.22.32.1', '3306'], 
            capture_output=True, 
            timeout=5
        )
        if result.returncode == 0:
            print("✅ MySQL port 3306 is reachable")
            return True
        else:
            print("❌ MySQL port 3306 is not reachable")
    except:
        print("❌ Cannot test MySQL connectivity (nc not available)")
    
    return False

def try_basic_mysql_connection():
    """Try basic MySQL connection with common CI patterns"""
    
    # Common CI MySQL configurations
    configs = [
        {
            'host': '172.22.32.1',
            'port': 3306,
            'user': 'root',
            'password': 'root'
        },
        {
            'host': '172.22.32.1', 
            'port': 3306,
            'user': 'root',
            'password': 'password'
        },
        {
            'host': '172.22.32.1',
            'port': 3306,
            'user': 'root',
            'password': ''
        },
        {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root', 
            'password': ''
        }
    ]
    
    for i, config in enumerate(configs):
        print(f"\n🔧 Test {i+1}: {config['user']}@{config['host']}:{config['port']} (pwd: {'***' if config['password'] else 'empty'})")
        
        try:
            import mysql.connector
            connection = mysql.connector.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                connect_timeout=5
            )
            
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            print(f"✅ Success! MySQL {version[0]}")
            print(f"📋 Databases: {databases}")
            
            return config, databases
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    return None, []

def main():
    print("🚀 CI Database Connectivity Test")
    print("=" * 40)
    
    # Environment info
    print(f"Environment: CI={os.getenv('CI', 'false')}")
    print(f"MySQL Host: {os.getenv('MYSQL_HOST', 'not set')}")
    
    # Check service
    if check_mysql_service():
        print("\n🔍 Attempting MySQL connections...")
        config, databases = try_basic_mysql_connection()
        
        if config:
            print(f"\n🎉 Found working configuration!")
            print(f"Use: {config}")
            return True
        else:
            print(f"\n❌ No working MySQL configuration found")
    else:
        print("\n💡 MySQL service may not be ready yet")
        print("💡 In CI environments, services may take time to start")
    
    return False

if __name__ == "__main__":
    main()