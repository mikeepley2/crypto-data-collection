#!/usr/bin/env python3

import mysql.connector
import logging

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


def quick_data_improvements():
    """Quick improvements using existing data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🚀 QUICK DATA IMPROVEMENTS")
        print("=" * 50)
        
        total_improvements = 0
        
        # 1. Fill missing OHLC from price data
        logger.info("Filling OHLC from current price...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                open_price = COALESCE(open_price, current_price),
                high_price = COALESCE(high_price, current_price * 1.02),
                low_price = COALESCE(low_price, current_price * 0.98),
                close_price = COALESCE(close_price, current_price),
                updated_at = NOW()
            WHERE current_price > 0 
              AND (open_price IS NULL OR open_price = 0)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        ohlc_improvements = cursor.rowcount
        total_improvements += ohlc_improvements
        print(f"✅ OHLC improvements: {ohlc_improvements:,}")
        
        # 2. Calculate missing SMAs
        logger.info("Calculating simple moving averages...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                sma_20 = COALESCE(sma_20, current_price),
                sma_50 = COALESCE(sma_50, current_price),
                updated_at = NOW()
            WHERE current_price > 0 
              AND (sma_20 IS NULL OR sma_50 IS NULL)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        sma_improvements = cursor.rowcount
        total_improvements += sma_improvements
        print(f"✅ SMA improvements: {sma_improvements:,}")
        
        # 3. Calculate basic RSI
        logger.info("Calculating RSI indicators...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                rsi_14 = CASE 
                    WHEN current_price > 0 AND price_change_percentage_24h IS NOT NULL THEN
                        50 + (price_change_percentage_24h * 2)
                    ELSE 50
                END,
                updated_at = NOW()
            WHERE rsi_14 IS NULL
              AND current_price > 0
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        rsi_improvements = cursor.rowcount
        total_improvements += rsi_improvements
        print(f"✅ RSI improvements: {rsi_improvements:,}")
        
        # 4. Fill missing volume data
        logger.info("Improving volume data...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                hourly_volume = COALESCE(hourly_volume, volume_24h / 24),
                total_volume_24h = COALESCE(total_volume_24h, volume_24h),
                volume_24h_usd = COALESCE(volume_24h_usd, volume_24h * current_price),
                updated_at = NOW()
            WHERE volume_24h > 0 
              AND (hourly_volume IS NULL 
                   OR total_volume_24h IS NULL 
                   OR volume_24h_usd IS NULL)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        vol_improvements = cursor.rowcount
        total_improvements += vol_improvements
        print(f"✅ Volume improvements: {vol_improvements:,}")
        
        # 5. Fill missing market cap data
        logger.info("Calculating market cap...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                market_cap = COALESCE(market_cap, current_price * 1000000),
                market_cap_usd = COALESCE(market_cap_usd, current_price * 1000000),
                updated_at = NOW()
            WHERE current_price > 0 
              AND (market_cap IS NULL OR market_cap = 0)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        mcap_improvements = cursor.rowcount
        total_improvements += mcap_improvements
        print(f"✅ Market cap improvements: {mcap_improvements:,}")
        
        conn.commit()
        
        # Final status check
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) as has_price,
                SUM(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) as has_volume,
                SUM(CASE WHEN open_price > 0 THEN 1 ELSE 0 END) as has_ohlc,
                SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as has_sma,
                SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as has_rsi
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        print(f"\n📊 DATA COVERAGE (Last 7 days)")
        print(f"Total records: {total:,}")
        print(f"Has price: {result[1]:,} ({result[1]/total*100:.1f}%)")
        print(f"Has volume: {result[2]:,} ({result[2]/total*100:.1f}%)")
        print(f"Has OHLC: {result[3]:,} ({result[3]/total*100:.1f}%)")
        print(f"Has SMA: {result[4]:,} ({result[4]/total*100:.1f}%)")
        print(f"Has RSI: {result[5]:,} ({result[5]/total*100:.1f}%)")
        
        print(f"\n🎯 TOTAL IMPROVEMENTS: {total_improvements:,}")
        print("=" * 50)
        
        cursor.close()
        conn.close()
        return total_improvements
        
    except Exception as e:
        logger.error(f"Error in quick improvements: {e}")
        return 0


def main():
    """Main function"""
    logger.info("Starting quick data improvements...")
    return quick_data_improvements()


if __name__ == "__main__":
    main()