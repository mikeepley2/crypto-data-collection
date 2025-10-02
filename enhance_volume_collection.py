#!/usr/bin/env python3

import mysql.connector
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )


def enhance_volume_from_price_data():
    """Enhance volume data using price_data table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Enhancing volume data from price_data table")
        
        # Update volume data from price_data where missing
        update_query = """
            UPDATE ml_features_materialized ml
            INNER JOIN (
                SELECT 
                    symbol,
                    timestamp,
                    volume_24h as pd_volume,
                    ROW_NUMBER() OVER (PARTITION BY symbol, timestamp ORDER BY timestamp DESC) as rn
                FROM price_data 
                WHERE volume_24h > 0
                  AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ) pd ON ml.symbol = pd.symbol 
                 AND ml.timestamp = pd.timestamp 
                 AND pd.rn = 1
            SET 
                ml.volume_24h = COALESCE(ml.volume_24h, pd.pd_volume),
                ml.hourly_volume = COALESCE(ml.hourly_volume, pd.pd_volume / 24),
                ml.updated_at = NOW()
            WHERE (ml.volume_24h IS NULL OR ml.volume_24h = 0)
              AND pd.pd_volume > 0
              AND ml.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """
        
        cursor.execute(update_query)
        updated_count = cursor.rowcount
        
        conn.commit()
        logger.info(f"✅ Enhanced volume data for {updated_count} records from price_data")
        
        cursor.close()
        conn.close()
        return updated_count
        
    except Exception as e:
        logger.error(f"Error enhancing volume from price data: {e}")
        return 0


def enhance_volume_from_ohlc():
    """Enhance volume data using OHLC data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Enhancing volume data from OHLC data")
        
        # Update volume data from OHLC where missing
        update_query = """
            UPDATE ml_features_materialized ml
            INNER JOIN (
                SELECT 
                    symbol,
                    timestamp,
                    volume as ohlc_volume,
                    ROW_NUMBER() OVER (PARTITION BY symbol, timestamp ORDER BY timestamp DESC) as rn
                FROM ohlc_data 
                WHERE volume > 0
                  AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ) ohlc ON ml.symbol = ohlc.symbol 
                   AND ml.timestamp = ohlc.timestamp 
                   AND ohlc.rn = 1
            SET 
                ml.volume_24h = COALESCE(ml.volume_24h, ohlc.ohlc_volume),
                ml.ohlc_volume = COALESCE(ml.ohlc_volume, ohlc.ohlc_volume),
                ml.total_volume_24h = COALESCE(ml.total_volume_24h, ohlc.ohlc_volume),
                ml.updated_at = NOW()
            WHERE (ml.volume_24h IS NULL OR ml.volume_24h = 0)
              AND ohlc.ohlc_volume > 0
              AND ml.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """
        
        cursor.execute(update_query)
        updated_count = cursor.rowcount
        
        conn.commit()
        logger.info(f"✅ Enhanced volume data for {updated_count} records from OHLC")
        
        cursor.close()
        conn.close()
        return updated_count
        
    except Exception as e:
        logger.error(f"Error enhancing volume from OHLC: {e}")
        return 0


def calculate_derived_volume_metrics():
    """Calculate derived volume metrics where base volume exists"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Calculating derived volume metrics")
        
        # Calculate volume-based metrics where volume exists but metrics are missing
        update_query = """
            UPDATE ml_features_materialized 
            SET 
                hourly_volume = COALESCE(hourly_volume, volume_24h / 24),
                volume_qty_24h = COALESCE(volume_qty_24h, volume_24h),
                volume_24h_usd = COALESCE(volume_24h_usd, volume_24h * current_price),
                total_volume_24h = COALESCE(total_volume_24h, volume_24h),
                updated_at = NOW()
            WHERE volume_24h > 0 
              AND (hourly_volume IS NULL 
                   OR volume_qty_24h IS NULL 
                   OR volume_24h_usd IS NULL
                   OR total_volume_24h IS NULL)
              AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """
        
        cursor.execute(update_query)
        updated_count = cursor.rowcount
        
        conn.commit()
        logger.info(f"✅ Calculated derived metrics for {updated_count} records")
        
        cursor.close()
        conn.close()
        return updated_count
        
    except Exception as e:
        logger.error(f"Error calculating derived volume metrics: {e}")
        return 0


def analyze_volume_improvements():
    """Analyze the volume data improvements"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check volume coverage before and after
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) as has_volume,
                SUM(CASE WHEN hourly_volume > 0 THEN 1 ELSE 0 END) as has_hourly_volume,
                SUM(CASE WHEN volume_24h_usd > 0 THEN 1 ELSE 0 END) as has_usd_volume,
                ROUND(SUM(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as volume_percentage
            FROM ml_features_materialized
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        has_volume = result[1]
        has_hourly = result[2]
        has_usd = result[3]
        percentage = result[4]
        
        print(f"\n📊 VOLUME DATA ANALYSIS (Last 7 days)")
        print(f"Total records: {total:,}")
        print(f"Has volume_24h: {has_volume:,} ({percentage}%)")
        print(f"Has hourly_volume: {has_hourly:,} ({has_hourly/total*100:.1f}%)")
        print(f"Has volume_24h_usd: {has_usd:,} ({has_usd/total*100:.1f}%)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error analyzing volume improvements: {e}")
        return False


def main():
    """Main function to enhance volume data collection"""
    logger.info("Starting volume data enhancement process...")
    
    print("📊 VOLUME DATA ENHANCEMENT PROCESS")
    print("=" * 60)
    
    total_improvements = 0
    
    # Step 1: Enhance from price_data
    print("\n🔄 Step 1: Enhancing volume from price_data...")
    price_improvements = enhance_volume_from_price_data()
    total_improvements += price_improvements
    
    # Step 2: Enhance from OHLC data
    print("\n🔄 Step 2: Enhancing volume from OHLC data...")
    ohlc_improvements = enhance_volume_from_ohlc()
    total_improvements += ohlc_improvements
    
    # Step 3: Calculate derived metrics
    print("\n🔄 Step 3: Calculating derived volume metrics...")
    derived_improvements = calculate_derived_volume_metrics()
    total_improvements += derived_improvements
    
    # Step 4: Analyze improvements
    print("\n📈 Step 4: Analyzing improvements...")
    analyze_volume_improvements()
    
    print(f"\n" + "=" * 60)
    print(f"✅ VOLUME ENHANCEMENT COMPLETED")
    print(f"Total records improved: {total_improvements:,}")
    print("=" * 60)
    
    return total_improvements > 0


if __name__ == "__main__":
    main()