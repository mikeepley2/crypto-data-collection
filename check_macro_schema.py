#!/usr/bin/env python3
"""
Check macro_indicators table schema
"""

import os
import mysql.connector


def check_schema():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 MACRO_INDICATORS TABLE SCHEMA")
        print("=" * 40)

        cursor.execute("DESCRIBE macro_indicators")
        columns = cursor.fetchall()

        for col in columns:
            print(f"{col[0]:<20} | {col[1]:<15} | Null: {col[2]:<3} | Key: {col[3]}")

        print("\n📊 SAMPLE DATA:")
        cursor.execute("SELECT * FROM macro_indicators LIMIT 3")
        samples = cursor.fetchall()

        for sample in samples:
            print(sample)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_schema()
