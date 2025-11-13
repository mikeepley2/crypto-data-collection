#!/usr/bin/env python3
"""
Optimized Historical Placeholder Generator
Creates placeholders with more reasonable frequencies to avoid overwhelming the system
"""

import pymysql
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
db_config = {
    'host': os.getenv("DB_HOST", "172.22.32.1"),
    'user': os.getenv("DB_USER", "news_collector"),
    'password': os.getenv("DB_PASSWORD", "99Rules!"),
    'database': os.getenv("DB_NAME", "crypto_prices"),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get database connection"""
    try:
        return pymysql.connect(**db_config)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_technical_placeholders_daily(cursor):
    """Create technical indicator placeholders with daily frequency (more manageable)"""
    placeholders_created = 0
    
    # Get active symbols
    try:
        cursor.execute("""
            SELECT symbol FROM crypto_assets 
            WHERE is_active = 1 
            ORDER BY market_cap_rank LIMIT 20
        """)
        symbols = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.warning(f"Could not get symbols, using defaults: {e}")
        symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']
    
    # Use daily frequency instead of hourly to be more manageable
    start_date = datetime(2023, 1, 1).date()
    end_date = datetime.now().date()
    total_days = (end_date - start_date).days + 1
    
    logger.info(f"Creating technical placeholders for {len(symbols)} symbols from {start_date} to {end_date} (daily frequency)")
    logger.info(f"Total estimated records: {total_days * len(symbols):,}")
    
    # Process in monthly batches to manage memory
    batch_size = 30  # 30 days at a time
    current_date = start_date
    processed_days = 0
    
    while current_date <= end_date:
        batch_end_date = min(current_date + timedelta(days=batch_size), end_date)
        
        # Process each symbol in this date batch
        for symbol in symbols:
            batch_date = current_date
            while batch_date <= batch_end_date:
                try:
                    # Use a specific hour (e.g., noon UTC) for daily technical data
                    timestamp = datetime.combine(batch_date, datetime.min.time().replace(hour=12))
                    
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
                    """, (symbol, timestamp))
                    
                    if cursor.rowcount > 0:
                        placeholders_created += 1
                        
                except Exception as e:
                    logger.debug(f"Error creating technical placeholder {symbol} {batch_date}: {e}")
                
                batch_date += timedelta(days=1)
        
        processed_days += (batch_end_date - current_date).days + 1
        progress = (processed_days / total_days) * 100
        logger.info(f"   Technical progress: {processed_days}/{total_days} days ({progress:.1f}%)")
        
        current_date = batch_end_date + timedelta(days=1)
        
        # Commit batch to prevent memory issues
        cursor.connection.commit()
    
    return placeholders_created

def create_onchain_placeholders_optimized(cursor):
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
    total_days = (end_date - start_date).days + 1
    
    logger.info(f"Creating onchain placeholders for {len(symbols)} symbols from {start_date} to {end_date} (daily frequency)")
    logger.info(f"Total estimated records: {total_days * len(symbols):,}")
    
    # Batch processing
    batch_size = 30  # 30 days at a time
    current_date = start_date
    processed_days = 0
    
    while current_date <= end_date:
        batch_end_date = min(current_date + timedelta(days=batch_size), end_date)
        
        for symbol in symbols:
            batch_date = current_date
            while batch_date <= batch_end_date:
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
                    """, (symbol, datetime.combine(batch_date, datetime.min.time())))
                    
                    if cursor.rowcount > 0:
                        placeholders_created += 1
                        
                except Exception as e:
                    logger.debug(f"Error creating onchain placeholder {symbol} {batch_date}: {e}")
                
                batch_date += timedelta(days=1)
        
        processed_days += (batch_end_date - current_date).days + 1
        progress = (processed_days / total_days) * 100
        logger.info(f"   Onchain progress: {processed_days}/{total_days} days ({progress:.1f}%)")
        
        current_date = batch_end_date + timedelta(days=1)
        
        # Commit batch
        cursor.connection.commit()
    
    return placeholders_created

def main():
    """Main function to complete historical placeholders"""
    logger.info("🔧 Completing HISTORICAL placeholder generation...")
    logger.info("   Creating remaining placeholders with optimized frequencies")
    
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Could not connect to database")
        return
    
    try:
        cursor = conn.cursor()
        total_created = 0
        start_time = datetime.now()
        
        # 1. Complete technical placeholders with daily frequency
        logger.info("\n📈 Creating technical indicator placeholders (daily frequency)...")
        technical_created = create_technical_placeholders_daily(cursor)
        logger.info(f"   ✅ Created {technical_created:,} technical placeholders")
        total_created += technical_created
        conn.commit()
        
        # 2. Create onchain placeholders
        logger.info("\n🔗 Creating onchain data placeholders...")
        onchain_created = create_onchain_placeholders_optimized(cursor)
        logger.info(f"   ✅ Created {onchain_created:,} onchain placeholders")
        total_created += onchain_created
        conn.commit()
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"\n🎯 HISTORICAL PLACEHOLDER COMPLETION DONE!")
        logger.info(f"   Duration: {duration}")
        logger.info(f"   New placeholders created: {total_created:,}")
        
        # Get final completeness summary
        try:
            logger.info(f"\n📊 Complete Data Status Summary:")
            
            # Macro completeness
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_source LIKE '%placeholder%' THEN 1 ELSE 0 END) as placeholders,
                    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records
                FROM macro_indicators 
                WHERE indicator_date >= '2023-01-01'
            """)
            macro_stats = cursor.fetchone()
            logger.info(f"   Macro Indicators: {macro_stats[0]:,} total, {macro_stats[1]:,} placeholders, {macro_stats[2]:,} filled")
            
            # Technical completeness
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_source LIKE '%placeholder%' THEN 1 ELSE 0 END) as placeholders,
                    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records
                FROM technical_indicators 
                WHERE timestamp_iso >= '2023-01-01'
            """)
            tech_stats = cursor.fetchone()
            logger.info(f"   Technical Indicators: {tech_stats[0]:,} total, {tech_stats[1]:,} placeholders, {tech_stats[2]:,} filled")
            
            # Onchain completeness
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_source LIKE '%placeholder%' THEN 1 ELSE 0 END) as placeholders,
                    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records
                FROM crypto_onchain_data 
                WHERE timestamp >= '2023-01-01'
            """)
            onchain_stats = cursor.fetchone()
            logger.info(f"   Onchain Data: {onchain_stats[0]:,} total, {onchain_stats[1]:,} placeholders, {onchain_stats[2]:,} filled")
            
            total_all = macro_stats[0] + tech_stats[0] + onchain_stats[0]
            total_placeholders_all = macro_stats[1] + tech_stats[1] + onchain_stats[1]
            logger.info(f"\n🎯 Grand Total: {total_all:,} records with {total_placeholders_all:,} placeholders")
            
        except Exception as e:
            logger.warning(f"Could not generate completeness summary: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error during historical placeholder completion: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()