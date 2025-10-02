#!/usr/bin/env python3
"""
Database Schema Fix - Create missing tables with correct users
"""
import subprocess
import pymysql
import time

def setup_database_users_and_tables():
    """Set up database users and tables that are missing"""
    print("🔧 SETTING UP DATABASE USERS AND TABLES")
    print("=" * 50)
    
    # Connect as root to set up users and databases
    try:
        print("🔐 Connecting as root to setup databases...")
        
        # Try different root connection methods
        connection_configs = [
            {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''},
            {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'rootpassword'},
            {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': ''},
            {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'rootpassword'},
        ]
        
        connection = None
        for config in connection_configs:
            try:
                print(f"  Trying {config['host']} with user {config['user']}...")
                connection = pymysql.connect(**config, charset='utf8mb4')
                print(f"  ✅ Connected!")
                break
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                continue
        
        if not connection:
            print("❌ Could not connect to MySQL as root")
            return False
        
        with connection.cursor() as cursor:
            # Create databases if they don't exist
            print("\n📊 Creating databases...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_prices")
            cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_news")
            print("✅ Databases created/verified")
            
            # Create users if they don't exist
            print("\n👤 Creating users...")
            
            users_to_create = [
                ('news_collector', '99Rules!', 'crypto_news'),
                ('price_collector', '99Rules!', 'crypto_prices'),
                ('enhanced_crypto_prices', '99Rules!', 'crypto_prices'),
                ('technical_indicators', '99Rules!', 'crypto_prices'),
                ('macro_economic', '99Rules!', 'crypto_prices'),
                ('social_other', '99Rules!', 'crypto_prices'),
                ('onchain_data', '99Rules!', 'crypto_prices'),
            ]
            
            for username, password, database in users_to_create:
                try:
                    # Drop user if exists and recreate
                    cursor.execute(f"DROP USER IF EXISTS '{username}'@'%'")
                    cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'")
                    cursor.execute(f"GRANT ALL PRIVILEGES ON {database}.* TO '{username}'@'%'")
                    cursor.execute("FLUSH PRIVILEGES")
                    print(f"  ✅ Created user {username} with access to {database}")
                except Exception as e:
                    print(f"  ❌ Failed to create user {username}: {e}")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup database: {e}")
        return False

def create_crypto_news_table():
    """Create the crypto_news table"""
    print("\n📰 CREATING CRYPTO_NEWS TABLE")
    print("-" * 40)
    
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='news_collector',
            password='99Rules!',
            database='crypto_news',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create crypto_news table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS crypto_news (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                content TEXT,
                url VARCHAR(1000) UNIQUE,
                source VARCHAR(100),
                published_at DATETIME,
                sentiment_score DECIMAL(3,2),
                sentiment_label VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_published_at (published_at),
                INDEX idx_source (source),
                INDEX idx_sentiment (sentiment_score)
            )
            """
            
            cursor.execute(create_table_sql)
            connection.commit()
            print("✅ crypto_news table created successfully")
            
            # Check if table exists and show structure
            cursor.execute("DESCRIBE crypto_news")
            columns = cursor.fetchall()
            print(f"📊 Table structure ({len(columns)} columns):")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
                
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create crypto_news table: {e}")
        return False

def create_crypto_prices_tables():
    """Create crypto_prices related tables"""
    print("\n💰 CREATING CRYPTO_PRICES TABLES")
    print("-" * 40)
    
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='price_collector',
            password='99Rules!',
            database='crypto_prices',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create main crypto_prices table
            create_prices_sql = """
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                price DECIMAL(20,8) NOT NULL,
                volume_24h DECIMAL(20,2),
                market_cap DECIMAL(20,2),
                price_change_24h DECIMAL(10,4),
                timestamp DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp),
                INDEX idx_timestamp (timestamp)
            )
            """
            
            cursor.execute(create_prices_sql)
            
            # Create technical indicators table
            create_tech_sql = """
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                rsi DECIMAL(10,4),
                macd DECIMAL(20,8),
                macd_signal DECIMAL(20,8),
                macd_histogram DECIMAL(20,8),
                bb_upper DECIMAL(20,8),
                bb_middle DECIMAL(20,8),
                bb_lower DECIMAL(20,8),
                sma_20 DECIMAL(20,8),
                ema_12 DECIMAL(20,8),
                ema_26 DECIMAL(20,8),
                timestamp DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp)
            )
            """
            
            cursor.execute(create_tech_sql)
            
            # Create macro economic indicators table
            create_macro_sql = """
            CREATE TABLE IF NOT EXISTS macro_indicators (
                id INT AUTO_INCREMENT PRIMARY KEY,
                indicator_name VARCHAR(50) NOT NULL,
                value DECIMAL(20,4),
                timestamp DATETIME NOT NULL,
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_indicator_timestamp (indicator_name, timestamp)
            )
            """
            
            cursor.execute(create_macro_sql)
            
            connection.commit()
            print("✅ crypto_prices tables created successfully")
            
            # Show table structure
            tables = ['crypto_prices', 'technical_indicators', 'macro_indicators']
            for table in tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"📊 {table} ({len(columns)} columns)")
                
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create crypto_prices tables: {e}")
        return False

def test_service_connections():
    """Test that services can now connect to their databases"""
    print("\n🔍 TESTING SERVICE CONNECTIONS")
    print("-" * 40)
    
    test_configs = [
        {
            'name': 'news_collector',
            'host': 'localhost',
            'port': 3306,
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_news',
            'table': 'crypto_news'
        },
        {
            'name': 'price_collector',
            'host': 'localhost',
            'port': 3306,
            'user': 'price_collector',
            'password': '99Rules!',
            'database': 'crypto_prices',
            'table': 'crypto_prices'
        }
    ]
    
    for config in test_configs:
        try:
            print(f"\n🎯 Testing {config['name']}...")
            connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset='utf8mb4'
            )
            
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {config['table']}")
                count = cursor.fetchone()[0]
                print(f"  ✅ Connected! Table {config['table']} has {count} records")
                
            connection.close()
            
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")

def main():
    print("🚀 DATABASE SCHEMA FIX")
    print("=" * 60)
    print("🎯 Setting up missing users, databases, and tables")
    print()
    
    # Step 1: Setup database users and permissions
    if not setup_database_users_and_tables():
        print("❌ Failed to setup database users")
        return
    
    # Step 2: Create crypto_news table
    if not create_crypto_news_table():
        print("❌ Failed to create crypto_news table")
        return
        
    # Step 3: Create crypto_prices tables
    if not create_crypto_prices_tables():
        print("❌ Failed to create crypto_prices tables")
        return
    
    # Step 4: Test connections
    test_service_connections()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE SCHEMA SETUP COMPLETE!")
    print("🎯 Services should now be able to connect and store data")

if __name__ == "__main__":
    main()