#!/usr/bin/env python3
"""
Monitor Technical Indicators Backfill Progress
Real-time tracking of records updated during backfill
"""

import mysql.connector
import time
from datetime import datetime


def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="news_collector",
        password="99Rules!",
        database="crypto_prices",
    )


def check_progress():
    """Check current backfill progress"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get overall stats
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as with_sma,
                SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as with_rsi,
                SUM(CASE WHEN macd IS NOT NULL THEN 1 ELSE 0 END) as with_macd,
                MAX(updated_at) as latest_update
            FROM technical_indicators
        """
        )

        result = cursor.fetchone()
        total = result["total"]
        with_sma = result["with_sma"] or 0
        with_rsi = result["with_rsi"] or 0
        with_macd = result["with_macd"] or 0
        latest = result["latest_update"]

        # Calculate percentages
        sma_pct = (100 * with_sma / total) if total > 0 else 0
        rsi_pct = (100 * with_rsi / total) if total > 0 else 0
        macd_pct = (100 * with_macd / total) if total > 0 else 0

        print("\n" + "=" * 70)
        print("TECHNICAL INDICATORS BACKFILL PROGRESS")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Latest update in DB: {latest}")
        print("\nCoverage Statistics:")
        print(f"  Total records: {total:,}")
        print(f"  With SMA 20:   {with_sma:>10,} ({sma_pct:>5.1f}%)")
        print(f"  With RSI 14:   {with_rsi:>10,} ({rsi_pct:>5.1f}%)")
        print(f"  With MACD:     {with_macd:>10,} ({macd_pct:>5.1f}%)")

        # Check recent updates
        cursor.execute(
            """
            SELECT 
                DATE(updated_at) as update_date,
                COUNT(*) as updated_count,
                COUNT(DISTINCT symbol) as symbols
            FROM technical_indicators
            WHERE updated_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            GROUP BY DATE(updated_at)
            ORDER BY update_date DESC
        """
        )

        recent = cursor.fetchall()
        if recent:
            print(f"\nRecent Updates (last hour):")
            for row in recent:
                print(
                    f"  {row['update_date']}: {row['updated_count']:,} records, {row['symbols']} symbols"
                )

        conn.close()
        return True

    except Exception as e:
        print(f"Error checking progress: {e}")
        return False


if __name__ == "__main__":
    print("Starting backfill progress monitor...")
    print("Press Ctrl+C to stop\n")

    try:
        iteration = 0
        while True:
            iteration += 1
            check_progress()

            if iteration == 1:
                print(f"\nNext check in 30 seconds...")

            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")

