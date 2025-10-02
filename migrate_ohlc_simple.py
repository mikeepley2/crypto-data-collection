#!/usr/bin/env python3
"""
Simple OHLC Data Migration Script
Migrates OHLC data from price_data_real to ohlc_data table
"""

import mysql.connector
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices',
        autocommit=False
    )


def migrate_ohlc_data():
    """Simple migration without complex JOINs to avoid collation issues"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("=== STARTING OHLC DATA MIGRATION ===")
    
    try:
        # First, get all records from price_data_real with OHLC data
        logger.info("Getting source records from price_data_real...")
        cursor.execute("""
            SELECT 
                symbol,
                coin_id,
                UNIX_TIMESTAMP(timestamp_iso) as timestamp_unix,
                timestamp_iso,
                open_24h,
                high_24h,
                low_24h,
                current_price,
                volume_qty_24h
            FROM price_data_real 
            WHERE high_24h IS NOT NULL 
            AND low_24h IS NOT NULL 
            AND open_24h IS NOT NULL
            AND current_price IS NOT NULL
            ORDER BY timestamp_iso ASC
        """)
        
        source_records = cursor.fetchall()
        logger.info(f"Found {len(source_records):,} potential records to migrate")
        
        # Create a set of existing ohlc_data entries for duplicate checking
        logger.info("Getting existing ohlc_data records for duplicate checking...")
        cursor.execute("""
            SELECT CONCAT(symbol, '|', DATE(timestamp_iso)) as key
            FROM ohlc_data
        """)
        
        existing_keys = set(row[0] for row in cursor.fetchall())
        logger.info(f"Found {len(existing_keys):,} existing ohlc_data entries")
        
        # Filter out duplicates
        records_to_insert = []
        duplicates_skipped = 0
        
        for record in source_records:
            symbol, coin_id, timestamp_unix, timestamp_iso, open_24h, high_24h, low_24h, current_price, volume_qty_24h = record
            
            # Create key for duplicate checking
            key = f"{symbol}|{timestamp_iso.date()}"
            
            if key not in existing_keys:
                records_to_insert.append((
                    symbol, coin_id, timestamp_unix, timestamp_iso,
                    open_24h, high_24h, low_24h, current_price, volume_qty_24h,
                    'migrated_from_price_data_real'
                ))
            else:
                duplicates_skipped += 1
        
        logger.info(f"Records to insert: {len(records_to_insert):,}")
        logger.info(f"Duplicates skipped: {duplicates_skipped:,}")
        
        if not records_to_insert:
            logger.info("No new records to migrate!")
            return
            
        # Show samples
        logger.info("Sample records to migrate:")
        for i, record in enumerate(records_to_insert[:5]):
            logger.info(f"  {i+1}. {record[0]} {record[3]} O:{record[4]} H:{record[5]} L:{record[6]} C:{record[7]}")
        
        # Insert in batches
        batch_size = 1000
        total_inserted = 0
        
        insert_query = """
            INSERT INTO ohlc_data 
            (symbol, coin_id, timestamp_unix, timestamp_iso, open_price, high_price, 
             low_price, close_price, volume, data_source, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        
        for i in range(0, len(records_to_insert), batch_size):
            batch = records_to_insert[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            total_inserted += len(batch)
            logger.info(f"Inserted batch: {total_inserted:,}/{len(records_to_insert):,} records")
            
        logger.info(f"Migration completed! Inserted {total_inserted:,} new OHLC records")
        
        # Verify final count
        cursor.execute("SELECT COUNT(*) FROM ohlc_data")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final ohlc_data table size: {final_count:,} records")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    start_time = time.time()
    
    try:
        migrate_ohlc_data()
        duration = time.time() - start_time
        logger.info(f"Migration completed in {duration:.2f} seconds")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()