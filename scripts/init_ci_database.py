#!/usr/bin/env python3
"""
CI Database Initialization Script
Sets up the containerized MySQL database for GitHub Actions CI/CD tests.
Uses exact production database schema from create_missing_tables.py.
"""

import mysql.connector
import os
import sys
import time
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from shared.database_config import get_db_connection

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_mysql(max_retries=30, retry_interval=2):
    """Wait for MySQL to be ready"""
    logger.info("🔄 Waiting for MySQL to be ready...")
    
    for attempt in range(max_retries):
        try:
            # Try to connect using CI configuration
            connection = mysql.connector.connect(
                host='127.0.0.1',
                port=3306,
                user='root',
                password='root',
                connect_timeout=10,
                autocommit=True
            )
            
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()
            
            logger.info("✅ MySQL is ready!")
            return True
            
        except Exception as e:
            logger.info(f"⏳ Attempt {attempt + 1}/{max_retries}: MySQL not ready yet ({e})")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
    
    logger.error("❌ MySQL failed to become ready")
    return False

def create_database_and_user():
    """Create crypto_data_test database and user"""
    logger.info("🔧 Creating database and user...")
    
    try:
        # Connect as root to create database and user
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='root',
            autocommit=True
        )
        cursor = connection.cursor()
        
        # Create database
        database_name = "crypto_data_test"
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        logger.info(f"📊 Database '{database_name}' created/verified")
        
        # Create user and grant privileges
        cursor.execute("CREATE USER IF NOT EXISTS 'news_collector'@'%' IDENTIFIED BY '99Rules!'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO 'news_collector'@'%'")
        cursor.execute("CREATE USER IF NOT EXISTS 'news_collector'@'localhost' IDENTIFIED BY '99Rules!'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO 'news_collector'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        logger.info("👤 User 'news_collector' created/verified with privileges")
        
        # Switch to test database
        cursor.execute(f"USE `{database_name}`")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False

def create_production_schema():
    """Create all tables using exact production schema from create_missing_tables.py"""
    logger.info("📊 Creating production schema tables...")
    
    try:
        # Connect to the test database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Production schema from create_missing_tables.py - EXACT MATCH
        table_schemas = {
            'onchain_data': """
            CREATE TABLE IF NOT EXISTS onchain_data (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'macro_indicators': """
            CREATE TABLE IF NOT EXISTS macro_indicators (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                indicator_name VARCHAR(100) NOT NULL,
                indicator_value DECIMAL(15,4),
                unit VARCHAR(50),
                source VARCHAR(100),
                frequency VARCHAR(20),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_indicator_timestamp (indicator_name, timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'technical_indicators': """
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'real_time_sentiment_signals': """
            CREATE TABLE IF NOT EXISTS real_time_sentiment_signals (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp),
                INDEX idx_source_timestamp (source, timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'ml_features_materialized': """
            CREATE TABLE IF NOT EXISTS ml_features_materialized (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp),
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'ohlc_data': """
            CREATE TABLE IF NOT EXISTS ohlc_data (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            # Additional tables commonly used in tests
            'crypto_assets': """
            CREATE TABLE IF NOT EXISTS crypto_assets (
                id VARCHAR(50) PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                market_cap_rank INT,
                current_price DECIMAL(20,8),
                market_cap BIGINT,
                total_volume BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol (symbol),
                INDEX idx_market_cap_rank (market_cap_rank)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'price_data_real': """
            CREATE TABLE IF NOT EXISTS price_data_real (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                current_price DECIMAL(20,8) NOT NULL,
                market_cap BIGINT,
                total_volume BIGINT,
                price_change_24h DECIMAL(10,4),
                price_change_percentage_24h DECIMAL(10,4),
                market_cap_change_24h BIGINT,
                market_cap_change_percentage_24h DECIMAL(10,4),
                circulating_supply DECIMAL(20,2),
                total_supply DECIMAL(20,2),
                max_supply DECIMAL(20,2),
                ath DECIMAL(20,8),
                ath_change_percentage DECIMAL(10,4),
                atl DECIMAL(20,8),
                atl_change_percentage DECIMAL(10,4),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol_time (symbol, last_updated),
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'news_data': """
            CREATE TABLE IF NOT EXISTS news_data (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                content TEXT,
                url VARCHAR(1000),
                source VARCHAR(100),
                author VARCHAR(200),
                published_at TIMESTAMP,
                sentiment_score DECIMAL(5,4),
                relevance_score DECIMAL(5,4),
                symbols JSON,
                tags JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_published_at (published_at),
                INDEX idx_source_published (source, published_at),
                INDEX idx_sentiment_score (sentiment_score)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        }
        
        # Create all tables
        created_tables = []
        failed_tables = []
        
        for table_name, schema_sql in table_schemas.items():
            try:
                logger.info(f"🔨 Creating table: {table_name}")
                cursor.execute(schema_sql)
                created_tables.append(table_name)
            except Exception as e:
                logger.error(f"❌ Failed to create {table_name}: {e}")
                failed_tables.append(table_name)
        
        # Verify tables exist
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        logger.info(f"✅ Tables created successfully: {created_tables}")
        if failed_tables:
            logger.warning(f"⚠️ Failed to create tables: {failed_tables}")
        logger.info(f"📋 Total tables in database: {existing_tables}")
        
        cursor.close()
        connection.close()
        return len(failed_tables) == 0
        
    except Exception as e:
        logger.error(f"❌ Failed to create schema: {e}")
        return False

def insert_sample_data():
    """Insert minimal sample data for testing"""
    logger.info("🌱 Inserting sample test data...")
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Sample crypto assets
        cursor.execute("""
            INSERT IGNORE INTO crypto_assets (id, symbol, name, market_cap_rank, current_price, market_cap, total_volume)
            VALUES 
            ('bitcoin', 'BTC', 'Bitcoin', 1, 45000.00, 850000000000, 25000000000),
            ('ethereum', 'ETH', 'Ethereum', 2, 3200.00, 380000000000, 15000000000),
            ('cardano', 'ADA', 'Cardano', 8, 0.45, 15000000000, 500000000)
        """)
        
        # Sample price data
        cursor.execute("""
            INSERT IGNORE INTO price_data_real (symbol, current_price, market_cap, total_volume, price_change_24h, price_change_percentage_24h)
            VALUES 
            ('BTC', 45000.00, 850000000000, 25000000000, 500.00, 1.12),
            ('ETH', 3200.00, 380000000000, 15000000000, 80.00, 2.56),
            ('ADA', 0.45, 15000000000, 500000000, 0.02, 4.65)
        """)
        
        # Sample onchain data
        cursor.execute("""
            INSERT IGNORE INTO onchain_data (symbol, active_addresses, transaction_count, large_transaction_count, network_utilization, hash_rate)
            VALUES 
            ('BTC', 850000, 250000, 1200, 65.5, 180000000.0),
            ('ETH', 650000, 1200000, 2500, 78.2, 750000000.0)
        """)
        
        # Sample technical indicators
        cursor.execute("""
            INSERT IGNORE INTO technical_indicators (symbol, rsi_14, sma_20, sma_50, macd, macd_signal, bollinger_upper, bollinger_middle, bollinger_lower)
            VALUES 
            ('BTC', 65.5, 44500.0, 43000.0, 120.5, 115.0, 46000.0, 45000.0, 44000.0),
            ('ETH', 58.3, 3150.0, 3050.0, 85.2, 82.1, 3300.0, 3200.0, 3100.0)
        """)
        
        # Sample sentiment data
        cursor.execute("""
            INSERT IGNORE INTO real_time_sentiment_signals (symbol, sentiment_score, sentiment_label, confidence, source, signal_strength)
            VALUES 
            ('BTC', 0.75, 'positive', 0.85, 'twitter_analysis', 0.8),
            ('ETH', 0.65, 'positive', 0.78, 'reddit_analysis', 0.7)
        """)
        
        # Sample ML features
        cursor.execute("""
            INSERT IGNORE INTO ml_features_materialized (symbol, price_momentum_24h, volatility_24h, sentiment_composite, data_completeness_percentage)
            VALUES 
            ('BTC', 0.25, 0.18, 0.75, 95.0),
            ('ETH', 0.18, 0.22, 0.65, 92.0)
        """)
        
        connection.commit()
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM crypto_assets")
        asset_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM price_data_real")
        price_count = cursor.fetchone()[0]
        
        logger.info(f"✅ Sample data inserted:")
        logger.info(f"   crypto_assets: {asset_count} rows")
        logger.info(f"   price_data_real: {price_count} rows")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to insert sample data: {e}")
        return False

def main():
    """Main initialization process"""
    logger.info("🚀 CI Database Initialization")
    logger.info("=" * 50)
    
    # Step 1: Wait for MySQL to be ready
    if not wait_for_mysql():
        logger.error("❌ MySQL not available")
        return False
    
    # Step 2: Create database and user
    if not create_database_and_user():
        logger.error("❌ Failed to create database/user")
        return False
    
    # Step 3: Create production schema
    if not create_production_schema():
        logger.error("❌ Failed to create schema")
        return False
    
    # Step 4: Insert sample data
    if not insert_sample_data():
        logger.warning("⚠️ Failed to insert sample data (schema created)")
        # Continue anyway - schema is more important than sample data
    
    logger.info("🎉 CI Database initialization complete!")
    logger.info("✅ Database is ready for integration tests")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)