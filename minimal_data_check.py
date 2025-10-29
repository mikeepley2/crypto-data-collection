#!/usr/bin/env python3
import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    user=os.getenv("DB_USER", "news_collector"),
    password=os.getenv("DB_PASSWORD", "99Rules!"),
    database=os.getenv("DB_NAME", "crypto_prices"),
)
cursor = conn.cursor()

print("MATERIALIZED TABLE - MINIMAL DATA CHECK")
print("=" * 50)

# Total records
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
total = cursor.fetchone()[0]
print(f"Total Records: {total:,}\n")

# Check only key columns
key_columns = [
    ("current_price", "Price"),
    ("avg_ml_overall_sentiment", "ML Sentiment"),
    ("active_addresses_24h", "Onchain"),
    ("sma_20", "Technical"),
]

print("KEY COLUMNS POPULATION")
print("-" * 50)
for col, label in key_columns:
    cursor.execute(
        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
    )
    count = cursor.fetchone()[0]
    pct = (count / total * 100) if total > 0 else 0
    print(f"{label:<20} {count:>10,} / {total:>10,} ({pct:>5.1f}%)")

# Recent data
cursor.execute(
    "SELECT COUNT(*) FROM ml_features_materialized WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)"
)
recent = cursor.fetchone()[0]
print(f"\nRecent records (24h): {recent:,}")

# Complete records
cursor.execute(
    """SELECT COUNT(*) FROM ml_features_materialized 
    WHERE current_price IS NOT NULL AND avg_ml_overall_sentiment IS NOT NULL 
    AND active_addresses_24h IS NOT NULL AND sma_20 IS NOT NULL"""
)
complete = cursor.fetchone()[0]
print(f"Complete records: {complete:,} ({complete/total*100:.1f}%)")

conn.close()
print("\n" + "=" * 50)
