#!/usr/bin/env python3
"""
Check crypto_news table schema
"""

import os
import mysql.connector


def check_crypto_news_schema():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("=== CRYPTO_NEWS TABLE SCHEMA ===")
        cursor.execute("DESCRIBE crypto_news")
        for row in cursor.fetchall():
            print(row)

        print("\n=== SAMPLE CRYPTO_NEWS DATA ===")
        cursor.execute(
            "SELECT * FROM crypto_news WHERE DATE(created_at) = CURDATE() LIMIT 3"
        )
        for row in cursor.fetchall():
            print(row)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    check_crypto_news_schema()
