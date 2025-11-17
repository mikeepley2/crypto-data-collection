#!/usr/bin/env python3
"""Diagnose materialized table issues systematically"""
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
print("MATERIALIZED TABLE ISSUES DIAGNOSTIC")
print("=" * 80)
print()

# 1. OHLC DATA
print("1️⃣  OHLC DATA ISSUE")
print("-" * 80)

# Check if ohlc_data table exists and has data
cursor.execute(
    """
    SELECT COUNT(*) as cnt 
    FROM information_schema.tables 
    WHERE table_schema = 'crypto_prices' 
    AND table_name = 'ohlc_data'
"""
)
table_exists = cursor.fetchone()["cnt"] > 0
print(f"   ohlc_data table exists: {table_exists}")

if table_exists:
    cursor.execute(
        """
        SELECT COUNT(*) as cnt, 
               COUNT(DISTINCT symbol) as symbols,
               MIN(DATE(timestamp)) as earliest,
               MAX(DATE(timestamp)) as latest
        FROM ohlc_data
        WHERE DATE(timestamp) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    """
    )
    ohlc_stats = cursor.fetchone()
    print(f"   Records in last 7 days: {ohlc_stats['cnt']:,}")
    print(f"   Symbols: {ohlc_stats['symbols']}")
    print(f"   Date range: {ohlc_stats['earliest']} to {ohlc_stats['latest']}")

    # Check schema
    cursor.execute(
        """
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM information_schema.columns 
        WHERE table_schema = 'crypto_prices' 
        AND table_name = 'ohlc_data'
        AND column_name IN ('symbol', 'timestamp', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'data_source')
    """
    )
    columns = cursor.fetchall()
    print(f"   Columns: {[c['COLUMN_NAME'] for c in columns]}")

    # Sample data
    if ohlc_stats["cnt"] > 0:
        cursor.execute(
            """
            SELECT symbol, DATE(timestamp) as date, open_price, high_price, low_price, close_price
            FROM ohlc_data
            WHERE DATE(timestamp) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            LIMIT 3
        """
        )
        samples = cursor.fetchall()
        print("   Sample records:")
        for s in samples:
            print(
                f"      {s['symbol']} on {s['date']}: O={s['open_price']}, H={s['high_price']}, L={s['low_price']}, C={s['close_price']}"
            )
    else:
        print("   ⚠️  No OHLC data in last 7 days")
else:
    print("   ❌ ohlc_data table does not exist")

# Check how many materialized records should have OHLC
cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized m
    INNER JOIN ohlc_data o
        ON BINARY m.symbol = BINARY o.symbol
        AND DATE(m.timestamp_iso) = DATE(o.timestamp)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND o.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
could_have_ohlc = cursor.fetchone()["cnt"]

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND open_price IS NOT NULL
"""
)
has_ohlc = cursor.fetchone()["cnt"]

print(f"   Materialized records that COULD have OHLC: {could_have_ohlc:,}")
print(f"   Materialized records WITH OHLC: {has_ohlc:,}")
if could_have_ohlc > 0:
    print(
        f"   Gap: {could_have_ohlc - has_ohlc:,} records missing OHLC ({((could_have_ohlc - has_ohlc)/could_have_ohlc*100):.1f}%)"
    )
print()

# 2. TECHNICAL INDICATORS
print("2️⃣  TECHNICAL INDICATORS ISSUE")
print("-" * 80)

# Check technical indicators data
cursor.execute(
    """
    SELECT 
        DATE(timestamp_iso) as date,
        HOUR(timestamp_iso) as hour,
        COUNT(*) as cnt
    FROM technical_indicators
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(timestamp_iso), HOUR(timestamp_iso)
    ORDER BY date DESC, hour DESC
    LIMIT 5
"""
)
tech_by_hour = cursor.fetchall()
print("   Technical indicators distribution by date/hour:")
for t in tech_by_hour:
    print(f"      {t['date']} {t['hour']:02d}:00 - {t['cnt']:,} records")

# Check how materialized updater looks up technical indicators
# It uses (date, hour) lookup: tech_lookup.get((timestamp_iso.date(), timestamp_iso.hour))
cursor.execute(
    """
    SELECT 
        DATE(m.timestamp_iso) as date,
        HOUR(m.timestamp_iso) as hour,
        COUNT(*) as materialized_count,
        COUNT(t.symbol) as tech_matched_count
    FROM ml_features_materialized m
    LEFT JOIN technical_indicators t
        ON BINARY m.symbol = BINARY t.symbol
        AND DATE(m.timestamp_iso) = DATE(t.timestamp_iso)
        AND HOUR(m.timestamp_iso) = HOUR(t.timestamp_iso)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(m.timestamp_iso), HOUR(m.timestamp_iso)
    ORDER BY date DESC, hour DESC
    LIMIT 5
"""
)
hourly_match = cursor.fetchall()
print("   Materialized records vs technical indicators match by (date, hour):")
for h in hourly_match:
    pct = (
        (h["tech_matched_count"] / h["materialized_count"] * 100)
        if h["materialized_count"] > 0
        else 0
    )
    print(
        f"      {h['date']} {h['hour']:02d}:00 - {h['materialized_count']:,} materialized, {h['tech_matched_count']:,} matched ({pct:.1f}%)"
    )

# Try matching by just date (not hour)
cursor.execute(
    """
    SELECT 
        DATE(m.timestamp_iso) as date,
        COUNT(*) as materialized_count,
        COUNT(t.symbol) as tech_matched_by_date
    FROM ml_features_materialized m
    LEFT JOIN technical_indicators t
        ON BINARY m.symbol = BINARY t.symbol
        AND DATE(m.timestamp_iso) = DATE(t.timestamp_iso)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(m.timestamp_iso)
    ORDER BY date DESC
    LIMIT 5
"""
)
date_match = cursor.fetchall()
print("   If matched by date only (not hour):")
for d in date_match:
    pct = (
        (d["tech_matched_by_date"] / d["materialized_count"] * 100)
        if d["materialized_count"] > 0
        else 0
    )
    print(
        f"      {d['date']} - {d['materialized_count']:,} materialized, {d['tech_matched_by_date']:,} matched ({pct:.1f}%)"
    )
print()

# 3. MACRO INDICATORS
print("3️⃣  MACRO INDICATORS ISSUE")
print("-" * 80)

# Check what macro_indicators has
cursor.execute(
    """
    SELECT indicator_name, indicator_date, value
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    ORDER BY indicator_date DESC, indicator_name
    LIMIT 10
"""
)
macro_samples = cursor.fetchall()
print("   Sample macro_indicators data:")
for m in macro_samples:
    print(f"      {m['indicator_date']} - {m['indicator_name']}: {m['value']}")

# Check materialized updater's macro lookup - it queries crypto_news.macro_economic_data, not macro_indicators!
cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM information_schema.tables 
    WHERE table_schema = 'crypto_news' 
    AND table_name = 'macro_economic_data'
"""
)
wrong_table_exists = cursor.fetchone()["cnt"] > 0
print(f"   crypto_news.macro_economic_data table exists: {wrong_table_exists}")
print(
    "   ⚠️  Issue: Materialized updater queries wrong table (crypto_news.macro_economic_data)"
)
print("   Should query: crypto_prices.macro_indicators")
print()

# 4. SENTIMENT
print("4️⃣  SENTIMENT DATA ISSUE")
print("-" * 80)

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM information_schema.tables 
    WHERE table_schema = 'crypto_news' 
    AND table_name = 'crypto_sentiment_data'
"""
)
sent_table_exists = cursor.fetchone()["cnt"] > 0
print(f"   crypto_news.crypto_sentiment_data table exists: {sent_table_exists}")

if sent_table_exists:
    cursor.execute(
        """
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT DATE(published_at)) as dates,
            MIN(DATE(published_at)) as earliest,
            MAX(DATE(published_at)) as latest
        FROM crypto_news.crypto_sentiment_data
        WHERE published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """
    )
    sent_stats = cursor.fetchone()
    print(f"   Records in last 7 days: {sent_stats['total']:,}")
    print(f"   Unique dates: {sent_stats['dates']}")
    print(f"   Date range: {sent_stats['earliest']} to {sent_stats['latest']}")
else:
    print("   ❌ crypto_sentiment_data table does not exist")
print()

# 5. ONCHAIN
print("5️⃣  ONCHAIN DATA ISSUE")
print("-" * 80)

cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT symbol) as symbols,
        MIN(DATE(timestamp)) as earliest,
        MAX(DATE(timestamp)) as latest
    FROM crypto_onchain_data
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
onchain_stats = cursor.fetchone()
print(f"   Records in last 7 days: {onchain_stats['total']:,}")
print(f"   Symbols: {onchain_stats['symbols']}")
print(f"   Date range: {onchain_stats['earliest']} to {onchain_stats['latest']}")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized m
    INNER JOIN crypto_onchain_data o
        ON BINARY m.symbol = BINARY o.symbol
        AND DATE(m.timestamp_iso) = DATE(o.timestamp)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND o.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
could_have_onchain = cursor.fetchone()["cnt"]

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND active_addresses_24h IS NOT NULL
"""
)
has_onchain = cursor.fetchone()["cnt"]

print(f"   Materialized records that COULD have onchain: {could_have_onchain:,}")
print(f"   Materialized records WITH onchain: {has_onchain:,}")
if could_have_onchain > 0:
    print(
        f"   Gap: {could_have_onchain - has_onchain:,} records ({((could_have_onchain - has_onchain)/could_have_onchain*100):.1f}%)"
    )
print()

print("=" * 80)
print("SUMMARY OF ISSUES:")
print("=" * 80)
print("1. OHLC: Check if ohlc_data has data")
print(
    "2. Technical: Lookup uses (date, hour) but may need (symbol, date) with latest timestamp"
)
print(
    "3. Macro: Updater queries wrong table (crypto_news.macro_economic_data vs macro_indicators)"
)
print("4. Sentiment: Check if crypto_sentiment_data exists and has data")
print("5. Onchain: Partial population - may be join logic issue")
print("=" * 80)

conn.close()


