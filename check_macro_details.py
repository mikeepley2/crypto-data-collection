#!/usr/bin/env python3
"""Check macro indicators in detail"""
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
print("MACRO INDICATORS DETAILED CHECK")
print("=" * 60)
print()

# Check by indicator name for recent dates
cursor.execute(
    """
    SELECT 
        indicator_name,
        MAX(indicator_date) as last_date,
        COUNT(*) as total,
        COUNT(CASE WHEN indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN 1 END) as recent_7d
    FROM macro_indicators
    GROUP BY indicator_name
    ORDER BY indicator_name
"""
)

print("📊 Indicators by name:")
for row in cursor.fetchall():
    print(
        f"   {row['indicator_name']:25} | Last: {row['last_date']} | Total: {row['total']:5,} | Recent: {row['recent_7d']:3}"
    )

print()

# Check dates in last 7 days
cursor.execute(
    """
    SELECT 
        indicator_date,
        COUNT(DISTINCT indicator_name) as indicator_count,
        COUNT(*) as total_records
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    GROUP BY indicator_date
    ORDER BY indicator_date DESC
"""
)

print("📅 Recent dates (last 7 days):")
for row in cursor.fetchall():
    print(
        f"   {row['indicator_date']}: {row['indicator_count']} indicators, {row['total_records']} total records"
    )

print()

# Check what was updated today
today = datetime.now().date()
cursor.execute(
    """
    SELECT 
        indicator_name,
        indicator_date,
        value,
        updated_at
    FROM macro_indicators
    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 3 DAY)
    ORDER BY indicator_date DESC, indicator_name
"""
)

print(f"📈 Latest updates (last 3 days):")
results = cursor.fetchall()
if results:
    for row in results:
        print(
            f"   {row['indicator_date']} | {row['indicator_name']:25} | Value: {row['value']}"
        )
else:
    print("   No recent updates")

print()
print("=" * 60)
conn.close()
