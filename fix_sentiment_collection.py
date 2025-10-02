#!/usr/bin/env python3

import mysql.connector
import logging
import requests
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection(database='crypto_prices'):
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database=database
    )


def trigger_news_collection():
    """Trigger news collection manually"""
    try:
        print("📰 TRIGGERING NEWS COLLECTION")
        print("=" * 50)
        
        # Try to trigger news collection
        collector_url = "http://crypto-news-collector:8000"
        
        # First check if service is reachable
        try:
            health_response = requests.get(f"{collector_url}/health", timeout=5)
            print(f"✅ News collector health: {health_response.status_code}")
        except Exception as e:
            print(f"❌ News collector health check failed: {e}")
            return False
        
        # Try to trigger collection
        try:
            collect_payload = {"limit": 100}
            collect_response = requests.post(
                f"{collector_url}/collect",
                json=collect_payload,
                timeout=30
            )
            print(f"📈 Collection trigger response: {collect_response.status_code}")
            if collect_response.status_code == 200:
                print("✅ News collection triggered successfully")
                return True
            else:
                print(f"⚠️ Collection response: {collect_response.text}")
                return False
        except Exception as e:
            print(f"❌ Failed to trigger collection: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error triggering news collection: {e}")
        return False


def trigger_social_collection():
    """Trigger social media collection"""
    try:
        print(f"\n📱 TRIGGERING SOCIAL MEDIA COLLECTION")
        print("=" * 50)
        
        services = [
            ("Reddit Sentiment", "http://reddit-sentiment-collector:8002"),
            ("Social Other", "http://social-other:8002"),
            ("Enhanced Sentiment", "http://enhanced-sentiment:8005")
        ]
        
        results = []
        
        for service_name, service_url in services:
            try:
                # Check health
                health_response = requests.get(f"{service_url}/health", timeout=5)
                print(f"✅ {service_name} health: {health_response.status_code}")
                
                # Try to trigger collection
                try:
                    collect_response = requests.post(
                        f"{service_url}/collect",
                        json={"symbols": ["BTC", "ETH", "ADA", "SOL"]},
                        timeout=30
                    )
                    print(f"📈 {service_name} collection: {collect_response.status_code}")
                    results.append(collect_response.status_code == 200)
                except Exception as e:
                    print(f"⚠️ {service_name} collection failed: {e}")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ {service_name} unreachable: {e}")
                results.append(False)
        
        return any(results)
        
    except Exception as e:
        logger.error(f"Error triggering social collection: {e}")
        return False


def trigger_sentiment_processing():
    """Trigger sentiment analysis processing"""
    try:
        print(f"\n🧠 TRIGGERING SENTIMENT PROCESSING")
        print("=" * 50)
        
        sentiment_services = [
            ("Sentiment Microservice", "http://sentiment-microservice:8004"),
            ("LLM Integration", "http://llm-integration-client:8006")
        ]
        
        results = []
        
        for service_name, service_url in sentiment_services:
            try:
                # Check health
                health_response = requests.get(f"{service_url}/health", timeout=5)
                print(f"✅ {service_name} health: {health_response.status_code}")
                
                # Try to trigger processing
                try:
                    process_response = requests.post(
                        f"{service_url}/process",
                        json={"force": True},
                        timeout=60
                    )
                    print(f"🔄 {service_name} processing: {process_response.status_code}")
                    results.append(process_response.status_code == 200)
                except Exception as e:
                    print(f"⚠️ {service_name} processing failed: {e}")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ {service_name} unreachable: {e}")
                results.append(False)
        
        return any(results)
        
    except Exception as e:
        logger.error(f"Error triggering sentiment processing: {e}")
        return False


def copy_sentiment_data_to_ml_features():
    """Copy sentiment data from crypto_news to ml_features_materialized"""
    try:
        print(f"\n🔄 INTEGRATING SENTIMENT DATA")
        print("=" * 50)
        
        # Connect to both databases
        news_conn = get_db_connection('crypto_news')
        prices_conn = get_db_connection('crypto_prices')
        
        news_cursor = news_conn.cursor()
        prices_cursor = prices_conn.cursor()
        
        # Get recent sentiment data from crypto_news
        news_cursor.execute("""
            SELECT 
                symbol,
                DATE(created_at) as sentiment_date,
                AVG(cryptobert_score) as avg_cryptobert,
                AVG(vader_score) as avg_vader,
                AVG(textblob_score) as avg_textblob,
                COUNT(*) as sentiment_count
            FROM sentiment_data
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
              AND symbol IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            ORDER BY sentiment_date DESC
        """)
        
        sentiment_data = news_cursor.fetchall()
        print(f"Found {len(sentiment_data)} sentiment records to integrate")
        
        if sentiment_data:
            # Update ml_features_materialized with sentiment scores
            updates = 0
            for row in sentiment_data:
                symbol, date, cryptobert, vader, textblob, count = row
                
                try:
                    prices_cursor.execute("""
                        UPDATE ml_features_materialized
                        SET 
                            avg_cryptobert_score = COALESCE(avg_cryptobert_score, %s),
                            avg_vader_score = COALESCE(avg_vader_score, %s),
                            avg_textblob_score = COALESCE(avg_textblob_score, %s),
                            crypto_sentiment_count = COALESCE(crypto_sentiment_count, %s),
                            updated_at = NOW()
                        WHERE symbol = %s 
                          AND DATE(created_at) = %s
                          AND (avg_cryptobert_score IS NULL 
                               OR avg_vader_score IS NULL 
                               OR avg_textblob_score IS NULL)
                    """, (cryptobert, vader, textblob, count, symbol, date))
                    
                    updates += prices_cursor.rowcount
                    
                except Exception as e:
                    logger.warning(f"Error updating sentiment for {symbol} on {date}: {e}")
                    continue
            
            prices_conn.commit()
            print(f"✅ Updated {updates} records with sentiment data")
        
        # Get social media data
        news_cursor.execute("""
            SELECT 
                symbol,
                DATE(created_at) as post_date,
                AVG(sentiment_score) as avg_social_sentiment,
                COUNT(*) as social_count
            FROM social_media_posts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
              AND symbol IS NOT NULL
              AND sentiment_score IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            ORDER BY post_date DESC
        """)
        
        social_data = news_cursor.fetchall()
        print(f"Found {len(social_data)} social media records to integrate")
        
        if social_data:
            # Update with social sentiment
            social_updates = 0
            for row in social_data:
                symbol, date, avg_sentiment, count = row
                
                try:
                    prices_cursor.execute("""
                        UPDATE ml_features_materialized
                        SET 
                            social_avg_sentiment = COALESCE(social_avg_sentiment, %s),
                            social_post_count = COALESCE(social_post_count, %s),
                            updated_at = NOW()
                        WHERE symbol = %s 
                          AND DATE(created_at) = %s
                          AND (social_avg_sentiment IS NULL 
                               OR social_post_count IS NULL)
                    """, (avg_sentiment, count, symbol, date))
                    
                    social_updates += prices_cursor.rowcount
                    
                except Exception as e:
                    logger.warning(f"Error updating social for {symbol} on {date}: {e}")
                    continue
            
            prices_conn.commit()
            print(f"✅ Updated {social_updates} records with social data")
        
        news_cursor.close()
        prices_cursor.close()
        news_conn.close()
        prices_conn.close()
        
        return updates > 0 or social_updates > 0
        
    except Exception as e:
        logger.error(f"Error integrating sentiment data: {e}")
        return False


def check_sentiment_integration_results():
    """Check the results of sentiment integration"""
    try:
        print(f"\n📊 SENTIMENT INTEGRATION RESULTS")
        print("=" * 50)
        
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # Check current sentiment coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cryptobert,
                SUM(CASE WHEN avg_vader_score IS NOT NULL THEN 1 ELSE 0 END) as has_vader,
                SUM(CASE WHEN avg_textblob_score IS NOT NULL THEN 1 ELSE 0 END) as has_textblob,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                SUM(CASE WHEN crypto_sentiment_count > 0 THEN 1 ELSE 0 END) as has_sentiment_count
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        if total > 0:
            print(f"📈 Sentiment Coverage (Last 7 days):")
            print(f"  Total records: {total:,}")
            print(f"  CryptoBERT: {result[1]:,} ({result[1]/total*100:.1f}%)")
            print(f"  VADER: {result[2]:,} ({result[2]/total*100:.1f}%)")
            print(f"  TextBlob: {result[3]:,} ({result[3]/total*100:.1f}%)")
            print(f"  Social Sentiment: {result[4]:,} ({result[4]/total*100:.1f}%)")
            print(f"  Sentiment Count: {result[5]:,} ({result[5]/total*100:.1f}%)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking integration results: {e}")
        return False


def main():
    """Main function to restart and fix sentiment collection"""
    logger.info("Starting sentiment collection and analysis fix...")
    
    print("🔧 SENTIMENT COLLECTION & ANALYSIS FIX")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Step 1: Trigger collections
    news_ok = trigger_news_collection()
    social_ok = trigger_social_collection()
    sentiment_ok = trigger_sentiment_processing()
    
    # Step 2: Integrate existing data
    integration_ok = copy_sentiment_data_to_ml_features()
    
    # Step 3: Check results
    check_sentiment_integration_results()
    
    # Summary
    print(f"\n🎯 FIX SUMMARY")
    print("=" * 50)
    print(f"News Collection: {'✅ Working' if news_ok else '❌ Issues'}")
    print(f"Social Collection: {'✅ Working' if social_ok else '❌ Issues'}")
    print(f"Sentiment Processing: {'✅ Working' if sentiment_ok else '❌ Issues'}")
    print(f"Data Integration: {'✅ Completed' if integration_ok else '❌ Issues'}")
    
    success_count = sum([news_ok, social_ok, sentiment_ok, integration_ok])
    print(f"\nOverall Success: {success_count}/4 components working")
    
    if success_count >= 3:
        print("🎉 Sentiment system mostly restored!")
    elif success_count >= 2:
        print("⚠️ Partial success - some issues remain")
    else:
        print("🚨 Major issues detected - manual intervention needed")
    
    print("=" * 70)
    
    return success_count >= 2


if __name__ == "__main__":
    main()