#!/usr/bin/env python3
"""Verify materialized updater is working correctly"""
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
print("MATERIALIZED UPDATER VERIFICATION")
print("=" * 80)
print()

# Check recent updates
cursor.execute(
    """
    SELECT 
        MAX(updated_at) as last_update,
        COUNT(*) as total_records,
        COUNT(CASE WHEN updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as updated_last_hour
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
stats = cursor.fetchone()
print(f"📊 Materialized Table Stats (last 7 days):")
print(f"   Total records: {stats['total_records']:,}")
print(f"   Last update: {stats['last_update']}")
print(f"   Updated in last hour: {stats['updated_last_hour']:,}")
print()

# Check if new records are being added
cursor.execute(
    """
    SELECT 
        DATE(timestamp_iso) as date,
        COUNT(*) as records,
        COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as new_last_hour
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 2 DAY)
    GROUP BY DATE(timestamp_iso)
    ORDER BY date DESC
    LIMIT 3
"""
)
recent = cursor.fetchall()
print(f"📅 Recent activity:")
for r in recent:
    print(
        f"   {r['date']}: {r['records']:,} records ({r['new_last_hour']:,} new in last hour)"
    )
print()

# Check completeness of key columns
print("🔍 Column Completeness Check:")
checks = [
    ("rsi_14", "Technical"),
    ("vix", "Macro"),
    ("open_price", "OHLC"),
    ("active_addresses_24h", "Onchain"),
]

for col, cat in checks:
    cursor.execute(
        f"""
        SELECT 
            COUNT({col}) as filled,
            COUNT(*) as total,
            ROUND(COUNT({col}) * 100.0 / COUNT(*), 1) as pct
        FROM ml_features_materialized
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    """
    )
    r = cursor.fetchone()
    status = "✅" if r["pct"] >= 50 else "⚠️" if r["pct"] > 0 else "❌"
    print(
        f"   {status} {cat:12} {col:25} {r['filled']:>6,}/{r['total']:>6,} ({r['pct']:>5.1f}%)"
    )
print()

# Check if source data exists
print("📦 Source Data Availability:")
cursor.execute(
    """
    SELECT COUNT(*) as cnt,
           MAX(timestamp_iso) as latest
    FROM technical_indicators
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
"""
)
tech = cursor.fetchone()
print(f"   Technical indicators: {tech['cnt']:,} records (latest: {tech['latest']})")

cursor.execute(
    """
    SELECT COUNT(*) as cnt,
           MAX(indicator_date) as latest
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 1 DAY)
"""
)
macro = cursor.fetchone()
print(f"   Macro indicators: {macro['cnt']:,} records (latest: {macro['latest']})")

cursor.execute(
    """
    SELECT COUNT(*) as cnt,
           MAX(timestamp_iso) as latest
    FROM ohlc_data
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
"""
)
ohlc = cursor.fetchone()
print(f"   OHLC data: {ohlc['cnt']:,} records (latest: {ohlc['latest']})")

cursor.execute(
    """
    SELECT COUNT(*) as cnt,
           MAX(timestamp) as latest
    FROM crypto_onchain_data
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
"""
)
onchain = cursor.fetchone()
print(f"   Onchain data: {onchain['cnt']:,} records (latest: {onchain['latest']})")
print()

print("=" * 80)
print("✅ Verification complete - Check if updater is populating new records")
print("   The updater should process new price data and populate all fields")
print("=" * 80)

conn.close()

