#!/usr/bin/env python3
"""
Enhanced Crypto News Collector - Template Compliant Version
Migrated from legacy implementation to standardized collector template
"""

import asyncio
import aiohttp
import feedparser
import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
import mysql.connector
import time

from base_collector_template import (
    BaseCollector, CollectorConfig, DataQualityReport, AlertRequest
)

class EnhancedNewsCollectorConfig(CollectorConfig):
    """Extended configuration for enhanced news collector"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # News-specific configuration
        self.rss_feeds = [
            {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss"},
            {"name": "CryptoSlate", "url": "https://cryptoslate.com/feed/"},
            {"name": "Decrypt", "url": "https://decrypt.co/feed"},
            {"name": "BeinCrypto", "url": "https://beincrypto.com/feed/"},
            {"name": "CoinJournal", "url": "https://coinjournal.net/feed/"}
        ]
        self.max_articles_per_feed = 20
        self.article_processing_batch = 10
        self.crypto_symbols = set()

    @classmethod
    def from_env(cls) -> 'EnhancedNewsCollectorConfig':
        """Load configuration from environment variables"""
        config = super().from_env()
        # Convert to EnhancedNewsCollectorConfig
        news_config = cls(**config.__dict__)
        news_config.service_name = "enhanced-crypto-news"
        return news_config

class EnhancedNewsCollector(BaseCollector):
    """
    Enhanced News Collector implementing the standardized collector template
    Collects cryptocurrency news from multiple RSS feeds with crypto mention detection
    """
    
    def __init__(self):
        config = EnhancedNewsCollectorConfig.from_env()
        super().__init__(config)
        self.session = None

    async def collect_data(self) -> int:
        """
        Collect news data from RSS feeds with crypto mention detection
        Returns number of articles collected
        """
        total_articles = 0
        
        self.logger.info("enhanced_news_collection_started", feeds=len(self.config.rss_feeds))
        
        # Load crypto symbols for mention detection
        await self._load_crypto_symbols()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.api_timeout)) as session:
            self.session = session
            
            for feed_info in self.config.rss_feeds:
                try:
                    # Rate limiting
                    if self.rate_limiter:
                        await self.rate_limiter.wait_for_token()
                    
                    # Circuit breaker for feed collection
                    articles = self.circuit_breaker.call(self._collect_from_feed, feed_info)
                    total_articles += await articles
                    
                    self.metrics['api_requests_total'].labels(endpoint=feed_info["url"], status='success').inc()
                    
                    # Small delay between feeds
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error("feed_collection_error", feed=feed_info["name"], error=str(e))
                    self.metrics['api_requests_total'].labels(endpoint=feed_info["url"], status='error').inc()
                    
                    # Send alert if enabled
                    if self.config.enable_alerting and self.collection_errors > self.config.alert_error_threshold:
                        await self._send_alert(AlertRequest(
                            alert_type="feed_collection_failure",
                            severity="warning",
                            message=f"Multiple feed collection failures: {feed_info['name']}",
                            service=self.config.service_name,
                            additional_data={"feed": feed_info["name"], "error": str(e)}
                        ))
        
        self.logger.info("enhanced_news_collection_completed", total_articles=total_articles)
        return total_articles

    async def _collect_from_feed(self, feed_info: Dict[str, str]) -> int:
        """Collect articles from a single RSS feed"""
        
        self.logger.debug("processing_feed", feed_name=feed_info["name"], url=feed_info["url"])
        
        try:
            # Fetch RSS feed
            headers = {'User-Agent': 'CryptoNewsCollector/2.0 (Enhanced Template Version)'}
            
            async with self.session.get(feed_info["url"], headers=headers) as response:
                if response.status != 200:
                    self.logger.warning("feed_request_failed", feed=feed_info["name"], status=response.status)
                    return 0
                
                content = await response.text()
                
            # Parse RSS feed
            feed = feedparser.parse(content)
            
            if feed.bozo:
                self.logger.warning("feed_parse_warning", feed=feed_info["name"], error=str(feed.bozo_exception))
            
            # Process articles
            articles_saved = 0
            articles_batch = []
            
            for entry in feed.entries[:self.config.max_articles_per_feed]:
                try:
                    article = await self._parse_article(entry, feed_info)
                    if article:
                        # Data validation if enabled
                        if self.config.enable_data_validation:
                            validation_result = await self._validate_data(article)
                            if not validation_result["is_valid"]:
                                self.logger.warning("article_validation_failed", 
                                                  title=article.get("title", "unknown"),
                                                  errors=validation_result["errors"])
                                continue
                        
                        articles_batch.append(article)
                        
                        if len(articles_batch) >= self.config.article_processing_batch:
                            saved = await self._save_articles_batch(articles_batch)
                            articles_saved += saved
                            articles_batch = []
                            
                except Exception as e:
                    self.logger.warning("article_parse_error", feed=feed_info["name"], error=str(e))
            
            # Save remaining articles
            if articles_batch:
                saved = await self._save_articles_batch(articles_batch)
                articles_saved += saved
            
            self.logger.info("feed_processed", feed=feed_info["name"], articles=articles_saved)
            return articles_saved
            
        except Exception as e:
            self.logger.error("feed_processing_error", feed=feed_info["name"], error=str(e))
            raise

    async def _parse_article(self, entry, feed_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a single RSS entry into article data with crypto mention detection"""
        
        try:
            # Extract basic article data
            title = getattr(entry, 'title', '').strip()
            url = getattr(entry, 'link', '').strip()
            content = ""
            
            # Extract content from various possible fields
            if hasattr(entry, 'summary'):
                content = re.sub(r'<[^>]+>', '', entry.summary)
            elif hasattr(entry, 'description'):
                content = re.sub(r'<[^>]+>', '', entry.description)
            
            # Parse publication date
            published_date = self._parse_date(getattr(entry, 'published', ''))
            if not published_date:
                published_date = datetime.now(timezone.utc)
            
            # Detect crypto mentions
            full_text = f"{title} {content}"
            crypto_mentions = await self._detect_crypto_mentions(full_text)
            
            # Generate URL hash for duplicate detection
            url_hash = hashlib.md5(
                (url or f"no_url_{title}").encode()
            ).hexdigest()
            
            article = {
                'title': title,
                'content': content,
                'url': url,
                'published_at': published_date,
                'source': feed_info["name"],
                'category': 'crypto_news',
                'crypto_mentions': ','.join(crypto_mentions),
                'url_hash': url_hash,
                'collected_at': datetime.now(timezone.utc)
            }
            
            # Validate required fields
            if not title or (not url and not content):
                return None
                
            return article
            
        except Exception as e:
            self.logger.warning("article_parse_error", entry_title=getattr(entry, 'title', 'unknown'), error=str(e))
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse RSS date string to datetime"""
        
        if not date_str:
            return None
            
        try:
            # feedparser usually handles this well
            time_struct = feedparser._parse_date(date_str)
            if time_struct:
                return datetime(*time_struct[:6], tzinfo=timezone.utc)
        except Exception:
            pass
            
        return None

    async def _load_crypto_symbols(self):
        """Load cryptocurrency symbols from database"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM crypto_assets ORDER BY symbol")
                symbols = {row[0] for row in cursor.fetchall()}
                self.config.crypto_symbols = symbols
                self.logger.info("crypto_symbols_loaded", count=len(symbols))
        except Exception as e:
            self.logger.warning("failed_to_load_symbols", error=str(e))
            # Fallback to common crypto symbols
            self.config.crypto_symbols = {'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'AAVE'}

    async def _detect_crypto_mentions(self, text: str) -> List[str]:
        """Detect cryptocurrency mentions in text"""
        
        mentions = []
        text_upper = text.upper()
        
        for symbol in self.config.crypto_symbols:
            if re.search(r'\b' + re.escape(symbol) + r'\b', text_upper):
                mentions.append(symbol)
                
        return mentions

    async def _save_articles_batch(self, articles: List[Dict[str, Any]]) -> int:
        """Save a batch of articles to database"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Insert articles with duplicate detection
                insert_query = """
                INSERT INTO crypto_news (
                    title, content, url, published_at, source, 
                    category, crypto_mentions, url_hash, 
                    created_at, updated_at
                ) VALUES (
                    %(title)s, %(content)s, %(url)s, %(published_at)s, %(source)s,
                    %(category)s, %(crypto_mentions)s, %(url_hash)s,
                    %(collected_at)s, %(collected_at)s
                )
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content),
                    crypto_mentions = VALUES(crypto_mentions),
                    updated_at = VALUES(updated_at)
                """
                
                articles_saved = 0
                for article in articles:
                    try:
                        cursor.execute(insert_query, article)
                        if cursor.rowcount > 0:
                            articles_saved += 1
                            
                    except mysql.connector.IntegrityError:
                        # Duplicate entry, skip
                        continue
                    except Exception as e:
                        self.logger.warning("article_save_error", article_url=article.get('url'), error=str(e))
                
                conn.commit()
                
                self.metrics['records_processed_total'].labels(operation='insert').inc(articles_saved)
                self.metrics['database_operations_total'].labels(operation='batch_insert', status='success').inc()
                
                return articles_saved
                
        except Exception as e:
            self.logger.error("batch_save_error", error=str(e))
            self.metrics['database_operations_total'].labels(operation='batch_insert', status='error').inc()
            raise

    async def backfill_data(self, missing_periods: List[Dict], force: bool = False) -> int:
        """
        Backfill missing news data
        For news, this is essentially the same as regular collection
        since RSS feeds contain recent articles
        """
        
        self.logger.info("news_backfill_started", periods=len(missing_periods), force=force)
        
        # For news, backfill is just regular collection
        # since RSS feeds contain recent articles
        backfilled_records = await self.collect_data()
        
        self.logger.info("news_backfill_completed", records=backfilled_records)
        return backfilled_records

    async def _get_table_status(self, cursor) -> Dict[str, Any]:
        """Get status of crypto_news table"""
        
        try:
            # Check if table exists and get stats
            cursor.execute("""
                SELECT COUNT(*) as total_articles,
                       MAX(published_at) as latest_article,
                       MAX(created_at) as last_collection,
                       COUNT(DISTINCT source) as sources_count
                FROM crypto_news
            """)
            
            result = cursor.fetchone()
            
            # Get articles by source
            cursor.execute("""
                SELECT source, COUNT(*) as count
                FROM crypto_news 
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY source
                ORDER BY count DESC
            """)
            
            recent_by_source = dict(cursor.fetchall())
            
            return {
                "crypto_news": {
                    "total_articles": result[0] if result else 0,
                    "latest_article": result[1] if result and result[1] else None,
                    "last_collection": result[2] if result and result[2] else None,
                    "sources_count": result[3] if result else 0,
                    "recent_by_source": recent_by_source
                }
            }
            
        except mysql.connector.Error as e:
            return {"error": str(e)}

    async def _analyze_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Analyze missing news data
        For news, we look for gaps in collection dates and low article counts
        """
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Find gaps in news collection by day
                cursor.execute("""
                    SELECT DATE(created_at) as news_date, 
                           COUNT(*) as article_count,
                           COUNT(DISTINCT source) as sources_count
                    FROM crypto_news
                    WHERE created_at BETWEEN %s AND %s
                    GROUP BY DATE(created_at)
                    ORDER BY news_date
                """, (start_date, end_date))
                
                results = cursor.fetchall()
                
                # Identify missing or low-count days
                missing_periods = []
                
                if not results:
                    # No data at all in range
                    missing_periods.append({
                        "start_date": start_date,
                        "end_date": end_date,
                        "reason": "no_data"
                    })
                else:
                    # Check for gaps and low counts
                    for news_date, article_count, sources_count in results:
                        if article_count < 10:  # Threshold for "low" news count
                            missing_periods.append({
                                "date": news_date,
                                "article_count": article_count,
                                "sources_count": sources_count,
                                "reason": "low_count"
                            })
                        elif sources_count < 3:  # Not enough sources
                            missing_periods.append({
                                "date": news_date,
                                "article_count": article_count,
                                "sources_count": sources_count,
                                "reason": "insufficient_sources"
                            })
                
                return missing_periods
                
        except Exception as e:
            self.logger.error("missing_data_analysis_error", error=str(e))
            return []

    async def _estimate_backfill_records(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> int:
        """
        Estimate number of articles that would be backfilled
        """
        
        # For news, estimate based on feeds and date range
        days = (end_date - start_date).days
        articles_per_day = len(self.config.rss_feeds) * 15  # Rough estimate
        
        return days * articles_per_day

    async def _get_required_fields(self) -> List[str]:
        """Get required fields for data validation"""
        return ["title", "source", "collected_at"]

    async def _generate_data_quality_report(self) -> DataQualityReport:
        """Generate comprehensive data quality report for news data"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Get total records
                cursor.execute("SELECT COUNT(*) FROM crypto_news")
                total_records = cursor.fetchone()[0]
                
                # Get records with missing titles or content
                cursor.execute("""
                    SELECT COUNT(*) FROM crypto_news 
                    WHERE title IS NULL OR title = '' OR (content IS NULL OR content = '')
                """)
                invalid_records = cursor.fetchone()[0]
                
                # Get duplicate records (same URL hash)
                cursor.execute("""
                    SELECT COUNT(*) - COUNT(DISTINCT url_hash) as duplicates
                    FROM crypto_news
                """)
                duplicate_records = cursor.fetchone()[0] or 0
                
                valid_records = total_records - invalid_records
                data_quality_score = (valid_records / max(total_records, 1)) * 100
                
                validation_errors = []
                if invalid_records > 0:
                    validation_errors.append(f"{invalid_records} records missing title or content")
                if duplicate_records > 0:
                    validation_errors.append(f"{duplicate_records} duplicate records detected")
                
                return DataQualityReport(
                    total_records=total_records,
                    valid_records=valid_records,
                    invalid_records=invalid_records,
                    duplicate_records=duplicate_records,
                    validation_errors=validation_errors,
                    data_quality_score=data_quality_score
                )
                
        except Exception as e:
            self.logger.error("data_quality_report_error", error=str(e))
            return DataQualityReport(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                duplicate_records=0,
                validation_errors=[f"Error generating report: {str(e)}"],
                data_quality_score=0.0
            )

async def main():
    """Main function to run the enhanced news collector"""
    collector = EnhancedNewsCollector()
    
    # Start the collection loop
    collection_task = asyncio.create_task(collector.run_collection_loop())
    
    # Start the web server for API endpoints
    server_task = asyncio.create_task(
        asyncio.to_thread(collector.run_server, host="0.0.0.0", port=8000)
    )
    
    # Wait for either task to complete (or shutdown signal)
    try:
        await asyncio.gather(collection_task, server_task, return_exceptions=True)
    except KeyboardInterrupt:
        collector.logger.info("shutdown_requested", signal="SIGINT")
        collector._shutdown_event.set()

if __name__ == "__main__":
    asyncio.run(main())