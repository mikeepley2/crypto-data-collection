#!/usr/bin/env python3
"""
OHLC Backfill Script
Populates ml_features_materialized records with real OHLC data from ohlc_data table.
Uses the 512K real OHLC records to enhance ML features.
"""

import mysql.connector
import os
import sys
import time
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OHLCBackfillProcessor:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'host.docker.internal'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        logger.info(f"🔗 Connecting to database: {self.db_config['host']}")

    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)

    def get_ohlc_statistics(self):
        """Get current OHLC population statistics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get total ML records
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_ml_records = cursor.fetchone()[0]
        
        # Get ML records with OHLC
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE open_price IS NOT NULL")
        ml_with_ohlc = cursor.fetchone()[0]
        
        # Get total OHLC records available
        cursor.execute("SELECT COUNT(*) FROM ohlc_data")
        total_ohlc_records = cursor.fetchone()[0]
        
        # Get unique symbols in ohlc_data
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ohlc_data")
        ohlc_symbols = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'total_ml_records': total_ml_records,
            'ml_with_ohlc': ml_with_ohlc,
            'total_ohlc_records': total_ohlc_records,
            'ohlc_symbols': ohlc_symbols,
            'ohlc_percentage': (ml_with_ohlc / total_ml_records * 100) if total_ml_records > 0 else 0
        }

    def get_matching_ohlc_data(self, symbol, date):
        """Get OHLC data for a specific symbol and date"""
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get daily OHLC data for the date (use most recent for that day)
        query = """
        SELECT 
            open_price,
            high_price,
            low_price,
            close_price,
            volume as ohlc_volume,
            data_source as ohlc_source
        FROM ohlc_data 
        WHERE symbol = %s 
        AND DATE(timestamp_iso) = %s
        ORDER BY timestamp_iso DESC
        LIMIT 1
        """
        cursor.execute(query, (symbol, date))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result

    def update_ml_record_with_ohlc(self, symbol, date, hour, ohlc_data):
        """Update ML record with OHLC data"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        update_sql = """
        UPDATE ml_features_materialized 
        SET 
            open_price = %s,
            high_price = %s,
            low_price = %s,
            close_price = %s,
            ohlc_volume = %s,
            ohlc_source = %s
        WHERE symbol = %s AND price_date = %s AND price_hour = %s
        """
        
        cursor.execute(update_sql, (
            ohlc_data['open_price'],
            ohlc_data['high_price'],
            ohlc_data['low_price'],
            ohlc_data['close_price'],
            ohlc_data['ohlc_volume'],
            ohlc_data['ohlc_source'],
            symbol,
            date,
            hour
        ))
        
        rows_updated = cursor.rowcount
        cursor.close()
        conn.close()
        
        return rows_updated

    def get_ml_records_needing_ohlc(self, batch_size=1000):
        """Get ML records that need OHLC data, in batches"""
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get records without OHLC data, ordered by date and symbol for efficient processing
        query = """
        SELECT symbol, price_date, price_hour
        FROM ml_features_materialized 
        WHERE open_price IS NULL
        ORDER BY symbol, price_date, price_hour
        LIMIT %s
        """
        
        cursor.execute(query, (batch_size,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results

    def run_ohlc_backfill(self, batch_size=1000, max_batches=None):
        """Run the OHLC backfill process"""
        logger.info("🚀 Starting OHLC Backfill Process")
        
        # Get initial statistics
        initial_stats = self.get_ohlc_statistics()
        logger.info(f"📊 Initial Statistics:")
        logger.info(f"   Total ML records: {initial_stats['total_ml_records']:,}")
        logger.info(f"   ML records with OHLC: {initial_stats['ml_with_ohlc']:,}")
        logger.info(f"   OHLC percentage: {initial_stats['ohlc_percentage']:.1f}%")
        logger.info(f"   Available OHLC records: {initial_stats['total_ohlc_records']:,}")
        logger.info(f"   OHLC covers {initial_stats['ohlc_symbols']} symbols")
        
        total_updated = 0
        total_processed = 0
        batch_count = 0
        start_time = time.time()
        
        while True:
            batch_count += 1
            if max_batches and batch_count > max_batches:
                logger.info(f"🛑 Reached maximum batch limit: {max_batches}")
                break
                
            # Get batch of ML records needing OHLC
            ml_records = self.get_ml_records_needing_ohlc(batch_size)
            
            if not ml_records:
                logger.info("✅ No more ML records need OHLC data")
                break
                
            logger.info(f"🔄 Processing batch {batch_count} - {len(ml_records)} records")
            
            batch_updated = 0
            batch_start = time.time()
            
            for record in ml_records:
                symbol = record['symbol']
                date = record['price_date']
                hour = record['price_hour']
                
                # Get matching OHLC data
                ohlc_data = self.get_matching_ohlc_data(symbol, date)
                
                if ohlc_data:
                    # Update ML record with OHLC data
                    rows_updated = self.update_ml_record_with_ohlc(symbol, date, hour, ohlc_data)
                    if rows_updated > 0:
                        batch_updated += 1
                        
                total_processed += 1
                
                # Progress logging every 100 records
                if total_processed % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = total_processed / elapsed if elapsed > 0 else 0
                    logger.info(f"⏳ Processed {total_processed:,} records, updated {total_updated:,} ({rate:.1f} rec/sec)")
            
            total_updated += batch_updated
            batch_time = time.time() - batch_start
            
            logger.info(f"✅ Batch {batch_count} complete: {batch_updated}/{len(ml_records)} updated in {batch_time:.1f}s")
            
            # Brief pause between batches to avoid overwhelming database
            time.sleep(0.1)
        
        # Final statistics
        end_time = time.time()
        total_time = end_time - start_time
        
        final_stats = self.get_ohlc_statistics()
        improvement = final_stats['ml_with_ohlc'] - initial_stats['ml_with_ohlc']
        
        logger.info(f"🎉 OHLC Backfill Complete!")
        logger.info(f"   Total processed: {total_processed:,} records")
        logger.info(f"   Total updated: {total_updated:,} records")
        logger.info(f"   Processing time: {total_time:.1f} seconds")
        logger.info(f"   Processing rate: {total_processed/total_time:.1f} records/sec")
        logger.info(f"📈 Final Statistics:")
        logger.info(f"   ML records with OHLC: {final_stats['ml_with_ohlc']:,}")
        logger.info(f"   OHLC percentage: {final_stats['ohlc_percentage']:.1f}%")
        logger.info(f"   Improvement: +{improvement:,} records ({((final_stats['ml_with_ohlc']/initial_stats['ml_with_ohlc'])-1)*100:+.1f}%)")

if __name__ == "__main__":
    processor = OHLCBackfillProcessor()
    
    # Parse command line arguments
    batch_size = 1000
    max_batches = None
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Test mode - process only a few batches
            max_batches = 5
            logger.info("🧪 Running in TEST mode (5 batches max)")
        elif sys.argv[1] == "--stats-only":
            # Just show statistics
            stats = processor.get_ohlc_statistics()
            print(f"ML Records: {stats['ml_with_ohlc']:,}/{stats['total_ml_records']:,} ({stats['ohlc_percentage']:.1f}%) have OHLC")
            print(f"Available OHLC: {stats['total_ohlc_records']:,} records covering {stats['ohlc_symbols']} symbols")
            sys.exit(0)
    
    try:
        processor.run_ohlc_backfill(batch_size=batch_size, max_batches=max_batches)
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error during OHLC backfill: {e}")
        raise