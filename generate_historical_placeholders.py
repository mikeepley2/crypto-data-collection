#!/usr/bin/env python3
"""
Historical Placeholder Generator - Optimized for Full 2023-Present Range
Creates placeholder records for all collectors with proper scheduling frequencies
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

def create_macro_placeholders_historical(cursor):
    """Create macro indicator placeholders from 2023 to present (daily frequency)"""
    placeholders_created = 0
    indicators = ['VIX', 'DXY', 'FEDFUNDS', 'DGS10', 'DGS2', 'UNRATE', 'CPIAUCSL', 'GDP']
    
    # Historical range: 2023-01-01 to present
    start_date = datetime(2023, 1, 1).date()
    end_date = datetime.now().date()
    total_days = (end_date - start_date).days + 1
    
    logger.info(f"Creating macro placeholders from {start_date} to {end_date} ({total_days} days × {len(indicators)} indicators)")
    
    # Batch processing for efficiency
    batch_size = 100
    current_date = start_date
    processed_days = 0
    
    while current_date <= end_date:
        batch_end_date = min(current_date + timedelta(days=batch_size), end_date)
        
        # Process batch
        for indicator in indicators:
            batch_date = current_date
            while batch_date <= batch_end_date:
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO macro_indicators 
                        (indicator_name, indicator_date, value, data_source, 
                         data_completeness_percentage, collected_at)
                        VALUES (%s, %s, NULL, 'placeholder_generator', 0.0, NOW())
                    """, (indicator, batch_date))
                    
                    if cursor.rowcount > 0:
                        placeholders_created += 1
                        
                except Exception as e:
                    logger.debug(f"Error creating macro placeholder {indicator} {batch_date}: {e}")
                
                batch_date += timedelta(days=1)
        
        processed_days += (batch_end_date - current_date).days + 1
        progress = (processed_days / total_days) * 100
        logger.info(f"   Macro progress: {processed_days}/{total_days} days ({progress:.1f}%)")
        
        current_date = batch_end_date + timedelta(days=1)
    
    return placeholders_created

def create_technical_placeholders_historical(cursor):
    """Create technical indicator placeholders from 2023 to present (hourly frequency for efficiency)"""
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
    
    # Use hourly instead of 5-minute intervals for historical data (more manageable)
    start_time = datetime(2023, 1, 1, 0, 0)
    end_time = datetime.now()
    total_hours = int((end_time - start_time).total_seconds() / 3600)
    
    logger.info(f"Creating technical placeholders for {len(symbols)} symbols from {start_time} to {end_time} (hourly intervals)")
    logger.info(f"Total estimated records: {total_hours * len(symbols):,}")
    
    # Process in monthly batches to manage memory
    current_time = start_time
    processed_hours = 0
    batch_hours = 24 * 30  # 30 days worth of hours
    
    while current_time <= end_time:
        batch_end_time = min(current_time + timedelta(hours=batch_hours), end_time)
        
        # Process each symbol in this time batch
        for symbol in symbols:
            batch_time = current_time
            while batch_time <= batch_end_time:
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
                    """, (symbol, batch_time))
                    
                    if cursor.rowcount > 0:
                        placeholders_created += 1
                        
                except Exception as e:
                    logger.debug(f"Error creating technical placeholder {symbol} {batch_time}: {e}")
                
                batch_time += timedelta(hours=1)
        
        processed_hours += int((batch_end_time - current_time).total_seconds() / 3600)
        progress = (processed_hours / total_hours) * 100
        logger.info(f"   Technical progress: {processed_hours:,}/{total_hours:,} hours ({progress:.1f}%)")
        
        current_time = batch_end_time + timedelta(hours=1)
        
        # Commit batch to prevent memory issues
        cursor.connection.commit()
    
    return placeholders_created

def create_onchain_placeholders_historical(cursor):
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
    """Main function to generate historical placeholders"""
    logger.info("🔧 Starting HISTORICAL placeholder generation (2023-present)...")
    logger.info("⚠️  This will create placeholders based on collector schedules:")
    logger.info("   - Macro indicators: Daily frequency")
    logger.info("   - Technical indicators: Hourly frequency") 
    logger.info("   - Onchain data: Daily frequency")
    
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Could not connect to database")
        return
    
    try:
        cursor = conn.cursor()
        total_created = 0
        start_time = datetime.now()
        
        # 1. Create macro placeholders
        logger.info("\n📊 Creating macro indicator placeholders...")
        macro_created = create_macro_placeholders_historical(cursor)
        logger.info(f"   ✅ Created {macro_created:,} macro placeholders")
        total_created += macro_created
        conn.commit()
        
        # 2. Create technical placeholders
        logger.info("\n📈 Creating technical indicator placeholders...")
        technical_created = create_technical_placeholders_historical(cursor)
        logger.info(f"   ✅ Created {technical_created:,} technical placeholders")
        total_created += technical_created
        conn.commit()
        
        # 3. Create onchain placeholders
        logger.info("\n🔗 Creating onchain data placeholders...")
        onchain_created = create_onchain_placeholders_historical(cursor)
        logger.info(f"   ✅ Created {onchain_created:,} onchain placeholders")
        total_created += onchain_created
        conn.commit()
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"\n🎯 HISTORICAL PLACEHOLDER GENERATION COMPLETED!")
        logger.info(f"   Duration: {duration}")
        logger.info(f"   Total placeholders created: {total_created:,}")
        logger.info(f"   Breakdown:")
        logger.info(f"     - Macro indicators: {macro_created:,}")
        logger.info(f"     - Technical indicators: {technical_created:,}")
        logger.info(f"     - Onchain data: {onchain_created:,}")
        
        # Get final completeness summary
        try:
            logger.info(f"\n📊 Final Data Completeness Summary:")
            
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
            logger.info(f"   Macro Indicators (since 2023): {macro_stats[1]:,}/{macro_stats[0]:,} filled ({macro_stats[2]}% avg)")
            
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
            logger.info(f"   Technical Indicators (since 2023): {tech_stats[1]:,}/{tech_stats[0]:,} filled ({tech_stats[2]}% avg)")
            
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
            logger.info(f"   Onchain Data (since 2023): {onchain_stats[1]:,}/{onchain_stats[0]:,} filled ({onchain_stats[2]}% avg)")
            
            total_all = macro_stats[0] + tech_stats[0] + onchain_stats[0]
            total_filled_all = macro_stats[1] + tech_stats[1] + onchain_stats[1]
            logger.info(f"\n🎯 Grand Total: {total_filled_all:,}/{total_all:,} records tracked ({(total_filled_all/total_all*100) if total_all > 0 else 0:.1f}% filled)")
            
        except Exception as e:
            logger.warning(f"Could not generate completeness summary: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error during historical placeholder generation: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Confirmation prompt for large operation
    print("⚠️  WARNING: This will create historical placeholders from 2023-01-01 to present.")
    print("   This could create millions of records and take significant time.")
    print("   Estimated records:")
    print("   - Macro: ~20,000 records (daily)")
    print("   - Technical: ~500,000+ records (hourly)")  
    print("   - Onchain: ~20,000 records (daily)")
    print("")
    
    confirm = input("Do you want to proceed? (yes/no): ").lower().strip()
    if confirm in ['yes', 'y']:
        main()
    else:
        print("Operation cancelled.")