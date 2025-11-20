#!/usr/bin/env python3
"""
Test Database Schema Creation
This script creates the required database schema for CI/CD tests.
It automatically detects what databases exist and works with available permissions.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import mysql.connector
from mysql.connector import Error

def get_available_databases():
    """Get list of available databases and suggest the best option"""
    
    configs_to_try = [
        # CI/CD configuration
        {
            'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', '')
        },
        # Local configuration
        {
            'host': '172.22.32.1',
            'port': 3306,
            'user': 'root',
            'password': ''
        },
        # Alternative configurations
        {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': ''
        }
    ]
    
    for config in configs_to_try:
        try:
            print(f"🔍 Trying connection: {config['user']}@{config['host']}:{config['port']}")
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            # Get available databases
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            print(f"✅ Connected successfully!")
            print(f"📋 Available databases: {databases}")
            
            return config, databases
            
        except Error as e:
            print(f"❌ Failed: {e}")
            continue
    
    return None, []

def setup_integration_test_tables(config, database_name):
    """Setup tables in the specified database"""
    
    # Simple table schema that definitely works
    table_schemas = {
        'news_data': """
        CREATE TABLE IF NOT EXISTS news_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(500),
            content TEXT,
            url VARCHAR(1000),
            source VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'crypto_assets': """
        CREATE TABLE IF NOT EXISTS crypto_assets (
            id VARCHAR(50) PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            current_price DECIMAL(20,8),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'price_data_real': """
        CREATE TABLE IF NOT EXISTS price_data_real (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            current_price DECIMAL(20,8) NOT NULL,
            market_cap BIGINT,
            total_volume BIGINT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """
    }
    
    print(f"🔧 Setting up tables in database '{database_name}'...")
    
    try:
        # Connect to specific database
        db_config = config.copy()
        db_config['database'] = database_name
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        created_count = 0
        
        for table_name, schema in table_schemas.items():
            try:
                print(f"🔨 Creating {table_name}...")
                cursor.execute(schema)
                created_count += 1
                print(f"✅ {table_name} created")
            except Error as e:
                if "already exists" in str(e).lower():
                    print(f"⏭️  {table_name} already exists")
                else:
                    print(f"❌ Error creating {table_name}: {e}")
        
        connection.commit()
        
        # Insert minimal test data
        print(f"📝 Inserting test data...")
        
        # Test crypto assets
        cursor.execute("""
            INSERT IGNORE INTO crypto_assets (id, symbol, name, current_price)
            VALUES 
                ('bitcoin', 'BTC', 'Bitcoin', 45000.00),
                ('ethereum', 'ETH', 'Ethereum', 3200.00)
        """)
        
        # Test price data
        cursor.execute("""
            INSERT IGNORE INTO price_data_real (symbol, current_price, market_cap, total_volume)
            VALUES 
                ('BTC', 45000.00, 850000000000, 25000000000),
                ('ETH', 3200.00, 380000000000, 15000000000)
        """)
        
        connection.commit()
        
        # Verify setup
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"✅ Setup complete!")
        print(f"📊 Tables in {database_name}: {tables}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error setting up database: {e}")
        return False

def main():
    """Main function"""
    
    print("🚀 Integration Test Database Setup")
    print("=" * 40)
    
    # Step 1: Find working database connection
    config, databases = get_available_databases()
    
    if not config:
        print("❌ No working database connection found!")
        print("💡 In CI/CD, MySQL service should be available")
        print("💡 Locally, ensure MySQL is running and accessible")
        return False
    
    # Step 2: Determine target database
    target_db = None
    
    if 'crypto_data_test' in databases:
        target_db = 'crypto_data_test'
        print(f"🎯 Using existing test database: {target_db}")
    elif 'test' in databases:
        target_db = 'test'
        print(f"🎯 Using test database: {target_db}")
    elif 'information_schema' in databases:
        # Create test database
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_data_test")
            connection.commit()
            cursor.close()
            connection.close()
            target_db = 'crypto_data_test'
            print(f"🎯 Created and using: {target_db}")
        except:
            # Fallback to any available database
            available_dbs = [db for db in databases if db not in ['information_schema', 'performance_schema', 'mysql', 'sys']]
            if available_dbs:
                target_db = available_dbs[0]
                print(f"🎯 Using available database: {target_db}")
    
    if not target_db:
        print("❌ No suitable database found")
        return False
    
    # Step 3: Setup tables
    success = setup_integration_test_tables(config, target_db)
    
    if success:
        print(f"\n🎉 Integration test database setup complete!")
        print(f"📊 Database: {target_db}")
        print(f"🔗 Connection: {config['user']}@{config['host']}:{config['port']}")
        print(f"✅ Integration tests should now find required tables")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)