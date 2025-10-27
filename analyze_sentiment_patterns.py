#!/usr/bin/env python3
"""
Analyze sentiment data patterns to determine best strategy for coverage
"""

import mysql.connector
import os
from datetime import datetime, timedelta

conn = mysql.connector.connect(
    host=os.environ["MYSQL_HOST"],
    user=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    database=os.environ["MYSQL_DATABASE"],
)
cursor = conn.cursor()

print("🔍 ANALYZING SENTIMENT DATA PATTERNS")
print("=" * 60)

# Check 1: Sentiment data frequency and patterns
print("📈 Sentiment Data Frequency Analysis:")
cursor.execute(
    """
    SELECT 
        DATE(published_at) as date,
        COUNT(*) as sentiment_count,
        AVG(ml_sentiment_score) as avg_sentiment
    FROM crypto_news
    WHERE ml_sentiment_score IS NOT NULL
    AND published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY DATE(published_at)
    ORDER BY date DESC
    LIMIT 10
"""
)
sentiment_freq = cursor.fetchall()
print("   Recent sentiment data by day:")
for date, count, avg_sent in sentiment_freq:
    print(f"   {date}: {count} articles, avg sentiment: {avg_sent:.3f}")

# Check 2: Price data frequency (for comparison)
print("\n💰 Price Data Frequency Analysis:")
cursor.execute(
    """
    SELECT 
        DATE(timestamp_iso) as date,
        COUNT(*) as price_count
    FROM price_data_real
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(timestamp_iso)
    ORDER BY date DESC
    LIMIT 7
"""
)
price_freq = cursor.fetchall()
print("   Recent price data by day:")
for date, count in price_freq:
    print(f"   {date}: {count} price records")

# Check 3: Sentiment data distribution by hour
print("\n⏰ Sentiment Data by Hour (last 7 days):")
cursor.execute(
    """
    SELECT 
        HOUR(published_at) as hour,
        COUNT(*) as count,
        AVG(ml_sentiment_score) as avg_sentiment
    FROM crypto_news
    WHERE ml_sentiment_score IS NOT NULL
    AND published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY HOUR(published_at)
    ORDER BY hour
"""
)
hourly_sentiment = cursor.fetchall()
print("   Sentiment distribution by hour:")
for hour, count, avg_sent in hourly_sentiment:
    print(f"   {hour:02d}:00 - {count:3d} articles, avg: {avg_sent:.3f}")

# Check 4: Current sentiment coverage in materialized table
print("\n📊 Current Sentiment Coverage Analysis:")
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
total_materialized = cursor.fetchone()[0]

cursor.execute(
    "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
)
sentiment_coverage = cursor.fetchone()[0]

print(f"   Total materialized records: {total_materialized:,}")
print(
    f"   With sentiment data: {sentiment_coverage:,} ({sentiment_coverage/total_materialized*100:.1f}%)"
)
print(
    f"   Without sentiment data: {total_materialized - sentiment_coverage:,} ({(total_materialized - sentiment_coverage)/total_materialized*100:.1f}%)"
)

# Check 5: Sentiment data availability by symbol
print("\n🪙 Sentiment Data by Symbol (top 10):")
cursor.execute(
    """
    SELECT 
        symbol,
        COUNT(*) as total_records,
        COUNT(avg_ml_overall_sentiment) as with_sentiment,
        ROUND(COUNT(avg_ml_overall_sentiment) / COUNT(*) * 100, 1) as coverage_pct
    FROM ml_features_materialized
    GROUP BY symbol
    HAVING COUNT(*) > 1000
    ORDER BY coverage_pct DESC
    LIMIT 10
"""
)
symbol_sentiment = cursor.fetchall()
print("   Top symbols by sentiment coverage:")
for symbol, total, with_sent, coverage in symbol_sentiment:
    print(f"   {symbol}: {with_sent:,}/{total:,} ({coverage}%)")

# Check 6: Sentiment data gaps analysis
print("\n📅 Sentiment Data Gaps Analysis:")
cursor.execute(
    """
    SELECT 
        DATE(timestamp_iso) as date,
        COUNT(*) as total_records,
        COUNT(avg_ml_overall_sentiment) as with_sentiment,
        ROUND(COUNT(avg_ml_overall_sentiment) / COUNT(*) * 100, 1) as coverage_pct
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(timestamp_iso)
    ORDER BY date DESC
"""
)
daily_gaps = cursor.fetchall()
print("   Daily sentiment coverage (last 7 days):")
for date, total, with_sent, coverage in daily_gaps:
    print(f"   {date}: {with_sent:,}/{total:,} ({coverage}%)")

# Check 7: Sentiment data freshness
print("\n🕐 Sentiment Data Freshness:")
cursor.execute(
    """
    SELECT 
        MAX(published_at) as latest_sentiment,
        MIN(published_at) as earliest_sentiment,
        COUNT(*) as total_articles
    FROM crypto_news
    WHERE ml_sentiment_score IS NOT NULL
"""
)
sentiment_freshness = cursor.fetchone()
latest, earliest, total_articles = sentiment_freshness
print(f"   Latest sentiment article: {latest}")
print(f"   Earliest sentiment article: {earliest}")
print(f"   Total articles with sentiment: {total_articles:,}")

# Check 8: Sentiment data correlation with time
print("\n📈 Sentiment Data Time Patterns:")
cursor.execute(
    """
    SELECT 
        CASE 
            WHEN HOUR(published_at) BETWEEN 0 AND 5 THEN 'Night (0-5)'
            WHEN HOUR(published_at) BETWEEN 6 AND 11 THEN 'Morning (6-11)'
            WHEN HOUR(published_at) BETWEEN 12 AND 17 THEN 'Afternoon (12-17)'
            ELSE 'Evening (18-23)'
        END as time_period,
        COUNT(*) as count,
        AVG(ml_sentiment_score) as avg_sentiment,
        STDDEV(ml_sentiment_score) as sentiment_volatility
    FROM crypto_news
    WHERE ml_sentiment_score IS NOT NULL
    AND published_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY time_period
    ORDER BY count DESC
"""
)
time_patterns = cursor.fetchall()
print("   Sentiment patterns by time of day:")
for period, count, avg_sent, volatility in time_patterns:
    print(
        f"   {period}: {count} articles, avg: {avg_sent:.3f}, volatility: {volatility:.3f}"
    )

conn.close()

print("\n" + "=" * 60)
print("🎯 RECOMMENDATIONS FOR SENTIMENT COVERAGE STRATEGY:")
print("=" * 60)
