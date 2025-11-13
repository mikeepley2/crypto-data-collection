#!/usr/bin/env python3
"""
Monitor Stock Sentiment Backfill Progress
"""

import mysql.connector
import time
import os


def get_db_connection():
    """Get database connection"""
    config = {
        "host": "127.0.0.1",
        "user": "news_collector",
        "password": "99Rules!",
        "database": "crypto_prices",
        "charset": "utf8mb4",
    }
    return mysql.connector.connect(**config)


def monitor_progress():
    """Monitor the stock sentiment backfill progress"""
    print("Monitoring Stock Sentiment Backfill Progress")
    print("=" * 60)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get current stats
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total_stock_articles,
            COUNT(CASE WHEN ml_sentiment_score IS NOT NULL THEN 1 END) as with_sentiment,
            COUNT(CASE WHEN ml_sentiment_score != 0 THEN 1 END) as non_zero_sentiment,
            AVG(ml_sentiment_score) as avg_sentiment
        FROM crypto_news 
        WHERE market_type = 'stock'
        """
        )
        stats = cursor.fetchone()
        total, with_sentiment, non_zero, avg_sentiment = stats

        sentiment_coverage = with_sentiment / total * 100 if total > 0 else 0
        non_zero_coverage = non_zero / with_sentiment * 100 if with_sentiment > 0 else 0

        print(f"Current Progress:")
        print(f"  Total stock articles: {total:,}")
        print(f"  With sentiment: {with_sentiment:,} ({sentiment_coverage:.1f}%)")
        print(f"  Non-zero sentiment: {non_zero:,} ({non_zero_coverage:.1f}%)")
        print(f"  Average sentiment: {avg_sentiment:.4f}")

        # Check recent activity
        cursor.execute(
            """
        SELECT 
            COUNT(*) as recent_updated,
            MAX(updated_at) as last_update
        FROM crypto_news 
        WHERE market_type = 'stock' 
        AND ml_sentiment_score IS NOT NULL
        AND updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        )
        recent_stats = cursor.fetchone()
        recent_updated, last_update = recent_stats

        print(f"\nRecent Activity (last hour):")
        print(f"  Articles updated: {recent_updated:,}")
        print(f"  Last update: {last_update}")

        # Calculate remaining work
        remaining = total - with_sentiment
        print(f"\nProgress Status:")
        print(f"  Completed: {with_sentiment:,} articles")
        print(f"  Remaining: {remaining:,} articles")
        print(f"  Progress: {sentiment_coverage:.1f}%")

        if remaining > 0:
            print(
                f"\nEstimated completion: {remaining/100:.0f} minutes at current rate"
            )

    except Exception as e:
        print(f"Error monitoring progress: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    monitor_progress()
