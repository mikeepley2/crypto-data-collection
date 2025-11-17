#!/usr/bin/env python3
"""
Enhanced Crypto News Collector Service

This service collects cryptocurrency news from various sources with:
- Dynamic symbol loading from crypto_assets table
- Comprehensive backfill capabilities
- Advanced sentiment analysis integration
- Multi-source RSS feed processing
- Gap detection and automatic healing
"""

import os
import sys
import logging
import requests
import time
import hashlib
import feedparser
import mysql.connector
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Set
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import aiohttp
import asyncio
import re
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NewsSource:
    """News source configuration"""
    name: str
    url: str
    type: str
    active: bool = True
    category: str = "general"
    
class CryptoNewsService:
    """Enhanced crypto news collection service with dynamic symbol management"""
    
    def __init__(self):
        """Initialize the enhanced news collection service"""
        self.setup_database()
        
        # Enhanced news sources with real RSS feeds
        self.news_sources = [
            NewsSource(
                name="CoinDesk", 
                url="https://feeds.coindesk.com/coindesk", 
                type="rss",
                category="market_analysis"
            ),
            NewsSource(
                name="CoinTelegraph", 
                url="https://cointelegraph.com/rss", 
                type="rss",
                category="market_analysis"
            ),
            NewsSource(
                name="CryptoSlate", 
                url="https://cryptoslate.com/feed/", 
                type="rss",
                category="market_analysis"
            ),
            NewsSource(
                name="Decrypt", 
                url="https://decrypt.co/feed", 
                type="rss",
                category="technology"
            ),
            NewsSource(
                name="Bitcoin Magazine", 
                url="https://bitcoinmagazine.com/feeds/articles", 
                type="rss",
                category="bitcoin"
            ),
            NewsSource(
                name="CoinMarketCap News", 
                url="https://coinmarketcap.com/alexandria/rss", 
                type="rss",
                category="market_analysis"
            ),
        ]
        
        # Collection stats
        self.stats = {
            "total_collected": 0,
            "total_stored": 0,
            "last_collection": None,
            "collection_errors": 0,
            "sources_active": len([s for s in self.news_sources if s.active]),
            "last_gap_check": None,
            "gap_hours_detected": 0,
            "backfill_records": 0,
            "health_score": 0.0,
            "symbols_tracked": 0,
        }
        
        # Crypto symbol patterns for mention detection
        self.crypto_symbols: Set[str] = set()
        self.load_symbols()
        
        # Rate limiting
        self.request_delay = 1.0  # Delay between requests
        self.max_retries = 3
        
    def setup_database(self):
        """Setup database connection"""
        self.db_config = {
            "host": os.getenv("DB_HOST", "172.22.32.1"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "news_collector"),
            "password": os.getenv("DB_PASSWORD", "99Rules!"),
            "database": os.getenv("DB_NAME", "crypto_prices")
        }
        
    def get_connection(self):
        """Get database connection with error handling"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
            
    def load_symbols(self):
        """Load active crypto symbols from crypto_assets table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT symbol 
                    FROM crypto_assets 
                    WHERE status = 'active'
                    ORDER BY symbol
                """)
                symbols = [row[0] for row in cursor.fetchall()]
                self.crypto_symbols = set(symbols)
                self.stats["symbols_tracked"] = len(symbols)
                logger.info(f"✅ Loaded {len(symbols)} crypto symbols from crypto_assets table")
                
        except Exception as e:
            logger.error(f"❌ Failed to load symbols from crypto_assets: {e}")
            # Fallback to common symbols
            self.crypto_symbols = {
                'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'ATOM', 'ALGO', 
                'XRP', 'LTC', 'BCH', 'LINK', 'UNI', 'AAVE', 'COMP', 'MKR', 'SNX'
            }
            self.stats["symbols_tracked"] = len(self.crypto_symbols)
            
    def detect_crypto_mentions(self, text: str) -> List[str]:
        """Detect crypto symbols mentioned in text"""
        mentions = []
        text_upper = text.upper()
        
        for symbol in self.crypto_symbols:
            # Look for symbol as standalone word
            pattern = r'\b' + re.escape(symbol) + r'\b'
            if re.search(pattern, text_upper):
                mentions.append(symbol)
                
        return mentions
        
    def fetch_rss_feed(self, source: NewsSource) -> List[Dict]:
        """Fetch and parse RSS feed from a source"""
        try:
            logger.info(f"📡 Fetching RSS feed from {source.name}")
            
            headers = {
                'User-Agent': 'CryptoNewsCollector/1.0 (+https://example.com/bot)'
            }
            
            # Fetch RSS feed
            response = requests.get(source.url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning(f"⚠️  No entries found in RSS feed from {source.name}")
                return []
                
            news_items = []
            for entry in feed.entries:
                try:
                    # Extract publication date
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6])
                    else:
                        published_at = datetime.now()
                        
                    # Extract content
                    content = ""
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value if entry.content else ""
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                        
                    # Clean HTML tags from content
                    content = re.sub(r'<[^>]+>', '', content)
                    
                    title = entry.title if hasattr(entry, 'title') else 'No title'
                    url = entry.link if hasattr(entry, 'link') else None
                    
                    # Detect crypto mentions
                    full_text = f"{title} {content}"
                    crypto_mentions = self.detect_crypto_mentions(full_text)
                    
                    news_item = {
                        "title": title,
                        "content": content,
                        "url": url,
                        "published_at": published_at,
                        "source": source.name,
                        "category": source.category,
                        "crypto_mentions": crypto_mentions,
                        "sentiment_score": None,  # Will be calculated by sentiment service
                        "sentiment_confidence": None,
                    }
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.error(f"❌ Error parsing RSS entry from {source.name}: {e}")
                    continue
                    
            logger.info(f"✅ Collected {len(news_items)} news items from {source.name}")
            return news_items
            
        except Exception as e:
            logger.error(f"❌ Error fetching RSS feed from {source.name}: {e}")
            self.stats["collection_errors"] += 1
            return []
            
    def store_news_items(self, news_items: List[Dict]) -> int:
        """Store news items in the database with duplicate detection"""
        if not news_items:
            return 0
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                stored_count = 0
                
                for item in news_items:
                    try:
                        # Generate URL hash for duplicate detection
                        url_hash = hashlib.md5(
                            (item.get("url", "") or f"no_url_{item['title']}").encode()
                        ).hexdigest()
                        
                        # Check if already exists
                        cursor.execute(
                            "SELECT id FROM crypto_news WHERE url_hash = %s",
                            (url_hash,)
                        )
                        
                        if cursor.fetchone():
                            continue  # Skip duplicates
                            
                        # Insert new news item
                        insert_sql = """
                        INSERT INTO crypto_news (
                            title, content, url, published_at, source, 
                            category, sentiment_score, sentiment_confidence,
                            llm_sentiment_score, llm_sentiment_confidence, llm_sentiment_analysis,
                            market_type, stock_sentiment_score, stock_sentiment_confidence, 
                            stock_sentiment_analysis, crypto_mentions, url_hash, 
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            NOW(), NOW()
                        )
                        """
                        
                        cursor.execute(insert_sql, (
                            item["title"],
                            item["content"],
                            item["url"],
                            item["published_at"],
                            item["source"],
                            item["category"],
                            item["sentiment_score"],
                            item["sentiment_confidence"],
                            None,  # llm_sentiment_score
                            None,  # llm_sentiment_confidence  
                            None,  # llm_sentiment_analysis
                            "crypto",  # market_type
                            None,  # stock_sentiment_score
                            None,  # stock_sentiment_confidence
                            None,  # stock_sentiment_analysis
                            ",".join(item["crypto_mentions"]) if item["crypto_mentions"] else "",
                            url_hash
                        ))
                        
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Error storing news item: {e}")
                        continue
                        
                conn.commit()
                logger.info(f"✅ Stored {stored_count} news items in database")
                return stored_count
                
        except Exception as e:
            logger.error(f"❌ Error storing news items: {e}")
            return 0
            
    def run_collection_cycle(self) -> Dict:
        """Run one complete news collection cycle across all sources"""
        logger.info("🔄 Starting comprehensive news collection cycle...")
        start_time = datetime.now()
        
        total_collected = 0
        total_stored = 0
        sources_processed = 0
        
        for source in self.news_sources:
            if not source.active:
                continue
                
            try:
                # Fetch news from source
                news_items = self.fetch_rss_feed(source)
                
                if news_items:
                    stored = self.store_news_items(news_items)
                    total_collected += len(news_items)
                    total_stored += stored
                    
                sources_processed += 1
                
                # Rate limiting between sources
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"❌ Error processing source {source.name}: {e}")
                self.stats["collection_errors"] += 1
                continue
                
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Update stats
        self.stats["total_collected"] += total_collected
        self.stats["total_stored"] += total_stored
        self.stats["last_collection"] = end_time
        
        result = {
            "status": "completed",
            "duration_seconds": duration,
            "items_collected": total_collected,
            "items_stored": total_stored,
            "sources_processed": sources_processed,
            "errors": self.stats["collection_errors"],
            "timestamp": end_time.isoformat()
        }
        
        logger.info(f"✅ Collection cycle completed: {result}")
        return result
        
    def detect_data_gaps(self) -> Optional[float]:
        """Detect gaps in news data collection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check for latest news across all sources
                cursor.execute("""
                    SELECT 
                        MAX(created_at) as last_update,
                        COUNT(*) as total_records,
                        COUNT(DISTINCT source) as active_sources
                    FROM crypto_news 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """)
                
                result = cursor.fetchone()
                
                if result and result[0]:
                    last_update = result[0]
                    if isinstance(last_update, str):
                        last_update = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                        
                    now = datetime.now()
                    gap_hours = (now - last_update).total_seconds() / 3600
                    
                    self.stats["gap_hours_detected"] = gap_hours
                    self.stats["last_gap_check"] = now
                    
                    logger.info(f"📊 Gap analysis: {gap_hours:.1f} hours since last update")
                    return gap_hours
                else:
                    logger.info("ℹ️  No recent news data found")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error detecting gaps: {e}")
            return None
            
    def get_missing_dates(self, start_date: date, end_date: date) -> List[date]:
        """Get dates with missing or insufficient news data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find dates with fewer than expected news items (less than 5 per day)
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as news_date,
                        COUNT(*) as daily_count
                    FROM crypto_news
                    WHERE DATE(created_at) BETWEEN %s AND %s
                    GROUP BY DATE(created_at)
                    HAVING COUNT(*) < 5
                    ORDER BY news_date
                """, (start_date, end_date))
                
                sparse_dates = [row[0] for row in cursor.fetchall()]
                
                # Also check for completely missing dates
                current_date = start_date
                all_dates = []
                while current_date <= end_date:
                    all_dates.append(current_date)
                    current_date += timedelta(days=1)
                    
                cursor.execute("""
                    SELECT DISTINCT DATE(created_at) as existing_date
                    FROM crypto_news
                    WHERE DATE(created_at) BETWEEN %s AND %s
                """, (start_date, end_date))
                
                existing_dates = {row[0] for row in cursor.fetchall()}
                missing_dates = [d for d in all_dates if d not in existing_dates]
                
                # Combine sparse and missing dates
                gap_dates = list(set(sparse_dates + missing_dates))
                gap_dates.sort()
                
                logger.info(f"📅 Found {len(gap_dates)} dates with insufficient news data")
                return gap_dates
                
        except Exception as e:
            logger.error(f"❌ Error finding missing dates: {e}")
            return []
            
    def backfill_historical_news(self, start_date: date, end_date: date = None) -> int:
        """Backfill news data for specified date range"""
        if end_date is None:
            end_date = date.today()
            
        logger.info(f"🔄 Starting news backfill from {start_date} to {end_date}")
        
        # Find dates needing backfill
        missing_dates = self.get_missing_dates(start_date, end_date)
        
        if not missing_dates:
            logger.info("✅ No backfill needed - data appears complete")
            return 0
            
        total_backfilled = 0
        
        # Process backfill in batches to avoid overwhelming sources
        for i, missing_date in enumerate(missing_dates, 1):
            try:
                logger.info(f"🔄 Backfilling date {i}/{len(missing_dates)}: {missing_date}")
                
                # Run collection cycle for this date
                # Note: RSS feeds typically only have recent data,
                # so this is more about filling recent gaps
                result = self.run_collection_cycle()
                total_backfilled += result.get("items_stored", 0)
                
                # Add delay between dates
                time.sleep(self.request_delay * 2)
                
            except Exception as e:
                logger.error(f"❌ Error backfilling date {missing_date}: {e}")
                continue
                
        self.stats["backfill_records"] = total_backfilled
        logger.info(f"✅ Backfill completed: {total_backfilled} records processed")
        return total_backfilled
        
    def auto_gap_detection_and_healing(self):
        """Automatically detect and heal data gaps"""
        logger.info("🔍 Running automatic gap detection and healing...")
        
        gap_hours = self.detect_data_gaps()
        
        if gap_hours is not None and gap_hours > 6:  # More than 6 hours gap
            logger.warning(f"⚠️  Significant gap detected: {gap_hours:.1f} hours")
            
            # Calculate backfill period (limit to 7 days)
            gap_days = min(int(gap_hours / 24) + 1, 7)
            start_date = date.today() - timedelta(days=gap_days)
            
            logger.info(f"🔧 Auto-healing: backfilling last {gap_days} days")
            self.backfill_historical_news(start_date)
            
        elif gap_hours is None:
            logger.info("ℹ️  No previous data found - running initial collection")
            self.run_collection_cycle()
        else:
            logger.info(f"✅ No significant gaps detected ({gap_hours:.1f} hours)")
            
    def calculate_health_score(self) -> float:
        """Calculate service health score"""
        try:
            health_score = 100.0
            
            # Check data freshness
            gap_hours = self.detect_data_gaps()
            if gap_hours:
                if gap_hours > 24:
                    health_score -= min(40, gap_hours)
                elif gap_hours > 6:
                    health_score -= gap_hours * 2
                    
            # Check collection success rate
            total_attempts = self.stats["total_collected"] + self.stats["collection_errors"]
            if total_attempts > 0:
                error_rate = self.stats["collection_errors"] / total_attempts
                health_score -= error_rate * 30
                
            # Check source diversity
            active_sources = len([s for s in self.news_sources if s.active])
            if active_sources < 3:
                health_score -= (3 - active_sources) * 10
                
            health_score = max(0.0, health_score)
            self.stats["health_score"] = health_score
            
            return health_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating health score: {e}")
            return 0.0

# Enhanced News Collector with FastAPI interface
class EnhancedCryptoNewsCollector:
    """Enhanced crypto news collector with FastAPI interface"""
    
    def __init__(self):
        self.service = CryptoNewsService()
        self.app = FastAPI(
            title="Enhanced Crypto News Collector",
            description="Advanced cryptocurrency news collection with dynamic symbol management",
            version="2.0.0"
        )
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        def health():
            return {"status": "ok", "service": "enhanced-crypto-news-collector"}
            
        @self.app.get("/status")
        def status():
            gap_hours = self.service.detect_data_gaps()
            health_score = self.service.calculate_health_score()
            
            return {
                "service": "enhanced-crypto-news-collector",
                "stats": self.service.stats,
                "sources": len(self.service.news_sources),
                "symbols_tracked": len(self.service.crypto_symbols),
                "gap_hours": gap_hours,
                "health_score": health_score,
                "data_freshness": "healthy" if (gap_hours or 0) < 6 else "stale",
                "timestamp": datetime.now().isoformat()
            }
            
        @self.app.post("/collect")
        def collect_news(background_tasks: BackgroundTasks):
            """Trigger news collection"""
            background_tasks.add_task(self.service.run_collection_cycle)
            return {"status": "started", "message": "News collection initiated"}
            
        @self.app.post("/backfill")
        def backfill_news(
            days: int = 7,
            background_tasks: BackgroundTasks = None
        ):
            """Trigger historical backfill"""
            if days > 30:
                return {"error": "Maximum backfill period is 30 days"}
                
            start_date = date.today() - timedelta(days=days)
            
            if background_tasks:
                background_tasks.add_task(
                    self.service.backfill_historical_news,
                    start_date
                )
                
            return {
                "status": "started",
                "message": f"Backfill initiated for {days} days",
                "start_date": start_date.isoformat()
            }
            
        @self.app.post("/gap-check")
        def gap_check():
            """Check for data gaps and auto-heal"""
            self.service.auto_gap_detection_and_healing()
            return {
                "status": "completed",
                "gap_hours": self.service.stats.get("gap_hours_detected", 0),
                "health_score": self.service.stats.get("health_score", 0)
            }
            
        @self.app.get("/symbols")
        def get_symbols():
            """Get tracked crypto symbols"""
            return {
                "symbols": sorted(list(self.service.crypto_symbols)),
                "count": len(self.service.crypto_symbols)
            }

# Create the enhanced service instance
news_collector = EnhancedCryptoNewsCollector()
app = news_collector.app

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Crypto News Collector")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--auto-heal", action="store_true", default=True,
                       help="Run automatic gap detection on startup")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting Enhanced Crypto News Collector on {args.host}:{args.port}")
    
    # Run automatic gap detection and healing on startup
    if args.auto_heal:
        logger.info("🔍 Running startup gap detection and healing...")
        news_collector.service.auto_gap_detection_and_healing()
        logger.info("✅ Startup gap check complete")
        
    uvicorn.run(app, host=args.host, port=args.port)