#!/usr/bin/env python3
"""Check column completeness in ml_features_materialized over last week"""
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
print("MATERIALIZED TABLE COLUMN COMPLETENESS CHECK (Last Week)")
print("=" * 80)
print()

# Get all columns in the materialized table
cursor.execute(
    """
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'crypto_prices'
    AND TABLE_NAME = 'ml_features_materialized'
    ORDER BY ORDINAL_POSITION
"""
)

columns_info = cursor.fetchall()
column_names = [
    col["COLUMN_NAME"]
    for col in columns_info
    if col["COLUMN_NAME"] not in ["id", "updated_at", "created_at"]
]

print(f"📊 Analyzing {len(column_names)} columns in ml_features_materialized")
print()

# Get total records in last week
cursor.execute(
    """
    SELECT COUNT(*) as total
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
total_records = cursor.fetchone()["total"]
print(f"📈 Total records in last 7 days: {total_records:,}")
print()

# Check completeness for each column
completeness_data = []

for col in column_names:
    # Skip if it's a timestamp or date column (they're always populated if row exists)
    if col in ["timestamp_iso", "symbol", "timestamp"]:
        continue

    try:
        cursor.execute(
            f"""
            SELECT 
                COUNT(*) as total,
                COUNT({col}) as non_null,
                COUNT(*) - COUNT({col}) as null_count,
                ROUND(COUNT({col}) * 100.0 / COUNT(*), 2) as completeness_pct
            FROM ml_features_materialized
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """
        )
        result = cursor.fetchone()

        completeness_data.append(
            {
                "column": col,
                "total": result["total"],
                "non_null": result["non_null"],
                "null_count": result["null_count"],
                "completeness_pct": result["completeness_pct"],
            }
        )
    except Exception as e:
        # Column might not exist or have issues
        completeness_data.append(
            {
                "column": col,
                "total": total_records,
                "non_null": 0,
                "null_count": total_records,
                "completeness_pct": 0.0,
                "error": str(e),
            }
        )

# Sort by completeness (lowest first)
completeness_data.sort(key=lambda x: x["completeness_pct"])

print("Column Completeness Report:")
print("-" * 80)
print(f"{'Column Name':<40} {'Non-NULL':<12} {'NULL':<12} {'Completeness %':<15}")
print("-" * 80)

for data in completeness_data:
    col_name = data["column"]
    if len(col_name) > 38:
        col_name = col_name[:35] + "..."

    non_null = data["non_null"]
    null_count = data["null_count"]
    pct = data["completeness_pct"]

    status = "✅" if pct >= 95 else "⚠️ " if pct >= 50 else "❌"

    print(f"{status} {col_name:<38} {non_null:>10,} {null_count:>10,} {pct:>13.2f}%")

print("-" * 80)
print()

# Summary statistics
total_cols = len(completeness_data)
complete_cols = sum(1 for d in completeness_data if d["completeness_pct"] >= 95)
partial_cols = sum(1 for d in completeness_data if 50 <= d["completeness_pct"] < 95)
incomplete_cols = sum(1 for d in completeness_data if d["completeness_pct"] < 50)

avg_completeness = (
    sum(d["completeness_pct"] for d in completeness_data) / total_cols
    if total_cols > 0
    else 0
)

print("Summary:")
print(f"   Total columns analyzed: {total_cols}")
print(f"   ✅ Complete (≥95%): {complete_cols}")
print(f"   ⚠️  Partial (50-94%): {partial_cols}")
print(f"   ❌ Incomplete (<50%): {incomplete_cols}")
print(f"   Average completeness: {avg_completeness:.2f}%")
print()

# Show dates coverage
cursor.execute(
    """
    SELECT 
        DATE(timestamp_iso) as date,
        COUNT(*) as records
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(timestamp_iso)
    ORDER BY DATE(timestamp_iso) DESC
"""
)
print("Records by date (last 7 days):")
for row in cursor.fetchall():
    print(f"   {row['date']}: {row['records']:,} records")
print()

print("=" * 80)

conn.close()


