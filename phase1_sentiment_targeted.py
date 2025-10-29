#!/usr/bin/env python3
"""
Phase 1: Targeted Sentiment Enhancement
Process sentiment data by date ranges to avoid lock timeouts
"""

import mysql.connector
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("phase1_sentiment_targeted")


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


def targeted_sentiment_update():
    """
    Targeted sentiment update by date ranges to avoid lock timeouts
    """
    logger.info("🚀 Starting Targeted Sentiment Enhancement")

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

        # Get date ranges to process (last 30 days)
        cursor.execute(
            """
            SELECT DISTINCT DATE(timestamp_iso) as date
            FROM ml_features_materialized
            WHERE avg_ml_overall_sentiment IS NULL
            AND timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY date DESC
            LIMIT 10
        """
        )
        dates = [row[0] for row in cursor.fetchall()]

        logger.info(f"Found {len(dates)} dates to process")

        total_updated = 0
        processed_dates = 0

        # Process each date
        for target_date in dates:
            try:
                logger.info(f"🔄 Processing date: {target_date}")

                # Update sentiment for this specific date
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
                    WHERE DATE(m.timestamp_iso) = %s
                    AND m.avg_ml_overall_sentiment IS NULL
                """,
                    (target_date,),
                )

                date_updated = cursor.rowcount
                total_updated += date_updated
                processed_dates += 1

                # Commit this date
                conn.commit()

                logger.info(
                    f"✅ {target_date}: {date_updated} records updated (total: {total_updated})"
                )

                # Small delay between dates
                import time

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing date {target_date}: {e}")
                conn.rollback()
                continue

        # Check final status
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
        )
        final_sentiment = cursor.fetchone()[0]
        final_pct = (final_sentiment / total_records * 100) if total_records > 0 else 0

        logger.info(f"🎉 Targeted sentiment update complete!")
        logger.info(
            f"📊 Final Status: {final_sentiment:,}/{total_records:,} ({final_pct:.1f}%)"
        )
        logger.info(f"📈 Records updated: {total_updated:,}")
        logger.info(
            f"📈 Improvement: +{final_sentiment - current_sentiment:,} records (+{final_pct - current_pct:.1f}%)"
        )

        return {"processed": total_updated, "errors": 0}

    except Exception as e:
        logger.error(f"Error in targeted sentiment update: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Targeted Sentiment Enhancement")
    logger.info("=" * 60)
    logger.info("Strategy: Process by date ranges to avoid lock timeouts")

    results = targeted_sentiment_update()

    logger.info("🎉 Phase 1 Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
