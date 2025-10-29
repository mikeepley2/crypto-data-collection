#!/usr/bin/env python3
"""
Quick check for today's data coverage
"""

import os
import mysql.connector


def quick_check():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        # Today's records
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        today_total = cursor.fetchone()[0]

        # Key columns
        cursor.execute(
            "SELECT COUNT(avg_ml_overall_sentiment) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        sentiment = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(vix) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        macro = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(sma_20) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        technical = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(active_addresses_24h) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        onchain = cursor.fetchone()[0]

        print(f"Today's Records: {today_total:,}")
        print(f"Sentiment: {sentiment:,} ({sentiment/today_total*100:.1f}%)")
        print(f"Macro: {macro:,} ({macro/today_total*100:.1f}%)")
        print(f"Technical: {technical:,} ({technical/today_total*100:.1f}%)")
        print(f"Onchain: {onchain:,} ({onchain/today_total*100:.1f}%)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    quick_check()
