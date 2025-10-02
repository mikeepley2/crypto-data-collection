#!/usr/bin/env python3
"""
Final comprehensive status check of crypto data collection system
"""
import mysql.connector
from datetime import datetime

print("🚀 FINAL COMPREHENSIVE STATUS CHECK")
print("=" * 80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

try:
    # Check crypto_prices database
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    print("\n💰 CRYPTO PRICES DATABASE:")
    print("-" * 40)
    
    # ML features status
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MAX(created_at) as latest,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h,
            SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_sentiment
        FROM ml_features_materialized
    """)
    
    result = cursor.fetchone()
    total, latest, recent_1h, recent_24h, has_sentiment = result
    
    print(f"📊 ML Features Materialized:")
    print(f"   Total records: {total:,}")
    if latest:
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        print(f"   Latest data: {latest} ({age_hours:.1f}h ago)")
        print(f"   Recent activity: {recent_1h} (1h), {recent_24h} (24h)")
        print(f"   Sentiment coverage: {has_sentiment:,} records ({has_sentiment/total*100:.1f}%)")
    else:
        print("   ❌ No data")
    
    # OHLC status
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MAX(created_at) as latest,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
        FROM ohlc_data
    """)
    
    result = cursor.fetchone()
    total, latest, recent_1h = result
    
    print(f"\n📈 OHLC Data:")
    print(f"   Total records: {total:,}")
    if latest:
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        print(f"   Latest data: {latest} ({age_hours:.1f}h ago)")
        print(f"   Recent activity: {recent_1h} (1h)")
    else:
        print("   ❌ No data")
    
    cursor.close()
    conn.close()
    
    # Check crypto_news database
    news_conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_news'
    )
    news_cursor = news_conn.cursor()
    
    print("\n📰 CRYPTO NEWS DATABASE:")
    print("-" * 40)
    
    # News data
    news_cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MAX(created_at) as latest,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
        FROM crypto_news_data
    """)
    
    result = news_cursor.fetchone()
    total, latest, recent_1h, recent_24h = result
    
    print(f"📰 News Data:")
    print(f"   Total records: {total:,}")
    if latest:
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        print(f"   Latest data: {latest} ({age_hours:.1f}h ago)")
        print(f"   Recent activity: {recent_1h} (1h), {recent_24h} (24h)")
    else:
        print("   ❌ No data")
    
    # Social media data
    news_cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MAX(created_at) as latest,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
        FROM social_media_posts
    """)
    
    result = news_cursor.fetchone()
    total, latest, recent_1h, recent_24h = result
    
    print(f"\n🐦 Social Media Data:")
    print(f"   Total records: {total:,}")
    if latest:
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        print(f"   Latest data: {latest} ({age_hours:.1f}h ago)")
        print(f"   Recent activity: {recent_1h} (1h), {recent_24h} (24h)")
    else:
        print("   ❌ No data")
    
    # Sentiment data
    news_cursor.execute("""
        SELECT 
            COUNT(*) as total,
            MAX(created_at) as latest,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
        FROM sentiment_data
    """)
    
    result = news_cursor.fetchone()
    total, latest, recent_1h, recent_24h = result
    
    print(f"\n🧠 Sentiment Data:")
    print(f"   Total records: {total:,}")
    if latest:
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        print(f"   Latest data: {latest} ({age_hours:.1f}h ago)")
        print(f"   Recent activity: {recent_1h} (1h), {recent_24h} (24h)")
    else:
        print("   ❌ No data")
    
    news_cursor.close()
    news_conn.close()
    
    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE STATUS CHECK COMPLETED")
    print("=" * 80)
    
    
except Exception as e:
    print(f"❌ Error during status check: {e}")