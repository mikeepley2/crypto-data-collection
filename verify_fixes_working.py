#!/usr/bin/env python3
"""Verify the fixes are actually working by checking if data is being populated"""
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
print("VERIFYING FIXES ARE WORKING")
print("=" * 80)
print()

# Check recent records that were updated today
cursor.execute(
    """
    SELECT 
        symbol,
        DATE(timestamp_iso) as date,
        COUNT(*) as records,
        COUNT(rsi_14) as has_rsi,
        COUNT(sma_20) as has_sma,
        COUNT(vix) as has_vix,
        COUNT(open_price) as has_ohlc,
        COUNT(active_addresses_24h) as has_onchain,
        MAX(updated_at) as last_update
    FROM ml_features_materialized
    WHERE DATE(timestamp_iso) = CURDATE()
    AND updated_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
    GROUP BY symbol, DATE(timestamp_iso)
    ORDER BY last_update DESC
    LIMIT 10
"""
)

recent_updates = cursor.fetchall()

print("📊 Recently Updated Records (Today, updated in last 2 hours):")
print("-" * 80)
if recent_updates:
    for r in recent_updates:
        rsi_pct = (r["has_rsi"] / r["records"] * 100) if r["records"] > 0 else 0
        sma_pct = (r["has_sma"] / r["records"] * 100) if r["records"] > 0 else 0
        vix_pct = (r["has_vix"] / r["records"] * 100) if r["records"] > 0 else 0
        ohlc_pct = (r["has_ohlc"] / r["records"] * 100) if r["records"] > 0 else 0
        onchain_pct = (r["has_onchain"] / r["records"] * 100) if r["records"] > 0 else 0

        print(f"{r['symbol']} on {r['date']}:")
        print(f"  Records: {r['records']}, Last update: {r['last_update']}")
        print(
            f"  Technical: RSI={rsi_pct:.1f}% ({r['has_rsi']}/{r['records']}), SMA={sma_pct:.1f}% ({r['has_sma']}/{r['records']})"
        )
        print(f"  Macro: VIX={vix_pct:.1f}% ({r['has_vix']}/{r['records']})")
        print(f"  OHLC: {ohlc_pct:.1f}% ({r['has_ohlc']}/{r['records']})")
        print(f"  Onchain: {onchain_pct:.1f}% ({r['has_onchain']}/{r['records']})")
        print()
else:
    print("  No recently updated records found")
    print()

# Check if source data exists for today
print("📦 Source Data Availability for Today:")
print("-" * 80)

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM technical_indicators
    WHERE DATE(timestamp_iso) = CURDATE()
"""
)
tech_today = cursor.fetchone()["cnt"]
print(f"  Technical indicators: {tech_today:,} records for today")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM macro_indicators
    WHERE indicator_date = CURDATE()
"""
)
macro_today = cursor.fetchone()["cnt"]
print(f"  Macro indicators: {macro_today:,} records for today")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ohlc_data
    WHERE DATE(timestamp_iso) = CURDATE()
"""
)
ohlc_today = cursor.fetchone()["cnt"]
print(f"  OHLC data: {ohlc_today:,} records for today")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM crypto_onchain_data
    WHERE DATE(timestamp) = CURDATE()
"""
)
onchain_today = cursor.fetchone()["cnt"]
print(f"  Onchain data: {onchain_today:,} records for today")
print()

# Check a specific example - see if technical indicators match
print("🔍 Detailed Check - Sample Symbol:")
print("-" * 80)

cursor.execute(
    """
    SELECT symbol
    FROM ml_features_materialized
    WHERE DATE(timestamp_iso) = CURDATE()
    AND updated_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
    LIMIT 1
"""
)
sample = cursor.fetchone()

if sample:
    symbol = sample["symbol"]
    print(f"Checking {symbol}...")

    # Check technical indicators available
    cursor.execute(
        """
        SELECT 
            DATE(timestamp_iso) as date,
            COUNT(*) as records,
            MAX(rsi_14) as sample_rsi,
            MAX(sma_20) as sample_sma
        FROM technical_indicators
        WHERE symbol = %s
        AND DATE(timestamp_iso) = CURDATE()
        GROUP BY DATE(timestamp_iso)
    """,
        (symbol,),
    )
    tech_avail = cursor.fetchone()

    if tech_avail:
        print(f"  ✅ Technical indicators available: {tech_avail['records']} records")
        print(
            f"     Sample: RSI={tech_avail['sample_rsi']}, SMA20={tech_avail['sample_sma']}"
        )
    else:
        print(f"  ❌ No technical indicators available for {symbol} today")

    # Check if materialized table has them
    cursor.execute(
        """
        SELECT 
            COUNT(*) as total,
            COUNT(rsi_14) as has_rsi,
            COUNT(sma_20) as has_sma,
            MAX(rsi_14) as sample_rsi,
            MAX(sma_20) as sample_sma
        FROM ml_features_materialized
        WHERE symbol = %s
        AND DATE(timestamp_iso) = CURDATE()
    """,
        (symbol,),
    )
    mat_has = cursor.fetchone()

    print(f"  Materialized table: {mat_has['total']} records")
    print(
        f"    Has RSI: {mat_has['has_rsi']} ({mat_has['has_rsi']/mat_has['total']*100 if mat_has['total'] > 0 else 0:.1f}%)"
    )
    print(
        f"    Has SMA: {mat_has['has_sma']} ({mat_has['has_sma']/mat_has['total']*100 if mat_has['total'] > 0 else 0:.1f}%)"
    )
    if mat_has["has_rsi"] > 0:
        print(f"    Sample RSI: {mat_has['sample_rsi']}")
    if mat_has["has_sma"] > 0:
        print(f"    Sample SMA: {mat_has['sample_sma']}")

# Check macro indicators
cursor.execute(
    """
    SELECT 
        indicator_date,
        COUNT(*) as indicators,
        MAX(CASE WHEN indicator_name = 'VIX' THEN value END) as vix,
        MAX(CASE WHEN indicator_name = 'SPX' THEN value END) as spx
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 3 DAY)
    GROUP BY indicator_date
    ORDER BY indicator_date DESC
"""
)
macro_dates = cursor.fetchall()

print()
print("📈 Macro Indicators Available:")
for m in macro_dates:
    print(
        f"  {m['indicator_date']}: {m['indicators']} indicators, VIX={m['vix']}, SPX={m['spx']}"
    )

conn.close()

print()
print("=" * 80)
print("If source data exists but materialized table doesn't have it,")
print("the updater may not be populating fields correctly.")
print("=" * 80)

