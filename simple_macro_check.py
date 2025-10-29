#!/usr/bin/env python3
"""
Simple macro data check
"""

import os
import mysql.connector


def check_macro():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        # Check macro coverage
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        total = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(vix) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        vix_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(dxy) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        dxy_count = cursor.fetchone()[0]

        print(f"Today's Records: {total:,}")
        print(f"VIX Coverage: {vix_count:,} ({vix_count/total*100:.1f}%)")
        print(f"DXY Coverage: {dxy_count:,} ({dxy_count/total*100:.1f}%)")

        # Check a sample record
        cursor.execute(
            "SELECT symbol, vix, dxy FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE() LIMIT 1"
        )
        sample = cursor.fetchone()
        if sample:
            print(f"Sample: {sample[0]} - VIX: {sample[1]}, DXY: {sample[2]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_macro()
