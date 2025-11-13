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

# Import centralized scheduling configuration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.scheduling_config import get_collector_schedule
except ImportError as e:
    logging.warning(f"Could not import centralized scheduling config: {e}. Using defaults.")
    get_collector_schedule = None

# Import shared database pool
sys.path.append("/app/shared")
try:
    from shared.database_pool import get_connection_context, execute_query
except ImportError:
    # Import centralized database configuration
    try:
        from shared.database_config import get_db_connection
        def get_connection_fallback():
            """Use centralized database configuration"""
            return get_db_connection()
    except ImportError:
        # Fallback for local development - use direct MySQL connection
        import mysql.connector
        
        def get_connection_fallback():
            """Simple database connection for testing"""
            return mysql.connector.connect(
                host=os.getenv("DB_HOST", "172.22.32.1"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER", "news_collector"),
                password=os.getenv("DB_PASSWORD", "99Rules!"),
                database=os.getenv("DB_NAME", "crypto_prices"),
        )

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
            "last_gap_check": None,
            "gap_hours_detected": 0,
            "backfill_records": 0,
            "health_score": 0.0,
        }

    def get_connection(self):
        """Get database connection from shared pool or direct connection"""
        try:
            # Try shared pool first
            from shared.database_pool import get_connection
            return get_connection()
        except Exception:
            # Fallback to direct connection for testing
            return get_connection_fallback()

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

    def detect_gap(self) -> Optional[float]:
        """
        Detect gaps in news data collection
        Returns number of hours since last update, or None if no data exists
        """
        try:
            conn = self.get_connection()
            if not conn:
                return None

            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(created_at) as last_update
                FROM crypto_news
                WHERE source IN ('CoinDesk', 'CoinTelegraph', 'CryptoSlate')
            """)
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0]:
                last_update = result[0]
                if isinstance(last_update, str):
                    last_update = datetime.fromisoformat(
                        last_update.replace("Z", "+00:00")
                    )
                
                now = datetime.now()
                gap_hours = (now - last_update).total_seconds() / 3600
                self.stats["gap_hours_detected"] = gap_hours
                self.stats["last_gap_check"] = now
                return gap_hours
            else:
                logger.info("No existing news data found - first run")
                return None
                
        except Exception as e:
            logger.error(f"Error detecting gap: {e}")
            return None

    def backfill_news_data(self, days: int = 7) -> int:
        """
        Backfill news data for the specified number of days
        Returns number of records processed
        """
        logger.info(f"Starting news backfill for last {days} days...")
        
        backfill_count = 0
        for day in range(days):
            try:
                # For each day, run collection cycle
                result = self.run_collection_cycle()
                backfill_count += result.get("items_stored", 0)
                
                # Small delay to avoid overwhelming APIs
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in backfill day {day}: {e}")
                continue
        
        self.stats["backfill_records"] = backfill_count
        logger.info(f"Backfill completed: {backfill_count} records processed")
        return backfill_count

    def calculate_health_score(self) -> float:
        """Calculate health score based on data freshness and collection success"""
        try:
            gap_hours = self.detect_gap()
            
            # Base score starts at 100
            health_score = 100.0
            
            # Deduct points for data gaps
            if gap_hours:
                if gap_hours > 24:  # More than 1 day old
                    health_score -= min(50, gap_hours * 2)  # Max 50 point deduction
                elif gap_hours > 6:  # More than 6 hours old
                    health_score -= gap_hours * 1.5
            
            # Deduct points for collection errors
            error_ratio = self.stats["collection_errors"] / max(1, self.stats["total_collected"])
            health_score -= error_ratio * 30  # Max 30 point deduction
            
            # Ensure score doesn't go below 0
            health_score = max(0.0, health_score)
            
            self.stats["health_score"] = health_score
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0

    def auto_gap_detection_and_backfill(self):
        """
        Automatically detect gaps and backfill if necessary
        Called on startup and periodically
        """
        logger.info("Running automatic gap detection...")
        
        gap_hours = self.detect_gap()
        if gap_hours:
            # Use centralized scheduling config with fallback
            if get_collector_schedule:
                config = get_collector_schedule('news')
                collection_interval_hours = config['frequency_hours']
            else:
                collection_interval_hours = 1  # Fallback: News should be collected hourly
            
            if gap_hours > collection_interval_hours:
                gap_days = min(int(gap_hours / 24) + 1, 7)  # Limit to 7 days max
                logger.warning(f"⚠️  Gap detected: {gap_hours:.1f} hours since last update")
                logger.info(f"🔄 Auto-backfilling last {gap_days} days to fill gap...")
                
                self.backfill_news_data(gap_days)
                logger.info("✅ Gap backfill complete")
            else:
                logger.info(f"✅ No significant gap detected ({gap_hours:.1f} hours)")
        else:
            logger.info("ℹ️  No previous data found - running initial collection")
            self.run_collection_cycle()

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")
        def health():
            return {"status": "ok", "service": "crypto-news-collector"}

        @self.app.get("/status")
        def status():
            gap_hours = self.detect_gap()
            health_score = self.calculate_health_score()
            
            return {
                "service": "crypto-news-collector",
                "stats": self.stats,
                "sources": len(self.news_sources),
                "uptime": "running",
                "gap_hours": gap_hours,
                "health_score": health_score,
                "data_freshness": "healthy" if (gap_hours or 0) < 6 else "stale",
            }

        @self.app.post("/collect")
        def collect_news(background_tasks: BackgroundTasks):
            """Trigger news collection"""
            background_tasks.add_task(self.run_collection_cycle)
            return {"status": "started", "message": "News collection initiated"}

        @self.app.post("/gap-check")
        def gap_check():
            """Check for data gaps and optionally backfill"""
            self.auto_gap_detection_and_backfill()
            return {
                "status": "completed",
                "gap_hours": self.stats.get("gap_hours_detected", 0),
                "health_score": self.stats.get("health_score", 0),
            }

        @self.app.post("/backfill/{days}")
        def manual_backfill(days: int, background_tasks: BackgroundTasks):
            """Manually trigger backfill for specified days"""
            if days > 30:
                return {"error": "Maximum backfill period is 30 days"}
            
            background_tasks.add_task(self.backfill_news_data, days)
            return {
                "status": "started",
                "message": f"Backfill initiated for {days} days"
            }

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
        default=3600,
        help="Collection interval in seconds (default: 1 hour)",
    )
    parser.add_argument(
        "--auto-gap-check",
        action="store_true",
        default=True,
        help="Run automatic gap detection on startup",
    )

    args = parser.parse_args()

    logger.info(f"Starting Crypto News Collector on {args.host}:{args.port}")
    logger.info(f"Collection interval: {args.interval} seconds")

    # Run automatic gap detection and backfill on startup
    if args.auto_gap_check:
        logger.info("🔍 Running startup gap detection...")
        news_collector.auto_gap_detection_and_backfill()
        logger.info("✅ Startup gap check complete")

    uvicorn.run(app, host=args.host, port=args.port)
