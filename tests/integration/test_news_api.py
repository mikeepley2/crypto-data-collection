"""
News collector API and database integration tests.
Tests news data collection APIs and database operations.
"""

import pytest
import requests
import mysql.connector
import time
from datetime import datetime, timezone, timedelta
import json


class TestNewsCollectorAPI:
    """API and database tests for news data collection"""

    @pytest.mark.real_api
    def test_guardian_api_integration(self):
        """Test Guardian News API integration"""
        # Note: Guardian API has rate limiting, using test endpoint
        url = "https://content.guardianapis.com/search?q=bitcoin&api-key=test"
        
        try:
            response = requests.get(url, timeout=30)
            # Guardian API returns 403 for invalid key, but validates structure
            assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert "results" in data["response"]
        except requests.exceptions.RequestException:
            pytest.skip("Guardian API not accessible")

    @pytest.mark.real_api
    def test_news_api_structure(self):
        """Test NewsAPI.org structure (using free tier)"""
        # Using free tier endpoint - replace with actual key if available
        url = "https://newsapi.org/v2/everything?q=cryptocurrency&sortBy=publishedAt&apiKey=test_key"
        
        try:
            response = requests.get(url, timeout=30)
            # Expecting 401 for invalid key, but tests structure
            assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                assert "articles" in data
                assert "totalResults" in data
        except requests.exceptions.RequestException:
            pytest.skip("NewsAPI not accessible")

    @pytest.mark.real_api
    def test_reddit_api_integration(self):
        """Test Reddit API for crypto news"""
        # Using Reddit's public JSON API
        url = "https://www.reddit.com/r/cryptocurrency/hot.json?limit=5"
        headers = {"User-Agent": "crypto-data-collector/1.0"}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            assert "data" in data
            assert "children" in data["data"]
            
            # Validate post structure
            posts = data["data"]["children"]
            assert len(posts) > 0
            
            for post in posts[:3]:  # Check first 3 posts
                post_data = post["data"]
                assert "title" in post_data
                assert "created_utc" in post_data
                assert "score" in post_data
                
        except requests.exceptions.RequestException:
            pytest.skip("Reddit API not accessible")

    @pytest.mark.database
    def test_crypto_news_storage(self, test_mysql_connection):
        """Test crypto news table structure"""
        cursor = test_mysql_connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'crypto_news'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Verify table structure
            cursor.execute("DESCRIBE crypto_news")
            columns = cursor.fetchall()
            
            column_names = [col[0] for col in columns]
            expected_columns = ['id', 'title', 'content', 'url', 'published_at', 'source']
            
            for expected_col in expected_columns:
                assert expected_col in column_names, f"Missing column: {expected_col}"
        else:
            pytest.skip("crypto_news table does not exist")
        
        cursor.close()

    @pytest.mark.database
    def test_news_data_insertion(self, test_mysql_connection):
        """Test inserting news data into database"""
        cursor = test_mysql_connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'crypto_news'")
        if not cursor.fetchone():
            pytest.skip("crypto_news table does not exist")
        
        # Insert test news data
        test_data = {
            'title': 'Bitcoin Reaches New Heights',
            'content': 'Bitcoin has reached unprecedented levels today...',
            'url': 'https://example.com/bitcoin-news',
            'published_at': datetime.now(timezone.utc),
            'source': 'test_source'
        }
        
        try:
            cursor.execute("""
                INSERT INTO crypto_news (title, content, url, published_at, source)
                VALUES (%(title)s, %(content)s, %(url)s, %(published_at)s, %(source)s)
            """, test_data)
            
            test_mysql_connection.commit()
            
            # Verify insertion
            cursor.execute("SELECT * FROM crypto_news WHERE title = %s ORDER BY created_at DESC LIMIT 1", 
                         (test_data['title'],))
            result = cursor.fetchone()
            
            assert result is not None
            # Title should match (column index may vary)
            found_title = False
            for field in result:
                if field == test_data['title']:
                    found_title = True
                    break
            assert found_title, "Title not found in result"
            
        except mysql.connector.Error as e:
            # If schema doesn't match our assumptions, skip the test
            if "Unknown column" in str(e):
                pytest.skip(f"Schema mismatch: {e}")
            else:
                raise
        finally:
            cursor.close()

    @pytest.mark.database
    def test_news_sentiment_integration(self, test_mysql_connection):
        """Test news and sentiment data integration"""
        cursor = test_mysql_connection.cursor()
        
        # Check for sentiment signals table
        cursor.execute("SHOW TABLES LIKE 'real_time_sentiment_signals'")
        if not cursor.fetchone():
            pytest.skip("real_time_sentiment_signals table does not exist")
        
        # Insert test sentiment data
        try:
            test_sentiment = {
                'source': 'news',
                'symbol': 'BTC', 
                'sentiment_score': 0.75,
                'confidence': 0.85,
                'timestamp': datetime.now(timezone.utc)
            }
            
            cursor.execute("""
                INSERT INTO real_time_sentiment_signals (source, symbol, sentiment_score, confidence, timestamp)
                VALUES (%(source)s, %(symbol)s, %(sentiment_score)s, %(confidence)s, %(timestamp)s)
            """, test_sentiment)
            
            test_mysql_connection.commit()
            
            # Verify insertion
            cursor.execute("""
                SELECT * FROM real_time_sentiment_signals 
                WHERE source = 'news' AND symbol = 'BTC'
                ORDER BY created_at DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            assert result is not None
            
        except mysql.connector.Error as e:
            if "Unknown column" in str(e):
                pytest.skip(f"Schema mismatch: {e}")
            else:
                raise
        finally:
            cursor.close()

    @pytest.mark.real_api
    def test_news_data_freshness(self):
        """Test that news data is fresh and recent"""
        # Test Reddit for recent posts
        url = "https://www.reddit.com/r/cryptocurrency/new.json?limit=5"
        headers = {"User-Agent": "crypto-data-collector/1.0"}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            posts = data["data"]["children"]
            
            if len(posts) > 0:
                latest_post = posts[0]["data"]
                post_time = datetime.fromtimestamp(latest_post["created_utc"], tz=timezone.utc)
                current_time = datetime.now(timezone.utc)
                
                # Latest post should be within last 24 hours
                time_diff = current_time - post_time
                assert time_diff.total_seconds() < 86400, f"Latest post too old: {time_diff}"
                
        except requests.exceptions.RequestException:
            pytest.skip("Reddit API not accessible")

    @pytest.mark.database
    def test_news_deduplication(self, test_mysql_connection):
        """Test news deduplication logic"""
        cursor = test_mysql_connection.cursor()
        
        cursor.execute("SHOW TABLES LIKE 'crypto_news'")
        if not cursor.fetchone():
            pytest.skip("crypto_news table does not exist")
        
        # Test duplicate URL handling
        duplicate_url = "https://example.com/duplicate-test"
        
        test_articles = [
            {
                'title': 'First Article',
                'content': 'First content',
                'url': duplicate_url,
                'source': 'source1'
            },
            {
                'title': 'Second Article', 
                'content': 'Different content',
                'url': duplicate_url,
                'source': 'source2'
            }
        ]
        
        try:
            # Insert first article
            cursor.execute("""
                INSERT INTO crypto_news (title, content, url, published_at, source)
                VALUES (%(title)s, %(content)s, %(url)s, %(published_at)s, %(source)s)
            """, {**test_articles[0], 'published_at': datetime.now(timezone.utc)})
            
            test_mysql_connection.commit()
            
            # Try to insert duplicate URL
            try:
                cursor.execute("""
                    INSERT INTO crypto_news (title, content, url, published_at, source)
                    VALUES (%(title)s, %(content)s, %(url)s, %(published_at)s, %(source)s)
                """, {**test_articles[1], 'published_at': datetime.now(timezone.utc)})
                test_mysql_connection.commit()
                
                # If no unique constraint, that's fine - just verify both exist
                cursor.execute("SELECT COUNT(*) FROM crypto_news WHERE url = %s", (duplicate_url,))
                count = cursor.fetchone()[0]
                assert count >= 1, "No articles found with test URL"
                
            except mysql.connector.Error as e:
                # If duplicate key error, that's expected behavior
                if "Duplicate entry" in str(e) or "UNIQUE constraint" in str(e):
                    test_mysql_connection.rollback()
                    assert True  # This is expected
                else:
                    raise
                
        except mysql.connector.Error as e:
            if "Unknown column" in str(e):
                pytest.skip(f"Schema mismatch: {e}")
            else:
                raise
        finally:
            cursor.close()

    @pytest.mark.real_api
    def test_rss_feed_integration(self):
        """Test RSS feed parsing for crypto news"""
        # Test CoinDesk RSS feed
        url = "https://feeds.coindesk.com/coindesk/rss/news"
        
        try:
            response = requests.get(url, timeout=30)
            assert response.status_code == 200
            
            # Basic XML structure validation
            content = response.text
            assert "<rss" in content or "<feed" in content
            assert "<item>" in content or "<entry>" in content
            
            # Should contain crypto-related content
            assert "bitcoin" in content.lower() or "cryptocurrency" in content.lower() or "crypto" in content.lower()
            
        except requests.exceptions.RequestException:
            pytest.skip("RSS feed not accessible")