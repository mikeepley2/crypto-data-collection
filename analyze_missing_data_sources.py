#!/usr/bin/env python3
"""Analyze missing data sources and determine what should have been populated"""
import mysql.connector
from datetime import datetime, timedelta

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("MISSING DATA ANALYSIS - What Should Have Been Filled?")
print("=" * 80)
print()

# 1. Technical Indicators - Check source data availability
print("📊 1. TECHNICAL INDICATORS")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(DISTINCT symbol) as symbols,
        COUNT(*) as total_records,
        MIN(timestamp_iso) as earliest,
        MAX(timestamp_iso) as latest
    FROM technical_indicators
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
tech_source = cursor.fetchone()
print(f"   Source (technical_indicators):")
print(f"      Records: {tech_source['total_records']:,}")
print(f"      Symbols: {tech_source['symbols']}")
print(f"      Date range: {tech_source['earliest']} to {tech_source['latest']}")

cursor.execute(
    """
    SELECT 
        COUNT(*) as records_with_data
    FROM ml_features_materialized m
    INNER JOIN technical_indicators t 
        ON BINARY m.symbol = BINARY t.symbol 
        AND DATE(m.timestamp_iso) = DATE(t.timestamp_iso)
        AND DATE(m.timestamp_iso) >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
tech_matched = cursor.fetchone()
print(
    f"   Materialized records that COULD have technical data: {tech_matched['records_with_data']:,}"
)

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND rsi_14 IS NOT NULL
"""
)
tech_populated = cursor.fetchone()
print(f"   Materialized records WITH technical data: {tech_populated['cnt']:,}")
print(
    f"   ⚠️  Gap: {tech_matched['records_with_data'] - tech_populated['cnt']:,} records missing technical indicators"
)
print()

# 2. Macro Indicators - Check source data availability
print("📈 2. MACRO INDICATORS")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        indicator_date,
        COUNT(*) as records
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    GROUP BY indicator_date
    ORDER BY indicator_date DESC
"""
)
macro_dates = cursor.fetchall()
print(f"   Source (macro_indicators) - dates with data:")
for row in macro_dates[:7]:
    print(f"      {row['indicator_date']}: {row['records']} indicators")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND vix IS NOT NULL
"""
)
macro_populated = cursor.fetchone()
print(f"   Materialized records WITH macro data: {macro_populated['cnt']:,}")
print(
    f"   ⚠️  Expected: Should have macro data for dates that exist in macro_indicators"
)
print()

# 3. Sentiment Data - Check source availability
print("💬 3. SENTIMENT INDICATORS")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT DATE(published_at)) as unique_dates
    FROM crypto_news.crypto_sentiment_data
    WHERE published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
sentiment_source = cursor.fetchone()
print(f"   Source (crypto_sentiment_data):")
print(f"      Records: {sentiment_source['total_records']:,}")
print(f"      Unique dates: {sentiment_source['unique_dates']}")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND avg_cryptobert_score IS NOT NULL
"""
)
sentiment_populated = cursor.fetchone()
print(f"   Materialized records WITH sentiment data: {sentiment_populated['cnt']:,}")
print()

# 4. OHLC Data - Check source availability
print("📊 4. OHLC DATA")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT symbol) as symbols
    FROM ohlc_data
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
ohlc_source = cursor.fetchone()
print(f"   Source (ohlc_data):")
print(f"      Records: {ohlc_source['total_records']:,}")
print(f"      Symbols: {ohlc_source['symbols']}")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND open_price IS NOT NULL
"""
)
ohlc_populated = cursor.fetchone()
print(f"   Materialized records WITH OHLC data: {ohlc_populated['cnt']:,}")
print()

# 5. Onchain Data - Check source availability
print("⛓️  5. ONCHAIN DATA")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT symbol) as symbols
    FROM crypto_onchain_data
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
onchain_source = cursor.fetchone()
print(f"   Source (crypto_onchain_data):")
print(f"      Records: {onchain_source['total_records']:,}")
print(f"      Symbols: {onchain_source['symbols']}")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND active_addresses_24h IS NOT NULL
"""
)
onchain_populated = cursor.fetchone()
print(f"   Materialized records WITH onchain data: {onchain_populated['cnt']:,}")
print()

# Summary
print("=" * 80)
print("SUMMARY - Data That SHOULD Be Populated:")
print("=" * 80)
print()

total_materialized = 103864

issues = []

# Technical indicators
if tech_source["total_records"] > 0:
    tech_should_have = min(total_materialized, tech_matched["records_with_data"])
    tech_missing = tech_should_have - tech_populated["cnt"]
    tech_pct = (
        (tech_populated["cnt"] / tech_should_have * 100) if tech_should_have > 0 else 0
    )
    print(
        f"✅ Technical Indicators: {tech_populated['cnt']:,}/{tech_should_have:,} populated ({tech_pct:.1f}%)"
    )
    if tech_missing > 0:
        issues.append(f"Technical indicators: Missing {tech_missing:,} records")
else:
    print("❌ Technical Indicators: No source data available")
    issues.append("Technical indicators: No source data in technical_indicators table")

# Macro indicators
if len(macro_dates) > 0:
    macro_should_have = (
        sum(len([r for r in cursor.fetchall()]) for date in macro_dates)
        if macro_dates
        else 0
    )
    # Count materialized records that match macro dates
    cursor.execute(
        """
        SELECT COUNT(*) as cnt
        FROM ml_features_materialized m
        WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND DATE(m.timestamp_iso) IN (
            SELECT DISTINCT indicator_date 
            FROM macro_indicators 
            WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        )
    """
    )
    macro_should_have = cursor.fetchone()["cnt"]
    macro_missing = macro_should_have - macro_populated["cnt"]
    macro_pct = (
        (macro_populated["cnt"] / macro_should_have * 100)
        if macro_should_have > 0
        else 0
    )
    print(
        f"⚠️  Macro Indicators: {macro_populated['cnt']:,}/{macro_should_have:,} populated ({macro_pct:.1f}%)"
    )
    if macro_missing > 0:
        issues.append(f"Macro indicators: Missing {macro_missing:,} records")
else:
    print("❌ Macro Indicators: No source data for last 7 days")
    issues.append("Macro indicators: Missing Oct 28-30 data (FRED API issue)")

# Sentiment
if sentiment_source["total_records"] > 0:
    sentiment_pct = (
        (sentiment_populated["cnt"] / total_materialized * 100)
        if total_materialized > 0
        else 0
    )
    print(
        f"❌ Sentiment Data: {sentiment_populated['cnt']:,}/{total_materialized:,} populated ({sentiment_pct:.1f}%)"
    )
    if sentiment_populated["cnt"] < total_materialized:
        issues.append(
            f"Sentiment: Missing {total_materialized - sentiment_populated['cnt']:,} records"
        )
else:
    print("❌ Sentiment Data: No source data available")
    issues.append("Sentiment: No source data in crypto_sentiment_data table")

# OHLC
if ohlc_source["total_records"] > 0:
    ohlc_pct = (
        (ohlc_populated["cnt"] / total_materialized * 100)
        if total_materialized > 0
        else 0
    )
    print(
        f"❌ OHLC Data: {ohlc_populated['cnt']:,}/{total_materialized:,} populated ({ohlc_pct:.1f}%)"
    )
    if ohlc_populated["cnt"] < total_materialized:
        issues.append(
            f"OHLC: Missing {total_materialized - ohlc_populated['cnt']:,} records"
        )
else:
    print("❌ OHLC Data: No source data available")
    issues.append("OHLC: No source data in ohlc_data table")

# Onchain
if onchain_source["total_records"] > 0:
    onchain_pct = (
        (onchain_populated["cnt"] / total_materialized * 100)
        if total_materialized > 0
        else 0
    )
    print(
        f"⚠️  Onchain Data: {onchain_populated['cnt']:,}/{total_materialized:,} populated ({onchain_pct:.1f}%)"
    )
    if onchain_populated["cnt"] < total_materialized * 0.8:
        issues.append(f"Onchain: Only {onchain_pct:.1f}% populated")
else:
    print("❌ Onchain Data: No source data available")
    issues.append("Onchain: No source data in crypto_onchain_data table")

print()
print("=" * 80)
print("KEY FINDINGS:")
print("=" * 80)
for issue in issues:
    print(f"   • {issue}")

print()
print("RECOMMENDATION:")
print("   The materialized table updater should be checking and populating")
print("   these fields when source data is available. This suggests:")
print("   1. Updater may not be running or processing all records")
print("   2. Join/matching logic may be incorrect (symbol + date matching)")
print("   3. Updater may be skipping records that should be updated")

conn.close()
