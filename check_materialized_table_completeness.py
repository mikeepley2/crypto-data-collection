#!/usr/bin/env python3
"""
Check Materialized Table Completeness
Verify all columns are populated and provide detailed statistics
"""

import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.environ["MYSQL_HOST"],
    user=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    database=os.environ["MYSQL_DATABASE"],
)
cursor = conn.cursor()

print("🔍 CHECKING MATERIALIZED TABLE COMPLETENESS")
print("=" * 60)

# Get table schema
cursor.execute("DESCRIBE ml_features_materialized")
columns = cursor.fetchall()

print("📋 TABLE SCHEMA:")
total_columns = len(columns)
for i, (col_name, col_type, null, key, default, extra) in enumerate(columns, 1):
    print(
        f"   {i:2d}. {col_name:<30} {col_type:<20} {'NULL' if null == 'YES' else 'NOT NULL'}"
    )

print(f"\n📊 TOTAL COLUMNS: {total_columns}")

# Get total records
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
total_records = cursor.fetchone()[0]

print(f"\n📈 TOTAL RECORDS: {total_records:,}")

# Check each column for NULL values
print(f"\n🔍 COLUMN POPULATION ANALYSIS:")
print("-" * 60)

populated_columns = 0
null_columns = 0

for col_name, col_type, null, key, default, extra in columns:
    # Skip auto-generated columns
    if col_name in ["id", "created_at", "updated_at"]:
        continue

    cursor.execute(
        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col_name} IS NOT NULL"
    )
    non_null_count = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col_name} IS NULL"
    )
    null_count = cursor.fetchone()[0]

    population_pct = (non_null_count / total_records) * 100 if total_records > 0 else 0

    if population_pct > 0:
        populated_columns += 1
        status = "✅"
    else:
        null_columns += 1
        status = "❌"

    print(
        f"   {status} {col_name:<30} {non_null_count:>8,}/{total_records:>8,} ({population_pct:>5.1f}%)"
    )

# Summary
print(f"\n📊 SUMMARY:")
print(f"   Total columns: {total_columns}")
print(f"   Populated columns: {populated_columns}")
print(f"   Empty columns: {null_columns}")
print(
    f"   Population rate: {populated_columns}/{total_columns} ({populated_columns/total_columns*100:.1f}%)"
)

# Check specific data types
print(f"\n🎯 DATA TYPE COVERAGE:")
print("-" * 40)

# Price data
cursor.execute(
    "SELECT COUNT(*) FROM ml_features_materialized WHERE current_price IS NOT NULL"
)
price_count = cursor.fetchone()[0]
print(f"   Price data: {price_count:,} ({price_count/total_records*100:.1f}%)")

# Sentiment data
cursor.execute(
    "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
)
sentiment_count = cursor.fetchone()[0]
print(
    f"   Sentiment data: {sentiment_count:,} ({sentiment_count/total_records*100:.1f}%)"
)

# Onchain data
cursor.execute(
    "SELECT COUNT(*) FROM ml_features_materialized WHERE active_addresses_24h IS NOT NULL"
)
onchain_count = cursor.fetchone()[0]
print(f"   Onchain data: {onchain_count:,} ({onchain_count/total_records*100:.1f}%)")

# Technical indicators
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE sma_20 IS NOT NULL")
technical_count = cursor.fetchone()[0]
print(
    f"   Technical data: {technical_count:,} ({technical_count/total_records*100:.1f}%)"
)

# Recent data quality (last 24 hours)
cursor.execute(
    """
    SELECT COUNT(*) FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
"""
)
recent_total = cursor.fetchone()[0]

cursor.execute(
    """
    SELECT COUNT(*) FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    AND current_price IS NOT NULL 
    AND avg_ml_overall_sentiment IS NOT NULL
    AND active_addresses_24h IS NOT NULL
    AND sma_20 IS NOT NULL
"""
)
recent_complete = cursor.fetchone()[0]

print(f"\n⏰ RECENT DATA QUALITY (Last 24 hours):")
print(f"   Total recent records: {recent_total:,}")
print(f"   Complete records: {recent_complete:,}")
if recent_total > 0:
    print(f"   Completeness: {recent_complete/recent_total*100:.1f}%")

conn.close()

print(f"\n" + "=" * 60)
print("🎯 CONCLUSION:")
if populated_columns == total_columns:
    print("✅ ALL COLUMNS ARE POPULATED!")
elif populated_columns / total_columns > 0.8:
    print("✅ EXCELLENT: Most columns are populated")
elif populated_columns / total_columns > 0.6:
    print("✅ GOOD: Majority of columns are populated")
else:
    print("⚠️ NEEDS IMPROVEMENT: Many columns are empty")
print("=" * 60)
