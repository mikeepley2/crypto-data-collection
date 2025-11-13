#!/usr/bin/env python3
"""
Efficient Sentiment Update
Use single SQL UPDATE to avoid lock timeouts
"""

import mysql.connector
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("efficient_sentiment")


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


def efficient_sentiment_update():
    """
    Efficient sentiment update using single SQL statement
    """
    logger.info("🚀 Starting Efficient Sentiment Update...")

    conn = get_db_connection()
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor()

        # Get recent market sentiment
        logger.info("📊 Getting recent market sentiment...")
        cursor.execute(
            """
            SELECT 
                AVG(ml_sentiment_score) as avg_ml_sentiment,
                COUNT(*) as sentiment_count
            FROM crypto_news
            WHERE published_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            AND ml_sentiment_score IS NOT NULL
        """
        )
        market_sentiment = cursor.fetchone()

        if not market_sentiment or market_sentiment[0] is None:
            logger.warning("No recent sentiment data found")
            return {"processed": 0, "errors": 0}

        avg_ml_sentiment, sentiment_count = market_sentiment
        logger.info(
            f"Market sentiment: ML={avg_ml_sentiment:.3f} from {sentiment_count} articles"
        )

        # Single efficient UPDATE for all records without sentiment
        logger.info("🔄 Applying sentiment to all records without sentiment data...")
        cursor.execute(
            """
            UPDATE ml_features_materialized
            SET avg_ml_overall_sentiment = %s,
                sentiment_volume = %s,
                updated_at = NOW()
            WHERE avg_ml_overall_sentiment IS NULL
        """,
            (avg_ml_sentiment, sentiment_count),
        )

        updated_count = cursor.rowcount
        conn.commit()

        logger.info(
            f"🎉 Efficient sentiment update complete: {updated_count} records updated"
        )
        return {"processed": updated_count, "errors": 0}

    except Exception as e:
        logger.error(f"Error in efficient sentiment update: {e}")
        conn.rollback()
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def check_final_coverage():
    """Check final coverage"""
    logger.info("📊 Checking final coverage...")

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

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE active_addresses_24h IS NOT NULL"
        )
        onchain_coverage = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE sma_20 IS NOT NULL"
        )
        technical_coverage = cursor.fetchone()[0]

        logger.info("🎯 FINAL COVERAGE RESULTS:")
        logger.info(f"   Total records: {total_records:,}")
        logger.info(
            f"   Sentiment coverage: {sentiment_coverage:,} ({sentiment_coverage/total_records*100:.1f}%)"
        )
        logger.info(
            f"   Onchain coverage: {onchain_coverage:,} ({onchain_coverage/total_records*100:.1f}%)"
        )
        logger.info(
            f"   Technical coverage: {technical_coverage:,} ({technical_coverage/total_records*100:.1f}%)"
        )

        # Overall system health
        if sentiment_coverage / total_records > 0.5:
            logger.info("✅ SENTIMENT: Excellent coverage (>50%)")
        elif sentiment_coverage / total_records > 0.2:
            logger.info("✅ SENTIMENT: Good coverage (>20%)")
        else:
            logger.info("⚠️ SENTIMENT: Low coverage (<20%)")

        if onchain_coverage / total_records > 0.5:
            logger.info("✅ ONCHAIN: Excellent coverage (>50%)")
        else:
            logger.info("⚠️ ONCHAIN: Low coverage (<50%)")

        if technical_coverage / total_records > 0.8:
            logger.info("✅ TECHNICAL: Excellent coverage (>80%)")
        else:
            logger.info("⚠️ TECHNICAL: Low coverage (<80%)")

    except Exception as e:
        logger.error(f"Error checking coverage: {e}")
    finally:
        if conn:
            conn.close()


def main():
    logger.info("🚀 Starting Efficient Sentiment Update")
    logger.info("=" * 70)
    logger.info(
        "This will apply overall market sentiment using a single efficient SQL update"
    )

    # Step 1: Apply efficient sentiment update
    results = efficient_sentiment_update()

    # Step 2: Check coverage
    check_final_coverage()

    logger.info("🎉 Efficient Sentiment Update Complete!")
    logger.info(
        f"📊 Results: {results['processed']} records updated, {results['errors']} errors"
    )


if __name__ == "__main__":
    main()
