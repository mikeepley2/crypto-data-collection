#!/usr/bin/env python3
"""
Example News Collector Implementation using Base Collector Template
Demonstrates how to extend the base collector for specific data collection needs
"""

import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import feedparser
import mysql.connector
from base_collector_template import BaseCollector, CollectorConfig

class NewsCollectorConfig(CollectorConfig):
    """Extended configuration for news collector"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # News-specific configuration
        self.rss_feeds = [
            'https://cryptoslate.com/feed/',
            'https://beincrypto.com/feed/',
            'https://coinjournal.net/feed/',
            'https://cryptonews.com/news/feed/'
        ]
        self.max_articles_per_feed = 50
        self.article_processing_batch = 10

    @classmethod
    def from_env(cls) -> 'NewsCollectorConfig':
        """Load configuration from environment variables"""
        config = super().from_env()
        # Convert to NewsCollectorConfig
        news_config = cls(**config.__dict__)
        news_config.service_name = "enhanced-crypto-news"
        return news_config

class EnhancedNewsCollector(BaseCollector):
    """
    Enhanced News Collector implementing the base collector template
    Collects cryptocurrency news from RSS feeds
    """
    
    def __init__(self):
        config = NewsCollectorConfig.from_env()
        super().__init__(config)
        self.session = None

    async def collect_data(self) -> int:
        """
        Collect news data from RSS feeds
        Returns number of articles collected
        """
        total_articles = 0
        
        self.logger.info("news_collection_started", feeds=len(self.config.rss_feeds))
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.api_timeout)) as session:
            self.session = session
            
            for feed_url in self.config.rss_feeds:
                try:
                    articles = await self._collect_from_feed(feed_url)
                    total_articles += articles
                    
                    self.metrics['api_requests_total'].labels(endpoint=feed_url, status='success').inc()
                    
                except Exception as e:
                    self.logger.error("feed_collection_error", feed=feed_url, error=str(e))
                    self.metrics['api_requests_total'].labels(endpoint=feed_url, status='error').inc()
        
        self.logger.info("news_collection_completed", total_articles=total_articles)
        return total_articles

    async def _collect_from_feed(self, feed_url: str) -> int:
        """Collect articles from a single RSS feed"""
        
        self.logger.debug("processing_feed", url=feed_url)
        
        try:
            # Fetch RSS feed
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    self.logger.warning("feed_request_failed", url=feed_url, status=response.status)
                    return 0
                
                content = await response.text()
                
            # Parse RSS feed
            feed = feedparser.parse(content)
            
            if feed.bozo:
                self.logger.warning("feed_parse_warning", url=feed_url, error=feed.bozo_exception)
            
            # Process articles
            articles_saved = 0
            articles_batch = []
            
            for entry in feed.entries[:self.config.max_articles_per_feed]:
                try:
                    article = self._parse_article(entry, feed_url)
                    if article:
                        articles_batch.append(article)
                        
                        if len(articles_batch) >= self.config.article_processing_batch:
                            saved = await self._save_articles_batch(articles_batch)
                            articles_saved += saved
                            articles_batch = []
                            
                except Exception as e:
                    self.logger.warning("article_parse_error", url=feed_url, error=str(e))
            
            # Save remaining articles
            if articles_batch:
                saved = await self._save_articles_batch(articles_batch)
                articles_saved += saved
            
            self.logger.info("feed_processed", url=feed_url, articles=articles_saved)
            return articles_saved
            
        except Exception as e:
            self.logger.error("feed_processing_error", url=feed_url, error=str(e))
            raise

    def _parse_article(self, entry, feed_url: str) -> Optional[Dict[str, Any]]:
        """Parse a single RSS entry into article data"""
        
        try:
            # Extract article data
            article = {
                'title': entry.get('title', '').strip(),
                'url': entry.get('link', '').strip(),
                'description': entry.get('summary', '').strip(),
                'published_date': self._parse_date(entry.get('published', '')),
                'source': feed_url,
                'collected_at': datetime.now(timezone.utc)
            }
            
            # Validate required fields
            if not article['title'] or not article['url']:
                return None
                
            return article
            
        except Exception as e:
            self.logger.warning("article_parse_error", entry_title=entry.get('title', 'unknown'), error=str(e))
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse RSS date string to datetime"""
        
        if not date_str:
            return None
            
        try:
            # feedparser usually handles this well
            import time
            time_struct = feedparser._parse_date(date_str)
            if time_struct:
                return datetime(*time_struct[:6], tzinfo=timezone.utc)
        except Exception:
            pass
            
        return None

    async def _save_articles_batch(self, articles: List[Dict[str, Any]]) -> int:
        """Save a batch of articles to database"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Insert articles
                insert_query = """
                INSERT INTO crypto_news (title, url, description, published_date, source, collected_at)
                VALUES (%(title)s, %(url)s, %(description)s, %(published_date)s, %(source)s, %(collected_at)s)
                ON DUPLICATE KEY UPDATE
                    description = VALUES(description),
                    collected_at = VALUES(collected_at)
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
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) as total_articles,
                       MAX(published_date) as latest_article,
                       MAX(collected_at) as last_collection
                FROM crypto_news
            """)
            
            result = cursor.fetchone()
            
            return {
                "crypto_news": {
                    "total_articles": result[0] if result else 0,
                    "latest_article": result[1] if result and result[1] else None,
                    "last_collection": result[2] if result and result[2] else None
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
        For news, we look for gaps in collection dates
        """
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Find gaps in news collection
                cursor.execute("""
                    SELECT DATE(published_date) as news_date, COUNT(*) as article_count
                    FROM crypto_news
                    WHERE published_date BETWEEN %s AND %s
                    GROUP BY DATE(published_date)
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
                    for i, (news_date, article_count) in enumerate(results):
                        if article_count < 10:  # Threshold for "low" news count
                            missing_periods.append({
                                "date": news_date,
                                "article_count": article_count,
                                "reason": "low_count"
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
        articles_per_day = len(self.config.rss_feeds) * 10  # Rough estimate
        
        return days * articles_per_day

async def main():
    """Main function to run the news collector"""
    collector = EnhancedNewsCollector()
    
    # Start the collection loop
    collection_task = asyncio.create_task(collector.run_collection_loop())
    
    # Start the web server
    server_task = asyncio.create_task(
        asyncio.to_thread(collector.run_server, host="0.0.0.0", port=8000)
    )
    
    # Wait for either task to complete
    await asyncio.gather(collection_task, server_task, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())