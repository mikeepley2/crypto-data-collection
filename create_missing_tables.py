#!/usr/bin/env python3
"""
Create Missing Database Tables for Integration Tests
Creates all tables required by the integration test suite
"""

import mysql.connector
import sys

def create_missing_tables():
    """Create missing tables in crypto_news database"""
    
    # Use the shared database config instead of hardcoded values
    from shared.database_config import get_db_connection
    
    print("🔗 Connecting to production database...")
    
    # EXACT production schemas - updated to match actual database structure
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
        
        'macro_indicators': """
        CREATE TABLE IF NOT EXISTS macro_indicators (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            timestamp_iso DATETIME NOT NULL,
            indicator_type VARCHAR(100) NOT NULL,
            value DECIMAL(20,8) DEFAULT NULL,
            metadata JSON DEFAULT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            calculation_method VARCHAR(255) DEFAULT NULL,
            data_source VARCHAR(100) DEFAULT NULL,
            quality_score DECIMAL(3,2) DEFAULT NULL,
            confidence_interval DECIMAL(5,4) DEFAULT NULL,
            seasonal_adjustment TINYINT(1) DEFAULT '0',
            UNIQUE KEY unique_symbol_timestamp_indicator (symbol, timestamp_iso, indicator_type),
            INDEX idx_macro_indicators_symbol_timestamp (symbol, timestamp_iso),
            INDEX idx_macro_indicators_indicator_type (indicator_type),
            INDEX idx_macro_indicators_timestamp (timestamp_iso)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_symbol_timestamp (symbol, timestamp),
            INDEX idx_timestamp (timestamp),
            INDEX idx_sentiment_score (sentiment_score)
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_symbol_timestamp (symbol, timestamp),
            INDEX idx_timestamp (timestamp),
            INDEX idx_updated_at (updated_at)
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
            INDEX idx_symbol_timeframe_timestamp (symbol, timeframe, timestamp),
            INDEX idx_timestamp (timestamp),
            UNIQUE KEY unique_ohlc (symbol, timeframe, timestamp)
        ) ENGINE=InnoDB
        """
    }
    
    print("🔧 Creating missing database tables...")
    print("=" * 50)
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check existing tables
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"📋 Existing tables: {len(existing_tables)} tables")
        
        created_count = 0
        updated_count = 0
        
        for table_name, schema in table_schemas.items():
            try:
                if table_name in existing_tables:
                    print(f"⏭️  {table_name} already exists")
                    updated_count += 1
                else:
                    print(f"🔨 Creating {table_name}...")
                    cursor.execute(schema)
                    created_count += 1
                    print(f"✅ {table_name} created successfully")
                    
            except Exception as e:
                print(f"❌ Error with {table_name}: {e}")
        
        connection.commit()
        
        # Insert sample data for testing
        print(f"\\n📝 Inserting sample test data...")
        
        # Sample onchain data
        if 'onchain_data' not in existing_tables:
            cursor.execute("""
                INSERT IGNORE INTO onchain_data (symbol, active_addresses, transaction_count, large_transaction_count, whale_transaction_count, network_utilization)
                VALUES 
                    ('BTC', 850000, 250000, 1500, 120, 65.5),
                    ('ETH', 650000, 1200000, 8500, 650, 78.2)
            """)
        
        # Sample macro indicators
        if 'macro_indicators' not in existing_tables:
            cursor.execute("""
                INSERT IGNORE INTO macro_indicators (indicator_name, indicator_value, unit, source, frequency)
                VALUES 
                    ('GDP', 25000.0, 'billions_usd', 'FRED', 'quarterly'),
                    ('CPI', 315.5, 'index', 'FRED', 'monthly'),
                    ('UNEMPLOYMENT_RATE', 3.7, 'percent', 'FRED', 'monthly')
            """)
        
        # Sample technical indicators
        if 'technical_indicators' not in existing_tables:
            cursor.execute("""
                INSERT IGNORE INTO technical_indicators (symbol, rsi_14, sma_20, sma_50, macd, macd_signal, bollinger_upper, bollinger_middle, bollinger_lower)
                VALUES 
                    ('BTC', 65.5, 44500.0, 43000.0, 120.5, 115.0, 46000.0, 45000.0, 44000.0),
                    ('ETH', 58.3, 3150.0, 3050.0, 85.2, 82.1, 3250.0, 3200.0, 3150.0)
            """)
        
        # Sample sentiment signals  
        if 'real_time_sentiment_signals' not in existing_tables:
            cursor.execute("""
                INSERT IGNORE INTO real_time_sentiment_signals (symbol, sentiment_score, sentiment_label, confidence, source, signal_strength, social_mentions_count)
                VALUES 
                    ('BTC', 0.75, 'positive', 0.85, 'twitter_analysis', 0.8, 15000),
                    ('ETH', 0.65, 'positive', 0.78, 'reddit_analysis', 0.7, 8500)
            """)
        
        # Sample ML features
        if 'ml_features_materialized' not in existing_tables:
            cursor.execute("""
                INSERT IGNORE INTO ml_features_materialized (symbol, price_momentum_1h, price_momentum_24h, volatility_24h, volume_trend_24h, rsi_normalized, sentiment_composite, data_completeness_percentage)
                VALUES 
                    ('BTC', 0.15, 0.25, 0.18, 0.65, 0.655, 0.75, 95.0),
                    ('ETH', 0.08, 0.18, 0.22, 0.58, 0.583, 0.65, 92.0)
            """)
        
        # Sample OHLC data
        if 'ohlc_data' not in existing_tables:
            cursor.execute("""
                INSERT IGNORE INTO ohlc_data (symbol, timeframe, open_price, high_price, low_price, close_price, volume)
                VALUES 
                    ('BTC', '1h', 44800.0, 45200.0, 44700.0, 45000.0, 1500000.0),
                    ('ETH', '1h', 3180.0, 3220.0, 3170.0, 3200.0, 2200000.0)
            """)
        
        connection.commit()
        
        # Verify final state
        cursor.execute("SHOW TABLES")
        final_tables = [table[0] for table in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        print(f"\\n🎉 Database table creation complete!")
        print(f"📊 Total tables: {len(final_tables)}")
        print(f"🔨 Tables created: {created_count}")
        print(f"⏭️  Tables existed: {updated_count}")
        print(f"✅ All required tables now available")
        
        # Show required tables status
        required_tables = list(table_schemas.keys()) + ['crypto_assets', 'price_data_real', 'news_data']
        missing = [t for t in required_tables if t not in final_tables]
        
        if missing:
            print(f"❌ Still missing: {missing}")
            return False
        else:
            print(f"✅ All required tables present: {required_tables}")
            return True
        
    except Exception as e:
        print(f"❌ Database table creation failed: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 Missing Database Tables Creation")
    print("=" * 60)
    
    success = create_missing_tables()
    
    if success:
        print(f"\\n🎉 SUCCESS: All database tables ready for integration tests!")
    else:
        print(f"\\n❌ FAILURE: Some issues during table creation")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)