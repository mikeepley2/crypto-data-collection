#!/usr/bin/env python3
"""
Check if materialized table has records for today
"""

import os
import mysql.connector


def check_records():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        # Check if there are any records for today
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        today_count = cursor.fetchone()[0]
        print(f"Today's records in materialized table: {today_count}")

        # Check if there are any records at all
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_count = cursor.fetchone()[0]
        print(f"Total records in materialized table: {total_count}")

        # Check if there are price records for today
        cursor.execute(
            "SELECT COUNT(*) FROM price_data_real WHERE DATE(timestamp_iso) = CURDATE()"
        )
        price_count = cursor.fetchone()[0]
        print(f"Today's price records: {price_count}")

        # Check if there are any records for today in materialized table
        if today_count == 0:
            print("❌ No records in materialized table for today!")
            print("The materialized updater is trying to UPDATE non-existent records.")
            print("We need to INSERT new records instead of UPDATE.")
        else:
            print("✅ Records exist for today")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_records()
