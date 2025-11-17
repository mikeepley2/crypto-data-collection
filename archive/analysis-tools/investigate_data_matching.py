#!/usr/bin/env python3
"""
Investigate why additional columns aren't being populated
"""

import os
import mysql.connector
from datetime import datetime


def investigate_data_matching():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("=== INVESTIGATING DATA MATCHING ===")

        # Check if there's any sentiment data for today
        cursor.execute(
            "SELECT symbol, COUNT(*) FROM crypto_news WHERE DATE(created_at) = CURDATE() GROUP BY symbol LIMIT 5"
        )
        sentiment_symbols = cursor.fetchall()
        print(f"Sentiment data symbols for today: {sentiment_symbols}")

        # Check if there's any technical data for today
        cursor.execute(
            "SELECT symbol, COUNT(*) FROM technical_indicators WHERE DATE(timestamp_iso) = CURDATE() GROUP BY symbol LIMIT 5"
        )
        tech_symbols = cursor.fetchall()
        print(f"Technical data symbols for today: {tech_symbols}")

        # Check if there's any onchain data for today
        cursor.execute(
            "SELECT coin_symbol, COUNT(*) FROM onchain_metrics WHERE DATE(collection_date) = CURDATE() GROUP BY coin_symbol LIMIT 5"
        )
        onchain_symbols = cursor.fetchall()
        print(f"Onchain data symbols for today: {onchain_symbols}")

        # Check if there's any macro data for today
        cursor.execute(
            "SELECT indicator_name, COUNT(*) FROM macro_indicators WHERE DATE(indicator_date) = CURDATE() GROUP BY indicator_name"
        )
        macro_indicators = cursor.fetchall()
        print(f"Macro indicators for today: {macro_indicators}")

        # Check what symbols are in the materialized table
        cursor.execute(
            "SELECT symbol, COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE() GROUP BY symbol LIMIT 10"
        )
        materialized_symbols = cursor.fetchall()
        print(f"Materialized table symbols for today: {materialized_symbols}")

        # Check if there's any overlap between sentiment data and materialized table
        cursor.execute(
            """
            SELECT m.symbol, COUNT(*) as materialized_count, 
                   (SELECT COUNT(*) FROM crypto_news c WHERE c.symbol = m.symbol AND DATE(c.created_at) = CURDATE()) as sentiment_count
            FROM ml_features_materialized m 
            WHERE DATE(m.timestamp_iso) = CURDATE() 
            GROUP BY m.symbol 
            HAVING sentiment_count > 0
            LIMIT 5
        """
        )
        overlap_data = cursor.fetchall()
        print(f"Symbols with both materialized and sentiment data: {overlap_data}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    investigate_data_matching()
