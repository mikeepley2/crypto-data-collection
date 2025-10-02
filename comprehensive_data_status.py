#!/usr/bin/env python3

import mysql.connector
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )


def check_overall_data_status():
    """Check overall data status and improvements"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("📊 COMPREHENSIVE DATA STATUS CHECK")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                MAX(created_at) as latest_timestamp,
                MIN(created_at) as earliest_timestamp
            FROM ml_features_materialized
        """)
        
        result = cursor.fetchone()
        total_records = result[0]
        unique_symbols = result[1]
        latest_ts = result[2]
        earliest_ts = result[3]
        
        print(f"\n🔍 OVERALL STATISTICS")
        print(f"Total records: {total_records:,}")
        print(f"Unique symbols: {unique_symbols:,}")
        print(f"Data range: {earliest_ts} to {latest_ts}")
        
        # Recent data (last 24 hours)
        cursor.execute("""
            SELECT 
                COUNT(*) as recent_records,
                COUNT(DISTINCT symbol) as recent_symbols,
                COUNT(CASE WHEN current_price > 0 THEN 1 END) as has_price,
                COUNT(CASE WHEN volume_24h > 0 THEN 1 END) as has_volume,
                COUNT(CASE WHEN sma_7 IS NOT NULL THEN 1 END) as has_sma7,
                COUNT(CASE WHEN sma_30 IS NOT NULL THEN 1 END) as has_sma30,
                COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_rsi,
                COUNT(CASE WHEN sentiment_score IS NOT NULL THEN 1 END) as has_sentiment,
                COUNT(CASE WHEN dxy IS NOT NULL THEN 1 END) as has_macro
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        recent_total = result[0]
        
        if recent_total > 0:
            print(f"\n📈 RECENT DATA (Last 24 hours)")
            print(f"Recent records: {recent_total:,}")
            print(f"Recent symbols: {result[1]:,}")
            print(f"Has price: {result[2]:,} ({result[2]/recent_total*100:.1f}%)")
            print(f"Has volume: {result[3]:,} ({result[3]/recent_total*100:.1f}%)")
            print(f"Has SMA-7: {result[4]:,} ({result[4]/recent_total*100:.1f}%)")
            print(f"Has SMA-30: {result[5]:,} ({result[5]/recent_total*100:.1f}%)")
            print(f"Has RSI: {result[6]:,} ({result[6]/recent_total*100:.1f}%)")
            print(f"Has sentiment: {result[7]:,} ({result[7]/recent_total*100:.1f}%)")
            print(f"Has macro: {result[8]:,} ({result[8]/recent_total*100:.1f}%)")
        
        # OHLC data coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN open_price > 0 THEN 1 ELSE 0 END) as has_open,
                SUM(CASE WHEN high_price > 0 THEN 1 ELSE 0 END) as has_high,
                SUM(CASE WHEN low_price > 0 THEN 1 ELSE 0 END) as has_low,
                SUM(CASE WHEN close_price > 0 THEN 1 ELSE 0 END) as has_close
            FROM ml_features_materialized
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        week_total = result[0]
        
        if week_total > 0:
            print(f"\n📊 OHLC COVERAGE (Last 7 days)")
            print(f"Total records: {week_total:,}")
            print(f"Has open: {result[1]:,} ({result[1]/week_total*100:.1f}%)")
            print(f"Has high: {result[2]:,} ({result[2]/week_total*100:.1f}%)")
            print(f"Has low: {result[3]:,} ({result[3]/week_total*100:.1f}%)")
            print(f"Has close: {result[4]:,} ({result[4]/week_total*100:.1f}%)")
        
        # Top symbols by data completeness
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as records,
                AVG(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) * 100 as price_coverage,
                AVG(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) * 100 as volume_coverage,
                AVG(CASE WHEN sma_7 IS NOT NULL THEN 1 ELSE 0 END) * 100 as tech_coverage
            FROM ml_features_materialized
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY symbol
            HAVING records >= 10
            ORDER BY (price_coverage + volume_coverage + tech_coverage) DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        print(f"\n🏆 TOP SYMBOLS BY DATA COMPLETENESS (Last 7 days)")
        print(f"{'Symbol':<12} {'Records':<8} {'Price%':<7} {'Vol%':<6} {'Tech%':<6}")
        print("-" * 45)
        
        for row in results:
            symbol = row[0]
            records = row[1]
            price_pct = row[2]
            vol_pct = row[3]
            tech_pct = row[4]
            print(f"{symbol:<12} {records:<8} {price_pct:<7.1f} {vol_pct:<6.1f} {tech_pct:<6.1f}")
        
        # Symbols needing attention
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as records,
                AVG(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) * 100 as price_coverage,
                AVG(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) * 100 as volume_coverage
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY symbol
            HAVING records >= 5 
              AND (price_coverage < 50 OR volume_coverage < 30)
            ORDER BY records DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"\n⚠️ SYMBOLS NEEDING ATTENTION (Low coverage)")
            print(f"{'Symbol':<12} {'Records':<8} {'Price%':<7} {'Vol%':<6}")
            print("-" * 35)
            
            for row in results:
                symbol = row[0]
                records = row[1]
                price_pct = row[2]
                vol_pct = row[3]
                print(f"{symbol:<12} {records:<8} {price_pct:<7.1f} {vol_pct:<6.1f}")
        
        # Recent updates check
        cursor.execute("""
            SELECT 
                COUNT(*) as updated_today,
                COUNT(CASE WHEN updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as updated_hour
            FROM ml_features_materialized
            WHERE updated_at >= CURDATE()
        """)
        
        result = cursor.fetchone()
        
        print(f"\n🔄 UPDATE ACTIVITY")
        print(f"Updated today: {result[0]:,}")
        print(f"Updated last hour: {result[1]:,}")
        
        print(f"\n" + "=" * 70)
        print(f"✅ STATUS CHECK COMPLETED")
        print("=" * 70)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking data status: {e}")
        return False


def main():
    """Main function to check comprehensive data status"""
    logger.info("Starting comprehensive data status check...")
    return check_overall_data_status()


if __name__ == "__main__":
    main()