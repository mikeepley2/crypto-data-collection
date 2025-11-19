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
    
    # Get MySQL configuration from environment variables with CI defaults
    mysql_host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
    mysql_user = os.environ.get('MYSQL_USER', 'news_collector')
    mysql_password = os.environ.get('MYSQL_PASSWORD', '99Rules!')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'crypto_data_test')
    mysql_root_password = os.environ.get('MYSQL_ROOT_PASSWORD', '99Rules!')
    
    # Try both root and configured user for initial connection
    connection_configs = [
        # First try the configured user (GitHub Actions setup)
        {
            'host': mysql_host,
            'port': mysql_port,
            'user': mysql_user,
            'password': mysql_password,
            'connect_timeout': 10,
            'autocommit': True
        },
        # Fallback to root if configured user isn't ready yet
        {
            'host': mysql_host,
            'port': mysql_port,
            'user': 'root',
            'password': mysql_root_password,
            'connect_timeout': 10,
            'autocommit': True
        }
    ]
    
    for attempt in range(max_retries):
        for config_idx, config in enumerate(connection_configs):
            try:
                connection = mysql.connector.connect(**config)
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                connection.close()
                
                logger.info(f"✅ MySQL is ready! (connected as {config['user']})")
                return True
                
            except mysql.connector.Error as e:
                # Only log on the last config attempt for this retry
                if config_idx == len(connection_configs) - 1:
                    logger.info(f"⏳ Attempt {attempt + 1}/{max_retries}: MySQL not ready yet ({e})")
                continue
        
        time.sleep(retry_interval)
    
    logger.error("❌ MySQL failed to become ready")
    return False

def create_database_and_user():
    """Create crypto_data_test database and user"""
    logger.info("🔧 Creating database and user...")
    
    try:
        # Get MySQL configuration from environment variables with CI defaults
        mysql_host = os.environ.get('MYSQL_HOST', '127.0.0.1')
        mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
        mysql_root_password = os.environ.get('MYSQL_ROOT_PASSWORD', '99Rules!')
        mysql_user = os.environ.get('MYSQL_USER', 'news_collector')
        mysql_password = os.environ.get('MYSQL_PASSWORD', '99Rules!')
        database_name = os.environ.get('MYSQL_DATABASE', 'crypto_data_test')
        
        # Try connecting as root first, fallback to configured user
        connection = None
        cursor = None
        connected_as_root = False
        
        try:
            # Try root connection first
            connection = mysql.connector.connect(
                host=mysql_host,
                port=mysql_port,
                user='root',
                password=mysql_root_password,
                autocommit=True
            )
            connected_as_root = True
            logger.info(f"✅ Connected as root for database setup")
            
        except mysql.connector.Error as e:
            # Root connection failed, try the configured user (GitHub Actions pre-setup scenario)
            logger.warning(f"⚠️ Root connection failed ({e}), trying configured user...")
            try:
                connection = mysql.connector.connect(
                    host=mysql_host,
                    port=mysql_port,
                    user=mysql_user,
                    password=mysql_password,
                    autocommit=True
                )
                logger.info(f"✅ Connected as {mysql_user} for database setup")
                
            except mysql.connector.Error as e2:
                logger.error(f"❌ Both root and user connections failed")
                logger.error(f"   Root error: {e}")
                logger.error(f"   User error: {e2}")
                return False
        
        cursor = connection.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        logger.info(f"📊 Database '{database_name}' created/verified")
        
        # Only try to create user if we're connected as root
        if connected_as_root:
            try:
                # Create user and grant privileges (only when connected as root)
                cursor.execute(f"CREATE USER IF NOT EXISTS '{mysql_user}'@'%' IDENTIFIED BY '{mysql_password}'")
                cursor.execute(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO '{mysql_user}'@'%'")
                cursor.execute(f"CREATE USER IF NOT EXISTS '{mysql_user}'@'localhost' IDENTIFIED BY '{mysql_password}'")
                cursor.execute(f"GRANT ALL PRIVILEGES ON `{database_name}`.* TO '{mysql_user}'@'localhost'")
                cursor.execute("FLUSH PRIVILEGES")
                logger.info(f"👤 User '{mysql_user}' created/verified with privileges")
            except mysql.connector.Error as user_error:
                logger.warning(f"⚠️ User creation failed (user might already exist): {user_error}")
        else:
            logger.info(f"⚠️ Connected as {mysql_user}, assuming user already exists")
        
        # Switch to test database
        cursor.execute(f"USE `{database_name}`")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database and user creation failed: {e}")
        return False
        
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
        # Updated to reflect actual database structure with correct field names
        table_schemas = {
            'crypto_assets': """
            CREATE TABLE IF NOT EXISTS crypto_assets (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(16) NOT NULL UNIQUE,
                name VARCHAR(64) NOT NULL,
                aliases JSON DEFAULT NULL,
                category VARCHAR(32) DEFAULT 'crypto',
                is_active TINYINT(1) DEFAULT '1',
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                coingecko_id VARCHAR(150) DEFAULT NULL,
                description TEXT,
                market_cap_rank INT DEFAULT NULL,
                coingecko_score DECIMAL(5,2) DEFAULT NULL,
                homepage VARCHAR(255) DEFAULT NULL,
                last_metadata_update TIMESTAMP NULL DEFAULT NULL,
                coinbase_supported TINYINT(1) DEFAULT '1',
                binance_us_supported TINYINT(1) DEFAULT '0',
                kucoin_supported TINYINT(1) DEFAULT '0',
                exchange_support_updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_crypto_assets_coinbase_supported (coinbase_supported)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'price_data_real': """
            CREATE TABLE IF NOT EXISTS price_data_real (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                coin_id VARCHAR(50),
                name VARCHAR(100),
                current_price DECIMAL(20,8) NOT NULL,
                market_cap BIGINT,
                volume_usd_24h BIGINT,
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
                timestamp BIGINT,
                timestamp_iso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol_time (symbol, timestamp_iso),
                INDEX idx_updated_at (updated_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'onchain_data': """
            CREATE TABLE IF NOT EXISTS onchain_data (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                coin_id VARCHAR(50),
                active_addresses BIGINT,
                transaction_count BIGINT,
                transaction_volume DECIMAL(20,8),
                large_transaction_count BIGINT,
                network_utilization DECIMAL(5,2),
                hash_rate DECIMAL(20,8),
                difficulty DECIMAL(25,8),
                block_time DECIMAL(10,4),
                fees_median DECIMAL(20,8),
                fees_average DECIMAL(20,8),
                timestamp_iso DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_symbol_timestamp (symbol, timestamp_iso),
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp_iso)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'macro_indicators': """
            CREATE TABLE IF NOT EXISTS macro_indicators (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                indicator_name VARCHAR(200) NOT NULL,
                fred_series_id VARCHAR(50),
                indicator_date DATE NOT NULL,
                value DECIMAL(20,8) DEFAULT NULL,
                unit VARCHAR(50),
                frequency VARCHAR(20),
                category VARCHAR(100),
                data_source VARCHAR(50),
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_indicator_date (indicator_name, indicator_date),
                INDEX idx_indicator_name (indicator_name),
                INDEX idx_indicator_date (indicator_date),
                INDEX idx_category (category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'technical_indicators': """
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                timestamp_iso DATETIME NOT NULL,
                sma_20 DECIMAL(20,8) DEFAULT NULL,
                sma_50 DECIMAL(20,8) DEFAULT NULL,
                sma_200 DECIMAL(20,8) DEFAULT NULL,
                ema_12 DECIMAL(20,8) DEFAULT NULL,
                ema_26 DECIMAL(20,8) DEFAULT NULL,
                macd DECIMAL(20,8) DEFAULT NULL,
                macd_signal DECIMAL(20,8) DEFAULT NULL,
                macd_histogram DECIMAL(20,8) DEFAULT NULL,
                rsi DECIMAL(10,4) DEFAULT NULL,
                bollinger_upper DECIMAL(20,8) DEFAULT NULL,
                bollinger_middle DECIMAL(20,8) DEFAULT NULL,
                bollinger_lower DECIMAL(20,8) DEFAULT NULL,
                stoch_k DECIMAL(10,4) DEFAULT NULL,
                stoch_d DECIMAL(10,4) DEFAULT NULL,
                williams_r DECIMAL(10,4) DEFAULT NULL,
                atr DECIMAL(20,8) DEFAULT NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_symbol_timestamp (symbol, timestamp_iso),
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp_iso)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'real_time_sentiment_signals': """
            CREATE TABLE IF NOT EXISTS real_time_sentiment_signals (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                symbol VARCHAR(20) NOT NULL,
                signal_type VARCHAR(50) NOT NULL,
                sentiment_score DECIMAL(10,6) DEFAULT NULL,
                confidence DECIMAL(10,6) DEFAULT NULL,
                metadata JSON DEFAULT NULL,
                signal_strength DECIMAL(10,6) DEFAULT NULL,
                INDEX idx_symbol_timestamp (symbol, timestamp),
                INDEX idx_signal_type (signal_type),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'ml_features_materialized': """
            CREATE TABLE IF NOT EXISTS ml_features_materialized (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                price_date DATE,
                price_hour TINYINT,
                timestamp_iso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_price DECIMAL(20,8),
                volume_24h DECIMAL(25,8),
                hourly_volume DECIMAL(25,8),
                market_cap BIGINT,
                price_change_24h DECIMAL(10,4),
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp_iso),
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
            INSERT IGNORE INTO crypto_assets (symbol, name, category, is_active, coingecko_id)
            VALUES 
            ('BTC', 'Bitcoin', 'crypto', 1, 'bitcoin'),
            ('ETH', 'Ethereum', 'crypto', 1, 'ethereum'),
            ('ADA', 'Cardano', 'crypto', 1, 'cardano')
        """)
        
        # Sample price data
        cursor.execute("""
            INSERT IGNORE INTO price_data_real (symbol, coin_id, name, current_price, market_cap, volume_usd_24h, price_change_24h, price_change_percentage_24h)
            VALUES 
            ('BTC', 'bitcoin', 'Bitcoin', 45000.00, 850000000000, 25000000000, 500.00, 1.12),
            ('ETH', 'ethereum', 'Ethereum', 3200.00, 380000000000, 15000000000, 80.00, 2.56),
            ('ADA', 'cardano', 'Cardano', 0.45, 15000000000, 500000000, 0.02, 4.65)
        """)
        
        # Sample onchain data
        cursor.execute("""
            INSERT IGNORE INTO onchain_data (symbol, coin_id, active_addresses, transaction_count, transaction_volume, timestamp_iso)
            VALUES 
            ('BTC', 'bitcoin', 850000, 250000, 125000000000.00, NOW()),
            ('ETH', 'ethereum', 650000, 1200000, 85000000000.00, NOW())
        """)
        
        # Sample technical indicators
        cursor.execute("""
            INSERT IGNORE INTO technical_indicators (symbol, rsi, sma_20, macd, timestamp_iso)
            VALUES 
            ('BTC', 65.5, 44500.0, 120.5, NOW()),
            ('ETH', 58.3, 3150.0, 85.2, NOW())
        """)
        
        # Sample sentiment data
        cursor.execute("""
            INSERT IGNORE INTO real_time_sentiment_signals (symbol, sentiment_score, signal_type, confidence, signal_strength)
            VALUES 
            ('BTC', 0.75, 'bullish', 0.85, 0.8),
            ('ETH', 0.65, 'bullish', 0.78, 0.7)
        """)
        
        # Sample macro indicators
        cursor.execute("""
            INSERT IGNORE INTO macro_indicators (indicator_name, fred_series_id, indicator_date, value, unit, frequency, category, data_source)
            VALUES 
            ('GDP_GROWTH', 'GDPC1', CURDATE(), 2.1, 'percentage', 'quarterly', 'economic', 'FRED'),
            ('INFLATION_RATE', 'CPIAUCSL', CURDATE(), 3.2, 'percentage', 'monthly', 'economic', 'FRED')
        """)
        
        # Sample ML features
        cursor.execute("""
            INSERT IGNORE INTO ml_features_materialized (symbol, price_date, price_hour, current_price, volume_24h, price_change_24h, timestamp_iso)
            VALUES 
            ('BTC', CURDATE(), HOUR(NOW()), 45000.00, 25000000000, 1.12, NOW()),
            ('ETH', CURDATE(), HOUR(NOW()), 3200.00, 15000000000, 2.56, NOW())
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