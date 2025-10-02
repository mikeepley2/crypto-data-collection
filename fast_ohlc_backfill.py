#!/usr/bin/env python3
"""
Fast OHLC Backfill Script using bulk SQL operations
Updates ml_features_materialized with real OHLC data using efficient JOIN queries
"""

import mysql.connector
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FastOHLCBackfill:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'host.docker.internal'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'charset': 'utf8mb4'
        }

    def get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    def get_stats(self):
        """Get current OHLC statistics"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE open_price IS NOT NULL")
        with_ohlc = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return total, with_ohlc, (with_ohlc / total * 100) if total > 0 else 0

    def run_bulk_update(self):
        """Run bulk OHLC update using efficient SQL JOIN"""
        logger.info("🚀 Starting Fast Bulk OHLC Update")
        
        # Get initial stats
        total, initial_ohlc, initial_pct = self.get_stats()
        logger.info(f"📊 Initial: {initial_ohlc:,}/{total:,} ({initial_pct:.1f}%) have OHLC")
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        start_time = time.time()
        
        # Bulk update using JOIN - updates records where OHLC data exists and ML record lacks it
        bulk_update_sql = """
        UPDATE ml_features_materialized ml
        JOIN (
            SELECT 
                symbol,
                DATE(timestamp_iso) as ohlc_date,
                open_price,
                high_price, 
                low_price,
                close_price,
                volume as ohlc_volume,
                data_source as ohlc_source,
                ROW_NUMBER() OVER (PARTITION BY symbol, DATE(timestamp_iso) ORDER BY timestamp_iso DESC) as rn
            FROM ohlc_data 
        ) ohlc ON ml.symbol = ohlc.symbol AND ml.price_date = ohlc.ohlc_date
        SET 
            ml.open_price = ohlc.open_price,
            ml.high_price = ohlc.high_price,
            ml.low_price = ohlc.low_price, 
            ml.close_price = ohlc.close_price,
            ml.ohlc_volume = ohlc.ohlc_volume,
            ml.ohlc_source = ohlc.ohlc_source
        WHERE 
            ohlc.rn = 1 
            AND ml.open_price IS NULL
            AND ohlc.open_price IS NOT NULL
        """
        
        logger.info("⚡ Executing bulk OHLC update (this may take several minutes)...")
        cursor.execute(bulk_update_sql)
        rows_updated = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get final stats
        total, final_ohlc, final_pct = self.get_stats()
        improvement = final_ohlc - initial_ohlc
        
        logger.info(f"✅ Bulk update complete!")
        logger.info(f"📊 Updated {rows_updated:,} records in {duration:.1f} seconds")
        logger.info(f"📈 Final: {final_ohlc:,}/{total:,} ({final_pct:.1f}%) have OHLC")
        logger.info(f"🎉 Improvement: +{improvement:,} records ({((final_ohlc/initial_ohlc)-1)*100:+.1f}%)")

if __name__ == "__main__":
    processor = FastOHLCBackfill()
    processor.run_bulk_update()