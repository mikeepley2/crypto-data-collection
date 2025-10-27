#!/usr/bin/env python3
"""
Stock Sentiment Backfill Script
Processes all stock articles without sentiment scores using CryptoBERT and FinBERT
"""

import mysql.connector
import logging
import time
import os
from datetime import datetime
from transformers import pipeline
import torch

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


def load_sentiment_models():
    """Load CryptoBERT and FinBERT models"""
    logger.info("Loading sentiment models...")

    try:
        # Load CryptoBERT for crypto sentiment
        crypto_sentiment = pipeline(
            "sentiment-analysis",
            model="ElKulako/cryptobert",
            tokenizer="ElKulako/cryptobert",
            device=0 if torch.cuda.is_available() else -1,
        )
        logger.info("✅ CryptoBERT loaded successfully")
    except Exception as e:
        logger.error(f"❌ Error loading CryptoBERT: {e}")
        crypto_sentiment = None

    try:
        # Load FinBERT for financial sentiment
        fin_sentiment = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            device=0 if torch.cuda.is_available() else -1,
        )
        logger.info("✅ FinBERT loaded successfully")
    except Exception as e:
        logger.error(f"❌ Error loading FinBERT: {e}")
        fin_sentiment = None

    return crypto_sentiment, fin_sentiment


def analyze_sentiment(text, crypto_model, fin_model):
    """Analyze sentiment using both models"""
    if not text or len(text.strip()) < 10:
        return None, None, None

    crypto_score = None
    fin_score = None
    combined_score = None

    try:
        # CryptoBERT analysis
        if crypto_model:
            crypto_result = crypto_model(text[:512])  # Limit text length
            crypto_score = (
                crypto_result[0]["score"]
                if crypto_result[0]["label"] == "POSITIVE"
                else -crypto_result[0]["score"]
            )
    except Exception as e:
        logger.warning(f"CryptoBERT error: {e}")

    try:
        # FinBERT analysis
        if fin_model:
            fin_result = fin_model(text[:512])  # Limit text length
            fin_score = (
                fin_result[0]["score"]
                if fin_result[0]["label"] == "POSITIVE"
                else -fin_result[0]["score"]
            )
    except Exception as e:
        logger.warning(f"FinBERT error: {e}")

    # Combine scores (weighted average)
    if crypto_score is not None and fin_score is not None:
        combined_score = (
            crypto_score * 0.6 + fin_score * 0.4
        )  # CryptoBERT gets more weight
    elif crypto_score is not None:
        combined_score = crypto_score
    elif fin_score is not None:
        combined_score = fin_score

    return crypto_score, fin_score, combined_score


def backfill_stock_sentiment():
    """Backfill sentiment for all stock articles"""
    logger.info("🚀 Starting Stock Sentiment Backfill")
    logger.info("=" * 60)

    # Load models
    crypto_model, fin_model = load_sentiment_models()

    if not crypto_model and not fin_model:
        logger.error("❌ No sentiment models available!")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all stock articles without sentiment
        cursor.execute(
            """
        SELECT id, title, content, published_at, source
        FROM crypto_news 
        WHERE market_type = 'stock' 
        AND ml_sentiment_score IS NULL
        ORDER BY published_at DESC
        """
        )

        articles = cursor.fetchall()
        total_articles = len(articles)
        logger.info(f"📊 Found {total_articles:,} stock articles without sentiment")

        if total_articles == 0:
            logger.info("✅ All stock articles already have sentiment scores!")
            return

        processed = 0
        updated = 0
        errors = 0

        for article_id, title, content, published_at, source in articles:
            try:
                # Combine title and content for analysis
                full_text = f"{title}\n\n{content}" if content else title

                # Analyze sentiment
                crypto_score, fin_score, combined_score = analyze_sentiment(
                    full_text, crypto_model, fin_model
                )

                if combined_score is not None:
                    # Update the article with sentiment scores
                    cursor.execute(
                        """
                    UPDATE crypto_news 
                    SET ml_sentiment_score = %s,
                        ml_sentiment_confidence = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                        (combined_score, abs(combined_score), article_id),
                    )

                    updated += 1
                else:
                    logger.warning(f"No sentiment score for article {article_id}")

                processed += 1

                # Progress reporting
                if processed % 100 == 0:
                    logger.info(
                        f"  Processed {processed:,}/{total_articles:,} articles, Updated: {updated:,}"
                    )
                    conn.commit()  # Commit every 100 articles

                # Rate limiting
                time.sleep(0.1)  # Small delay to prevent overwhelming the system

            except Exception as e:
                logger.error(f"Error processing article {article_id}: {e}")
                errors += 1
                continue

        # Final commit
        conn.commit()

        logger.info("=" * 60)
        logger.info("🎉 STOCK SENTIMENT BACKFILL COMPLETED")
        logger.info(f"📊 Total articles processed: {processed:,}")
        logger.info(f"✅ Articles updated: {updated:,}")
        logger.info(f"❌ Errors: {errors:,}")
        logger.info(f"📈 Success rate: {updated/processed*100:.1f}%")

    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def check_backfill_results():
    """Check the results of the backfill"""
    logger.info("🔍 Checking backfill results...")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check current stock sentiment coverage
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total_stock_articles,
            COUNT(CASE WHEN ml_sentiment_score IS NOT NULL THEN 1 END) as with_sentiment,
            COUNT(CASE WHEN ml_sentiment_score != 0 THEN 1 END) as non_zero_sentiment,
            AVG(ml_sentiment_score) as avg_sentiment
        FROM crypto_news 
        WHERE market_type = 'stock'
        """
        )

        stats = cursor.fetchone()
        total, with_sentiment, non_zero, avg_sentiment = stats

        sentiment_coverage = with_sentiment / total * 100 if total > 0 else 0
        non_zero_coverage = non_zero / with_sentiment * 100 if with_sentiment > 0 else 0

        logger.info(f"📊 Stock Sentiment Coverage:")
        logger.info(f"  Total articles: {total:,}")
        logger.info(f"  With sentiment: {with_sentiment:,} ({sentiment_coverage:.1f}%)")
        logger.info(f"  Non-zero sentiment: {non_zero:,} ({non_zero_coverage:.1f}%)")
        logger.info(f"  Average sentiment: {avg_sentiment:.4f}")

        # Check recent activity
        cursor.execute(
            """
        SELECT COUNT(*) as recent_updated
        FROM crypto_news 
        WHERE market_type = 'stock' 
        AND ml_sentiment_score IS NOT NULL
        AND updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        )

        recent_updated = cursor.fetchone()[0]
        logger.info(f"  Recently updated (last hour): {recent_updated:,}")

    except Exception as e:
        logger.error(f"❌ Error checking results: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    logger.info("🚀 Starting Stock Sentiment Backfill Process")

    # Run the backfill
    backfill_stock_sentiment()

    # Check results
    check_backfill_results()

    logger.info("✅ Stock sentiment backfill process completed!")
