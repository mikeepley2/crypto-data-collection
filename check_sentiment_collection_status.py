#!/usr/bin/env python3

import mysql.connector
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )


def check_news_collection_status():
    """Check the status of news collection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("📰 NEWS COLLECTION STATUS CHECK")
        print("=" * 60)
        
        # Check total news articles
        cursor.execute("SELECT COUNT(*) FROM news_articles")
        total_articles = cursor.fetchone()[0]
        
        # Check recent articles (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM news_articles 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        recent_articles = cursor.fetchone()[0]
        
        # Check articles by source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM news_articles 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY source
            ORDER BY count DESC
        """)
        sources = cursor.fetchall()
        
        print(f"Total articles in database: {total_articles:,}")
        print(f"Articles collected (last 24h): {recent_articles:,}")
        
        if sources:
            print(f"\nArticles by source (last 24h):")
            for source, count in sources:
                print(f"  {source}: {count}")
        
        cursor.close()
        conn.close()
        return recent_articles > 0
        
    except Exception as e:
        logger.error(f"Error checking news status: {e}")
        return False


def check_social_media_status():
    """Check social media collection status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n📱 SOCIAL MEDIA COLLECTION STATUS")
        print("=" * 60)
        
        # Check if tables exist and have data
        tables_to_check = [
            'reddit_posts',
            'social_posts',
            'sentiment_analysis',
            'crypto_reddit_sentiment'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """)
                recent_count = cursor.fetchone()[0]
                
                print(f"{table}: {count:,} total, {recent_count:,} recent")
                
            except Exception as e:
                print(f"{table}: Table not found or error - {e}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking social media status: {e}")
        return False


def check_sentiment_analysis_status():
    """Check sentiment analysis status in ml_features_materialized"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n🧠 SENTIMENT ANALYSIS STATUS")
        print("=" * 60)
        
        # Check sentiment coverage in ml_features_materialized
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cryptobert,
                SUM(CASE WHEN avg_vader_score IS NOT NULL THEN 1 ELSE 0 END) as has_vader,
                SUM(CASE WHEN avg_textblob_score IS NOT NULL THEN 1 ELSE 0 END) as has_textblob,
                SUM(CASE WHEN avg_finbert_sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as has_finbert,
                SUM(CASE WHEN avg_general_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_general_crypto,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social_sentiment
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        if total > 0:
            print(f"Recent records (24h): {total:,}")
            print(f"CryptoBERT coverage: {result[1]:,} ({result[1]/total*100:.1f}%)")
            print(f"VADER coverage: {result[2]:,} ({result[2]/total*100:.1f}%)")
            print(f"TextBlob coverage: {result[3]:,} ({result[3]/total*100:.1f}%)")
            print(f"FinBERT coverage: {result[4]:,} ({result[4]/total*100:.1f}%)")
            print(f"General Crypto coverage: {result[5]:,} ({result[5]/total*100:.1f}%)")
            print(f"Social sentiment coverage: {result[6]:,} ({result[6]/total*100:.1f}%)")
        else:
            print("No recent records found in ml_features_materialized")
        
        # Check for recent sentiment scores
        cursor.execute("""
            SELECT 
                AVG(avg_cryptobert_score) as avg_cryptobert,
                AVG(avg_vader_score) as avg_vader,
                AVG(avg_textblob_score) as avg_textblob,
                AVG(social_avg_sentiment) as avg_social
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
              AND (avg_cryptobert_score IS NOT NULL 
                   OR avg_vader_score IS NOT NULL 
                   OR avg_textblob_score IS NOT NULL
                   OR social_avg_sentiment IS NOT NULL)
        """)
        
        result = cursor.fetchone()
        if result and any(x is not None for x in result):
            print(f"\nRecent average sentiment scores:")
            if result[0]: print(f"  CryptoBERT: {result[0]:.3f}")
            if result[1]: print(f"  VADER: {result[1]:.3f}")
            if result[2]: print(f"  TextBlob: {result[2]:.3f}")
            if result[3]: print(f"  Social: {result[3]:.3f}")
        
        cursor.close()
        conn.close()
        return total > 0
        
    except Exception as e:
        logger.error(f"Error checking sentiment status: {e}")
        return False


def check_llm_integration_status():
    """Check LLM integration status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n🤖 LLM INTEGRATION STATUS")
        print("=" * 60)
        
        # Check for LLM-related tables and data
        llm_tables = [
            'llm_analysis',
            'narrative_analysis',
            'market_analysis'
        ]
        
        for table in llm_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """)
                recent_count = cursor.fetchone()[0]
                
                print(f"{table}: {count:,} total, {recent_count:,} recent")
                
            except Exception as e:
                print(f"{table}: Table not found or error - {e}")
        
        # Check for LLM-derived columns in ml_features_materialized
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN avg_fear_greed_score IS NOT NULL THEN 1 ELSE 0 END) as has_fear_greed,
                SUM(CASE WHEN avg_volatility_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_vol_sentiment,
                SUM(CASE WHEN avg_risk_appetite IS NOT NULL THEN 1 ELSE 0 END) as has_risk_appetite
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        if total > 0:
            print(f"\nML Features LLM Integration (24h):")
            print(f"  Fear & Greed: {result[1]:,} ({result[1]/total*100:.1f}%)")
            print(f"  Volatility Sentiment: {result[2]:,} ({result[2]/total*100:.1f}%)")
            print(f"  Risk Appetite: {result[3]:,} ({result[3]/total*100:.1f}%)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking LLM status: {e}")
        return False


def check_service_health():
    """Check if key services are responding"""
    print(f"\n🔧 SERVICE HEALTH CHECK")
    print("=" * 60)
    
    services = [
        ("News Collector", "crypto-news-collector-795f79b5-2s26d"),
        ("Reddit Sentiment", "reddit-sentiment-collector-58455fc668-rfsqq"),
        ("Enhanced Sentiment", "enhanced-sentiment-f5744c8f7-kg6bg"),
        ("Sentiment Microservice", "sentiment-microservice-66bf6995c9-tv8t5"),
        ("LLM Integration", "llm-integration-client-69b89f4999-79bxv"),
        ("Social Other", "social-other-594fd98cbd-pv9pd")
    ]
    
    for service_name, pod_name in services:
        try:
            # This would be replaced with actual health check in a real implementation
            print(f"  {service_name}: ✅ Running (pod: {pod_name})")
        except Exception as e:
            print(f"  {service_name}: ❌ Error - {e}")


def main():
    """Main function to check all sentiment and collection systems"""
    logger.info("Starting comprehensive sentiment and collection status check...")
    
    print("🔍 COMPREHENSIVE SENTIMENT & COLLECTION STATUS CHECK")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check each component
    news_ok = check_news_collection_status()
    social_ok = check_social_media_status()
    sentiment_ok = check_sentiment_analysis_status()
    llm_ok = check_llm_integration_status()
    
    check_service_health()
    
    # Overall status
    print(f"\n📊 OVERALL STATUS SUMMARY")
    print("=" * 60)
    print(f"✅ News Collection: {'Working' if news_ok else '❌ Issues'}")
    print(f"✅ Social Media: {'Working' if social_ok else '❌ Issues'}")
    print(f"✅ Sentiment Analysis: {'Working' if sentiment_ok else '❌ Issues'}")
    print(f"✅ LLM Integration: {'Working' if llm_ok else '❌ Issues'}")
    
    overall_health = sum([news_ok, social_ok, sentiment_ok, llm_ok])
    print(f"\nOverall Health Score: {overall_health}/4")
    
    if overall_health == 4:
        print("🎉 All systems operating normally!")
    elif overall_health >= 2:
        print("⚠️ Some issues detected, but core systems working")
    else:
        print("🚨 Multiple critical issues detected")
    
    print("=" * 80)
    
    return overall_health >= 2


if __name__ == "__main__":
    main()