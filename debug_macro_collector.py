#!/usr/bin/env python3
"""
Debug macro collector and check for valid data
"""

import os
import mysql.connector


def debug_macro_collector():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 MACRO COLLECTOR DEBUG")
        print("=" * 50)

        # Check all macro indicators with non-null values
        cursor.execute(
            """
            SELECT indicator_name, value, indicator_date, data_source
            FROM macro_indicators 
            WHERE value IS NOT NULL
            ORDER BY indicator_name, indicator_date DESC
            LIMIT 20
        """
        )

        valid_data = cursor.fetchall()
        print(f"📊 Valid Macro Data ({len(valid_data)} records):")
        for name, value, date, source in valid_data:
            print(f"  • {name}: {value} ({date}) - {source}")

        # Check latest data for each indicator
        cursor.execute(
            """
            SELECT indicator_name, MAX(indicator_date) as latest_date, 
                   COUNT(*) as total_records, COUNT(value) as non_null_records
            FROM macro_indicators 
            GROUP BY indicator_name
            ORDER BY indicator_name
        """
        )

        indicator_stats = cursor.fetchall()
        print(f"\n📈 Indicator Statistics:")
        for name, latest_date, total, non_null in indicator_stats:
            print(
                f"  • {name}: Latest={latest_date}, Total={total}, Non-null={non_null}"
            )

        # Check if there are any recent non-null values
        cursor.execute(
            """
            SELECT indicator_name, value, indicator_date
            FROM macro_indicators 
            WHERE value IS NOT NULL
            AND indicator_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY indicator_date DESC
            LIMIT 10
        """
        )

        recent_data = cursor.fetchall()
        print(f"\n🕒 Recent Valid Data (30 days):")
        for name, value, date in recent_data:
            print(f"  • {name}: {value} ({date})")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    debug_macro_collector()
