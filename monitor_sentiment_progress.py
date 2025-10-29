#!/usr/bin/env python3
"""
Monitor sentiment data enhancement progress
"""

import mysql.connector
import os
import time
from datetime import datetime


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


def check_progress():
    conn = get_db_connection()
    if not conn:
        return None

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

        # Get recent updates (last 5 minutes)
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
            AND avg_ml_overall_sentiment IS NOT NULL
        """
        )
        recent_5m = cursor.fetchone()[0]

        # Get recent updates (last 10 minutes)
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
            AND avg_ml_overall_sentiment IS NOT NULL
        """
        )
        recent_10m = cursor.fetchone()[0]

        # Calculate target
        target_records = int(total_records * 0.8)
        remaining = target_records - sentiment_records

        conn.close()

        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "total_records": total_records,
            "sentiment_records": sentiment_records,
            "percentage": pct,
            "recent_5m": recent_5m,
            "recent_10m": recent_10m,
            "target_records": target_records,
            "remaining": remaining,
        }

    except Exception as e:
        print(f"Error: {e}")
        return None


def monitor_progress(duration_minutes=10):
    print("🔍 Monitoring Sentiment Enhancement Progress")
    print("=" * 60)
    print(f"Monitoring for {duration_minutes} minutes...")
    print()

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    previous_records = None
    start_records = None

    while time.time() < end_time:
        progress = check_progress()
        if progress:
            if start_records is None:
                start_records = progress["sentiment_records"]
                print(
                    f"📊 Starting Status: {progress['sentiment_records']:,}/{progress['total_records']:,} ({progress['percentage']:.1f}%)"
                )
                print(
                    f"🎯 Target: {progress['target_records']:,} records (80%) - {progress['remaining']:,} remaining"
                )
                print()

            # Calculate progress since start
            records_processed = progress["sentiment_records"] - start_records
            rate_5m = progress["recent_5m"] / 5 if progress["recent_5m"] > 0 else 0
            rate_10m = progress["recent_10m"] / 10 if progress["recent_10m"] > 0 else 0

            print(
                f"[{progress['timestamp']}] {progress['sentiment_records']:,}/{progress['total_records']:,} ({progress['percentage']:.1f}%) | "
                f"Rate: {rate_5m:.0f}/min (5m), {rate_10m:.0f}/min (10m) | "
                f"Processed: +{records_processed:,} | Remaining: {progress['remaining']:,}"
            )

            if previous_records is not None:
                diff = progress["sentiment_records"] - previous_records
                if diff > 0:
                    print(f"  📈 +{diff:,} records since last check")

            previous_records = progress["sentiment_records"]
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Failed to get status")

        time.sleep(30)  # Check every 30 seconds

    # Final summary
    final_progress = check_progress()
    if final_progress and start_records is not None:
        total_processed = final_progress["sentiment_records"] - start_records
        time_elapsed = (time.time() - start_time) / 60
        avg_rate = total_processed / time_elapsed if time_elapsed > 0 else 0

        print()
        print("📊 Final Summary:")
        print(f"  Starting: {start_records:,} records")
        print(f"  Current:  {final_progress['sentiment_records']:,} records")
        print(f"  Processed: +{total_processed:,} records")
        print(f"  Time: {time_elapsed:.1f} minutes")
        print(f"  Rate: {avg_rate:.0f} records/minute")
        print(f"  Progress: {final_progress['percentage']:.1f}%")
        print(f"  Remaining: {final_progress['remaining']:,} records")

        if avg_rate > 0:
            eta_minutes = final_progress["remaining"] / avg_rate
            eta_hours = eta_minutes / 60
            print(f"  ETA: {eta_hours:.1f} hours ({eta_minutes:.0f} minutes)")


if __name__ == "__main__":
    monitor_progress(10)  # Monitor for 10 minutes
