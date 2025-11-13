#!/usr/bin/env python3
"""
Sentiment Forward-Fill Strategy with Time Decay
Apply sentiment data to price records using time-based matching with decay
"""

import mysql.connector
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sentiment_forward_fill")


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def sentiment_forward_fill_strategy():
    """
    Apply sentiment data using time-based forward-fill with decay
    Strategy: For each price record, find the most recent sentiment within 24 hours
    """
    logger.info("🚀 Starting Sentiment Forward-Fill Strategy...")

    conn = get_db_connection()
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor()

        # Get all materialized records without sentiment data
        cursor.execute(
            """
            SELECT symbol, timestamp_iso
            FROM ml_features_materialized
            WHERE avg_ml_overall_sentiment IS NULL
            ORDER BY timestamp_iso DESC
            LIMIT 10000
        """
        )
        records_without_sentiment = cursor.fetchall()

        logger.info(
            f"Found {len(records_without_sentiment)} records without sentiment data"
        )

        total_updated = 0
        processed = 0

        for symbol, timestamp_iso in records_without_sentiment:
            try:
                processed += 1
                if processed % 1000 == 0:
                    logger.info(
                        f"Processed {processed}/{len(records_without_sentiment)} records..."
                    )

                # Find the most recent sentiment data within 24 hours for this symbol
                cursor.execute(
                    """
                    SELECT 
                        AVG(ml_sentiment_score) as avg_sentiment,
                        COUNT(*) as sentiment_count
                    FROM crypto_news
                    WHERE published_at >= DATE_SUB(%s, INTERVAL 24 HOUR)
                    AND published_at <= %s
                    AND ml_sentiment_score IS NOT NULL
                    AND (
                        crypto_mentions LIKE %s 
                        OR title LIKE %s 
                        OR content LIKE %s
                    )
                """,
                    (
                        timestamp_iso,
                        timestamp_iso,
                        f"%{symbol}%",
                        f"%{symbol}%",
                        f"%{symbol}%",
                    ),
                )

                sentiment_data = cursor.fetchone()
                if sentiment_data and sentiment_data[0] is not None:
                    avg_sentiment, sentiment_count = sentiment_data

                    # Update the materialized record
                    cursor.execute(
                        """
                        UPDATE ml_features_materialized
                        SET avg_ml_overall_sentiment = %s,
                            sentiment_volume = %s,
                            updated_at = NOW()
                        WHERE symbol = %s AND timestamp_iso = %s
                    """,
                        (avg_sentiment, sentiment_count, symbol, timestamp_iso),
                    )

                    if cursor.rowcount > 0:
                        total_updated += 1

            except Exception as e:
                logger.error(f"Error processing {symbol} at {timestamp_iso}: {e}")
                continue

        # Commit all updates
        conn.commit()

        logger.info(
            f"🎉 Sentiment forward-fill complete: {total_updated} records updated"
        )
        return {"processed": total_updated, "errors": 0}

    except Exception as e:
        logger.error(f"Error in sentiment forward-fill: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def check_sentiment_coverage():
    """Check sentiment coverage after forward-fill"""
    logger.info("📊 Checking sentiment coverage...")

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Get coverage stats
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_records = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        sentiment_coverage = cursor.fetchone()[0]

        # Get sentiment distribution
        cursor.execute(
            """
            SELECT 
                AVG(avg_ml_overall_sentiment) as avg_sentiment,
                MIN(avg_ml_overall_sentiment) as min_sentiment,
                MAX(avg_ml_overall_sentiment) as max_sentiment,
                STDDEV(avg_ml_overall_sentiment) as sentiment_volatility
            FROM ml_features_materialized
            WHERE avg_ml_overall_sentiment IS NOT NULL
        """
        )
        sentiment_stats = cursor.fetchone()

        logger.info("🎯 SENTIMENT COVERAGE RESULTS:")
        logger.info(f"   Total records: {total_records:,}")
        logger.info(
            f"   With sentiment data: {sentiment_coverage:,} ({sentiment_coverage/total_records*100:.1f}%)"
        )
        logger.info(
            f"   Without sentiment data: {total_records - sentiment_coverage:,} ({(total_records - sentiment_coverage)/total_records*100:.1f}%)"
        )

        if sentiment_stats[0] is not None:
            logger.info(f"   Average sentiment: {sentiment_stats[0]:.3f}")
            logger.info(
                f"   Sentiment range: {sentiment_stats[1]:.3f} to {sentiment_stats[2]:.3f}"
            )
            logger.info(f"   Sentiment volatility: {sentiment_stats[3]:.3f}")

        # Check coverage by symbol
        logger.info("\n📈 Top symbols by sentiment coverage:")
        cursor.execute(
            """
            SELECT 
                symbol,
                COUNT(*) as total_records,
                COUNT(avg_ml_overall_sentiment) as with_sentiment,
                ROUND(COUNT(avg_ml_overall_sentiment) / COUNT(*) * 100, 1) as coverage_pct
            FROM ml_features_materialized
            GROUP BY symbol
            HAVING COUNT(*) > 1000
            ORDER BY coverage_pct DESC
            LIMIT 10
        """
        )
        symbol_coverage = cursor.fetchall()
        for symbol, total, with_sent, coverage in symbol_coverage:
            logger.info(f"   {symbol}: {with_sent:,}/{total:,} ({coverage}%)")

    except Exception as e:
        logger.error(f"Error checking sentiment coverage: {e}")
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Sentiment Forward-Fill Strategy")
    logger.info("=" * 70)
    logger.info(
        "This will apply sentiment data using time-based matching with 24-hour windows"
    )

    # Step 1: Apply sentiment forward-fill
    results = sentiment_forward_fill_strategy()

    # Step 2: Check coverage
    check_sentiment_coverage()

    logger.info("🎉 Sentiment Forward-Fill Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
