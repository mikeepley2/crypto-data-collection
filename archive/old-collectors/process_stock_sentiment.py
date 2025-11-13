#!/usr/bin/env python3
"""
Process Stock Sentiment Script
Manually processes stock articles for sentiment analysis
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


def process_stock_articles():
    """Process stock articles for sentiment analysis"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting stock sentiment processing...")

        # Get stock articles that need sentiment processing
        cursor.execute(
            """
        SELECT id, title, content, published_at
        FROM crypto_news
        WHERE market_type = 'stock'
        AND (ml_sentiment_score IS NULL OR ml_sentiment_score = 0)
        AND published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY published_at DESC
        """
        )
        stock_articles = cursor.fetchall()

        logger.info(
            f"Found {len(stock_articles)} stock articles needing sentiment processing"
        )

        if len(stock_articles) == 0:
            logger.warning("No stock articles found for processing!")
            return

        processed_count = 0

        for article_id, title, content, published_at in stock_articles:
            try:
                # For now, let's assign a basic sentiment score based on keywords
                # This is a simplified approach - in production, you'd use the ML models

                text = f"{title} {content or ''}".lower()

                # Simple keyword-based sentiment analysis
                positive_keywords = [
                    "bullish",
                    "positive",
                    "growth",
                    "profit",
                    "gain",
                    "rise",
                    "up",
                    "strong",
                    "excellent",
                    "good",
                    "benefit",
                    "success",
                    "win",
                    "increase",
                    "surge",
                ]
                negative_keywords = [
                    "bearish",
                    "negative",
                    "decline",
                    "loss",
                    "fall",
                    "down",
                    "weak",
                    "poor",
                    "bad",
                    "risk",
                    "failure",
                    "lose",
                    "decrease",
                    "crash",
                ]

                positive_count = sum(
                    1 for keyword in positive_keywords if keyword in text
                )
                negative_count = sum(
                    1 for keyword in negative_keywords if keyword in text
                )

                # Calculate sentiment score (-1 to 1)
                if positive_count > negative_count:
                    sentiment_score = min(
                        0.8, 0.2 + (positive_count - negative_count) * 0.1
                    )
                elif negative_count > positive_count:
                    sentiment_score = max(
                        -0.8, -0.2 - (negative_count - positive_count) * 0.1
                    )
                else:
                    sentiment_score = 0.0

                confidence = min(0.9, 0.5 + abs(positive_count - negative_count) * 0.1)
                analysis = f"Keyword-based analysis: {positive_count} positive, {negative_count} negative keywords"

                # Update database with sentiment scores
                cursor.execute(
                    """
                UPDATE crypto_news 
                SET ml_sentiment_score = %s,
                    ml_sentiment_confidence = %s,
                    ml_sentiment_analysis = %s,
                    sentiment_updated_at = NOW()
                WHERE id = %s
                """,
                    (sentiment_score, confidence, analysis, article_id),
                )

                processed_count += 1
                logger.info(
                    f"Processed article {article_id}: sentiment {sentiment_score:.3f}"
                )

            except Exception as e:
                logger.error(f"Error processing article {article_id}: {e}")
                continue

        conn.commit()
        logger.info(f"Stock sentiment processing completed!")
        logger.info(f"Processed {processed_count} articles")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error in stock sentiment processing: {e}")


if __name__ == "__main__":
    process_stock_articles()




