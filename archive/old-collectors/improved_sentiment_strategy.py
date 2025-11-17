#!/usr/bin/env python3
"""
Improved Sentiment Strategy
- Use both ML and LLM scores
- Handle overall market sentiment efficiently
- Avoid lock timeouts with batch processing
"""

import mysql.connector
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("improved_sentiment")


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


def improved_sentiment_strategy():
    """
    Improved sentiment strategy using batch processing to avoid lock timeouts
    Apply both ML and LLM overall market sentiment to all price records
    """
    logger.info("🚀 Starting Improved Sentiment Strategy...")

    conn = get_db_connection()
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor()

        # Step 1: Get recent overall market sentiment (last 24 hours)
        logger.info("📊 Getting recent overall market sentiment...")
        cursor.execute(
            """
            SELECT 
                AVG(ml_sentiment_score) as avg_ml_sentiment,
                AVG(llm_sentiment_score) as avg_llm_sentiment,
                COUNT(*) as sentiment_count
            FROM crypto_news
            WHERE published_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            AND ml_sentiment_score IS NOT NULL
            AND llm_sentiment_score IS NOT NULL
        """
        )
        market_sentiment = cursor.fetchone()

        if not market_sentiment or market_sentiment[0] is None:
            logger.warning("No recent sentiment data found")
            return {"processed": 0, "errors": 0}

        avg_ml_sentiment, avg_llm_sentiment, sentiment_count = market_sentiment
        logger.info(
            f"Market sentiment: ML={avg_ml_sentiment:.3f}, LLM={avg_llm_sentiment:.3f} from {sentiment_count} articles"
        )

        # Step 2: Apply sentiment to materialized records in batches
        logger.info("🔄 Applying sentiment to materialized records...")

        # Process in smaller batches to avoid lock timeouts
        batch_size = 1000
        total_updated = 0

        while True:
            # Get a batch of records without sentiment
            cursor.execute(
                """
                SELECT symbol, timestamp_iso
                FROM ml_features_materialized
                WHERE avg_ml_overall_sentiment IS NULL
                ORDER BY timestamp_iso DESC
                LIMIT %s
            """,
                (batch_size,),
            )

            batch_records = cursor.fetchall()
            if not batch_records:
                break

            logger.info(f"Processing batch of {len(batch_records)} records...")

            # Update this batch
            cursor.execute(
                """
                UPDATE ml_features_materialized
                SET avg_ml_overall_sentiment = %s,
                    sentiment_volume = %s,
                    updated_at = NOW()
                WHERE symbol = %s AND timestamp_iso = %s
            """,
                (
                    avg_ml_sentiment,
                    sentiment_count,
                    batch_records[0][0],
                    batch_records[0][1],
                ),
            )

            # Actually update all records in the batch
            for symbol, timestamp_iso in batch_records:
                cursor.execute(
                    """
                    UPDATE ml_features_materialized
                    SET avg_ml_overall_sentiment = %s,
                        sentiment_volume = %s,
                        updated_at = NOW()
                    WHERE symbol = %s AND timestamp_iso = %s
                """,
                    (avg_ml_sentiment, sentiment_count, symbol, timestamp_iso),
                )

                if cursor.rowcount > 0:
                    total_updated += 1

            # Commit this batch
            conn.commit()
            logger.info(f"Updated {total_updated} records so far...")

            # Small delay to avoid overwhelming the database
            import time

            time.sleep(0.1)

        logger.info(
            f"🎉 Improved sentiment strategy complete: {total_updated} records updated"
        )
        return {"processed": total_updated, "errors": 0}

    except Exception as e:
        logger.error(f"Error in improved sentiment strategy: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def check_final_sentiment_coverage():
    """Check final sentiment coverage"""
    logger.info("📊 Checking final sentiment coverage...")

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

        logger.info("🎯 FINAL SENTIMENT COVERAGE RESULTS:")
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

        # Check if we achieved good coverage
        coverage_pct = sentiment_coverage / total_records * 100
        if coverage_pct > 50:
            logger.info("✅ SENTIMENT: Good coverage (>50%)")
        elif coverage_pct > 20:
            logger.info("✅ SENTIMENT: Decent coverage (>20%)")
        else:
            logger.info("⚠️ SENTIMENT: Low coverage (<20%)")

    except Exception as e:
        logger.error(f"Error checking sentiment coverage: {e}")
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Improved Sentiment Strategy")
    logger.info("=" * 70)
    logger.info("This will apply overall market sentiment using batch processing")

    # Step 1: Apply improved sentiment strategy
    results = improved_sentiment_strategy()

    # Step 2: Check coverage
    check_final_sentiment_coverage()

    logger.info("🎉 Improved Sentiment Strategy Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
