#!/usr/bin/env python3

import mysql.connector
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection(database='crypto_news'):
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database=database
    )


def test_news_collection():
    """Test if news collection is working by monitoring database"""
    try:
        print("📰 TESTING NEWS COLLECTION")
        print("=" * 50)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get initial count
        cursor.execute("SELECT COUNT(*) FROM crypto_news_data")
        initial_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(created_at) FROM crypto_news_data")
        latest_before = cursor.fetchone()[0]
        
        print(f"Initial article count: {initial_count:,}")
        print(f"Latest article before test: {latest_before}")
        
        # Wait and check again
        print(f"Waiting 30 seconds for collection...")
        time.sleep(30)
        
        cursor.execute("SELECT COUNT(*) FROM crypto_news_data")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(created_at) FROM crypto_news_data")
        latest_after = cursor.fetchone()[0]
        
        print(f"Article count after wait: {new_count:,}")
        print(f"Latest article after test: {latest_after}")
        
        articles_added = new_count - initial_count
        print(f"New articles collected: {articles_added}")
        
        if articles_added > 0:
            print("✅ News collection is working!")
            
            # Show recent articles
            cursor.execute("""
                SELECT source, title, created_at 
                FROM crypto_news_data 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            recent_articles = cursor.fetchall()
            print(f"\nRecent articles:")
            for source, title, created_at in recent_articles:
                print(f"  {source}: {title[:60]}... ({created_at})")
                
        else:
            print("⚠️ No new articles collected during test")
        
        cursor.close()
        conn.close()
        return articles_added > 0
        
    except Exception as e:
        logger.error(f"Error testing news collection: {e}")
        return False


def test_sentiment_processing():
    """Test if sentiment processing is working"""
    try:
        print(f"\n🧠 TESTING SENTIMENT PROCESSING")
        print("=" * 50)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check recent sentiment data
        cursor.execute("""
            SELECT COUNT(*) FROM sentiment_data 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        recent_sentiment = cursor.fetchone()[0]
        
        print(f"Sentiment records (last hour): {recent_sentiment}")
        
        # Check social media posts
        cursor.execute("""
            SELECT COUNT(*) FROM social_media_posts 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        recent_social = cursor.fetchone()[0]
        
        print(f"Social posts (last hour): {recent_social}")
        
        # Check overall recent activity
        cursor.execute("""
            SELECT 
                'news' as type, COUNT(*) as count
            FROM crypto_news_data 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            UNION ALL
            SELECT 
                'social' as type, COUNT(*) as count
            FROM social_media_posts 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            UNION ALL
            SELECT 
                'sentiment' as type, COUNT(*) as count
            FROM sentiment_data 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        activity = cursor.fetchall()
        print(f"\n24-hour activity summary:")
        for activity_type, count in activity:
            print(f"  {activity_type}: {count} records")
        
        cursor.close()
        conn.close()
        return recent_sentiment > 0 or recent_social > 0
        
    except Exception as e:
        logger.error(f"Error testing sentiment processing: {e}")
        return False


def check_ml_features_sentiment():
    """Check if sentiment data is making it to ml_features_materialized"""
    try:
        print(f"\n📊 CHECKING ML FEATURES SENTIMENT INTEGRATION")
        print("=" * 50)
        
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        # Check recent sentiment updates
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cb,
                SUM(CASE WHEN avg_vader_score IS NOT NULL THEN 1 ELSE 0 END) as has_vader,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_news
            FROM ml_features_materialized
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        print(f"Records updated (last hour): {total}")
        if total > 0:
            print(f"  With CryptoBERT: {result[1]}")
            print(f"  With VADER: {result[2]}")
            print(f"  With Social: {result[3]}")
            print(f"  With News: {result[4]}")
        
        # Check overall sentiment coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cb,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_news
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        print(f"\nOverall sentiment coverage (24h):")
        print(f"  Total records: {total}")
        if total > 0:
            print(f"  CryptoBERT: {result[1]} ({result[1]/total*100:.1f}%)")
            print(f"  Social: {result[2]} ({result[2]/total*100:.1f}%)")
            print(f"  News: {result[3]} ({result[3]/total*100:.1f}%)")
        
        cursor.close()
        conn.close()
        return total > 0
        
    except Exception as e:
        logger.error(f"Error checking ML features: {e}")
        return False


def main():
    """Main function to test sentiment collection system"""
    logger.info("Starting sentiment collection system test...")
    
    print("🔍 SENTIMENT COLLECTION SYSTEM TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Test components
    news_working = test_news_collection()
    sentiment_working = test_sentiment_processing()
    ml_integration = check_ml_features_sentiment()
    
    # Summary
    print(f"\n🎯 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"News Collection: {'✅ Working' if news_working else '❌ Not Working'}")
    print(f"Sentiment Processing: {'✅ Working' if sentiment_working else '❌ Not Working'}")
    print(f"ML Integration: {'✅ Working' if ml_integration else '❌ Not Working'}")
    
    working_count = sum([news_working, sentiment_working, ml_integration])
    print(f"\nWorking Components: {working_count}/3")
    
    if working_count == 3:
        print("🎉 All sentiment systems are working!")
    elif working_count >= 2:
        print("⚠️ Most systems working, minor issues remain")
    elif working_count == 1:
        print("🔧 Some systems working, significant issues detected")
    else:
        print("🚨 Major issues - sentiment system needs attention")
    
    print("=" * 70)
    
    return working_count >= 2


if __name__ == "__main__":
    main()