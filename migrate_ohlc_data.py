#!/usr/bin/env python3
"""
OHLC Data Migration Script

This script migrates OHLC data from price_data_real to ohlc_data table
to consolidate all OHLC information in one location.

Current situation:
- ohlc_data: 188,105 records 
- price_data_real: 324,196 records with OHLC data
- Goal: Migrate 136,000+ additional OHLC records to ohlc_data

Data mapping:
- price_data_real.open_24h → ohlc_data.open_price
- price_data_real.high_24h → ohlc_data.high_price 
- price_data_real.low_24h → ohlc_data.low_price
- price_data_real.current_price → ohlc_data.close_price
- price_data_real.volume_qty_24h → ohlc_data.volume
"""

import mysql.connector
import logging
from datetime import datetime
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ohlc_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host='localhost',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices',
        autocommit=False
    )

def analyze_migration_scope():
    """Analyze what data needs to be migrated"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    logger.info("=== ANALYZING MIGRATION SCOPE ===")
    
    # Current ohlc_data count
    cursor.execute("SELECT COUNT(*) as count FROM ohlc_data")
    ohlc_count = cursor.fetchone()['count']
    
    # Price_data_real records with OHLC data
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM price_data_real 
        WHERE high_24h IS NOT NULL 
        AND low_24h IS NOT NULL 
        AND open_24h IS NOT NULL
        AND current_price IS NOT NULL
    """)
    pdr_ohlc_count = cursor.fetchone()['count']
    
    # Check for existing duplicates by symbol and date
    cursor.execute("""
        SELECT COUNT(*) as potential_duplicates
        FROM price_data_real pdr
        INNER JOIN ohlc_data od ON (
            pdr.symbol = od.symbol 
            AND DATE(pdr.timestamp_iso) = DATE(od.timestamp_iso)
        )
        WHERE pdr.high_24h IS NOT NULL
    """)
    duplicates = cursor.fetchone()['potential_duplicates']
    
    # Estimate new records to migrate
    cursor.execute("""
        SELECT COUNT(*) as new_records
        FROM price_data_real pdr
        LEFT JOIN ohlc_data od ON (
            pdr.symbol = od.symbol 
            AND DATE(pdr.timestamp_iso) = DATE(od.timestamp_iso)
        )
        WHERE pdr.high_24h IS NOT NULL 
        AND od.id IS NULL
    """)
    new_records = cursor.fetchone()['new_records']
    
    logger.info(f"Current ohlc_data records: {ohlc_count:,}")
    logger.info(f"price_data_real OHLC records: {pdr_ohlc_count:,}")
    logger.info(f"Potential date/symbol duplicates: {duplicates:,}")
    logger.info(f"New records to migrate: {new_records:,}")
    logger.info(f"Expected final ohlc_data size: {ohlc_count + new_records:,}")
    
    cursor.close()
    conn.close()
    
    return {
        'current_ohlc': ohlc_count,
        'source_ohlc': pdr_ohlc_count, 
        'duplicates': duplicates,
        'new_records': new_records
    }

def migrate_ohlc_data(batch_size=1000, dry_run=False):
    """Migrate OHLC data from price_data_real to ohlc_data"""
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    logger.info("=== STARTING OHLC DATA MIGRATION ===")
    logger.info(f"Batch size: {batch_size}, Dry run: {dry_run}")
    
    try:
        # Migration query - select records that don't exist in ohlc_data
        migration_query = """
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
            'migrated_from_price_data_real' as data_source
        FROM price_data_real pdr
        LEFT JOIN ohlc_data od ON (
            pdr.symbol = od.symbol 
            AND DATE(pdr.timestamp_iso) = DATE(od.timestamp_iso)
        )
        WHERE pdr.high_24h IS NOT NULL 
        AND pdr.low_24h IS NOT NULL 
        AND pdr.open_24h IS NOT NULL
        AND pdr.current_price IS NOT NULL
        AND od.id IS NULL
        ORDER BY pdr.timestamp_iso ASC
        LIMIT %s OFFSET %s
        """
        
        # Insert query for ohlc_data
        insert_query = """
        INSERT INTO ohlc_data 
        (symbol, coin_id, timestamp_unix, timestamp_iso, open_price, high_price, 
         low_price, close_price, volume, data_source, created_at)
        VALUES (%(symbol)s, %(coin_id)s, %(timestamp_unix)s, %(timestamp_iso)s, 
                %(open_price)s, %(high_price)s, %(low_price)s, %(close_price)s, 
                %(volume)s, %(data_source)s, NOW())
        """
        
        offset = 0
        total_migrated = 0
        
        while True:
            # Get batch of records to migrate
            cursor.execute(migration_query, (batch_size, offset))
            batch = cursor.fetchall()
            
            if not batch:
                logger.info("No more records to migrate")
                break
                
            logger.info(f"Processing batch of {len(batch)} records (offset: {offset})")
            
            if not dry_run:
                # Insert batch into ohlc_data
                cursor.executemany(insert_query, batch)
                conn.commit()
                logger.info(f"Inserted {len(batch)} records")
            else:
                logger.info(f"[DRY RUN] Would insert {len(batch)} records")
                # Show sample of what would be migrated
                if offset == 0:  # Show samples from first batch only
                    logger.info("Sample records that would be migrated:")
                    for i, record in enumerate(batch[:3]):
                        logger.info(f"  {i+1}. {record['symbol']} {record['timestamp_iso']} O:{record['open_price']} H:{record['high_price']} L:{record['low_price']} C:{record['close_price']}")
            
            total_migrated += len(batch)
            offset += batch_size
            
            # Progress update every 10 batches
            if offset % (batch_size * 10) == 0:
                logger.info(f"Progress: {total_migrated:,} records processed")
                
        logger.info(f"Migration completed! Total records processed: {total_migrated:,}")
        
        if not dry_run:
            # Verify final counts
            cursor.execute("SELECT COUNT(*) as count FROM ohlc_data")
            final_count = cursor.fetchone()['count']
            logger.info(f"Final ohlc_data table size: {final_count:,} records")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def validate_migration():
    """Validate the migration results"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    logger.info("=== VALIDATING MIGRATION RESULTS ===")
    
    # Check total records
    cursor.execute("SELECT COUNT(*) as count FROM ohlc_data")
    total_count = cursor.fetchone()['count']
    
    # Check migrated records
    cursor.execute("SELECT COUNT(*) as count FROM ohlc_data WHERE data_source = 'migrated_from_price_data_real'")
    migrated_count = cursor.fetchone()['count']
    
    # Check symbol coverage
    cursor.execute("SELECT COUNT(DISTINCT symbol) as count FROM ohlc_data")
    symbol_count = cursor.fetchone()['count']
    
    # Check date range
    cursor.execute("SELECT MIN(timestamp_iso) as min_date, MAX(timestamp_iso) as max_date FROM ohlc_data")
    date_range = cursor.fetchone()
    
    # Sample of migrated data
    cursor.execute("""
        SELECT symbol, timestamp_iso, open_price, high_price, low_price, close_price 
        FROM ohlc_data 
        WHERE data_source = 'migrated_from_price_data_real' 
        ORDER BY timestamp_iso DESC 
        LIMIT 5
    """)
    samples = cursor.fetchall()
    
    logger.info(f"Total ohlc_data records: {total_count:,}")
    logger.info(f"Migrated records: {migrated_count:,}")
    logger.info(f"Unique symbols: {symbol_count}")
    logger.info(f"Date range: {date_range['min_date']} to {date_range['max_date']}")
    
    logger.info("Sample migrated records:")
    for sample in samples:
        logger.info(f"  {sample['symbol']} {sample['timestamp_iso']} O:{sample['open_price']} H:{sample['high_price']} L:{sample['low_price']} C:{sample['close_price']}")
    
    cursor.close()
    conn.close()

def main():
    """Main migration function"""
    start_time = time.time()
    
    try:
        logger.info("Starting OHLC data migration process")
        
        # Step 1: Analyze scope
        scope = analyze_migration_scope()
        
        if scope['new_records'] == 0:
            logger.info("No new records to migrate. Migration complete!")
            return
            
        # Step 2: Confirm migration
        logger.info(f"\nReady to migrate {scope['new_records']:,} new OHLC records")
        
        # For safety, run a small dry run first
        logger.info("Running small dry run first...")
        migrate_ohlc_data(batch_size=100, dry_run=True)
        
        # Ask for confirmation (in real script, but auto-proceed for automation)
        response = input("\nProceed with full migration? (y/N): ").lower().strip()
        if response != 'y':
            logger.info("Migration cancelled by user")
            return
            
        # Step 3: Run migration
        migrate_ohlc_data(batch_size=1000, dry_run=False)
        
        # Step 4: Validate results
        validate_migration()
        
        duration = time.time() - start_time
        logger.info(f"Migration completed successfully in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()