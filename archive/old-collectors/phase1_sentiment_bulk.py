#!/usr/bin/env python3
"""
Phase 1: Bulk Sentiment Enhancement
Using SQL-based bulk updates for maximum efficiency
"""

import mysql.connector
import os
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("phase1_sentiment_bulk")


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
            autocommit=False,
            connection_timeout=30,
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def bulk_sentiment_update():
    """
    Bulk sentiment update using SQL-based approach for maximum efficiency
    """
    logger.info("🚀 Starting Bulk Sentiment Enhancement")

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

        # Target: 80% coverage
        target_records = int(total_records * 0.8)
        records_needed = target_records - current_sentiment
        logger.info(
            f"🎯 Target: {target_records:,} records (80%) - Need {records_needed:,} more"
        )

        # Use bulk SQL UPDATE with time-based sentiment matching
        logger.info("🔄 Applying bulk sentiment update with time-based decay...")

        # Process in chunks to avoid overwhelming the database
        chunk_size = 50000  # Process 50k records at a time
        total_updated = 0
        offset = 0
        chunk_count = 0
        max_chunks = 50  # Process up to 2.5M records

        while chunk_count < max_chunks and total_updated < records_needed:
            chunk_count += 1
            logger.info(f"🔄 Processing chunk {chunk_count} (offset {offset})...")

            # Bulk update using SQL with time-based sentiment matching
            try:
                cursor.execute(
                    """
                    UPDATE ml_features_materialized m
                    SET 
                        avg_ml_overall_sentiment = (
                            SELECT 
                                AVG(CASE 
                                    WHEN n.published_at >= DATE_SUB(m.timestamp_iso, INTERVAL 1 HOUR) THEN n.ml_sentiment_score * 1.0
                                    WHEN n.published_at >= DATE_SUB(m.timestamp_iso, INTERVAL 6 HOUR) THEN n.ml_sentiment_score * 0.8
                                    WHEN n.published_at >= DATE_SUB(m.timestamp_iso, INTERVAL 24 HOUR) THEN n.ml_sentiment_score * 0.6
                                    ELSE n.ml_sentiment_score * 0.3
                                END)
                            FROM crypto_news n
                            WHERE n.published_at >= DATE_SUB(m.timestamp_iso, INTERVAL 24 HOUR)
                            AND n.published_at <= m.timestamp_iso
                            AND n.ml_sentiment_score IS NOT NULL
                        ),
                        sentiment_volume = (
                            SELECT COUNT(*)
                            FROM crypto_news n
                            WHERE n.published_at >= DATE_SUB(m.timestamp_iso, INTERVAL 24 HOUR)
                            AND n.published_at <= m.timestamp_iso
                            AND n.ml_sentiment_score IS NOT NULL
                        ),
                        updated_at = NOW()
                    WHERE m.avg_ml_overall_sentiment IS NULL
                    LIMIT %s
                """,
                    (chunk_size,),
                )

                chunk_updated = cursor.rowcount
                total_updated += chunk_updated

                # Commit this chunk
                conn.commit()

                logger.info(
                    f"✅ Chunk {chunk_count} complete: {chunk_updated} records updated (total: {total_updated})"
                )

                # Check progress
                cursor.execute(
                    "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
                )
                current_progress = cursor.fetchone()[0]
                progress_pct = (
                    (current_progress / total_records * 100) if total_records > 0 else 0
                )
                remaining = target_records - current_progress

                logger.info(
                    f"📈 Progress: {current_progress:,}/{total_records:,} ({progress_pct:.1f}%) - {remaining:,} remaining"
                )

                # If we've reached our target, stop
                if current_progress >= target_records:
                    logger.info("🎯 Target reached! Stopping processing.")
                    break

                # Small delay between chunks
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error in chunk {chunk_count}: {e}")
                conn.rollback()
                continue

        # Check final status
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        final_sentiment = cursor.fetchone()[0]
        final_pct = (final_sentiment / total_records * 100) if total_records > 0 else 0

        logger.info(f"🎉 Bulk sentiment update complete!")
        logger.info(
            f"📊 Final Status: {final_sentiment:,}/{total_records:,} ({final_pct:.1f}%)"
        )
        logger.info(f"📈 Records updated: {total_updated:,}")
        logger.info(
            f"📈 Improvement: +{final_sentiment - current_sentiment:,} records (+{final_pct - current_pct:.1f}%)"
        )

        return {"processed": total_updated, "errors": 0}

    except Exception as e:
        logger.error(f"Error in bulk sentiment update: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Bulk Sentiment Enhancement")
    logger.info("=" * 60)
    logger.info("Strategy: SQL-based bulk updates for maximum efficiency")

    results = bulk_sentiment_update()

    logger.info("🎉 Phase 1 Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
