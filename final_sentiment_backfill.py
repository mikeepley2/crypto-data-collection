#!/usr/bin/env python3
"""
Final Sentiment Backfill Script

This script processes articles with proper datetime handling and text truncation
to work within the ML model's 512 token limit.
"""

import requests
import mysql.connector
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("final_sentiment_backfill")

# Configuration
SENTIMENT_SERVICE_URL = "http://localhost:8000"

# Database configurations
CRYPTO_NEWS_DB = {
    "host": "host.docker.internal",
    "port": 3306,
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_news",
    "autocommit": True,
}


def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**CRYPTO_NEWS_DB)
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None


def analyze_sentiment_with_ml(text, market_type="crypto"):
    """Analyze sentiment using the ML service"""
    try:
        # Truncate text to avoid 512 token limit (roughly 400 characters)
        text = text[:400]  # Conservative limit to stay under 512 tokens

        payload = {"text": text, "market_type": market_type}
        response = requests.post(
            f"{SENTIMENT_SERVICE_URL}/sentiment", json=payload, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "sentiment_score": result.get("sentiment_score", 0.0),
                "confidence": result.get("confidence", 0.0),
                "analysis": result.get("analysis", ""),
                "market_type": market_type,
            }
        else:
            logger.error(
                f"❌ Sentiment analysis failed: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        logger.error(f"❌ Error analyzing sentiment: {e}")
        return None


def detect_market_type(text):
    """Detect if text is about crypto or stock market"""
    text_lower = text.lower()

    crypto_keywords = [
        "bitcoin",
        "btc",
        "ethereum",
        "eth",
        "cryptocurrency",
        "crypto",
        "blockchain",
        "altcoin",
        "defi",
        "nft",
        "mining",
        "wallet",
    ]
    stock_keywords = [
        "stock",
        "stocks",
        "nasdaq",
        "nyse",
        "s&p",
        "dow jones",
        "equity",
        "dividend",
        "earnings",
        "revenue",
        "profit",
    ]

    crypto_count = sum(1 for keyword in crypto_keywords if keyword in text_lower)
    stock_count = sum(1 for keyword in stock_keywords if keyword in text_lower)

    return "crypto" if crypto_count > stock_count else "stock"


def convert_timestamp_to_datetime(timestamp):
    """Convert Unix timestamp to proper datetime format"""
    try:
        if isinstance(timestamp, (int, float)):
            # Handle Unix timestamps
            if timestamp > 1000000000:  # Unix timestamp in seconds
                return datetime.fromtimestamp(timestamp)
            else:  # Unix timestamp in milliseconds
                return datetime.fromtimestamp(timestamp / 1000)
        elif isinstance(timestamp, str):
            # Try to parse as Unix timestamp
            try:
                ts = float(timestamp)
                if ts > 1000000000:
                    return datetime.fromtimestamp(ts)
                else:
                    return datetime.fromtimestamp(ts / 1000)
            except ValueError:
                # If not a number, try to parse as datetime string
                return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            return datetime.now()
    except Exception as e:
        logger.warning(f"⚠️ Could not convert timestamp {timestamp}: {e}")
        return datetime.now()


def update_existing_sentiment_records():
    """Update existing sentiment records with improved ML models"""
    logger.info("🔄 Updating existing sentiment records with improved ML models...")

    conn = get_db_connection()
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor(dictionary=True)

        # Get sentiment records that need updating (focus on recent ones without ML sentiment)
        query = """
        SELECT text_id, article_id, text, cryptobert_score, ml_sentiment_score
        FROM crypto_sentiment_data 
        WHERE text IS NOT NULL
        AND LENGTH(text) > 10
        AND (ml_sentiment_score IS NULL OR cryptobert_score IS NULL)
        ORDER BY timestamp DESC
        LIMIT 50
        """

        cursor.execute(query)
        records = cursor.fetchall()

        logger.info(
            f"📊 Found {len(records)} sentiment records needing ML model updates"
        )

        if len(records) == 0:
            logger.info("✅ All sentiment records already have ML model scores!")
            return {"processed": 0, "errors": 0}

        processed = 0
        errors = 0

        for i, record in enumerate(records):
            try:
                logger.info(
                    f"🔄 Processing {i+1}/{len(records)}: {record['text_id'][:50]}..."
                )

                # Detect market type
                market_type = detect_market_type(record["text"])
                logger.info(f"   Market type: {market_type}")

                # Analyze sentiment with appropriate model
                logger.info(f"   Analyzing sentiment with {market_type} model...")
                sentiment_data = analyze_sentiment_with_ml(record["text"], market_type)

                if sentiment_data:
                    # Update the record with ML sentiment data
                    update_query = """
                    UPDATE crypto_sentiment_data 
                    SET ml_sentiment_score = %s,
                        ml_sentiment_confidence = %s,
                        ml_sentiment_analysis = %s,
                        ml_market_type = %s,
                        cryptobert_score = %s,
                        cryptobert_confidence = %s,
                        sentiment_score = %s,
                        sentiment_label = %s,
                        confidence = %s
                    WHERE text_id = %s
                    """

                    cursor.execute(
                        update_query,
                        (
                            sentiment_data["sentiment_score"],
                            sentiment_data["confidence"],
                            sentiment_data["analysis"],
                            sentiment_data["market_type"],
                            sentiment_data[
                                "sentiment_score"
                            ],  # Use same score for cryptobert
                            sentiment_data[
                                "confidence"
                            ],  # Use same confidence for cryptobert
                            sentiment_data["sentiment_score"],
                            (
                                "positive"
                                if sentiment_data["sentiment_score"] > 0
                                else "negative"
                            ),
                            sentiment_data["confidence"],
                            record["text_id"],
                        ),
                    )

                    processed += 1
                    logger.info(
                        f"   ✅ Updated {market_type} sentiment: {sentiment_data['sentiment_score']:.3f} (confidence: {sentiment_data['confidence']:.3f})"
                    )
                else:
                    errors += 1
                    logger.error(f"   ❌ Failed to analyze sentiment")

            except Exception as e:
                logger.error(f"❌ Error processing record {record['text_id']}: {e}")
                errors += 1

        return {"processed": processed, "errors": errors}

    except Exception as e:
        logger.error(f"❌ Error in update_existing_sentiment_records: {e}")
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def process_new_articles():
    """Process new articles that don't have any sentiment data yet"""
    logger.info("🔄 Processing new articles without sentiment data...")

    conn = get_db_connection()
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor(dictionary=True)

        # Get articles from crypto_news that don't have sentiment data
        query = """
        SELECT cn.article_id, cn.title, cn.content, cn.published_at
        FROM crypto_news cn
        WHERE cn.article_id NOT IN (
            SELECT DISTINCT article_id 
            FROM crypto_sentiment_data 
            WHERE article_id IS NOT NULL
        )
        ORDER BY cn.published_at DESC
        LIMIT 20
        """

        cursor.execute(query)
        articles = cursor.fetchall()

        logger.info(f"📊 Found {len(articles)} new articles needing sentiment analysis")

        if len(articles) == 0:
            logger.info("✅ All articles already have sentiment data!")
            return {"processed": 0, "errors": 0}

        processed = 0
        errors = 0

        for i, article in enumerate(articles):
            try:
                logger.info(
                    f"🔄 Processing new article {i+1}/{len(articles)}: {article['article_id']}"
                )

                # Prepare text
                text = article["title"]
                if article["content"]:
                    text += f" {article['content']}"

                logger.info(f"   Text length: {len(text)} characters")

                # Detect market type
                market_type = detect_market_type(text)
                logger.info(f"   Market type: {market_type}")

                # Analyze sentiment
                logger.info(f"   Analyzing sentiment...")
                sentiment_data = analyze_sentiment_with_ml(text, market_type)

                if sentiment_data:
                    # Convert published_at to proper datetime format
                    published_at = convert_timestamp_to_datetime(
                        article["published_at"]
                    )

                    # Insert new sentiment record using existing structure
                    insert_query = """
                    INSERT INTO crypto_sentiment_data 
                    (text_id, timestamp, text, sentiment_score, sentiment_label, confidence, 
                     method, data_type, article_id, collection_source, created_at, 
                     cryptobert_score, cryptobert_confidence, published_at,
                     ml_sentiment_score, ml_sentiment_confidence, ml_sentiment_analysis, ml_market_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(
                        insert_query,
                        (
                            f"ml_new_{article['article_id']}",
                            int(time.time()),
                            text[:1000],  # Truncate for storage
                            sentiment_data["sentiment_score"],
                            (
                                "positive"
                                if sentiment_data["sentiment_score"] > 0
                                else "negative"
                            ),
                            sentiment_data["confidence"],
                            f"ml_{market_type}",
                            "news",
                            article["article_id"],
                            "ml_backfill",
                            datetime.now(),
                            sentiment_data[
                                "sentiment_score"
                            ],  # Use same score for cryptobert
                            sentiment_data[
                                "confidence"
                            ],  # Use same confidence for cryptobert
                            published_at,  # Use converted datetime
                            sentiment_data["sentiment_score"],
                            sentiment_data["confidence"],
                            sentiment_data["analysis"],
                            sentiment_data["market_type"],
                        ),
                    )

                    processed += 1
                    logger.info(
                        f"   ✅ {market_type} sentiment: {sentiment_data['sentiment_score']:.3f} (confidence: {sentiment_data['confidence']:.3f})"
                    )
                else:
                    errors += 1
                    logger.error(f"   ❌ Failed to analyze sentiment")

            except Exception as e:
                logger.error(
                    f"❌ Error processing article {article['article_id']}: {e}"
                )
                errors += 1

        return {"processed": processed, "errors": errors}

    except Exception as e:
        logger.error(f"❌ Error in process_new_articles: {e}")
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def run_final_sentiment_backfill():
    """Run final sentiment score updates"""
    logger.info("🚀 Starting Final Sentiment Score Updates")

    # Check service health
    try:
        response = requests.get(f"{SENTIMENT_SERVICE_URL}/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Sentiment service is not healthy")
            return
        logger.info("✅ Sentiment service is healthy")
    except Exception as e:
        logger.error(f"❌ Cannot connect to sentiment service: {e}")
        return

    total_stats = {"processed": 0, "errors": 0}

    # Update existing sentiment records
    logger.info("📦 Updating existing sentiment records...")
    stats1 = update_existing_sentiment_records()
    total_stats["processed"] += stats1["processed"]
    total_stats["errors"] += stats1["errors"]
    logger.info(f"📊 Existing records complete: {stats1}")

    # Process new articles
    logger.info("📦 Processing new articles...")
    stats2 = process_new_articles()
    total_stats["processed"] += stats2["processed"]
    total_stats["errors"] += stats2["errors"]
    logger.info(f"📊 New articles complete: {stats2}")

    logger.info(f"🎉 Final Sentiment Score Updates Complete!")
    logger.info(f"📊 Final stats: {total_stats}")


if __name__ == "__main__":
    run_final_sentiment_backfill()


