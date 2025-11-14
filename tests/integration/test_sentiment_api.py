"""
Sentiment analysis collector API and database integration tests.
Tests sentiment data collection and analysis operations.
"""

import pytest
import requests
import mysql.connector
import time
import json
from datetime import datetime, timezone, timedelta


class TestSentimentCollectorAPI:
    """API and database tests for sentiment analysis collection"""

    @pytest.mark.real_api
    def test_twitter_sentiment_structure(self):
        """Test Twitter API structure for sentiment analysis"""
        # Note: Twitter API v2 requires authentication, testing structure
        # This would normally require valid bearer token
        
        # Test public endpoint structure (will return 401 but validates structure)
        url = "https://api.twitter.com/2/tweets/search/recent?query=bitcoin"
        
        try:
            response = requests.get(url, timeout=30)
            # Expecting 401 Unauthorized without valid token
            assert response.status_code in [200, 401, 429], f"Unexpected status: {response.status_code}"
            
            if response.status_code == 401:
                # Check error structure
                try:
                    error_data = response.json()
                    assert "errors" in error_data or "title" in error_data
                except json.JSONDecodeError:
                    pass  # Some endpoints return plain text errors
                    
        except requests.exceptions.RequestException:
            pytest.skip("Twitter API not accessible")

    @pytest.mark.real_api
    def test_reddit_sentiment_data(self):
        """Test Reddit data for sentiment analysis"""
        # Test Reddit cryptocurrency discussions
        url = "https://www.reddit.com/r/cryptocurrency/hot.json?limit=10"
        headers = {"User-Agent": "crypto-sentiment-collector/1.0"}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            posts = data["data"]["children"]
            
            assert len(posts) > 0
            
            # Check for sentiment-relevant data
            for post in posts[:5]:
                post_data = post["data"]
                assert "title" in post_data
                assert "selftext" in post_data or "url" in post_data
                assert "score" in post_data  # Upvotes - downvotes
                assert "num_comments" in post_data
                
                # Validate engagement metrics
                score = post_data["score"]
                comments = post_data["num_comments"]
                
                assert isinstance(score, int)
                assert isinstance(comments, int)
                assert comments >= 0
                
        except requests.exceptions.RequestException:
            pytest.skip("Reddit API not accessible")

    @pytest.mark.database
    def test_sentiment_signals_storage(self, test_mysql_connection):
        """Test sentiment signals table structure"""
        cursor = test_mysql_connection.cursor()
        
        # Verify real_time_sentiment_signals table exists
        cursor.execute("DESCRIBE real_time_sentiment_signals")
        columns = cursor.fetchall()
        
        column_names = [col[0] for col in columns]
        expected_columns = ['id', 'source', 'symbol', 'sentiment_score', 'confidence', 'timestamp']
        
        for expected_col in expected_columns:
            assert expected_col in column_names, f"Missing column: {expected_col}"
        
        cursor.close()

    @pytest.mark.database
    def test_sentiment_data_insertion(self, test_mysql_connection):
        """Test inserting sentiment analysis data"""
        cursor = test_mysql_connection.cursor()
        
        # Insert test sentiment data
        test_sentiments = [
            {'source': 'twitter', 'symbol': 'BTC', 'sentiment_score': 0.75, 'confidence': 0.85},
            {'source': 'reddit', 'symbol': 'ETH', 'sentiment_score': -0.25, 'confidence': 0.70},
            {'source': 'news', 'symbol': 'ADA', 'sentiment_score': 0.10, 'confidence': 0.60},
        ]
        
        current_time = datetime.now(timezone.utc)
        
        for sentiment in test_sentiments:
            cursor.execute("""
                INSERT INTO real_time_sentiment_signals (source, symbol, sentiment_score, confidence, timestamp)
                VALUES (%(source)s, %(symbol)s, %(sentiment_score)s, %(confidence)s, %(timestamp)s)
            """, {**sentiment, 'timestamp': current_time})
        
        test_mysql_connection.commit()
        
        # Verify insertions
        cursor.execute("SELECT COUNT(*) FROM real_time_sentiment_signals WHERE symbol IN ('BTC', 'ETH', 'ADA')")
        count = cursor.fetchone()[0]
        assert count >= 3, f"Expected at least 3 sentiment records, found {count}"
        
        # Verify sentiment score ranges
        cursor.execute("""
            SELECT sentiment_score, confidence FROM real_time_sentiment_signals 
            WHERE symbol IN ('BTC', 'ETH', 'ADA')
        """)
        
        for score, confidence in cursor.fetchall():
            assert -1.0 <= float(score) <= 1.0, f"Sentiment score {score} outside valid range [-1,1]"
            assert 0.0 <= float(confidence) <= 1.0, f"Confidence {confidence} outside valid range [0,1]"
        
        cursor.close()

    @pytest.mark.database
    def test_sentiment_aggregation(self, test_mysql_connection):
        """Test sentiment data aggregation and analysis"""
        cursor = test_mysql_connection.cursor()
        
        # Insert multiple sentiment readings for aggregation
        symbol = 'SENT_AGG'
        sentiments = [
            {'source': 'twitter', 'score': 0.8, 'confidence': 0.9},
            {'source': 'twitter', 'score': 0.6, 'confidence': 0.8},
            {'source': 'reddit', 'score': -0.2, 'confidence': 0.7},
            {'source': 'news', 'score': 0.4, 'confidence': 0.85},
        ]
        
        base_time = datetime.now(timezone.utc)
        
        for i, sentiment in enumerate(sentiments):
            timestamp = base_time - timedelta(minutes=i*15)  # 15 minute intervals
            cursor.execute("""
                INSERT INTO real_time_sentiment_signals (source, symbol, sentiment_score, confidence, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (sentiment['source'], symbol, sentiment['score'], sentiment['confidence'], timestamp))
        
        test_mysql_connection.commit()
        
        # Test aggregation queries
        # Average sentiment by source
        cursor.execute("""
            SELECT source, AVG(sentiment_score) as avg_sentiment, AVG(confidence) as avg_confidence
            FROM real_time_sentiment_signals 
            WHERE symbol = %s
            GROUP BY source
        """, (symbol,))
        
        source_aggregates = cursor.fetchall()
        assert len(source_aggregates) >= 2, "Should have aggregates for at least 2 sources"
        
        # Overall weighted sentiment (by confidence)
        cursor.execute("""
            SELECT 
                SUM(sentiment_score * confidence) / SUM(confidence) as weighted_sentiment,
                AVG(confidence) as avg_confidence,
                COUNT(*) as total_signals
            FROM real_time_sentiment_signals 
            WHERE symbol = %s
        """, (symbol,))
        
        overall_result = cursor.fetchone()
        weighted_sentiment, avg_confidence, total_signals = overall_result
        
        assert total_signals >= 4, f"Expected at least 4 signals, found {total_signals}"
        assert -1.0 <= float(weighted_sentiment) <= 1.0, f"Weighted sentiment {weighted_sentiment} outside valid range"
        assert 0.0 <= float(avg_confidence) <= 1.0, f"Average confidence {avg_confidence} outside valid range"
        
        cursor.close()

    @pytest.mark.database
    def test_sentiment_time_series(self, test_mysql_connection):
        """Test sentiment time series analysis"""
        cursor = test_mysql_connection.cursor()
        
        symbol = 'TIME_SERIES'
        
        # Create 24 hours of sentiment data (hourly)
        base_sentiment = 0.2
        for hour in range(24):
            # Simulate sentiment trend over time
            trend = 0.01 * hour  # Gradual positive trend
            noise = 0.1 * ((-1) ** hour)  # Some volatility
            sentiment = base_sentiment + trend + noise
            
            # Clamp to valid range
            sentiment = max(-1.0, min(1.0, sentiment))
            
            timestamp = datetime.now(timezone.utc) - timedelta(hours=23-hour)
            
            cursor.execute("""
                INSERT INTO real_time_sentiment_signals (source, symbol, sentiment_score, confidence, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, ('synthetic', symbol, sentiment, 0.8, timestamp))
        
        test_mysql_connection.commit()
        
        # Analyze time series
        cursor.execute("""
            SELECT sentiment_score, timestamp 
            FROM real_time_sentiment_signals 
            WHERE symbol = %s 
            ORDER BY timestamp ASC
        """, (symbol,))
        
        time_series = [(float(row[0]), row[1]) for row in cursor.fetchall()]
        
        assert len(time_series) >= 20, f"Expected at least 20 time series points, found {len(time_series)}"
        
        # Check for general positive trend
        first_half = time_series[:len(time_series)//2]
        second_half = time_series[len(time_series)//2:]
        
        avg_first = sum(score for score, _ in first_half) / len(first_half)
        avg_second = sum(score for score, _ in second_half) / len(second_half)
        
        # Should show positive trend overall
        assert avg_second > avg_first - 0.1, "Expected positive sentiment trend over time"
        
        cursor.close()

    @pytest.mark.database
    def test_sentiment_ml_features(self, test_mysql_connection):
        """Test sentiment ML features generation and storage"""
        cursor = test_mysql_connection.cursor()
        
        # Check if ML features table exists
        cursor.execute("SHOW TABLES LIKE 'ml_features_materialized'")
        if not cursor.fetchone():
            pytest.skip("ml_features_materialized table does not exist")
        
        # Insert sentiment-derived features
        try:
            test_features = {
                'symbol': 'ML_TEST',
                'feature_name': 'sentiment_momentum_7d',
                'feature_value': 0.15,
                'timestamp': datetime.now(timezone.utc)
            }
            
            cursor.execute("""
                INSERT INTO ml_features_materialized (symbol, feature_name, feature_value, timestamp)
                VALUES (%(symbol)s, %(feature_name)s, %(feature_value)s, %(timestamp)s)
            """, test_features)
            
            test_mysql_connection.commit()
            
            # Verify insertion
            cursor.execute("""
                SELECT feature_value FROM ml_features_materialized 
                WHERE symbol = 'ML_TEST' AND feature_name = 'sentiment_momentum_7d'
            """)
            
            result = cursor.fetchone()
            assert result is not None
            assert abs(float(result[0]) - 0.15) < 0.001
            
        except mysql.connector.Error as e:
            if "Unknown column" in str(e):
                pytest.skip(f"ML features schema mismatch: {e}")
            else:
                raise
        finally:
            cursor.close()

    @pytest.mark.real_api
    def test_fear_greed_index_integration(self):
        """Test Fear & Greed Index API integration"""
        # Alternative.me Fear & Greed Index
        url = "https://api.alternative.me/fng/?limit=10"
        
        try:
            response = requests.get(url, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            assert "data" in data
            
            fng_data = data["data"]
            assert len(fng_data) > 0
            
            # Validate Fear & Greed data structure
            latest = fng_data[0]
            assert "value" in latest
            assert "value_classification" in latest
            assert "timestamp" in latest
            
            # Validate value range (0-100)
            fng_value = int(latest["value"])
            assert 0 <= fng_value <= 100, f"Fear & Greed value {fng_value} outside valid range"
            
            # Validate classification
            classification = latest["value_classification"]
            valid_classifications = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
            assert classification in valid_classifications, f"Invalid classification: {classification}"
            
        except requests.exceptions.RequestException:
            pytest.skip("Fear & Greed Index API not accessible")

    @pytest.mark.database
    def test_sentiment_source_reliability(self, test_mysql_connection):
        """Test sentiment source reliability tracking"""
        cursor = test_mysql_connection.cursor()
        
        # Insert sentiment data with different source reliabilities
        sources_data = [
            {'source': 'high_reliability', 'symbol': 'REL_TEST', 'score': 0.8, 'confidence': 0.95},
            {'source': 'medium_reliability', 'symbol': 'REL_TEST', 'score': 0.6, 'confidence': 0.75},
            {'source': 'low_reliability', 'symbol': 'REL_TEST', 'score': -0.5, 'confidence': 0.45},
        ]
        
        for source_data in sources_data:
            cursor.execute("""
                INSERT INTO real_time_sentiment_signals (source, symbol, sentiment_score, confidence, timestamp)
                VALUES (%(source)s, %(symbol)s, %(score)s, %(confidence)s, %(timestamp)s)
            """, {**source_data, 'timestamp': datetime.now(timezone.utc)})
        
        test_mysql_connection.commit()
        
        # Calculate reliability-weighted sentiment
        cursor.execute("""
            SELECT 
                source,
                sentiment_score,
                confidence,
                sentiment_score * confidence as weighted_sentiment
            FROM real_time_sentiment_signals 
            WHERE symbol = 'REL_TEST'
        """)
        
        results = cursor.fetchall()
        assert len(results) >= 3, "Should have data from at least 3 sources"
        
        # Verify that high confidence sources have more impact
        high_conf_impact = None
        low_conf_impact = None
        
        for source, score, confidence, weighted in results:
            if confidence > 0.9:
                high_conf_impact = abs(float(weighted))
            elif confidence < 0.5:
                low_conf_impact = abs(float(weighted))
        
        if high_conf_impact and low_conf_impact:
            assert high_conf_impact >= low_conf_impact, "High confidence sources should have more impact"
        
        cursor.close()

    @pytest.mark.real_api
    def test_crypto_news_sentiment_relevance(self):
        """Test crypto news relevance for sentiment analysis"""
        # Test CoinDesk RSS feed for sentiment-relevant content
        url = "https://feeds.coindesk.com/coindesk/rss/news"
        
        try:
            response = requests.get(url, timeout=30)
            assert response.status_code == 200
            
            content = response.text.lower()
            
            # Check for sentiment-relevant keywords
            positive_keywords = ['bullish', 'surge', 'rally', 'gains', 'optimistic', 'breakthrough']
            negative_keywords = ['bearish', 'crash', 'decline', 'fear', 'pessimistic', 'concern']
            
            positive_found = any(keyword in content for keyword in positive_keywords)
            negative_found = any(keyword in content for keyword in negative_keywords)
            
            # Should contain some sentiment-relevant content
            assert positive_found or negative_found, "No sentiment-relevant keywords found in crypto news"
            
            # Should contain crypto-related terms
            crypto_keywords = ['bitcoin', 'ethereum', 'cryptocurrency', 'crypto', 'blockchain']
            crypto_found = any(keyword in content for keyword in crypto_keywords)
            assert crypto_found, "No crypto-related keywords found in news feed"
            
        except requests.exceptions.RequestException:
            pytest.skip("Crypto news feed not accessible")