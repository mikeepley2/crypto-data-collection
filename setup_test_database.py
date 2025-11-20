#!/usr/bin/env python3
"""
Test Database Schema Setup
Creates all required tables for integration tests in the crypto_data_test database.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from shared.database_config import get_db_connection
import mysql.connector
from mysql.connector import Error

def create_test_schema():
    """Create all required tables for integration tests"""
    
    # SQL statements to create all required tables
    table_schemas = {
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
        
        'ohlc_data': """
        CREATE TABLE IF NOT EXISTS ohlc_data (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            open_price DECIMAL(20,8) NOT NULL,
            high_price DECIMAL(20,8) NOT NULL,
            low_price DECIMAL(20,8) NOT NULL,
            close_price DECIMAL(20,8) NOT NULL,
            volume DECIMAL(20,2),
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_timeframe_timestamp (symbol, timeframe, timestamp),
            INDEX idx_symbol_timeframe_time (symbol, timeframe, timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'onchain_data': """
        CREATE TABLE IF NOT EXISTS onchain_data (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            network VARCHAR(50),
            address_count BIGINT,
            transaction_count BIGINT,
            total_value_locked DECIMAL(30,8),
            gas_price DECIMAL(20,8),
            block_height BIGINT,
            hash_rate DECIMAL(30,8),
            difficulty DECIMAL(30,8),
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_symbol_time (symbol, timestamp),
            INDEX idx_network_time (network, timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'macro_indicators': """
        CREATE TABLE IF NOT EXISTS macro_indicators (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            indicator_name VARCHAR(100) NOT NULL,
            value DECIMAL(20,8),
            date DATE NOT NULL,
            source VARCHAR(50),
            frequency VARCHAR(20),
            units VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_indicator_date (indicator_name, date),
            INDEX idx_indicator_date (indicator_name, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'technical_indicators': """
        CREATE TABLE IF NOT EXISTS technical_indicators (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            indicator_type VARCHAR(50) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            value DECIMAL(20,8),
            additional_data JSON,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_indicator_timeframe_timestamp (symbol, indicator_type, timeframe, timestamp),
            INDEX idx_symbol_time (symbol, timestamp),
            INDEX idx_indicator_type (indicator_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'real_time_sentiment_signals': """
        CREATE TABLE IF NOT EXISTS real_time_sentiment_signals (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            source VARCHAR(100) NOT NULL,
            sentiment_score DECIMAL(5,4) NOT NULL,
            confidence DECIMAL(5,4),
            signal_strength DECIMAL(5,4),
            text_snippet TEXT,
            metadata JSON,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_symbol_time (symbol, timestamp),
            INDEX idx_source_time (source, timestamp),
            INDEX idx_sentiment_time (sentiment_score, timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'ml_features_materialized': """
        CREATE TABLE IF NOT EXISTS ml_features_materialized (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            feature_set VARCHAR(50) NOT NULL,
            features JSON NOT NULL,
            target_price DECIMAL(20,8),
            prediction_horizon INT,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_features_timestamp (symbol, feature_set, timestamp),
            INDEX idx_symbol_time (symbol, timestamp),
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
    
    print("🔧 Creating test database schema...")
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check current tables
        cursor.execute("SHOW TABLES")
        existing_tables = {table[0] for table in cursor.fetchall()}
        print(f"📊 Existing tables: {existing_tables}")
        
        created_tables = []
        skipped_tables = []
        
        for table_name, schema_sql in table_schemas.items():
            if table_name in existing_tables:
                print(f"⏭️  Skipping {table_name} (already exists)")
                skipped_tables.append(table_name)
            else:
                print(f"🔨 Creating table: {table_name}")
                cursor.execute(schema_sql)
                created_tables.append(table_name)
        
        # Commit changes
        connection.commit()
        
        print(f"\n✅ Schema setup complete!")
        print(f"   Created tables: {created_tables}")
        print(f"   Skipped tables: {skipped_tables}")
        
        # Verify all tables exist
        cursor.execute("SHOW TABLES")
        final_tables = {table[0] for table in cursor.fetchall()}
        
        missing_tables = set(table_schemas.keys()) - final_tables
        if missing_tables:
            print(f"⚠️  Still missing tables: {missing_tables}")
        else:
            print(f"🎉 All {len(table_schemas)} required tables are now present!")
        
        cursor.close()
        connection.close()
        
        return len(missing_tables) == 0
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def populate_test_data():
    """Insert minimal test data for integration tests"""
    
    print("\n🔧 Populating test data...")
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert test crypto assets
        crypto_assets_data = [
            ('bitcoin', 'BTC', 'Bitcoin', 1, 45000.00, 850000000000, 25000000000),
            ('ethereum', 'ETH', 'Ethereum', 2, 3200.00, 380000000000, 15000000000),
            ('cardano', 'ADA', 'Cardano', 8, 0.45, 15000000000, 500000000)
        ]
        
        for asset in crypto_assets_data:
            cursor.execute("""
                INSERT IGNORE INTO crypto_assets 
                (id, symbol, name, market_cap_rank, current_price, market_cap, total_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, asset)
        
        # Insert test price data
        price_data = [
            ('BTC', 45000.00, 850000000000, 25000000000, 500.00, 1.12),
            ('ETH', 3200.00, 380000000000, 15000000000, 80.00, 2.56),
            ('ADA', 0.45, 15000000000, 500000000, 0.02, 4.65)
        ]
        
        for price in price_data:
            cursor.execute("""
                INSERT IGNORE INTO price_data_real 
                (symbol, current_price, market_cap, total_volume, price_change_24h, price_change_percentage_24h)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, price)
        
        connection.commit()
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM crypto_assets")
        asset_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM price_data_real")
        price_count = cursor.fetchone()[0]
        
        print(f"✅ Test data populated:")
        print(f"   crypto_assets: {asset_count} rows")
        print(f"   price_data_real: {price_count} rows")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error populating test data: {e}")
        return False

def main():
    """Main function to set up test database"""
    
    print("🚀 Test Database Schema Setup")
    print("=" * 35)
    
    # Set environment for testing
    os.environ['TESTING'] = 'true'
    
    # Step 1: Create schema
    schema_success = create_test_schema()
    
    if not schema_success:
        print("❌ Failed to create schema")
        return False
    
    # Step 2: Populate test data
    data_success = populate_test_data()
    
    if not data_success:
        print("⚠️  Schema created but failed to populate test data")
        return False
    
    print("\n🎉 Test database setup complete!")
    print("   Integration tests should now pass database schema checks.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)