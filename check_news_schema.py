#!/usr/bin/env python3
"""
Check crypto_news table schema
"""

import os
import mysql.connector


def check_news_schema():
    """Check crypto_news table schema"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 CRYPTO_NEWS TABLE SCHEMA")
        print("=" * 50)

        cursor.execute("DESCRIBE crypto_news")
        columns = cursor.fetchall()

        for col in columns:
            print(f"{col[0]:<30} | {col[1]:<20} | Null: {col[2]:<3} | Key: {col[3]}")

        # Check sample data
        cursor.execute("SELECT * FROM crypto_news LIMIT 3")
        samples = cursor.fetchall()

        print(f"\n📊 SAMPLE DATA:")
        for i, sample in enumerate(samples, 1):
            print(f"Record {i}: {sample}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_news_schema()
