#!/usr/bin/env python3
"""
Check data sources for today's data
"""

import os
import mysql.connector
from datetime import datetime


def check_data_sources():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("=== DATA SOURCES CHECK FOR TODAY ===")

        # Check macro indicators
        cursor.execute(
            "SELECT COUNT(*) FROM macro_indicators WHERE DATE(indicator_date) = CURDATE()"
        )
        macro_count = cursor.fetchone()[0]
        print(f"Macro indicators for today: {macro_count}")

        # Check sentiment data
        cursor.execute(
            "SELECT COUNT(*) FROM crypto_news WHERE DATE(created_at) = CURDATE()"
        )
        sentiment_count = cursor.fetchone()[0]
        print(f"Sentiment data for today: {sentiment_count}")

        # Check technical indicators
        cursor.execute(
            "SELECT COUNT(*) FROM technical_indicators WHERE DATE(timestamp_iso) = CURDATE()"
        )
        tech_count = cursor.fetchone()[0]
        print(f"Technical indicators for today: {tech_count}")

        # Check onchain data
        cursor.execute(
            "SELECT COUNT(*) FROM onchain_metrics WHERE DATE(collection_date) = CURDATE()"
        )
        onchain_count = cursor.fetchone()[0]
        print(f"Onchain data for today: {onchain_count}")

        # Check price data
        cursor.execute(
            "SELECT COUNT(*) FROM price_data_real WHERE DATE(timestamp_iso) = CURDATE()"
        )
        price_count = cursor.fetchone()[0]
        print(f"Price data for today: {price_count}")

        print(f"\n=== MATERIALIZED TABLE STATUS ===")
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        materialized_count = cursor.fetchone()[0]
        print(f"Materialized records for today: {materialized_count}")

        # Check if any additional columns have data
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE() AND avg_ml_overall_sentiment IS NOT NULL"
        )
        sentiment_coverage = cursor.fetchone()[0]
        print(f"Records with sentiment data: {sentiment_coverage}")

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE() AND vix IS NOT NULL"
        )
        macro_coverage = cursor.fetchone()[0]
        print(f"Records with macro data: {macro_coverage}")

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE() AND sma_20 IS NOT NULL"
        )
        tech_coverage = cursor.fetchone()[0]
        print(f"Records with technical data: {tech_coverage}")

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE() AND active_addresses_24h IS NOT NULL"
        )
        onchain_coverage = cursor.fetchone()[0]
        print(f"Records with onchain data: {onchain_coverage}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    check_data_sources()
