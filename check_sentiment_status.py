#!/usr/bin/env python3
"""
Check current sentiment coverage status
"""

import mysql.connector
import os


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None


def check_status():
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Get current status
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_records = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        sentiment_records = cursor.fetchone()[0]

        pct = (sentiment_records / total_records * 100) if total_records > 0 else 0

        print(
            f"📊 Current Status: {sentiment_records:,}/{total_records:,} ({pct:.1f}%)"
        )

        # Get recent updates
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            AND avg_ml_overall_sentiment IS NOT NULL
        """
        )
        recent_updates = cursor.fetchone()[0]
        print(f"🔄 Recent updates (1h): {recent_updates:,}")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_status()
