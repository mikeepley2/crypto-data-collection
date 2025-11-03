#!/usr/bin/env python3
"""Check backfill progress for technical and macro collectors"""
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
print("COLLECTOR BACKFILL PROGRESS CHECK")
print("=" * 60)
print()

# Check macro indicators
cursor.execute(
    """
    SELECT 
        MAX(indicator_date) as last_update,
        COUNT(*) as total_records,
        COUNT(DISTINCT indicator_date) as unique_dates
    FROM macro_indicators
"""
)
result = cursor.fetchone()
print("📈 Macro Collector:")
print(f"   Last update: {result['last_update']}")
print(f"   Total records: {result['total_records']:,}")
print(f"   Unique dates: {result['unique_dates']}")

# Check last 7 days
cursor.execute(
    """
    SELECT indicator_date, COUNT(*) as cnt
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    GROUP BY indicator_date
    ORDER BY indicator_date DESC
"""
)
print("   Last 7 days:")
for row in cursor.fetchall():
    print(f"      {row['indicator_date']}: {row['cnt']} records")
print()

# Check technical indicators
cursor.execute(
    """
    SELECT 
        MAX(timestamp_iso) as last_update,
        COUNT(*) as total_records,
        COUNT(DISTINCT DATE(timestamp_iso)) as unique_dates
    FROM technical_indicators
"""
)
result = cursor.fetchone()
print("📉 Technical Calculator:")
print(f"   Last update: {result['last_update']}")
print(f"   Total records: {result['total_records']:,}")
print(f"   Unique dates: {result['unique_dates']}")

# Check last 7 days
cursor.execute(
    """
    SELECT DATE(timestamp_iso) as date, COUNT(*) as cnt
    FROM technical_indicators
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(timestamp_iso)
    ORDER BY DATE(timestamp_iso) DESC
"""
)
print("   Last 7 days:")
for row in cursor.fetchall():
    print(f"      {row['date']}: {row['cnt']:,} records")
print()

# Check for gaps
today = datetime.now().date()
gap_start = today - timedelta(days=7)

# Macro gaps
cursor.execute(
    f"""
    SELECT DISTINCT indicator_date
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    ORDER BY indicator_date
"""
)
existing_macro_dates = {row["indicator_date"] for row in cursor.fetchall()}
expected_macro_dates = set()
current = gap_start
while current <= today:
    expected_macro_dates.add(current)
    current += timedelta(days=1)
missing_macro = expected_macro_dates - existing_macro_dates

# Technical gaps
cursor.execute(
    f"""
    SELECT DISTINCT DATE(timestamp_iso) as date
    FROM technical_indicators
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    ORDER BY DATE(timestamp_iso)
"""
)
existing_tech_dates = {row["date"] for row in cursor.fetchall()}
expected_tech_dates = set()
current = gap_start
while current <= today:
    expected_tech_dates.add(current)
    current += timedelta(days=1)
missing_tech = expected_tech_dates - existing_tech_dates

print("=" * 60)
if missing_macro:
    print(f"⚠️  Macro: Missing {len(missing_macro)} dates in last 7 days")
    print(f"   Missing: {sorted(missing_macro)}")
else:
    print("✅ Macro: All dates present in last 7 days")

if missing_tech:
    print(f"⚠️  Technical: Missing {len(missing_tech)} dates in last 7 days")
    print(f"   Missing: {sorted(missing_tech)}")
else:
    print("✅ Technical: All dates present in last 7 days")
print("=" * 60)

conn.close()


