#!/usr/bin/env python3
"""Backfill materialized table with fixed joins for existing records"""
import mysql.connector
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "src/docker/materialized_updater")

# Import the updater class
from realtime_materialized_updater import RealTimeMaterializedTableUpdater

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("BACKFILLING MATERIALIZED TABLE WITH FIXED JOINS")
print("=" * 80)
print()

# Get all symbols and dates that need updating
cursor.execute(
    """
    SELECT DISTINCT symbol, DATE(timestamp_iso) as date
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    ORDER BY symbol, date
    LIMIT 100
"""
)
records_to_update = cursor.fetchall()
print(f"Found {len(records_to_update)} symbol-date combinations to update")
print()

# Process each symbol
updater = RealTimeMaterializedTableUpdater()
processed = 0

for record in records_to_update[:10]:  # Process first 10 for testing
    symbol = record["symbol"]
    date = record["date"]
    print(f"Processing {symbol} for {date}...")

    # Force process this symbol with specific date range
    updater.start_date = date
    updater.end_date = date
    updater.update_if_changed = True
    updater.insert_only = False

    try:
        count = updater.process_symbol_updates(symbol)
        processed += count
        print(f"  Updated {count} records for {symbol} on {date}")
    except Exception as e:
        print(f"  Error: {e}")
        continue

print()
print("=" * 80)
print(f"Backfill complete: {processed} records processed")
print("Run check_materialized_completeness.py to verify improvements")
print("=" * 80)

conn.close()


