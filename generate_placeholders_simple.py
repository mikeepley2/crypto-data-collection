#!/usr/bin/env python3
"""
Simple Placeholder Generator
Creates placeholder records for all collectors without complex dependencies
"""

import pymysql
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
db_config = {
    'host': os.getenv("DB_HOST", "127.0.0.1"),
    'user': os.getenv("DB_USER", "news_collector"),
    'password': os.getenv("DB_PASSWORD", "99Rules!"),
    'database': os.getenv("DB_NAME", "crypto_prices"),
    'charset': 'utf8mb4',
    'autocommit': False
}

def get_db_connection():
    """Get database connection"""
    try:
        return pymysql.connect(**db_config)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_macro_placeholders(cursor, days=None):
    """Create macro indicator placeholders from 2023 to present (daily frequency)"""
    placeholders_created = 0
    indicators = ['VIX', 'DXY', 'FEDFUNDS', 'DGS10', 'DGS2', 'UNRATE', 'CPIAUCSL', 'GDP']
    
    # Historical range: 2023-01-01 to present
    start_date = datetime(2023, 1, 1).date()
    end_date = datetime.now().date()
    
    logger.info(f"Creating macro placeholders from {start_date} to {end_date} (daily frequency)")
    
    current_date = start_date
    while current_date <= end_date:
        for indicator in indicators:
            try:
                cursor.execute("""
                    INSERT IGNORE INTO macro_indicators 
                    (indicator_name, indicator_date, value, data_source, 
                     data_completeness_percentage, collected_at)
                    VALUES (%s, %s, NULL, 'placeholder_generator', 0.0, NOW())
                """, (indicator, current_date))
                
                if cursor.rowcount > 0:
                    placeholders_created += 1
                    
            except Exception as e:
                logger.debug(f"Error creating macro placeholder {indicator} {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    return placeholders_created

def create_technical_placeholders(cursor, hours=None):
    """Create technical indicator placeholders from 2023 to present (5-minute frequency)"""
    placeholders_created = 0
    
    # Get active symbols
    try:
        cursor.execute("""
            SELECT symbol FROM price_data_real 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
            ORDER BY symbol LIMIT 50
        """)
        symbols = [row[0] for row in cursor.fetchall()]
        
        if not symbols:
            # Fallback to crypto_assets if no recent price data
            cursor.execute("""
                SELECT symbol FROM crypto_assets 
                WHERE is_active = 1 
                ORDER BY market_cap_rank LIMIT 50
            """)
            symbols = [row[0] for row in cursor.fetchall()]
            
    except Exception as e:
        logger.warning(f"Could not get symbols, using defaults: {e}")
        symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']
    
    # Historical range: 2023-01-01 to present, 5-minute intervals
    start_time = datetime(2023, 1, 1, 0, 0)
    end_time = datetime.now()
    
    logger.info(f"Creating technical placeholders for {len(symbols)} symbols from {start_time} to {end_time} (5-minute intervals)")
    
    current_time = start_time
    while current_time <= end_time:
        # Round to nearest 5-minute mark
        minutes = current_time.minute
        rounded_minutes = (minutes // 5) * 5
        target_time = current_time.replace(minute=rounded_minutes, second=0, microsecond=0)
        
        for symbol in symbols:
            try:
                cursor.execute("""
                    INSERT IGNORE INTO technical_indicators
                    (symbol, timestamp_iso, 
                     rsi_14, sma_20, sma_50, ema_12, ema_26,
                     macd, macd_signal, macd_histogram,
                     bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, atr_14, vwap,
                     data_completeness_percentage, data_source, created_at)
                    VALUES (%s, %s, 
                           NULL, NULL, NULL, NULL, NULL,
                           NULL, NULL, NULL, 
                           NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                           0.0, 'placeholder_generator', NOW())
                """, (symbol, target_time))
                
                if cursor.rowcount > 0:
                    placeholders_created += 1
                    
            except Exception as e:
                logger.debug(f"Error creating technical placeholder {symbol} {target_time}: {e}")
        
        current_time += timedelta(minutes=5)
    
    return placeholders_created

def create_onchain_placeholders(cursor, days=None):
    """Create onchain data placeholders from 2023 to present (daily frequency)"""
    placeholders_created = 0
    
    # Get crypto symbols
    try:
        cursor.execute("""
            SELECT symbol FROM crypto_assets 
            WHERE is_active = 1 
            ORDER BY market_cap_rank LIMIT 20
        """)
        symbols = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.warning(f"Could not get crypto symbols, using defaults: {e}")
        symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'AVAX', 'MATIC', 'ATOM', 'SOL', 'NEAR']
    
    # Historical range: 2023-01-01 to present
    start_date = datetime(2023, 1, 1).date()
    end_date = datetime.now().date()
    
    logger.info(f"Creating onchain placeholders for {len(symbols)} symbols from {start_date} to {end_date} (daily frequency)")
    
    current_date = start_date
    while current_date <= end_date:
        for symbol in symbols:
            try:
                cursor.execute("""
                    INSERT IGNORE INTO crypto_onchain_data
                    (symbol, timestamp, 
                     current_price, total_volume, high_24h, low_24h, price_change_24h,
                     market_cap, market_cap_rank, circulating_supply, total_supply, max_supply,
                     data_completeness_percentage, data_source)
                    VALUES (%s, %s,
                           NULL, NULL, NULL, NULL, NULL,
                           NULL, NULL, NULL, NULL, NULL,
                           0.0, 'placeholder_generator')
                """, (symbol, datetime.combine(current_date, datetime.min.time())))
                
                if cursor.rowcount > 0:
                    placeholders_created += 1
                    
            except Exception as e:
                logger.debug(f"Error creating onchain placeholder {symbol} {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    return placeholders_created

def create_sentiment_placeholders(cursor, days=None):
    """Create sentiment analysis placeholders from 2023 to present (hourly frequency)"""
    placeholders_created = 0
    
    # Get symbols for sentiment analysis
    try:
        cursor.execute("""
            SELECT symbol FROM price_data_real 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
            ORDER BY symbol LIMIT 30
        """)
        symbols = [row[0] for row in cursor.fetchall()]
        
        if not symbols:
            # Fallback to crypto_assets if no recent price data
            cursor.execute("""
                SELECT symbol FROM crypto_assets 
                WHERE is_active = 1 
                ORDER BY market_cap_rank LIMIT 30
            """)
            symbols = [row[0] for row in cursor.fetchall()]
            
    except Exception as e:
        logger.warning(f"Could not get symbols for sentiment, using defaults: {e}")
        symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']
    
    # Historical range: 2023-01-01 to present
    start_date = datetime(2023, 1, 1).date()
    end_date = datetime.now().date()
    
    logger.info(f"Creating sentiment placeholders for {len(symbols)} symbols from {start_date} to {end_date} (hourly frequency)")
    
    current_date = start_date
    while current_date <= end_date:
        for symbol in symbols:
            # Create hourly placeholders for sentiment data
            for hour in range(24):
                try:
                    timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                    
                    cursor.execute("""
                        INSERT IGNORE INTO sentiment_analysis_results
                        (symbol, timestamp, 
                         sentiment_score, confidence_level, data_source,
                         data_completeness_percentage, created_at)
                        VALUES (%s, %s, NULL, NULL, 'placeholder_generator', 0.0, NOW())
                    """, (symbol, timestamp))
                    
                    if cursor.rowcount > 0:
                        placeholders_created += 1
                        
                except Exception as e:
                    logger.debug(f"Error creating sentiment placeholder {symbol} {timestamp}: {e}")
        
        current_date += timedelta(days=1)
    
    return placeholders_created

def main():
    """Main function to generate all placeholders"""
    logger.info("🔧 Starting comprehensive placeholder generation...")
    
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Could not connect to database")
        return
    
    try:
        cursor = conn.cursor()
        total_created = 0
        
        # 1. Create macro placeholders
        logger.info("📊 Creating macro indicator placeholders...")
        macro_created = create_macro_placeholders(cursor)
        logger.info(f"   Created {macro_created} macro placeholders")
        total_created += macro_created
        
        # 2. Create technical placeholders
        logger.info("📈 Creating technical indicator placeholders...")
        technical_created = create_technical_placeholders(cursor)
        logger.info(f"   Created {technical_created} technical placeholders")
        total_created += technical_created
        
        # 3. Create onchain placeholders
        logger.info("🔗 Creating onchain data placeholders...")
        onchain_created = create_onchain_placeholders(cursor)
        logger.info(f"   Created {onchain_created} onchain placeholders")
        total_created += onchain_created
        
        # 4. Create sentiment placeholders (if table exists)
        try:
            cursor.execute("SHOW TABLES LIKE 'sentiment_analysis_results'")
            if cursor.fetchone():
                logger.info("💭 Creating sentiment analysis placeholders...")
                sentiment_created = create_sentiment_placeholders(cursor)
                logger.info(f"   Created {sentiment_created} sentiment placeholders")
                total_created += sentiment_created
            else:
                logger.info("⚠️  Sentiment table not found, skipping sentiment placeholders")
        except Exception as e:
            logger.warning(f"Could not check sentiment table: {e}")
        
        # Commit all changes
        conn.commit()
        
        logger.info(f"✅ Placeholder generation completed!")
        logger.info(f"   Total placeholders created: {total_created}")
        
        # Get completeness summary
        try:
            logger.info("\n📊 Current Data Completeness Summary:")
            
            # Macro completeness
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
                    ROUND(AVG(COALESCE(data_completeness_percentage, 0)), 1) as avg_completeness
                FROM macro_indicators 
                WHERE indicator_date >= '2023-01-01'
            """)
            macro_stats = cursor.fetchone()
            logger.info(f"   Macro Indicators (since 2023): {macro_stats[1]}/{macro_stats[0]} filled ({macro_stats[2]}% avg)")
            
            # Technical completeness
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
                    ROUND(AVG(COALESCE(data_completeness_percentage, 0)), 1) as avg_completeness
                FROM technical_indicators 
                WHERE timestamp_iso >= '2023-01-01'
            """)
            tech_stats = cursor.fetchone()
            logger.info(f"   Technical Indicators (since 2023): {tech_stats[1]}/{tech_stats[0]} filled ({tech_stats[2]}% avg)")
            
            # Onchain completeness
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
                    ROUND(AVG(COALESCE(data_completeness_percentage, 0)), 1) as avg_completeness
                FROM crypto_onchain_data 
                WHERE timestamp >= '2023-01-01'
            """)
            onchain_stats = cursor.fetchone()
            logger.info(f"   Onchain Data (since 2023): {onchain_stats[1]}/{onchain_stats[0]} filled ({onchain_stats[2]}% avg)")
            
        except Exception as e:
            logger.warning(f"Could not generate completeness summary: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error during placeholder generation: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()