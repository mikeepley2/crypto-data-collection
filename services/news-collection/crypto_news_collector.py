#!/usr/bin/env python3
"""
Crypto News Collector Service

This service collects cryptocurrency news from various sources and stores them in the database.
It provides a FastAPI interface for manual collection triggers and health monitoring.
"""

import os
import sys
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

# Import shared database pool
sys.path.append("/app/shared")
try:
    from shared.database_pool import get_connection_context, execute_query
except ImportError:
    # Fallback for local development
    sys.path.append("../../src/shared")
    from database_pool import get_connection_context, execute_query

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoNewsCollector:
    """Crypto news collection service"""

    def __init__(self):
        self.app = FastAPI(
            title="Crypto News Collector",
            description="Collects cryptocurrency news from various sources",
            version="1.0.0",
        )
        self.setup_routes()

        # News sources configuration
        self.news_sources = [
            {
                "name": "CoinDesk",
                "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
                "type": "rss",
            },
            {
                "name": "CoinTelegraph",
                "url": "https://cointelegraph.com/rss",
                "type": "rss",
            },
            {
                "name": "CryptoSlate",
                "url": "https://cryptoslate.com/feed/",
                "type": "rss",
            },
        ]

        # Collection stats
        self.stats = {
            "total_collected": 0,
            "last_collection": None,
            "collection_errors": 0,
            "sources_active": len(self.news_sources),
        }

    def get_connection(self):
        """Get database connection from shared pool"""
        try:
            from shared.database_pool import get_connection

            return get_connection()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None

    def collect_news_from_source(self, source: Dict) -> List[Dict]:
        """Collect news from a single source"""
        try:
            logger.info(f"Collecting news from {source['name']}")

            # For now, create mock news data since we don't have actual RSS parsing
            # In a real implementation, you would parse RSS feeds or use news APIs
            mock_news = [
                {
                    "title": f'Crypto Market Update - {source["name"]}',
                    "content": f'Latest cryptocurrency market analysis from {source["name"]}...',
                    "url": f"https://example.com/news/{int(time.time())}",
                    "published_at": datetime.now(),
                    "source": source["name"],
                    "category": "market_analysis",
                    "sentiment_score": 0.0,  # Will be calculated by sentiment service
                    "crypto_mentions": ["BTC", "ETH"],
                }
            ]

            logger.info(f"Collected {len(mock_news)} news items from {source['name']}")
            return mock_news

        except Exception as e:
            logger.error(f"Error collecting news from {source['name']}: {e}")
            self.stats["collection_errors"] += 1
            return []

    def store_news_items(self, news_items: List[Dict]) -> int:
        """Store news items in the database"""
        if not news_items:
            return 0

        try:
            conn = self.get_connection()
            if not conn:
                logger.error("No database connection available")
                return 0

            cursor = conn.cursor()

            stored_count = 0
            for item in news_items:
                try:
                    # Insert into crypto_news table with unified schema
                    insert_sql = """
                    INSERT INTO crypto_news (
                        title, content, url, published_at, source, 
                        category, sentiment_score, sentiment_confidence,
                        llm_sentiment_score, llm_sentiment_confidence, llm_sentiment_analysis,
                        market_type, stock_sentiment_score, stock_sentiment_confidence, stock_sentiment_analysis,
                        crypto_mentions, url_hash, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        content = VALUES(content),
                        sentiment_score = VALUES(sentiment_score),
                        sentiment_confidence = VALUES(sentiment_confidence),
                        updated_at = NOW()
                    """

                    # Generate URL hash for duplicate detection
                    import hashlib

                    url_hash = (
                        hashlib.md5(item["url"].encode()).hexdigest()
                        if item["url"]
                        else hashlib.md5(f"no_url_{item['title']}".encode()).hexdigest()
                    )

                    cursor.execute(
                        insert_sql,
                        (
                            item["title"],
                            item["content"],
                            item["url"],
                            item["published_at"],
                            item["source"],
                            item["category"],
                            item["sentiment_score"],
                            item.get("sentiment_confidence", None),
                            None,  # llm_sentiment_score
                            None,  # llm_sentiment_confidence
                            None,  # llm_sentiment_analysis
                            "crypto",  # market_type (default for news collector)
                            None,  # stock_sentiment_score
                            None,  # stock_sentiment_confidence
                            None,  # stock_sentiment_analysis
                            ",".join(item["crypto_mentions"]),
                            url_hash,
                        ),
                    )
                    stored_count += 1

                except Exception as e:
                    logger.error(f"Error storing news item: {e}")
                    continue

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Stored {stored_count} news items in database")
            return stored_count

        except Exception as e:
            logger.error(f"Error storing news items: {e}")
            return 0

    def run_collection_cycle(self) -> Dict:
        """Run one complete news collection cycle"""
        logger.info("Starting news collection cycle...")
        start_time = datetime.now()

        total_collected = 0
        total_stored = 0

        for source in self.news_sources:
            try:
                news_items = self.collect_news_from_source(source)
                if news_items:
                    stored = self.store_news_items(news_items)
                    total_collected += len(news_items)
                    total_stored += stored

                # Small delay between sources
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error processing source {source['name']}: {e}")
                continue

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Update stats
        self.stats["total_collected"] += total_collected
        self.stats["last_collection"] = end_time

        result = {
            "status": "completed",
            "duration_seconds": duration,
            "items_collected": total_collected,
            "items_stored": total_stored,
            "sources_processed": len(self.news_sources),
            "errors": self.stats["collection_errors"],
        }

        logger.info(f"Collection cycle completed: {result}")
        return result

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")
        def health():
            return {"status": "ok", "service": "crypto-news-collector"}

        @self.app.get("/status")
        def status():
            return {
                "service": "crypto-news-collector",
                "stats": self.stats,
                "sources": len(self.news_sources),
                "uptime": "running",
            }

        @self.app.post("/collect")
        def collect_news(background_tasks: BackgroundTasks):
            """Trigger news collection"""
            background_tasks.add_task(self.run_collection_cycle)
            return {"status": "started", "message": "News collection initiated"}

        @self.app.get("/metrics")
        def metrics():
            """Prometheus metrics endpoint"""
            metrics_text = f"""# HELP crypto_news_collector_total_collected Total number of news items collected
# TYPE crypto_news_collector_total_collected counter
crypto_news_collector_total_collected {self.stats['total_collected']}

# HELP crypto_news_collector_collection_errors Total number of collection errors
# TYPE crypto_news_collector_collection_errors counter
crypto_news_collector_collection_errors {self.stats['collection_errors']}

# HELP crypto_news_collector_sources_active Number of active news sources
# TYPE crypto_news_collector_sources_active gauge
crypto_news_collector_sources_active {self.stats['sources_active']}

# HELP crypto_news_collector_running Service running status
# TYPE crypto_news_collector_running gauge
crypto_news_collector_running 1
"""
            return JSONResponse(content=metrics_text, media_type="text/plain")


# Create the service instance
news_collector = CryptoNewsCollector()
app = news_collector.app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Crypto News Collector Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument(
        "--interval",
        type=int,
        default=900,
        help="Collection interval in seconds (default: 15 minutes)",
    )

    args = parser.parse_args()

    logger.info(f"Starting Crypto News Collector on {args.host}:{args.port}")
    logger.info(f"Collection interval: {args.interval} seconds")

    uvicorn.run(app, host=args.host, port=args.port)
