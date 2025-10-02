#!/usr/bin/env python3

import mysql.connector
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_db_connection(database='crypto_prices'):
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database=database
    )


def check_final_status():
    """Check final status of news and sentiment systems"""
    try:
        print("📊 FINAL NEWS & SENTIMENT SYSTEM STATUS")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Check crypto_news database
        news_conn = get_db_connection('crypto_news')
        news_cursor = news_conn.cursor()
        
        # News collection status
        news_cursor.execute("SELECT COUNT(*) FROM crypto_news_data")
        total_news = news_cursor.fetchone()[0]
        
        news_cursor.execute("SELECT MAX(created_at) FROM crypto_news_data")
        latest_news = news_cursor.fetchone()[0]
        
        print(f"📰 NEWS COLLECTION STATUS:")
        print(f"  Total news articles: {total_news:,}")
        print(f"  Latest article: {latest_news}")
        
        # Social media status
        news_cursor.execute("SELECT COUNT(*) FROM social_media_posts")
        total_social = news_cursor.fetchone()[0]
        
        news_cursor.execute("SELECT MAX(created_at) FROM social_media_posts")
        latest_social = news_cursor.fetchone()[0]
        
        print(f"\n📱 SOCIAL MEDIA STATUS:")
        print(f"  Total social posts: {total_social:,}")
        print(f"  Latest social post: {latest_social}")
        
        # Sentiment data status
        news_cursor.execute("SELECT COUNT(*) FROM sentiment_data")
        total_sentiment = news_cursor.fetchone()[0]
        
        news_cursor.execute("SELECT MAX(created_at) FROM sentiment_data")
        latest_sentiment = news_cursor.fetchone()[0]
        
        print(f"\n🧠 SENTIMENT ANALYSIS STATUS:")
        print(f"  Total sentiment records: {total_sentiment:,}")
        print(f"  Latest sentiment: {latest_sentiment}")
        
        news_cursor.close()
        news_conn.close()
        
        # Check ml_features_materialized
        prices_conn = get_db_connection('crypto_prices')
        prices_cursor = prices_conn.cursor()
        
        prices_cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cb,
                SUM(CASE WHEN avg_vader_score IS NOT NULL THEN 1 ELSE 0 END) as has_vader,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_news,
                SUM(CASE WHEN crypto_sentiment_count > 0 THEN 1 ELSE 0 END) as has_count
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = prices_cursor.fetchone()
        total = result[0]
        
        print(f"\n📈 ML FEATURES SENTIMENT INTEGRATION (7 days):")
        print(f"  Total ML records: {total:,}")
        if total > 0:
            print(f"  CryptoBERT coverage: {result[1]:,} ({result[1]/total*100:.1f}%)")
            print(f"  VADER coverage: {result[2]:,} ({result[2]/total*100:.1f}%)")
            print(f"  Social sentiment: {result[3]:,} ({result[3]/total*100:.1f}%)")
            print(f"  News sentiment: {result[4]:,} ({result[4]/total*100:.1f}%)")
            print(f"  Sentiment counts: {result[5]:,} ({result[5]/total*100:.1f}%)")
        
        # Check recent activity
        prices_cursor.execute("""
            SELECT COUNT(*) FROM ml_features_materialized
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
              AND (avg_cryptobert_score IS NOT NULL 
                   OR social_avg_sentiment IS NOT NULL 
                   OR news_sentiment IS NOT NULL)
        """)
        
        recent_updates = prices_cursor.fetchone()[0]
        print(f"\n⏰ RECENT ACTIVITY:")
        print(f"  Sentiment updates (last hour): {recent_updates}")
        
        prices_cursor.close()
        prices_conn.close()
        
        # Assessment
        print(f"\n🎯 SYSTEM ASSESSMENT:")
        
        # News freshness (within last 48 hours)
        news_fresh = latest_news and (datetime.now() - latest_news).days < 2
        print(f"  News Collection: {'✅ Fresh' if news_fresh else '⚠️ Stale'}")
        
        # Social freshness (within last week)
        social_fresh = latest_social and (datetime.now() - latest_social).days < 7
        print(f"  Social Collection: {'✅ Recent' if social_fresh else '⚠️ Stale'}")
        
        # Sentiment coverage
        sentiment_coverage = (result[4]/total*100) if total > 0 else 0
        sentiment_good = sentiment_coverage > 5
        print(f"  Sentiment Integration: {'✅ Working' if sentiment_good else '⚠️ Limited'}")
        
        # Overall assessment
        working_systems = sum([news_fresh, social_fresh, sentiment_good])
        
        print(f"\n🏆 OVERALL STATUS: {working_systems}/3 systems healthy")
        
        if working_systems == 3:
            print("🎉 All sentiment systems operational!")
        elif working_systems == 2:
            print("✅ Most systems working well")
        elif working_systems == 1:
            print("⚠️ Some systems need attention")
        else:
            print("🔧 Systems require maintenance")
        
        print("=" * 70)
        
        return working_systems >= 2
        
    except Exception as e:
        logger.error(f"Error checking final status: {e}")
        return False


def main():
    """Main function"""
    logger.info("Checking final news and sentiment system status...")
    return check_final_status()


if __name__ == "__main__":
    main()