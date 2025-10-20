#!/usr/bin/env python3
"""
Comprehensive ML Sentiment Backfill Script

This script processes all articles across both databases and populates
the existing sentiment tables with ML sentiment analysis using FinBERT and CryptoBERT.
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
logger = logging.getLogger("comprehensive_ml_backfill")

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

CRYPTO_PRICES_DB = {
    "host": "host.docker.internal",
    "port": 3306,
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
    "autocommit": True,
}


def get_db_connection(database="crypto_news"):
    """Get database connection"""
    config = CRYPTO_NEWS_DB if database == "crypto_news" else CRYPTO_PRICES_DB
    try:
        return mysql.connector.connect(**config)
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None


def analyze_sentiment_with_ml(text, market_type="crypto"):
    """Analyze sentiment using the ML service"""
    try:
        payload = {"text": text, "market_type": market_type}
        response = requests.post(
            f"{SENTIMENT_SERVICE_URL}/sentiment", json=payload, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "ml_sentiment_score": result.get("sentiment_score", 0.0),
                "ml_sentiment_confidence": result.get("confidence", 0.0),
                "ml_sentiment_analysis": result.get("analysis", ""),
                "market_type": market_type,
            }
        else:
            logger.error(f"❌ Sentiment analysis failed: {response.status_code}")
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


def process_crypto_news_table():
    """Process crypto_news table in crypto_news database"""
    logger.info("🔄 Processing crypto_news table in crypto_news database")

    conn = get_db_connection("crypto_news")
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor(dictionary=True)

        # Get articles that need ML sentiment
        query = """
        SELECT article_id, title, content, published_at
        FROM crypto_news
        WHERE article_id NOT IN (
            SELECT DISTINCT article_id 
            FROM crypto_sentiment_data 
            WHERE cryptobert_score IS NOT NULL
        )
        ORDER BY published_at DESC
        LIMIT 100
        """

        cursor.execute(query)
        articles = cursor.fetchall()

        logger.info(
            f"📊 Found {len(articles)} articles needing ML sentiment in crypto_news"
        )

        processed = 0
        errors = 0

        for article in articles:
            try:
                # Prepare text
                text = article["title"]
                if article["content"]:
                    text += f" {article['content']}"

                # Detect market type
                market_type = detect_market_type(text)

                # Analyze sentiment
                sentiment_data = analyze_sentiment_with_ml(text, market_type)

                if sentiment_data:
                    # Insert into crypto_sentiment_data table
                    insert_query = """
                    INSERT INTO crypto_sentiment_data 
                    (text_id, timestamp, text, sentiment_score, sentiment_label, confidence, 
                     method, data_type, article_id, collection_source, created_at, 
                     cryptobert_score, cryptobert_confidence, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(
                        insert_query,
                        (
                            f"ml_{article['article_id']}",
                            int(time.time()),
                            text[:1000],  # Truncate for storage
                            sentiment_data["ml_sentiment_score"],
                            (
                                "positive"
                                if sentiment_data["ml_sentiment_score"] > 0
                                else "negative"
                            ),
                            sentiment_data["ml_sentiment_confidence"],
                            "ml_cryptobert",
                            "news",
                            article["article_id"],
                            "ml_backfill",
                            datetime.now(),
                            sentiment_data["ml_sentiment_score"],
                            sentiment_data["ml_sentiment_confidence"],
                            article["published_at"],
                        ),
                    )

                    processed += 1
                    if processed % 10 == 0:
                        logger.info(
                            f"✅ Processed {processed} articles from crypto_news"
                        )
                else:
                    errors += 1

            except Exception as e:
                logger.error(
                    f"❌ Error processing article {article['article_id']}: {e}"
                )
                errors += 1

        return {"processed": processed, "errors": errors}

    except Exception as e:
        logger.error(f"❌ Error in process_crypto_news_table: {e}")
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def process_news_data_table():
    """Process news_data table in crypto_news database"""
    logger.info("🔄 Processing news_data table in crypto_news database")

    conn = get_db_connection("crypto_news")
    if not conn:
        return {"processed": 0, "errors": 0}

    try:
        cursor = conn.cursor(dictionary=True)

        # Get articles that need ML sentiment
        query = """
        SELECT id, title, content
        FROM news_data
        WHERE id NOT IN (
            SELECT DISTINCT article_id 
            FROM crypto_sentiment_data 
            WHERE cryptobert_score IS NOT NULL
        )
        ORDER BY id DESC
        LIMIT 100
        """

        cursor.execute(query)
        articles = cursor.fetchall()

        logger.info(
            f"📊 Found {len(articles)} articles needing ML sentiment in news_data"
        )

        processed = 0
        errors = 0

        for article in articles:
            try:
                # Prepare text
                text = article["title"]
                if article["content"]:
                    text += f" {article['content']}"

                # Detect market type
                market_type = detect_market_type(text)

                # Analyze sentiment
                sentiment_data = analyze_sentiment_with_ml(text, market_type)

                if sentiment_data:
                    # Insert into crypto_sentiment_data table
                    insert_query = """
                    INSERT INTO crypto_sentiment_data 
                    (text_id, timestamp, text, sentiment_score, sentiment_label, confidence, 
                     method, data_type, article_id, collection_source, created_at, 
                     cryptobert_score, cryptobert_confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(
                        insert_query,
                        (
                            f"ml_news_{article['id']}",
                            int(time.time()),
                            text[:1000],  # Truncate for storage
                            sentiment_data["ml_sentiment_score"],
                            (
                                "positive"
                                if sentiment_data["ml_sentiment_score"] > 0
                                else "negative"
                            ),
                            sentiment_data["ml_sentiment_confidence"],
                            "ml_cryptobert",
                            "news",
                            str(article["id"]),
                            "ml_backfill",
                            datetime.now(),
                            sentiment_data["ml_sentiment_score"],
                            sentiment_data["ml_sentiment_confidence"],
                        ),
                    )

                    processed += 1
                    if processed % 10 == 0:
                        logger.info(f"✅ Processed {processed} articles from news_data")
                else:
                    errors += 1

            except Exception as e:
                logger.error(f"❌ Error processing article {article['id']}: {e}")
                errors += 1

        return {"processed": processed, "errors": errors}

    except Exception as e:
        logger.error(f"❌ Error in process_news_data_table: {e}")
        return {"processed": 0, "errors": 1}
    finally:
        if conn:
            conn.close()


def run_comprehensive_backfill():
    """Run comprehensive ML sentiment backfill"""
    logger.info("🚀 Starting Comprehensive ML Sentiment Backfill")

    # Check service health
    try:
        response = requests.get(f"{SENTIMENT_SERVICE_URL}/health", timeout=10)
        if response.status_code != 200:
            logger.error("❌ Sentiment service is not healthy")
            return
        logger.info("✅ Sentiment service is healthy")
    except Exception as e:
        logger.error(f"❌ Cannot connect to sentiment service: {e}")
        return

    total_stats = {"processed": 0, "errors": 0}

    # Process different tables
    tables_to_process = [
        ("crypto_news", process_crypto_news_table),
        ("news_data", process_news_data_table),
    ]

    for table_name, process_func in tables_to_process:
        logger.info(f"📦 Processing {table_name} table")
        stats = process_func()

        total_stats["processed"] += stats["processed"]
        total_stats["errors"] += stats["errors"]

        logger.info(f"📊 {table_name} complete: {stats}")
        logger.info(f"📊 Total progress: {total_stats}")

        # Small delay between tables
        time.sleep(2)

    logger.info(f"🎉 Comprehensive ML Sentiment Backfill Complete!")
    logger.info(f"📊 Final stats: {total_stats}")


if __name__ == "__main__":
    run_comprehensive_backfill()
