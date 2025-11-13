#!/usr/bin/env python3
"""
Enhanced LLM-based Sentiment Analysis Service

This service provides advanced sentiment analysis using LLM (OpenAI) for both
crypto and stock market news, with separate sentiment tracking for each market type.
"""

import os
import sys
import logging
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import mysql.connector
from mysql.connector import pooling

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("enhanced_llm_sentiment")

# Configuration
ENABLE_LLM_SENTIMENT = os.getenv("ENABLE_LLM_SENTIMENT", "false").lower() in [
    "true",
    "1",
    "yes",
]


# FastAPI models
class SentimentRequest(BaseModel):
    article_id: Optional[int] = None
    text: Optional[str] = None
    market_type: Optional[str] = None  # 'crypto' or 'stock'


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    ollama_available: bool
    database_connected: bool


# Initialize FastAPI app
app = FastAPI(
    title="Enhanced LLM Sentiment Analysis",
    description="Advanced sentiment analysis using LLM for crypto and stock market news",
    version="2.0.0",
)

# Database connection pool
db_pool = None


def init_database_pool():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="sentiment_pool",
            pool_size=5,
            pool_reset_session=True,
            host=os.getenv("MYSQL_HOST", "host.docker.internal"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
            autocommit=True,
        )
        logger.info("✅ Database connection pool initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Database pool initialization failed: {e}")
        return False


def get_db_connection():
    """Get database connection from pool"""
    try:
        return db_pool.get_connection()
    except Exception as e:
        logger.error(f"❌ Failed to get database connection: {e}")
        return None


def detect_market_type(text: str) -> str:
    """
    Detect if the text is about crypto or stock market

    Args:
        text: The text to analyze

    Returns:
        'crypto' or 'stock'
    """
    text_lower = text.lower()

    # Crypto keywords
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
        "exchange",
        "binance",
        "coinbase",
        "dogecoin",
        "doge",
        "solana",
        "sol",
        "cardano",
        "ada",
        "polkadot",
        "dot",
        "chainlink",
        "link",
        "uniswap",
        "pancakeswap",
        "yield farming",
        "staking",
        "metamask",
        "ledger",
        "trezor",
        "hodl",
        "diamond hands",
        "moon",
        "pump",
        "dump",
        "fud",
        "fomo",
        "rekt",
        "rug pull",
        "whale",
        "bullish",
        "bearish",
    ]

    # Stock market keywords
    stock_keywords = [
        "stock",
        "stocks",
        "equity",
        "equities",
        "nasdaq",
        "nyse",
        "s&p",
        "dow jones",
        "trading",
        "investor",
        "portfolio",
        "dividend",
        "earnings",
        "revenue",
        "profit",
        "market cap",
        "pe ratio",
        "analyst",
        "upgrade",
        "downgrade",
        "buy",
        "sell",
        "hold",
        "bull market",
        "bear market",
        "recession",
        "inflation",
        "fed",
        "federal reserve",
        "interest rate",
        "bond",
        "bonds",
        "treasury",
        "etf",
        "mutual fund",
        "hedge fund",
    ]

    # Count keyword matches
    crypto_count = sum(1 for keyword in crypto_keywords if keyword in text_lower)
    stock_count = sum(1 for keyword in stock_keywords if keyword in text_lower)

    # Determine market type based on keyword density
    if crypto_count > stock_count:
        return "crypto"
    elif stock_count > crypto_count:
        return "stock"
    else:
        # If equal or no matches, default to crypto for this system
        return "crypto"


async def analyze_sentiment_traditional(
    text: str, market_type: str
) -> Tuple[float, float, str]:
    """
    Analyze sentiment using traditional methods (TextBlob/VADER)

    Args:
        text: The text to analyze
        market_type: 'crypto' or 'stock'

    Returns:
        Tuple of (sentiment_score, confidence, analysis_text)
    """
    try:
        # Import traditional sentiment libraries
        from textblob import TextBlob
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        # Initialize VADER
        vader_analyzer = SentimentIntensityAnalyzer()

        # Analyze with TextBlob
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity  # -1 to 1
        textblob_subjectivity = blob.sentiment.subjectivity  # 0 to 1

        # Analyze with VADER
        vader_scores = vader_analyzer.polarity_scores(text)
        vader_compound = vader_scores["compound"]  # -1 to 1

        # Combine scores (weighted average)
        sentiment_score = textblob_polarity * 0.6 + vader_compound * 0.4

        # Calculate confidence (higher subjectivity = lower confidence)
        confidence = 1.0 - textblob_subjectivity

        # Generate analysis text
        if sentiment_score > 0.1:
            sentiment_label = "positive"
        elif sentiment_score < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        analysis_text = f"Traditional analysis: {sentiment_label} sentiment ({sentiment_score:.3f}) for {market_type} market"

        logger.info(
            f"Traditional sentiment analysis: {sentiment_score:.3f} (confidence: {confidence:.3f})"
        )

        return sentiment_score, confidence, analysis_text

    except ImportError:
        logger.error(
            "Traditional sentiment libraries not available, falling back to neutral sentiment"
        )
        return 0.0, 0.0, "Traditional sentiment analysis not available"
    except Exception as e:
        logger.error(f"Traditional sentiment analysis failed: {e}")
        return 0.0, 0.0, f"Analysis error: {str(e)}"


async def analyze_sentiment_with_llm(
    text: str, market_type: str
) -> Tuple[float, float, str]:
    """
    Analyze sentiment using Ollama LLM (if enabled) or fallback to traditional methods

    Args:
        text: The text to analyze
        market_type: 'crypto' or 'stock'

    Returns:
        Tuple of (sentiment_score, confidence, analysis_text)
    """
    # Check if LLM sentiment is enabled
    if not ENABLE_LLM_SENTIMENT:
        logger.info("LLM sentiment disabled, using traditional sentiment analysis")
        return await analyze_sentiment_traditional(text, market_type)

    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    model_name = os.getenv("OLLAMA_MODEL", "llama3.1")

    # Create market-specific prompt
    if market_type == "crypto":
        system_prompt = """You are a crypto sentiment analyst. Analyze the sentiment of crypto news text.

Return ONLY valid JSON in this exact format:
{"sentiment_score": -1.0 to 1.0, "confidence": 0.0 to 1.0, "analysis": "short explanation"}

Keep analysis under 50 words."""
    else:
        system_prompt = """You are a stock market sentiment analyst. Analyze the sentiment of stock market news text.

Return ONLY valid JSON in this exact format:
{"sentiment_score": -1.0 to 1.0, "confidence": 0.0 to 1.0, "analysis": "short explanation"}

Keep analysis under 50 words."""

    user_prompt = (
        f"Analyze the sentiment of this {market_type} market text:\n\n{text[:1000]}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
            }

            data = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                },
            }

            async with session.post(
                f"{ollama_url}/api/chat",
                headers=headers,
                json=data,
                timeout=120,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result["message"]["content"]

                    # Parse JSON response
                    try:
                        import json

                        # Try to fix truncated JSON by adding missing closing brace
                        if content.strip().endswith(
                            '"'
                        ) and not content.strip().endswith("}"):
                            content = content.strip() + "}"

                        sentiment_data = json.loads(content)
                        score = float(sentiment_data.get("sentiment_score", 0.0))
                        confidence = float(sentiment_data.get("confidence", 0.5))
                        analysis = sentiment_data.get(
                            "analysis", "No analysis provided"
                        )

                        # Ensure score is in [-1, 1] range
                        score = max(-1.0, min(1.0, score))
                        # Ensure confidence is in [0, 1] range
                        confidence = max(0.0, min(1.0, confidence))

                        logger.info(
                            f"✅ Ollama sentiment analysis: {score:.3f} (confidence: {confidence:.3f})"
                        )
                        return score, confidence, analysis
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.error(f"Failed to parse Ollama response: {e}")
                        logger.error(f"Raw response: {content}")
                        raise Exception(f"Invalid response format from Ollama: {e}")
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    raise Exception(f"Ollama API error: {response.status}")

    except Exception as e:
        logger.error(f"Ollama sentiment analysis failed: {e}")
        raise Exception(f"Ollama sentiment analysis failed: {e}")


async def process_news_article(article_id: int, conn) -> bool:
    """
    Process a single news article for LLM sentiment analysis

    Args:
        article_id: The article ID to process
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor(dictionary=True)

        # Get article data
        cursor.execute(
            """
            SELECT id, title, content, market_type, llm_sentiment_score, llm_sentiment_confidence
            FROM crypto_news 
            WHERE id = %s
        """,
            (article_id,),
        )

        article = cursor.fetchone()
        if not article:
            logger.warning(f"Article {article_id} not found")
            return False

        # Skip if already processed
        if (
            article["llm_sentiment_score"] is not None
            and article["llm_sentiment_score"] != 0
        ):
            logger.info(f"Article {article_id} already has LLM sentiment")
            return True

        # Combine title and content for analysis
        text = f"{article['title']}"
        if article["content"]:
            text += f" {article['content']}"

        # Detect market type if not set
        market_type = article["market_type"] or detect_market_type(text)

        # Analyze sentiment with LLM
        llm_score, llm_confidence, llm_analysis = await analyze_sentiment_with_llm(
            text, market_type
        )

        # For stock market articles, also analyze as stock sentiment
        stock_score, stock_confidence, stock_analysis = 0.0, 0.0, None
        if market_type == "stock":
            stock_score, stock_confidence, stock_analysis = (
                llm_score,
                llm_confidence,
                llm_analysis,
            )

        # Update database
        cursor.execute(
            """
            UPDATE crypto_news 
            SET llm_sentiment_score = %s,
                llm_sentiment_confidence = %s,
                llm_sentiment_analysis = %s,
                market_type = %s,
                stock_sentiment_score = %s,
                stock_sentiment_confidence = %s,
                stock_sentiment_analysis = %s,
                sentiment_updated_at = NOW()
            WHERE id = %s
        """,
            (
                llm_score,
                llm_confidence,
                llm_analysis,
                market_type,
                stock_score,
                stock_confidence,
                stock_analysis,
                article_id,
            ),
        )

        logger.info(
            f"✅ Processed article {article_id}: {market_type} sentiment {llm_score:.3f}"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Error processing article {article_id}: {e}")
        return False
    finally:
        cursor.close()


async def process_pending_articles(limit: int = 10) -> Dict[str, int]:
    """
    Process pending articles for LLM sentiment analysis

    Args:
        limit: Maximum number of articles to process

    Returns:
        Dictionary with processing statistics
    """
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    try:
        cursor = conn.cursor()

        # Get articles that need LLM sentiment analysis
        cursor.execute(
            """
            SELECT id FROM crypto_news 
            WHERE (llm_sentiment_score IS NULL OR llm_sentiment_score = 0)
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY created_at DESC
            LIMIT %s
        """,
            (limit,),
        )

        article_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()

        if not article_ids:
            return {"processed": 0, "skipped": 0, "errors": 0}

        logger.info(
            f"Processing {len(article_ids)} articles for LLM sentiment analysis"
        )

        processed = 0
        errors = 0

        # Process articles concurrently (but not too many to avoid rate limits)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests

        async def process_with_semaphore(article_id):
            async with semaphore:
                return await process_news_article(article_id, conn)

        tasks = [process_with_semaphore(article_id) for article_id in article_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                errors += 1
                logger.error(f"Task failed: {result}")
            elif result:
                processed += 1
            else:
                errors += 1

        return {
            "processed": processed,
            "skipped": len(article_ids) - processed - errors,
            "errors": errors,
            "total": len(article_ids),
        }

    except Exception as e:
        logger.error(f"❌ Error in batch processing: {e}")
        return {"error": str(e)}
    finally:
        conn.close()


# FastAPI endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    ollama_available = False

    # Test Ollama connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ollama_url}/api/tags", timeout=5) as response:
                ollama_available = response.status == 200
    except Exception:
        ollama_available = False

    database_connected = db_pool is not None

    # If LLM is disabled, we don't need Ollama to be available
    if not ENABLE_LLM_SENTIMENT:
        status = "healthy" if database_connected else "degraded"
        ollama_available = True  # Not relevant when disabled
    else:
        status = "healthy" if database_connected and ollama_available else "degraded"

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow().isoformat(),
        ollama_available=ollama_available,
        database_connected=database_connected,
    )


@app.get("/status")
async def get_status():
    """Get detailed service status"""
    conn = get_db_connection()
    db_connected = conn is not None
    if conn:
        conn.close()

    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    ollama_available = False

    # Test Ollama connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ollama_url}/api/tags", timeout=5) as response:
                ollama_available = response.status == 200
    except Exception:
        ollama_available = False

    return {
        "service": "enhanced_llm_sentiment",
        "version": "2.0.0",
        "status": "operational" if db_connected and ollama_available else "degraded",
        "ollama_available": ollama_available,
        "ollama_url": ollama_url,
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "database_connected": db_connected,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/sentiment")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment for given text or article"""
    try:
        if request.article_id:
            # Process specific article
            conn = get_db_connection()
            if not conn:
                raise HTTPException(
                    status_code=500, detail="Database connection failed"
                )

            success = await process_news_article(request.article_id, conn)
            conn.close()

            if success:
                return {"status": "success", "article_id": request.article_id}
            else:
                raise HTTPException(
                    status_code=404, detail="Article not found or processing failed"
                )

        elif request.text:
            # Analyze provided text
            market_type = request.market_type or detect_market_type(request.text)
            score, confidence, analysis = await analyze_sentiment_with_llm(
                request.text, market_type
            )

            return {
                "status": "success",
                "market_type": market_type,
                "sentiment_score": score,
                "confidence": confidence,
                "analysis": analysis,
            }

        else:
            raise HTTPException(
                status_code=400, detail="Either article_id or text must be provided"
            )

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-batch")
async def process_batch(background_tasks: BackgroundTasks, limit: int = 10):
    """Process pending articles in background"""
    background_tasks.add_task(process_pending_articles, limit)
    return {"status": "processing_started", "limit": limit}


@app.get("/process-batch")
async def process_batch_sync(limit: int = 10):
    """Process pending articles synchronously"""
    result = await process_pending_articles(limit)
    return result


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(
        "# HELP enhanced_sentiment_collector_health Health status\n# TYPE enhanced_sentiment_collector_health gauge\nenhanced_sentiment_collector_health 1\n"
    )


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "enhanced-llm-sentiment",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "sentiment": "/sentiment",
            "process-batch": "/process-batch",
            "metrics": "/metrics",
            "docs": "/docs",
        },
    }


# Background task to process articles periodically
async def background_processor():
    """Background task to process articles periodically"""
    while True:
        try:
            logger.info("🔄 Starting background LLM sentiment processing")
            result = await process_pending_articles(5)  # Process 5 articles at a time
            logger.info(f"✅ Background processing completed: {result}")
        except Exception as e:
            logger.error(f"❌ Background processing error: {e}")

        # Wait 5 minutes before next batch
        await asyncio.sleep(300)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("🚀 Starting Enhanced LLM Sentiment Analysis Service")

    # Initialize database pool
    if not init_database_pool():
        logger.error("❌ Failed to initialize database pool")

    # Start background processor
    asyncio.create_task(background_processor())
    logger.info("✅ Background processor started")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
