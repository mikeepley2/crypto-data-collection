#!/usr/bin/env python3
"""Check collector backfill progress"""
import mysql.connector
from datetime import datetime

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

# Check Macro Collector
cursor.execute(
    """
    SELECT 
        MAX(indicator_date) as last_update,
        COUNT(*) as total,
        COUNT(CASE WHEN indicator_date >= DATE_SUB(CURDATE(), INTERVAL 3 DAY) THEN 1 END) as recent_3d,
        COUNT(CASE WHEN indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN 1 END) as recent_7d
    FROM macro_indicators
"""
)
result = cursor.fetchone()
print("📈 Macro Collector:")
print(f"   Last update: {result['last_update']}")
print(f"   Total records: {result['total']:,}")
print(f"   Last 3 days: {result['recent_3d']:,}")
print(f"   Last 7 days: {result['recent_7d']:,}")

# Get recent dates
cursor.execute(
    """
    SELECT 
        indicator_date,
        COUNT(*) as count
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    GROUP BY indicator_date
    ORDER BY indicator_date DESC
"""
)
print("   Recent dates:")
for row in cursor.fetchall():
    print(f"      {row['indicator_date']}: {row['count']} records")
print()

# Check Technical Calculator
cursor.execute(
    """
    SELECT 
        MAX(timestamp_iso) as last_update,
        COUNT(*) as total,
        COUNT(CASE WHEN timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as recent_1d,
        COUNT(CASE WHEN timestamp_iso >= DATE_SUB(NOW(), INTERVAL 15 DAY) THEN 1 END) as recent_15d
    FROM technical_indicators
"""
)
result = cursor.fetchone()
print("📉 Technical Calculator:")
print(f"   Last update: {result['last_update']}")
print(f"   Total records: {result['total']:,}")
print(f"   Last 24 hours: {result['recent_1d']:,}")
print(f"   Last 15 days: {result['recent_15d']:,}")

# Get recent dates
cursor.execute(
    """
    SELECT 
        DATE(timestamp_iso) as date,
        COUNT(*) as count
    FROM technical_indicators
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 2 DAY)
    GROUP BY DATE(timestamp_iso)
    ORDER BY DATE(timestamp_iso) DESC
    LIMIT 5
"""
)
print("   Recent dates:")
for row in cursor.fetchall():
    print(f"      {row['date']}: {row['count']:,} records")
print()

print("=" * 60)
conn.close()
