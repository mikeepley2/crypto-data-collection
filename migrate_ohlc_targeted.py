#!/usr/bin/env python3
"""
Targeted OHLC Migration Script
Migrates non-duplicate OHLC data from price_data_real to ohlc_data
"""

import mysql.connector
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_ohlc_targeted():
    """Migrate only non-duplicate OHLC records"""
    
    conn = mysql.connector.connect(
        host='localhost',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    logger.info("=== TARGETED OHLC MIGRATION ===")
    
    try:
        # Strategy: Insert records where there's no existing ohlc_data for that symbol/date
        # Use direct INSERT with NOT EXISTS to avoid loading all data into memory
        
        insert_query = """
        INSERT INTO ohlc_data 
        (symbol, coin_id, timestamp_unix, timestamp_iso, open_price, high_price, 
         low_price, close_price, volume, data_source, created_at)
        SELECT 
            pdr.symbol,
            pdr.coin_id,
            UNIX_TIMESTAMP(pdr.timestamp_iso) as timestamp_unix,
            pdr.timestamp_iso,
            pdr.open_24h as open_price,
            pdr.high_24h as high_price,
            pdr.low_24h as low_price,
            pdr.current_price as close_price,
            pdr.volume_qty_24h as volume,
            'migrated_from_price_data_real' as data_source,
            NOW() as created_at
        FROM price_data_real pdr
        WHERE pdr.high_24h IS NOT NULL 
        AND pdr.low_24h IS NOT NULL 
        AND pdr.open_24h IS NOT NULL
        AND pdr.current_price IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM ohlc_data od 
            WHERE od.symbol = pdr.symbol 
            AND DATE(od.timestamp_iso) = DATE(pdr.timestamp_iso)
        )
        ORDER BY pdr.timestamp_iso ASC
        """
        
        # Get count first to show progress
        count_query = """
        SELECT COUNT(*)
        FROM price_data_real pdr
        WHERE pdr.high_24h IS NOT NULL 
        AND pdr.low_24h IS NOT NULL 
        AND pdr.open_24h IS NOT NULL
        AND pdr.current_price IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM ohlc_data od 
            WHERE od.symbol = pdr.symbol 
            AND DATE(od.timestamp_iso) = DATE(pdr.timestamp_iso)
        )
        """
        
        logger.info("Calculating records to migrate...")
        cursor.execute(count_query)
        records_to_migrate = cursor.fetchone()[0]
        logger.info(f"Records to migrate: {records_to_migrate:,}")
        
        if records_to_migrate == 0:
            logger.info("No new records to migrate!")
            return
        
        # Before migration count
        cursor.execute("SELECT COUNT(*) FROM ohlc_data")
        before_count = cursor.fetchone()[0]
        logger.info(f"Before migration - ohlc_data records: {before_count:,}")
        
        # Execute the migration
        logger.info("Executing migration...")
        cursor.execute(insert_query)
        inserted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"Migration completed! Inserted {inserted_count:,} records")
        
        # After migration count
        cursor.execute("SELECT COUNT(*) FROM ohlc_data")
        after_count = cursor.fetchone()[0]
        logger.info(f"After migration - ohlc_data records: {after_count:,}")
        logger.info(f"Increase: {after_count - before_count:,} records")
        
        # Show sample of migrated data
        cursor.execute("""
            SELECT symbol, timestamp_iso, open_price, high_price, low_price, close_price
            FROM ohlc_data 
            WHERE data_source = 'migrated_from_price_data_real'
            ORDER BY timestamp_iso DESC 
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        logger.info("Sample migrated records:")
        for sample in samples:
            logger.info(f"  {sample[0]} {sample[1]} O:{sample[2]} H:{sample[3]} L:{sample[4]} C:{sample[5]}")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate_ohlc_targeted()