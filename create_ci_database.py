#!/usr/bin/env python3
"""
CI Environment Database Setup
Creates crypto_data_test database and all required tables on CI MySQL instance
"""

import mysql.connector
import sys
import os

def try_mysql_instances():
    """Try different MySQL instances to find the working one in CI"""
    
    instances = [
        # CI environment possibilities
        {'host': '127.0.0.1', 'port': 3306},
        {'host': '172.22.32.1', 'port': 3306},
        {'host': 'localhost', 'port': 3306},
        {'host': 'mysql', 'port': 3306},  # Docker service
    ]
    
    # Common CI credentials to try
    credentials = [
        {'user': 'root', 'password': ''},
        {'user': 'root', 'password': 'root'},
        {'user': 'root', 'password': 'password'},
        {'user': 'news_collector', 'password': '99Rules!'},
        {'user': 'test', 'password': 'test'},
    ]
    
    print("🔍 Scanning for available MySQL instances...")
    
    for instance in instances:
        host, port = instance['host'], instance['port']
        print(f"\n🎯 Testing {host}:{port}")
        
        for creds in credentials:
            user, password = creds['user'], creds['password']
            pwd_display = '***' if password else 'empty'
            
            try:
                print(f"   Trying {user}@{host}:{port} (pwd: {pwd_display})")
                
                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    connect_timeout=10
                )
                
                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                
                cursor.execute("SHOW DATABASES")
                databases = [db[0] for db in cursor.fetchall()]
                
                cursor.close()
                connection.close()
                
                print(f"   ✅ SUCCESS! MySQL {version}")
                print(f"   📋 Databases: {databases}")
                
                return {
                    'host': host,
                    'port': port,
                    'user': user,
                    'password': password
                }, databases
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                continue
    
    return None, []

def create_crypto_data_test_database(config):
    """Create crypto_data_test database and all required tables"""
    
    print(f"\n🔧 Setting up crypto_data_test database...")
    
    # Define all required tables with schemas
    table_schemas = {
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
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'news_data': """
        CREATE TABLE IF NOT EXISTS news_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(500),
            content TEXT,
            url VARCHAR(1000),
            source VARCHAR(100),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'onchain_data': """
        CREATE TABLE IF NOT EXISTS onchain_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            active_addresses INT,
            transaction_count INT,
            large_transaction_count INT,
            whale_transaction_count INT,
            network_utilization DECIMAL(5,2),
            hash_rate DECIMAL(20,2),
            difficulty DECIMAL(30,2),
            total_supply DECIMAL(25,8),
            circulating_supply DECIMAL(25,8),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'macro_indicators': """
        CREATE TABLE IF NOT EXISTS macro_indicators (
            id INT AUTO_INCREMENT PRIMARY KEY,
            indicator_name VARCHAR(100) NOT NULL,
            indicator_value DECIMAL(15,4),
            unit VARCHAR(50),
            source VARCHAR(100),
            frequency VARCHAR(20),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'technical_indicators': """
        CREATE TABLE IF NOT EXISTS technical_indicators (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            rsi_14 DECIMAL(5,2),
            sma_20 DECIMAL(20,8),
            sma_50 DECIMAL(20,8),
            sma_200 DECIMAL(20,8),
            ema_12 DECIMAL(20,8),
            ema_26 DECIMAL(20,8),
            macd DECIMAL(20,8),
            macd_signal DECIMAL(20,8),
            macd_histogram DECIMAL(20,8),
            bollinger_upper DECIMAL(20,8),
            bollinger_middle DECIMAL(20,8),
            bollinger_lower DECIMAL(20,8),
            stoch_k DECIMAL(5,2),
            stoch_d DECIMAL(5,2),
            williams_r DECIMAL(5,2),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'real_time_sentiment_signals': """
        CREATE TABLE IF NOT EXISTS real_time_sentiment_signals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            sentiment_score DECIMAL(5,4),
            sentiment_label VARCHAR(20),
            confidence DECIMAL(5,4),
            source VARCHAR(100),
            signal_strength DECIMAL(5,4),
            volume_weighted_sentiment DECIMAL(5,4),
            social_mentions_count INT,
            news_sentiment_score DECIMAL(5,4),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'ml_features_materialized': """
        CREATE TABLE IF NOT EXISTS ml_features_materialized (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            price_momentum_1h DECIMAL(10,6),
            price_momentum_4h DECIMAL(10,6),
            price_momentum_24h DECIMAL(10,6),
            volatility_1h DECIMAL(10,6),
            volatility_24h DECIMAL(10,6),
            volume_trend_1h DECIMAL(10,6),
            volume_trend_24h DECIMAL(10,6),
            rsi_normalized DECIMAL(10,6),
            macd_normalized DECIMAL(10,6),
            bollinger_position DECIMAL(10,6),
            sentiment_composite DECIMAL(10,6),
            onchain_activity_score DECIMAL(10,6),
            social_sentiment_score DECIMAL(10,6),
            news_sentiment_score DECIMAL(10,6),
            technical_strength DECIMAL(10,6),
            market_cap_rank INT,
            volume_rank INT,
            data_completeness_percentage DECIMAL(5,2),
            feature_vector_hash VARCHAR(64),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """,
        
        'ohlc_data': """
        CREATE TABLE IF NOT EXISTS ohlc_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            open_price DECIMAL(20,8),
            high_price DECIMAL(20,8),
            low_price DECIMAL(20,8),
            close_price DECIMAL(20,8),
            volume DECIMAL(25,8),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_ohlc (symbol, timeframe, timestamp)
        ) ENGINE=InnoDB
        """
    }
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_data_test")
        cursor.execute("USE crypto_data_test")
        print("✅ Database crypto_data_test created/selected")
        
        # Create tables
        created_count = 0
        for table_name, schema in table_schemas.items():
            try:
                cursor.execute(schema)
                created_count += 1
                print(f"✅ {table_name} created")
            except Exception as e:
                print(f"❌ Error creating {table_name}: {e}")
        
        # Insert sample data for testing
        print(f"\n📝 Inserting sample test data...")
        
        sample_data_queries = [
            """INSERT IGNORE INTO crypto_assets (id, symbol, name, current_price)
               VALUES ('bitcoin', 'BTC', 'Bitcoin', 45000.00), ('ethereum', 'ETH', 'Ethereum', 3200.00)""",
            
            """INSERT IGNORE INTO price_data_real (symbol, current_price, market_cap, total_volume)
               VALUES ('BTC', 45000.00, 850000000000, 25000000000), ('ETH', 3200.00, 380000000000, 15000000000)""",
               
            """INSERT IGNORE INTO news_data (title, content, url, source)
               VALUES ('Test Bitcoin News', 'Bitcoin test content', 'https://test.com/btc', 'TestSource')""",
               
            """INSERT IGNORE INTO onchain_data (symbol, active_addresses, transaction_count, network_utilization)
               VALUES ('BTC', 850000, 250000, 65.5), ('ETH', 650000, 1200000, 78.2)""",
               
            """INSERT IGNORE INTO macro_indicators (indicator_name, indicator_value, unit, source, frequency)
               VALUES ('GDP', 25000.0, 'billions_usd', 'FRED', 'quarterly'), ('CPI', 315.5, 'index', 'FRED', 'monthly')""",
               
            """INSERT IGNORE INTO technical_indicators (symbol, rsi_14, sma_20, sma_50, macd, macd_signal)
               VALUES ('BTC', 65.5, 44500.0, 43000.0, 120.5, 115.0), ('ETH', 58.3, 3150.0, 3050.0, 85.2, 82.1)""",
               
            """INSERT IGNORE INTO real_time_sentiment_signals (symbol, sentiment_score, sentiment_label, confidence, source)
               VALUES ('BTC', 0.75, 'positive', 0.85, 'twitter_analysis'), ('ETH', 0.65, 'positive', 0.78, 'reddit_analysis')""",
               
            """INSERT IGNORE INTO ml_features_materialized (symbol, price_momentum_24h, volatility_24h, sentiment_composite, data_completeness_percentage)
               VALUES ('BTC', 0.25, 0.18, 0.75, 95.0), ('ETH', 0.18, 0.22, 0.65, 92.0)""",
               
            """INSERT IGNORE INTO ohlc_data (symbol, timeframe, open_price, high_price, low_price, close_price, volume)
               VALUES ('BTC', '1h', 44800.0, 45200.0, 44700.0, 45000.0, 1500000.0), ('ETH', '1h', 3180.0, 3220.0, 3170.0, 3200.0, 2200000.0)"""
        ]
        
        for query in sample_data_queries:
            try:
                cursor.execute(query)
            except Exception as e:
                print(f"⚠️ Sample data insert warning: {e}")
        
        connection.commit()
        
        # Verify setup
        cursor.execute("SHOW TABLES")
        final_tables = [table[0] for table in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        print(f"\n🎉 Database setup complete!")
        print(f"📊 Tables created: {created_count}/{len(table_schemas)}")
        print(f"📋 Available tables: {final_tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 CI Environment Database Setup")
    print("=" * 60)
    
    # Find working MySQL instance
    config, databases = try_mysql_instances()
    
    if not config:
        print("\n❌ No working MySQL instance found!")
        print("💡 Ensure MySQL service is running and accessible")
        return False
    
    print(f"\n🎯 Using MySQL: {config['user']}@{config['host']}:{config['port']}")
    
    # Create crypto_data_test database and tables
    success = create_crypto_data_test_database(config)
    
    if success:
        print(f"\n🎉 CI Database setup complete!")
        print(f"✅ crypto_data_test database ready for integration tests")
        print(f"🔗 Connection: {config['user']}@{config['host']}:{config['port']}")
    else:
        print(f"\n❌ Database setup failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)