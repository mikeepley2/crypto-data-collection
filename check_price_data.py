#!/usr/bin/env python3
"""Check price data availability for technical calculator"""
import mysql.connector
from datetime import datetime, timedelta

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 60)
print("PRICE DATA AVAILABILITY CHECK")
print("=" * 60)
print()

# Check price_data_real table
cursor.execute(
    """
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT symbol) as unique_symbols,
        MAX(timestamp) as latest_timestamp,
        MIN(timestamp) as earliest_timestamp,
        MAX(timestamp_iso) as latest_timestamp_iso,
        MIN(timestamp_iso) as earliest_timestamp_iso
    FROM price_data_real
"""
)
result = cursor.fetchone()
print("📊 price_data_real table:")
print(f"   Total records: {result['total_records']:,}")
print(f"   Unique symbols: {result['unique_symbols']}")
print(f"   Latest timestamp (ms): {result['latest_timestamp']}")
print(f"   Earliest timestamp (ms): {result['earliest_timestamp']}")
if result["latest_timestamp_iso"]:
    print(f"   Latest timestamp_iso: {result['latest_timestamp_iso']}")
if result["earliest_timestamp_iso"]:
    print(f"   Earliest timestamp_iso: {result['earliest_timestamp_iso']}")
print()

# Check symbols in last 30 days
cutoff_ms = int((datetime.utcnow().timestamp() - 30 * 86400) * 1000)
cursor.execute(
    f"""
    SELECT COUNT(DISTINCT symbol) as count
    FROM price_data_real
    WHERE timestamp > {cutoff_ms}
"""
)
result = cursor.fetchone()
print(
    f"📈 Symbols with data in last 30 days (timestamp > {cutoff_ms}): {result['count']}"
)
print()

# Check symbols in last 7 days using timestamp_iso
cursor.execute(
    """
    SELECT COUNT(DISTINCT symbol) as count
    FROM price_data_real
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
result = cursor.fetchone()
print(f"📈 Symbols with data in last 7 days (timestamp_iso): {result['count']}")
print()

# Get sample of recent symbols
cursor.execute(
    """
    SELECT DISTINCT symbol
    FROM price_data_real
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    LIMIT 10
"""
)
symbols = cursor.fetchall()
print("📋 Sample symbols with recent data:")
for row in symbols:
    print(f"   {row['symbol']}")
print()

# Check if there are any symbols at all
cursor.execute(
    """
    SELECT DISTINCT symbol
    FROM price_data_real
    LIMIT 10
"""
)
symbols = cursor.fetchall()
print(f"📋 Sample symbols (any time): {len(symbols)} found")
for row in symbols[:5]:
    print(f"   {row['symbol']}")
print()

conn.close()
