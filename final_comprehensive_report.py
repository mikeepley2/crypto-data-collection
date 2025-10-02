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


def final_comprehensive_check():
    """Final comprehensive data quality check"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🎯 FINAL COMPREHENSIVE DATA QUALITY REPORT")
        print("=" * 70)
        
        # Overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                MAX(created_at) as latest_data
            FROM ml_features_materialized
        """)
        
        result = cursor.fetchone()
        total_records = result[0]
        unique_symbols = result[1]
        latest_data = result[2]
        
        print(f"\n📊 OVERALL DATABASE STATUS")
        print(f"Total records: {total_records:,}")
        print(f"Unique symbols: {unique_symbols:,}")
        print(f"Latest data: {latest_data}")
        
        # Recent data coverage (last 24 hours)
        cursor.execute("""
            SELECT 
                COUNT(*) as recent_total,
                COUNT(DISTINCT symbol) as recent_symbols,
                SUM(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) as has_price,
                SUM(CASE WHEN open_price > 0 THEN 1 ELSE 0 END) as has_ohlc,
                SUM(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) as has_volume,
                SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as has_sma,
                SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as has_rsi,
                SUM(CASE WHEN ema_12 IS NOT NULL THEN 1 ELSE 0 END) as has_ema,
                SUM(CASE WHEN macd_line IS NOT NULL THEN 1 ELSE 0 END) as has_macd,
                SUM(CASE WHEN bb_upper IS NOT NULL THEN 1 ELSE 0 END) as has_bb,
                SUM(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) as has_macro,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_sentiment
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        recent_total = result[0]
        
        print(f"\n📈 DATA COVERAGE (Last 24 hours)")
        print(f"Recent records: {recent_total:,}")
        print(f"Recent symbols: {result[1]:,}")
        
        if recent_total > 0:
            coverage_data = [
                ("Price data", result[2], result[2]/recent_total*100),
                ("OHLC data", result[3], result[3]/recent_total*100),
                ("Volume data", result[4], result[4]/recent_total*100),
                ("SMA indicators", result[5], result[5]/recent_total*100),
                ("RSI indicators", result[6], result[6]/recent_total*100),
                ("EMA indicators", result[7], result[7]/recent_total*100),
                ("MACD indicators", result[8], result[8]/recent_total*100),
                ("Bollinger Bands", result[9], result[9]/recent_total*100),
                ("Macro indicators", result[10], result[10]/recent_total*100),
                ("Sentiment data", result[11], result[11]/recent_total*100),
            ]
            
            for name, count, percentage in coverage_data:
                status = "✅" if percentage > 90 else "⚠️" if percentage > 50 else "❌"
                print(f"{status} {name}: {count:,} ({percentage:.1f}%)")
        
        # Weekly trend analysis
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as daily_records,
                COUNT(DISTINCT symbol) as daily_symbols,
                AVG(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) * 100 as avg_price_coverage,
                AVG(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) * 100 as avg_volume_coverage
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        
        results = cursor.fetchall()
        
        print(f"\n📅 DAILY TREND ANALYSIS (Last 7 days)")
        print(f"{'Date':<12} {'Records':<8} {'Symbols':<8} {'Price%':<7} {'Vol%':<6}")
        print("-" * 45)
        
        for row in results:
            date = row[0]
            records = row[1]
            symbols = row[2]
            price_pct = row[3]
            vol_pct = row[4]
            print(f"{date} {records:<8} {symbols:<8} {price_pct:<7.1f} {vol_pct:<6.1f}")
        
        # Symbol performance ranking
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as records,
                AVG(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) * 100 as price_coverage,
                AVG(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) * 100 as volume_coverage,
                AVG(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) * 100 as technical_coverage,
                (AVG(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) +
                 AVG(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) +
                 AVG(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END)) * 100 / 3 as overall_score
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY symbol
            HAVING records >= 10
            ORDER BY overall_score DESC, records DESC
            LIMIT 15
        """)
        
        results = cursor.fetchall()
        
        print(f"\n🏆 TOP PERFORMING SYMBOLS (Data Quality)")
        print(f"{'Symbol':<10} {'Records':<8} {'Price':<6} {'Vol':<6} {'Tech':<6} {'Score':<6}")
        print("-" * 50)
        
        for row in results:
            symbol = row[0]
            records = row[1]
            price_pct = row[2]
            vol_pct = row[3]
            tech_pct = row[4]
            score = row[5]
            print(f"{symbol:<10} {records:<8} {price_pct:<6.1f} {vol_pct:<6.1f} {tech_pct:<6.1f} {score:<6.1f}")
        
        # Data freshness check
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 'Last Hour'
                    WHEN created_at >= DATE_SUB(NOW(), INTERVAL 6 HOUR) THEN 'Last 6 Hours'
                    WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 'Last 24 Hours'
                    WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Last Week'
                    ELSE 'Older'
                END as age_group,
                COUNT(*) as records,
                COUNT(DISTINCT symbol) as symbols
            FROM ml_features_materialized
            GROUP BY age_group
            ORDER BY 
                CASE age_group
                    WHEN 'Last Hour' THEN 1
                    WHEN 'Last 6 Hours' THEN 2
                    WHEN 'Last 24 Hours' THEN 3
                    WHEN 'Last Week' THEN 4
                    ELSE 5
                END
        """)
        
        results = cursor.fetchall()
        
        print(f"\n⏰ DATA FRESHNESS DISTRIBUTION")
        print(f"{'Age Group':<15} {'Records':<10} {'Symbols':<8}")
        print("-" * 35)
        
        for row in results:
            age_group = row[0]
            records = row[1]
            symbols = row[2]
            print(f"{age_group:<15} {records:<10,} {symbols:<8}")
        
        # Quality score calculation
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN current_price > 0 THEN 1 ELSE 0 END) * 100 as price_score,
                AVG(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) * 100 as volume_score,
                AVG(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) * 100 as technical_score,
                AVG(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) * 100 as macro_score,
                AVG(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) * 100 as sentiment_score
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        
        price_score = result[0]
        volume_score = result[1]
        technical_score = result[2]
        macro_score = result[3]
        sentiment_score = result[4]
        
        overall_quality = (price_score + volume_score + technical_score + macro_score + sentiment_score) / 5
        
        print(f"\n🎯 OVERALL DATA QUALITY SCORE")
        print(f"Price Data: {price_score:.1f}%")
        print(f"Volume Data: {volume_score:.1f}%")
        print(f"Technical Indicators: {technical_score:.1f}%")
        print(f"Macro Indicators: {macro_score:.1f}%")
        print(f"Sentiment Data: {sentiment_score:.1f}%")
        print(f"OVERALL SCORE: {overall_quality:.1f}%")
        
        # Quality grade
        if overall_quality >= 90:
            grade = "A+ (Excellent)"
        elif overall_quality >= 80:
            grade = "A (Very Good)"
        elif overall_quality >= 70:
            grade = "B (Good)"
        elif overall_quality >= 60:
            grade = "C (Fair)"
        else:
            grade = "D (Needs Improvement)"
        
        print(f"QUALITY GRADE: {grade}")
        
        print(f"\n" + "=" * 70)
        print(f"✅ COMPREHENSIVE DATA QUALITY CHECK COMPLETED")
        print("=" * 70)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error in final check: {e}")
        return False


def main():
    """Main function"""
    logger.info("Starting final comprehensive check...")
    return final_comprehensive_check()


if __name__ == "__main__":
    main()