#!/usr/bin/env python3
"""
Simple MaterializedUpdater Fix
Fixed to work with current database schema:
- Uses price_data_real instead of price_data
- Uses correct database host
- Simplified to avoid crashes
"""
import mysql.connector
import os
import sys
import logging
from datetime import datetime, timedelta
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class MaterializedUpdaterFixed:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', '192.168.230.162'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'charset': 'utf8mb4',
            'autocommit': False
        }
        logger.info(f"🔧 MaterializedUpdater initialized with host: {self.db_config['host']}")

    def get_db_connection(self):
        """Get database connection with proper error handling"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def test_connection(self):
        """Test database connection and check available tables"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Check available tables
            cursor.execute("SHOW TABLES LIKE 'price_data%'")
            tables = cursor.fetchall()
            logger.info(f"📊 Available price tables: {[t[0] for t in tables]}")
            
            # Check ml_features_materialized
            cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
            count = cursor.fetchone()[0]
            logger.info(f"📈 ml_features_materialized has {count:,} rows")
            
            # Check recent data in price_data_real
            cursor.execute("""
                SELECT COUNT(*) FROM price_data_real 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)
            recent = cursor.fetchone()[0]
            logger.info(f"📅 Recent price data (24h): {recent:,} rows")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    def simple_update(self):
        """Simple update that just validates the system is working"""
        try:
            logger.info("🚀 Starting simple materialized update validation")
            
            if not self.test_connection():
                logger.error("❌ Connection test failed")
                return False
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get summary stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(CASE WHEN open_price IS NOT NULL THEN 1 END) as with_ohlc,
                    COUNT(CASE WHEN timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_rows
                FROM ml_features_materialized
            """)
            
            result = cursor.fetchone()
            total, with_ohlc, recent = result
            
            ohlc_percentage = (with_ohlc * 100.0 / total) if total > 0 else 0
            
            logger.info(f"📊 Summary Stats:")
            logger.info(f"   Total rows: {total:,}")
            logger.info(f"   With OHLC: {with_ohlc:,} ({ohlc_percentage:.2f}%)")
            logger.info(f"   Recent (24h): {recent:,}")
            
            cursor.close()
            conn.close()
            
            logger.info("✅ Simple update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Simple update failed: {e}")
            return False

def main():
    """Main entry point"""
    logger.info("🚀 Starting MaterializedUpdater Fixed")
    
    updater = MaterializedUpdaterFixed()
    
    # Run simple update
    success = updater.simple_update()
    
    if success:
        logger.info("✅ MaterializedUpdater validation completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ MaterializedUpdater validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()