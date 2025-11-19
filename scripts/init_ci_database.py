#!/usr/bin/env python3
"""
CI Database Initialization Script
Sets up the containerized MySQL database for integration tests
"""

import os
import sys
import time
import mysql.connector
from mysql.connector import Error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_mysql(host='127.0.0.1', port=3306, user='root', password='99Rules!', max_retries=30):
    """Wait for MySQL service to be available"""
    logger.info(f"🔄 Waiting for MySQL at {host}:{port}...")
    
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connect_timeout=5
            )
            connection.close()
            logger.info(f"✅ MySQL is ready after {attempt + 1} attempts")
            return True
        except Error as e:
            logger.debug(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(2)
    
    logger.error(f"❌ MySQL not available after {max_retries} attempts")
    return False

def create_test_database():
    """Create and populate test database"""
    logger.info("🗄️ Setting up test database...")
    
    # Database configuration from environment
    config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': os.getenv('MYSQL_ROOT_PASSWORD', '99Rules!'),
    }
    
    try:
        # Connect as root to create database and user
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Create test database
        database_name = os.getenv('MYSQL_DATABASE', 'crypto_data_test')
        logger.info(f"📦 Creating database: {database_name}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        
        # Create test user with proper permissions
        user = os.getenv('MYSQL_USER', 'news_collector')
        password = os.getenv('MYSQL_PASSWORD', '99Rules!')
        
        logger.info(f"👤 Creating user: {user}")
        cursor.execute(f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{password}'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO '{user}'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        
        # Switch to test database
        cursor.execute(f"USE `{database_name}`")
        
        # Create required tables for tests
        logger.info("📊 Creating test tables...")
        
        # crypto_assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_assets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol (symbol)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # price_data_real table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_data_real (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                price DECIMAL(20,8) NOT NULL,
                volume DECIMAL(20,8) DEFAULT NULL,
                market_cap DECIMAL(20,2) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_symbol_timestamp (symbol, timestamp),
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # onchain_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS onchain_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                active_addresses INT DEFAULT NULL,
                transaction_count INT DEFAULT NULL,
                transaction_volume DECIMAL(20,8) DEFAULT NULL,
                network_hash_rate DECIMAL(25,2) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_symbol_timestamp (symbol, timestamp),
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # macro_indicators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS macro_indicators (
                id INT AUTO_INCREMENT PRIMARY KEY,
                indicator_name VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                value DECIMAL(15,6) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_indicator_timestamp (indicator_name, timestamp),
                INDEX idx_indicator (indicator_name),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # technical_indicators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                sma_20 DECIMAL(20,8) DEFAULT NULL,
                sma_50 DECIMAL(20,8) DEFAULT NULL,
                ema_20 DECIMAL(20,8) DEFAULT NULL,
                rsi DECIMAL(5,2) DEFAULT NULL,
                macd DECIMAL(20,8) DEFAULT NULL,
                bollinger_upper DECIMAL(20,8) DEFAULT NULL,
                bollinger_lower DECIMAL(20,8) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_symbol_timestamp (symbol, timestamp),
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # real_time_sentiment_signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_time_sentiment_signals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                sentiment_score DECIMAL(4,3) NOT NULL,
                confidence_score DECIMAL(4,3) DEFAULT NULL,
                source VARCHAR(50) NOT NULL,
                text_sample TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp),
                INDEX idx_source (source)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # ml_features_materialized table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_features_materialized (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                price_features JSON DEFAULT NULL,
                technical_features JSON DEFAULT NULL,
                sentiment_features JSON DEFAULT NULL,
                macro_features JSON DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_symbol_timestamp (symbol, timestamp),
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # ohlc_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ohlc_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open_price DECIMAL(20,8) NOT NULL,
                high_price DECIMAL(20,8) NOT NULL,
                low_price DECIMAL(20,8) NOT NULL,
                close_price DECIMAL(20,8) NOT NULL,
                volume DECIMAL(20,8) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_symbol_timestamp (symbol, timestamp),
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # news_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                content TEXT,
                url VARCHAR(767),
                source VARCHAR(100) NOT NULL,
                published_at TIMESTAMP NOT NULL,
                symbols JSON DEFAULT NULL,
                sentiment_score DECIMAL(4,3) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_url (url(191)),
                INDEX idx_source (source),
                INDEX idx_published_at (published_at),
                INDEX idx_sentiment_score (sentiment_score)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # Insert sample data for tests
        logger.info("🌱 Inserting sample test data...")
        
        # Sample crypto assets
        cursor.execute("""
            INSERT IGNORE INTO crypto_assets (symbol, name) VALUES
            ('BTC', 'Bitcoin'),
            ('ETH', 'Ethereum'),
            ('ADA', 'Cardano')
        """)
        
        # Sample price data
        cursor.execute("""
            INSERT IGNORE INTO price_data_real (symbol, timestamp, price, volume, market_cap) VALUES
            ('BTC', '2024-01-01 00:00:00', 42000.00, 1000000.0, 800000000000.00),
            ('ETH', '2024-01-01 00:00:00', 2500.00, 2000000.0, 300000000000.00)
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info("✅ Test database setup complete!")
        return True
        
    except Error as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

def verify_setup():
    """Verify the database setup is working"""
    logger.info("🧪 Verifying database setup...")
    
    config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': os.getenv('MYSQL_USER', 'news_collector'),
        'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
        'database': os.getenv('MYSQL_DATABASE', 'crypto_data_test')
    }
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM crypto_assets")
        count = cursor.fetchone()[0]
        logger.info(f"✅ crypto_assets table has {count} records")
        
        # Test all required tables exist
        required_tables = [
            'crypto_assets', 'price_data_real', 'onchain_data', 'macro_indicators',
            'technical_indicators', 'real_time_sentiment_signals', 
            'ml_features_materialized', 'ohlc_data', 'news_data'
        ]
        
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        missing_tables = set(required_tables) - set(existing_tables)
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        logger.info(f"✅ All {len(required_tables)} required tables present")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main initialization process"""
    logger.info("🚀 Starting CI database initialization")
    
    # Wait for MySQL service
    if not wait_for_mysql():
        sys.exit(1)
    
    # Create database and tables
    if not create_test_database():
        sys.exit(1)
    
    # Verify setup
    if not verify_setup():
        sys.exit(1)
    
    logger.info("🎉 Database initialization successful!")

if __name__ == "__main__":
    main()