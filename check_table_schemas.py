#!/usr/bin/env python3
"""
Check table schemas to fix SQL column errors
"""

import os
import mysql.connector


def check_schemas():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        # Check macro_indicators table schema
        print("=== MACRO_INDICATORS TABLE SCHEMA ===")
        cursor.execute("DESCRIBE macro_indicators")
        for row in cursor.fetchall():
            print(f"{row[0]} - {row[1]}")

        print("\n=== PRICE_DATA_REAL TABLE SCHEMA ===")
        cursor.execute("DESCRIBE price_data_real")
        for row in cursor.fetchall():
            print(f"{row[0]} - {row[1]}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_schemas()
