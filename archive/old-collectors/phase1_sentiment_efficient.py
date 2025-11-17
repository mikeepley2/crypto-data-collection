#!/usr/bin/env python3
"""
Phase 1: Efficient Sentiment Enhancement
Memory-optimized version for large-scale sentiment data population
"""

import mysql.connector
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("phase1_sentiment_efficient")


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


def efficient_sentiment_update():
    """
    Efficient sentiment update using single SQL UPDATE with time-based decay
    """
    logger.info("🚀 Starting Efficient Sentiment Enhancement")

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

        # Single efficient UPDATE using SQL time-based sentiment matching
        logger.info("🔄 Applying time-based sentiment with decay...")

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
        """
        )

        updated_count = cursor.rowcount
        conn.commit()

        # Check final status
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        final_sentiment = cursor.fetchone()[0]
        final_pct = (final_sentiment / total_records * 100) if total_records > 0 else 0

        logger.info(f"🎉 Efficient sentiment update complete!")
        logger.info(
            f"📊 Final Status: {final_sentiment:,}/{total_records:,} ({final_pct:.1f}%)"
        )
        logger.info(f"📈 Records updated: {updated_count:,}")
        logger.info(
            f"📈 Improvement: +{final_sentiment - current_sentiment:,} records (+{final_pct - current_pct:.1f}%)"
        )

        return {"processed": updated_count, "errors": 0}

    except Exception as e:
        logger.error(f"Error in efficient sentiment update: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Efficient Sentiment Enhancement")
    logger.info("=" * 60)
    logger.info("Strategy: Single SQL UPDATE with time-based decay weights")

    results = efficient_sentiment_update()

    logger.info("🎉 Phase 1 Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
