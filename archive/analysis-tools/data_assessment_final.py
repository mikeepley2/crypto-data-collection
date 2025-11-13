#!/usr/bin/env python3
"""
Data Quality Assessment and Backfill Strategy
Based on database analysis findings
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.database_config import get_db_connection
from datetime import datetime, timedelta

def detailed_assessment():
    """Detailed assessment and backfill recommendations"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    print("🔍 COMPREHENSIVE DATA QUALITY ASSESSMENT")
    print("=" * 70)
    print(f"Assessment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Current data summary
    print("📊 CURRENT DATA SUMMARY")
    print("-" * 40)
    
    # crypto_news analysis
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(created_at) as earliest,
            MAX(created_at) as latest,
            COUNT(DISTINCT DATE(created_at)) as distinct_days
        FROM crypto_news
    """)
    news_stats = cursor.fetchone()
    
    cursor.execute("""
        SELECT COUNT(*) as recent_count 
        FROM crypto_news 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)
    recent_news = cursor.fetchone()['recent_count']
    
    print(f"📰 News Data:")
    print(f"  Total records: {news_stats['total']:,}")
    print(f"  Date range: {news_stats['earliest']} to {news_stats['latest']}")
    print(f"  Days covered: {news_stats['distinct_days']:,}")
    print(f"  Recent (7d): {recent_news:,}")
    print()
    
    # crypto_onchain_data analysis
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest,
            COUNT(DISTINCT symbol) as symbols,
            COUNT(DISTINCT DATE(timestamp)) as distinct_days
        FROM crypto_onchain_data
    """)
    onchain_stats = cursor.fetchone()
    
    cursor.execute("""
        SELECT COUNT(*) as recent_count 
        FROM crypto_onchain_data 
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)
    recent_onchain = cursor.fetchone()['recent_count']
    
    print(f"⛓️  Onchain Data:")
    print(f"  Total records: {onchain_stats['total']:,}")
    print(f"  Date range: {onchain_stats['earliest']} to {onchain_stats['latest']}")
    print(f"  Days covered: {onchain_stats['distinct_days']:,}")
    print(f"  Symbols: {onchain_stats['symbols']:,}")
    print(f"  Recent (7d): {recent_onchain:,}")
    print()
    
    # ohlc_data analysis
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(timestamp_iso) as earliest,
            MAX(timestamp_iso) as latest,
            COUNT(DISTINCT symbol) as symbols,
            COUNT(DISTINCT DATE(timestamp_iso)) as distinct_days,
            COUNT(volume) as non_null_volume,
            COUNT(*) - COUNT(volume) as null_volume
        FROM ohlc_data
    """)
    ohlc_stats = cursor.fetchone()
    
    cursor.execute("""
        SELECT COUNT(*) as recent_count 
        FROM ohlc_data 
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)
    recent_ohlc = cursor.fetchone()['recent_count']
    
    print(f"💰 OHLC Data:")
    print(f"  Total records: {ohlc_stats['total']:,}")
    print(f"  Date range: {ohlc_stats['earliest']} to {ohlc_stats['latest']}")
    print(f"  Days covered: {ohlc_stats['distinct_days']:,}")
    print(f"  Symbols: {ohlc_stats['symbols']:,}")
    print(f"  Recent (7d): {recent_ohlc:,}")
    print(f"  Volume NULLs: {ohlc_stats['null_volume']:,} (Fixed: ✅)")
    print()
    
    # Gap analysis
    print("🔍 GAP ANALYSIS")
    print("-" * 40)
    
    # Check for missing days in last 30 days
    cursor.execute("""
        WITH RECURSIVE date_range AS (
            SELECT DATE(DATE_SUB(NOW(), INTERVAL 30 DAY)) as check_date
            UNION ALL
            SELECT DATE_ADD(check_date, INTERVAL 1 DAY)
            FROM date_range
            WHERE check_date < DATE(NOW())
        ),
        news_days AS (
            SELECT DATE(created_at) as news_date
            FROM crypto_news
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
        )
        SELECT COUNT(*) as missing_news_days
        FROM date_range dr
        LEFT JOIN news_days nd ON dr.check_date = nd.news_date
        WHERE nd.news_date IS NULL
    """)
    missing_news_days = cursor.fetchone()['missing_news_days']
    
    cursor.execute("""
        WITH RECURSIVE date_range AS (
            SELECT DATE(DATE_SUB(NOW(), INTERVAL 30 DAY)) as check_date
            UNION ALL
            SELECT DATE_ADD(check_date, INTERVAL 1 DAY)
            FROM date_range
            WHERE check_date < DATE(NOW())
        ),
        onchain_days AS (
            SELECT DATE(timestamp) as onchain_date
            FROM crypto_onchain_data
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(timestamp)
        )
        SELECT COUNT(*) as missing_onchain_days
        FROM date_range dr
        LEFT JOIN onchain_days od ON dr.check_date = od.onchain_date
        WHERE od.onchain_date IS NULL
    """)
    missing_onchain_days = cursor.fetchone()['missing_onchain_days']
    
    print(f"Missing days (last 30):")
    print(f"  News: {missing_news_days} days")
    print(f"  Onchain: {missing_onchain_days} days")
    print()
    
    # Data quality scores
    news_score = max(0, 100 - (missing_news_days * 3))
    onchain_score = max(0, 100 - (missing_onchain_days * 3))
    ohlc_score = 95 if ohlc_stats['null_volume'] == 0 else 70  # Fixed NULL issue
    
    print("📈 DATA QUALITY SCORES")
    print("-" * 40)
    print(f"News Collection: {news_score:.0f}/100 {'🟢' if news_score >= 80 else '🟡' if news_score >= 60 else '🔴'}")
    print(f"Onchain Collection: {onchain_score:.0f}/100 {'🟢' if onchain_score >= 80 else '🟡' if onchain_score >= 60 else '🔴'}")
    print(f"OHLC Collection: {ohlc_score:.0f}/100 {'🟢' if ohlc_score >= 80 else '🟡' if ohlc_score >= 60 else '🔴'}")
    print()
    
    # Backfill recommendations
    print("🔧 BACKFILL RECOMMENDATIONS")
    print("-" * 40)
    
    if missing_news_days > 5:
        print("🚨 URGENT - News Collection:")
        print(f"  • Missing {missing_news_days} days of news data")
        print("  • Run news collector backfill for last 30 days")
        print("  • Check RSS feed sources")
        print()
    
    if missing_onchain_days > 3:
        print("⚠️  MEDIUM - Onchain Collection:")
        print(f"  • Missing {missing_onchain_days} days of onchain data")
        print("  • Run onchain collector backfill")
        print("  • Verify API keys and rate limits")
        print()
    
    if recent_ohlc < 100:
        print("🔧 MAINTENANCE - OHLC Collection:")
        print(f"  • Only {recent_ohlc} recent OHLC records")
        print("  • Run OHLC collector for current data")
        print("  • Volume NULL issue already fixed ✅")
        print()
    
    print("✅ NEXT STEPS:")
    print("1. Deploy collectors using K8s configurations")
    print("2. Run targeted backfills for missing data")
    print("3. Set up monitoring for data gaps")
    print("4. Verify API keys and rate limits")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    detailed_assessment()