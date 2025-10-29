#!/usr/bin/env python3
"""
Debug why UPDATE statements aren't working
"""

import os
import mysql.connector


def debug_update_issue():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 DEBUGGING UPDATE ISSUE")
        print("=" * 50)

        # Check if records exist for today
        cursor.execute(
            """
            SELECT symbol, timestamp_iso, current_price
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            LIMIT 3
        """
        )

        records = cursor.fetchall()
        print(f"📊 Sample records for today:")
        for symbol, timestamp_iso, price in records:
            print(f"  • {symbol}: {timestamp_iso} - ${price}")

        # Test a simple UPDATE on one record
        if records:
            test_symbol = records[0][0]
            test_timestamp = records[0][1]

            print(f"\n🧪 Testing UPDATE on {test_symbol} at {test_timestamp}")

            # Try to update just VIX
            cursor.execute(
                """
                UPDATE ml_features_materialized 
                SET vix = %s, updated_at = NOW()
                WHERE symbol = %s AND timestamp_iso = %s
            """,
                (16.28, test_symbol, test_timestamp),
            )

            print(f"  • Rows affected: {cursor.rowcount}")

            # Check if it worked
            cursor.execute(
                """
                SELECT vix FROM ml_features_materialized 
                WHERE symbol = %s AND timestamp_iso = %s
            """,
                (test_symbol, test_timestamp),
            )

            result = cursor.fetchone()
            print(f"  • VIX after update: {result[0] if result else 'None'}")

            # Commit the transaction
            conn.commit()
            print(f"  • Transaction committed")

            # Check again after commit
            cursor.execute(
                """
                SELECT vix FROM ml_features_materialized 
                WHERE symbol = %s AND timestamp_iso = %s
            """,
                (test_symbol, test_timestamp),
            )

            result = cursor.fetchone()
            print(f"  • VIX after commit: {result[0] if result else 'None'}")

        # Check if there are any database locks
        cursor.execute("SHOW PROCESSLIST")
        processes = cursor.fetchall()

        long_running = [
            p for p in processes if p[5] and p[5] > 10
        ]  # Processes running > 10 seconds
        if long_running:
            print(f"\n⚠️ Long running processes:")
            for p in long_running:
                print(f"  • ID: {p[0]}, User: {p[1]}, Time: {p[5]}s, State: {p[4]}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    debug_update_issue()
