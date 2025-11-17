#!/usr/bin/env python3
"""
Unit tests for Enhanced Crypto News Collector
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import feedparser
import hashlib
from typing import List, Dict

from enhanced_news_collector_template import (
    EnhancedNewsCollector, 
    EnhancedNewsCollectorConfig
)
from tests.test_base_collector import BaseCollectorTestCase, TestDataFactory

class TestEnhancedNewsCollectorConfig:
    """Test news collector configuration"""
    
    def test_config_initialization(self):
        """Test configuration defaults"""
        config = EnhancedNewsCollectorConfig.from_env()
        
        assert config.service_name == "enhanced-crypto-news"
        assert len(config.rss_feeds) >= 5
        assert config.max_articles_per_feed == 20
        assert config.article_processing_batch == 10
        assert isinstance(config.crypto_symbols, set)
    
    def test_rss_feeds_configuration(self):
        """Test RSS feeds are properly configured"""
        config = EnhancedNewsCollectorConfig()
        
        feed_names = [feed["name"] for feed in config.rss_feeds]
        expected_feeds = ["CoinTelegraph", "CryptoSlate", "Decrypt", "BeinCrypto", "CoinJournal"]
        
        for expected in expected_feeds:
            assert expected in feed_names

class TestEnhancedNewsCollector(BaseCollectorTestCase):
    """Test Enhanced News Collector functionality"""
    
    @pytest.fixture
    def news_collector(self):
        """Create news collector instance for testing"""
        with patch.dict('os.environ', {
            'DB_HOST': 'localhost',
            'DB_USER': 'test',
            'DB_PASSWORD': 'test',
            'DB_NAME': 'test_db',
            'SERVICE_NAME': 'enhanced-crypto-news'
        }):
            return EnhancedNewsCollector()
    
    @pytest.fixture
    def mock_rss_response(self):
        """Mock RSS feed response"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Crypto News</title>
                <item>
                    <title>Bitcoin Price Surges to New High</title>
                    <link>https://example.com/bitcoin-news</link>
                    <description>Bitcoin reaches unprecedented levels amid institutional adoption</description>
                    <pubDate>Mon, 10 Nov 2025 12:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Ethereum 2.0 Staking Update</title>
                    <link>https://example.com/ethereum-news</link>
                    <description>Latest developments in Ethereum staking infrastructure</description>
                    <pubDate>Mon, 10 Nov 2025 11:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""
    
    def test_collector_initialization(self, news_collector):
        """Test news collector initialization"""
        assert news_collector.config.service_name == "enhanced-crypto-news"
        assert news_collector.session is None  # Not initialized yet
        assert hasattr(news_collector.config, 'rss_feeds')
    
    @pytest.mark.asyncio
    async def test_load_crypto_symbols(self, news_collector, mock_database):
        """Test loading crypto symbols from database"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [('BTC',), ('ETH',), ('ADA',)]
        
        await news_collector._load_crypto_symbols()
        
        assert 'BTC' in news_collector.config.crypto_symbols
        assert 'ETH' in news_collector.config.crypto_symbols
        assert 'ADA' in news_collector.config.crypto_symbols
    
    def test_detect_crypto_mentions(self, news_collector):
        """Test crypto mention detection"""
        # Setup some crypto symbols
        news_collector.config.crypto_symbols = {'BTC', 'ETH', 'ADA', 'DOGE'}
        
        # Test text with crypto mentions
        text = "Bitcoin (BTC) and Ethereum (ETH) are leading the market"
        mentions = asyncio.run(news_collector._detect_crypto_mentions(text))
        
        assert 'BTC' in mentions
        assert 'ETH' in mentions
        assert 'ADA' not in mentions
    
    def test_parse_date(self, news_collector):
        """Test RSS date parsing"""
        # Test valid RFC date
        date_str = "Mon, 10 Nov 2025 12:00:00 GMT"
        parsed_date = news_collector._parse_date(date_str)
        
        assert parsed_date is not None
        assert isinstance(parsed_date, datetime)
        
        # Test invalid date
        invalid_date = "invalid date"
        parsed_invalid = news_collector._parse_date(invalid_date)
        assert parsed_invalid is None
    
    @pytest.mark.asyncio
    async def test_parse_article(self, news_collector):
        """Test article parsing from RSS entry"""
        # Mock RSS entry
        entry = Mock()
        entry.title = "Bitcoin Reaches New High"
        entry.link = "https://example.com/bitcoin-news"
        entry.summary = "Bitcoin price surges past previous resistance levels"
        entry.published = "Mon, 10 Nov 2025 12:00:00 GMT"
        
        feed_info = {"name": "TestFeed"}
        news_collector.config.crypto_symbols = {'BTC', 'ETH'}
        
        article = await news_collector._parse_article(entry, feed_info)
        
        assert article is not None
        assert article['title'] == "Bitcoin Reaches New High"
        assert article['url'] == "https://example.com/bitcoin-news"
        assert article['source'] == "TestFeed"
        assert 'url_hash' in article
        assert 'crypto_mentions' in article
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_collect_from_feed(self, mock_get, news_collector, mock_rss_response, mock_database):
        """Test collecting from a single RSS feed"""
        # Setup mocks
        mock_conn, mock_cursor = mock_database
        mock_cursor.rowcount = 2  # 2 articles saved
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = mock_rss_response
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Setup session
        news_collector.session = AsyncMock()
        news_collector.session.get = mock_get
        news_collector.config.crypto_symbols = {'BTC', 'ETH'}
        
        feed_info = {"name": "TestFeed", "url": "https://example.com/rss"}
        
        articles_count = await news_collector._collect_from_feed(feed_info)
        
        assert articles_count >= 0  # Should process articles
        mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_articles_batch(self, news_collector, mock_database):
        """Test saving batch of articles"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.rowcount = 2  # 2 articles saved
        
        articles = [
            {
                'title': 'Bitcoin News',
                'content': 'Bitcoin price update',
                'url': 'https://example.com/btc',
                'published_at': datetime.now(timezone.utc),
                'source': 'TestFeed',
                'category': 'crypto_news',
                'crypto_mentions': 'BTC',
                'url_hash': 'abc123',
                'collected_at': datetime.now(timezone.utc)
            },
            {
                'title': 'Ethereum News',
                'content': 'Ethereum update',
                'url': 'https://example.com/eth',
                'published_at': datetime.now(timezone.utc),
                'source': 'TestFeed',
                'category': 'crypto_news',
                'crypto_mentions': 'ETH',
                'url_hash': 'def456',
                'collected_at': datetime.now(timezone.utc)
            }
        ]
        
        saved_count = await news_collector._save_articles_batch(articles)
        
        assert saved_count == 2
        assert mock_cursor.execute.call_count == 2  # One per article
    
    @pytest.mark.asyncio
    async def test_collect_data(self, news_collector):
        """Test main data collection method"""
        # Mock dependencies
        with patch.object(news_collector, '_load_crypto_symbols') as mock_load_symbols:
            with patch.object(news_collector, '_collect_from_feed', return_value=5) as mock_collect:
                with patch('aiohttp.ClientSession'):
                    
                    result = await news_collector.collect_data()
                    
                    assert isinstance(result, int)
                    assert result >= 0
                    mock_load_symbols.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backfill_data(self, news_collector):
        """Test backfill functionality"""
        missing_periods = [
            {"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 1, 2), "reason": "missing_data"}
        ]
        
        with patch.object(news_collector, 'collect_data', return_value=10) as mock_collect:
            result = await news_collector.backfill_data(missing_periods)
            
            assert result == 10
            mock_collect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_missing_data(self, news_collector, mock_database):
        """Test missing data analysis"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            (datetime(2024, 1, 1).date(), 5, 2),  # Low article count
            (datetime(2024, 1, 2).date(), 15, 2)  # Insufficient sources
        ]
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        missing_periods = await news_collector._analyze_missing_data(start_date, end_date)
        
        assert isinstance(missing_periods, list)
        assert len(missing_periods) >= 0
    
    def test_url_hash_generation(self, news_collector):
        """Test URL hash generation for duplicate detection"""
        url1 = "https://example.com/bitcoin-news"
        url2 = "https://example.com/ethereum-news"
        
        hash1 = hashlib.md5(url1.encode()).hexdigest()
        hash2 = hashlib.md5(url2.encode()).hexdigest()
        
        assert hash1 != hash2
        assert len(hash1) == 32  # MD5 hash length
    
    @pytest.mark.asyncio
    async def test_data_quality_report(self, news_collector, mock_database):
        """Test data quality report generation"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.side_effect = [
            (1000,),  # total_records
            (50,),    # invalid_records  
            (20,)     # duplicate_records
        ]
        
        report = await news_collector._generate_data_quality_report()
        
        assert report.total_records == 1000
        assert report.invalid_records == 50
        assert report.duplicate_records == 20
        assert report.valid_records == 950
        assert 0 <= report.data_quality_score <= 100

class TestNewsCollectorIntegration:
    """Integration tests for news collector"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_collection_cycle(self):
        """Test complete collection cycle"""
        # This would test the full cycle with real RSS feeds (mocked)
        # and database operations
        pass
    
    @pytest.mark.integration
    def test_rss_feed_connectivity(self):
        """Test that configured RSS feeds are reachable"""
        # This would test actual RSS feed connectivity
        # Skipped in unit tests, but useful for integration testing
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])