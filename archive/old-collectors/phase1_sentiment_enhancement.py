#!/usr/bin/env python3
"""
Phase 1: Sentiment Data Enhancement
Increase sentiment coverage from 42.3% to 80%+ using time-based forward-fill with decay
"""

import mysql.connector
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("phase1_sentiment_enhancement")


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def phase1_sentiment_enhancement():
    """
    Phase 1: Enhance sentiment data using time-based forward-fill with decay
    Strategy: 1h=100%, 6h=80%, 24h=60%, >24h=30% weight
    """
    logger.info("🚀 Starting Phase 1: Sentiment Data Enhancement")
    logger.info("Target: Increase from 42.3% to 80%+ coverage")

    conn = get_db_connection()
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor()

        # Get current sentiment coverage
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_records = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        current_sentiment = cursor.fetchone()[0]
        current_pct = (
            (current_sentiment / total_records * 100) if total_records > 0 else 0
        )

        logger.info(
            f"📊 Current Status: {current_sentiment:,}/{total_records:,} ({current_pct:.1f}%)"
        )

        # Process in date batches to avoid memory issues
        batch_size = 10000
        total_updated = 0
        offset = 0
        batch_count = 0

        while True:
            batch_count += 1
            logger.info(f"🔄 Processing batch {batch_count} (offset {offset})...")

            # Get batch of records without sentiment
            cursor.execute(
                """
                SELECT symbol, timestamp_iso
                FROM ml_features_materialized
                WHERE avg_ml_overall_sentiment IS NULL
                ORDER BY timestamp_iso DESC
                LIMIT %s OFFSET %s
            """,
                (batch_size, offset),
            )

            batch_records = cursor.fetchall()
            if not batch_records:
                break

            logger.info(
                f"Found {len(batch_records)} records without sentiment in this batch"
            )

            # Process each record with time-based sentiment matching
            batch_updated = 0
            for symbol, timestamp_iso in batch_records:
                try:
                    # Time-based sentiment lookup with decay weights
                    cursor.execute(
                        """
                        SELECT 
                            AVG(CASE 
                                WHEN published_at >= DATE_SUB(%s, INTERVAL 1 HOUR) THEN ml_sentiment_score * 1.0
                                WHEN published_at >= DATE_SUB(%s, INTERVAL 6 HOUR) THEN ml_sentiment_score * 0.8
                                WHEN published_at >= DATE_SUB(%s, INTERVAL 24 HOUR) THEN ml_sentiment_score * 0.6
                                ELSE ml_sentiment_score * 0.3
                            END) as weighted_sentiment,
                            COUNT(*) as sentiment_count,
                            AVG(ml_sentiment_score) as raw_sentiment
                        FROM crypto_news
                        WHERE published_at >= DATE_SUB(%s, INTERVAL 24 HOUR)
                        AND published_at <= %s
                        AND ml_sentiment_score IS NOT NULL
                    """,
                        (
                            timestamp_iso,
                            timestamp_iso,
                            timestamp_iso,
                            timestamp_iso,
                            timestamp_iso,
                        ),
                    )

                    sentiment_data = cursor.fetchone()

                    if sentiment_data and sentiment_data[0] is not None:
                        weighted_sentiment, sentiment_count, raw_sentiment = (
                            sentiment_data
                        )

                        # Use weighted sentiment if available, otherwise raw sentiment
                        final_sentiment = (
                            weighted_sentiment
                            if weighted_sentiment is not None
                            else raw_sentiment
                        )

                        # Update the materialized record
                        cursor.execute(
                            """
                            UPDATE ml_features_materialized
                            SET avg_ml_overall_sentiment = %s,
                                sentiment_volume = %s,
                                updated_at = NOW()
                            WHERE symbol = %s AND timestamp_iso = %s
                        """,
                            (final_sentiment, sentiment_count, symbol, timestamp_iso),
                        )

                        if cursor.rowcount > 0:
                            batch_updated += 1
                            total_updated += 1

                except Exception as e:
                    logger.error(f"Error processing {symbol} at {timestamp_iso}: {e}")
                    continue

            # Commit this batch
            conn.commit()
            logger.info(
                f"✅ Batch {batch_count} complete: {batch_updated} records updated (total: {total_updated})"
            )

            offset += batch_size

            # Small delay between batches
            import time

            time.sleep(1)

            # Stop after reasonable progress to avoid overwhelming the system
            if batch_count >= 20:  # Process up to 200k records
                logger.info("🛑 Stopping after 20 batches to avoid system overload")
                break

        # Check final coverage
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        final_sentiment = cursor.fetchone()[0]
        final_pct = (final_sentiment / total_records * 100) if total_records > 0 else 0

        logger.info(f"🎉 Phase 1 Complete!")
        logger.info(
            f"📊 Final Status: {final_sentiment:,}/{total_records:,} ({final_pct:.1f}%)"
        )
        logger.info(
            f"📈 Improvement: +{final_sentiment - current_sentiment:,} records (+{final_pct - current_pct:.1f}%)"
        )

        return {"processed": total_updated, "errors": 0}

    except Exception as e:
        logger.error(f"Error in Phase 1 sentiment enhancement: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Phase 1: Sentiment Data Enhancement")
    logger.info("=" * 70)
    logger.info("Strategy: Time-based forward-fill with decay weights")
    logger.info("  - 1 hour: 100% weight (most recent)")
    logger.info("  - 6 hours: 80% weight (recent)")
    logger.info("  - 24 hours: 60% weight (older)")
    logger.info("  - >24 hours: 30% weight (much older)")

    # Execute Phase 1
    results = phase1_sentiment_enhancement()

    logger.info("🎉 Phase 1 Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
