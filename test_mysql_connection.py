#!/usr/bin/env python3
"""
Database Connection Test - Try different MySQL connection methods
"""
import pymysql
import mysql.connector
import subprocess
import os

def test_mysql_connections():
    """Test various MySQL connection configurations"""
    print("🔍 TESTING MYSQL CONNECTION METHODS")
    print("=" * 50)
    
    # Different connection configurations to try
    connection_configs = [
        # PyMySQL configurations
        {
            'name': 'PyMySQL - root with empty password',
            'method': 'pymysql',
            'config': {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '', 'charset': 'utf8mb4'}
        },
        {
            'name': 'PyMySQL - root with rootpassword',
            'method': 'pymysql',
            'config': {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'rootpassword', 'charset': 'utf8mb4'}
        },
        {
            'name': 'PyMySQL - root with 99Rules!',
            'method': 'pymysql',
            'config': {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '99Rules!', 'charset': 'utf8mb4'}
        },
        
        # MySQL Connector configurations
        {
            'name': 'MySQL Connector - root with empty password',
            'method': 'mysql_connector',
            'config': {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''}
        },
        {
            'name': 'MySQL Connector - root with rootpassword',
            'method': 'mysql_connector',
            'config': {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'rootpassword'}
        },
        {
            'name': 'MySQL Connector - root with 99Rules!',
            'method': 'mysql_connector',
            'config': {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '99Rules!'}
        },
    ]
    
    successful_config = None
    
    for test_config in connection_configs:
        try:
            print(f"\n🎯 Testing: {test_config['name']}")
            
            if test_config['method'] == 'pymysql':
                connection = pymysql.connect(**test_config['config'])
            else:  # mysql_connector
                connection = mysql.connector.connect(**test_config['config'])
            
            print(f"  ✅ Connection successful!")
            
            # Test basic query
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"  📊 MySQL Version: {version[0] if version else 'Unknown'}")
            
            # List databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print(f"  📚 Databases: {[db[0] for db in databases]}")
            
            # Check for crypto databases
            cursor.execute("SHOW DATABASES LIKE 'crypto_%'")
            crypto_dbs = cursor.fetchall()
            print(f"  🔍 Crypto Databases: {[db[0] for db in crypto_dbs]}")
            
            cursor.close()
            connection.close()
            
            successful_config = test_config
            break
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    return successful_config

def check_database_structure(config):
    """Check the structure of crypto databases"""
    print("\n🏗️ CHECKING DATABASE STRUCTURE")
    print("-" * 40)
    
    try:
        if config['method'] == 'pymysql':
            connection = pymysql.connect(**config['config'])
        else:
            connection = mysql.connector.connect(**config['config'])
            
        cursor = connection.cursor()
        
        # Check crypto_news database
        try:
            cursor.execute("USE crypto_news")
            cursor.execute("SHOW TABLES")
            news_tables = cursor.fetchall()
            print(f"📰 crypto_news tables: {[table[0] for table in news_tables]}")
            
            if news_tables:
                for table in news_tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} records")
        except Exception as e:
            print(f"❌ crypto_news database issue: {e}")
        
        # Check crypto_prices database
        try:
            cursor.execute("USE crypto_prices")
            cursor.execute("SHOW TABLES")
            price_tables = cursor.fetchall()
            print(f"\n💰 crypto_prices tables: {[table[0] for table in price_tables]}")
            
            if price_tables:
                for table in price_tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} records")
        except Exception as e:
            print(f"❌ crypto_prices database issue: {e}")
        
        # Check users
        cursor.execute("SELECT user, host FROM mysql.user WHERE user LIKE '%collector%' OR user = 'root'")
        users = cursor.fetchall()
        print(f"\n👤 Relevant users: {[(user[0], user[1]) for user in users]}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Failed to check database structure: {e}")

def create_missing_users_and_tables(config):
    """Create missing users and tables using the working connection"""
    print("\n🔧 CREATING MISSING USERS AND TABLES")
    print("-" * 40)
    
    try:
        if config['method'] == 'pymysql':
            connection = pymysql.connect(**config['config'])
        else:
            connection = mysql.connector.connect(**config['config'])
            
        cursor = connection.cursor()
        
        # Create databases
        print("📊 Creating databases...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_news")
        cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_prices")
        connection.commit()
        print("✅ Databases created/verified")
        
        # Create users
        print("\n👤 Creating users...")
        users_to_create = [
            ('news_collector', '99Rules!'),
            ('price_collector', '99Rules!'),
            ('enhanced_crypto_prices', '99Rules!'),
            ('technical_indicators', '99Rules!'),
            ('macro_economic', '99Rules!'),
            ('social_other', '99Rules!'),
            ('onchain_data', '99Rules!'),
        ]
        
        for username, password in users_to_create:
            try:
                cursor.execute(f"DROP USER IF EXISTS '{username}'@'%'")
                cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'")
                cursor.execute(f"GRANT ALL PRIVILEGES ON crypto_news.* TO '{username}'@'%'")
                cursor.execute(f"GRANT ALL PRIVILEGES ON crypto_prices.* TO '{username}'@'%'")
                print(f"  ✅ Created user {username}")
            except Exception as e:
                print(f"  ❌ Failed to create user {username}: {e}")
        
        cursor.execute("FLUSH PRIVILEGES")
        connection.commit()
        
        # Create crypto_news table
        print("\n📰 Creating crypto_news table...")
        cursor.execute("USE crypto_news")
        create_news_table = """
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
        cursor.execute(create_news_table)
        print("✅ crypto_news table created")
        
        # Create crypto_prices tables
        print("\n💰 Creating crypto_prices tables...")
        cursor.execute("USE crypto_prices")
        
        create_prices_table = """
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
        cursor.execute(create_prices_table)
        
        create_tech_table = """
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
        cursor.execute(create_tech_table)
        print("✅ crypto_prices tables created")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n✅ DATABASE SETUP COMPLETE!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create users and tables: {e}")
        return False

def main():
    print("🚀 MYSQL CONNECTION AND SETUP TEST")
    print("=" * 60)
    
    # Test connections
    working_config = test_mysql_connections()
    
    if not working_config:
        print("\n❌ Could not establish any MySQL connection")
        return
    
    print(f"\n✅ Using working configuration: {working_config['name']}")
    
    # Check current structure
    check_database_structure(working_config)
    
    # Create missing components
    success = create_missing_users_and_tables(working_config)
    
    if success:
        print("\n🎉 SUCCESS! Database setup complete.")
        print("Services should now be able to connect and store data.")
    else:
        print("\n❌ Setup failed. Check the errors above.")

if __name__ == "__main__":
    main()