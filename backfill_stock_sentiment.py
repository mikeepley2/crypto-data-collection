#!/usr/bin/env python3
"""
Stock Sentiment Backfill Script
Backfills stock sentiment data into the materialized table
"""

import mysql.connector
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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


def backfill_stock_sentiment():
    """Backfill stock sentiment data into materialized table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting stock sentiment backfill...")

        # Get stock articles with sentiment scores
        cursor.execute(
            """
        SELECT 
            published_at,
            ml_sentiment_score,
            market_type
        FROM crypto_news
        WHERE market_type = 'stock'
        AND ml_sentiment_score IS NOT NULL
        AND published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY published_at DESC
        """
        )
        stock_articles = cursor.fetchall()

        logger.info(f"Found {len(stock_articles)} stock articles with sentiment scores")

        if len(stock_articles) == 0:
            logger.warning("No stock articles with sentiment scores found!")
            return

        # Get all symbols from materialized table that need stock sentiment
        cursor.execute(
            """
        SELECT DISTINCT symbol, timestamp_iso
        FROM ml_features_materialized
        WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND (avg_ml_stock_sentiment IS NULL OR avg_ml_stock_sentiment = 0)
        ORDER BY symbol, timestamp_iso
        """
        )
        materialized_records = cursor.fetchall()

        logger.info(
            f"Found {len(materialized_records)} materialized records needing stock sentiment"
        )

        updated_count = 0

        for symbol, timestamp_iso in materialized_records:
            try:
                # Get stock sentiment for this time period (last 24 hours from timestamp)
                cursor.execute(
                    """
                SELECT 
                    AVG(ml_sentiment_score) as avg_stock_sentiment,
                    COUNT(*) as sentiment_count
                FROM crypto_news
                WHERE market_type = 'stock'
                AND ml_sentiment_score IS NOT NULL
                AND published_at >= DATE_SUB(%s, INTERVAL 24 HOUR)
                AND published_at <= %s
                """,
                    (timestamp_iso, timestamp_iso),
                )

                sentiment_data = cursor.fetchone()
                avg_stock_sentiment, sentiment_count = sentiment_data

                if avg_stock_sentiment is not None and sentiment_count > 0:
                    # Update materialized table with stock sentiment
                    cursor.execute(
                        """
                    UPDATE ml_features_materialized 
                    SET avg_ml_stock_sentiment = %s,
                        updated_at = NOW()
                    WHERE symbol = %s 
                    AND timestamp_iso = %s
                    """,
                        (avg_stock_sentiment, symbol, timestamp_iso),
                    )

                    if cursor.rowcount > 0:
                        updated_count += cursor.rowcount

            except Exception as e:
                logger.error(f"Error processing {symbol} at {timestamp_iso}: {e}")
                continue

        conn.commit()
        logger.info(f"Stock sentiment backfill completed!")
        logger.info(f"Updated {updated_count} records with stock sentiment")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error in stock sentiment backfill: {e}")


if __name__ == "__main__":
    backfill_stock_sentiment()
