#!/usr/bin/env python3
"""
Phase 1: Optimized Sentiment Enhancement
Memory-efficient approach with smaller batches and better error handling
"""

import mysql.connector
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("phase1_sentiment_optimized")


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


def optimized_sentiment_update():
    """
    Optimized sentiment update using smaller batches and better error handling
    """
    logger.info("🚀 Starting Optimized Sentiment Enhancement")

    conn = get_db_connection()
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor()

        # Get current status
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

        # Process in very small batches to avoid timeouts
        batch_size = 1000
        total_updated = 0
        offset = 0
        batch_count = 0
        max_batches = 50  # Limit to prevent overwhelming the system

        while batch_count < max_batches:
            batch_count += 1
            logger.info(f"🔄 Processing batch {batch_count} (offset {offset})...")

            # Get batch of records without sentiment (most recent first)
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
                logger.info("No more records to process")
                break

            logger.info(
                f"Found {len(batch_records)} records without sentiment in this batch"
            )

            # Process each record individually to avoid large transactions
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

            time.sleep(2)

            # Check if we've made good progress
            if batch_count % 10 == 0:
                cursor.execute(
                    "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
                )
                current_progress = cursor.fetchone()[0]
                progress_pct = (
                    (current_progress / total_records * 100) if total_records > 0 else 0
                )
                logger.info(
                    f"📈 Progress: {current_progress:,}/{total_records:,} ({progress_pct:.1f}%)"
                )

        # Check final status
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        final_sentiment = cursor.fetchone()[0]
        final_pct = (final_sentiment / total_records * 100) if total_records > 0 else 0

        logger.info(f"🎉 Optimized sentiment update complete!")
        logger.info(
            f"📊 Final Status: {final_sentiment:,}/{total_records:,} ({final_pct:.1f}%)"
        )
        logger.info(f"📈 Records updated: {total_updated:,}")
        logger.info(
            f"📈 Improvement: +{final_sentiment - current_sentiment:,} records (+{final_pct - current_pct:.1f}%)"
        )

        return {"processed": total_updated, "errors": 0}

    except Exception as e:
        logger.error(f"Error in optimized sentiment update: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Optimized Sentiment Enhancement")
    logger.info("=" * 60)
    logger.info("Strategy: Small batches with individual record processing")

    results = optimized_sentiment_update()

    logger.info("🎉 Phase 1 Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
