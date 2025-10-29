#!/usr/bin/env python3
"""
Debug why macro data isn't being populated
"""

import os
import mysql.connector


def debug_macro():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        # Check a sample record
        cursor.execute(
            """
            SELECT symbol, vix, treasury_10y, dxy, unemployment_rate, inflation_rate, gold_price, oil_price
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            LIMIT 1
        """
        )

        record = cursor.fetchone()
        print(f"Sample record: {record}")

        # Check macro data availability
        cursor.execute(
            """
            SELECT indicator_name, value, indicator_date
            FROM macro_indicators 
            WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ORDER BY indicator_date DESC
        """
        )

        macro_data = cursor.fetchall()
        print(f"\nAvailable macro data:")
        for name, value, date in macro_data:
            print(f"  {name}: {value} ({date})")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    debug_macro()
