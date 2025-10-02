#!/usr/bin/env python3

import mysql.connector
import logging
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


def integrate_sentiment_data():
    """Integrate sentiment data from crypto_news to ml_features_materialized"""
    try:
        print("🔄 INTEGRATING SENTIMENT DATA FROM CRYPTO_NEWS DB")
        print("=" * 60)
        
        # Connect to both databases
        news_conn = get_db_connection('crypto_news')
        prices_conn = get_db_connection('crypto_prices')
        
        news_cursor = news_conn.cursor()
        prices_cursor = prices_conn.cursor()
        
        # Get available sentiment data from crypto_news
        news_cursor.execute("""
            SELECT 
                symbol,
                DATE(created_at) as sentiment_date,
                AVG(CASE WHEN cryptobert_score BETWEEN -1 AND 1 THEN cryptobert_score END) as avg_cryptobert,
                AVG(CASE WHEN vader_score BETWEEN -1 AND 1 THEN vader_score END) as avg_vader,
                AVG(CASE WHEN textblob_score BETWEEN -1 AND 1 THEN textblob_score END) as avg_textblob,
                COUNT(*) as sentiment_count
            FROM sentiment_data
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 60 DAY)
              AND symbol IN (SELECT DISTINCT symbol FROM crypto_prices.ml_features_materialized)
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY sentiment_date DESC
            LIMIT 1000
        """)
        
        sentiment_data = news_cursor.fetchall()
        print(f"Found {len(sentiment_data)} sentiment records to integrate")
        
        sentiment_updates = 0
        if sentiment_data:
            for row in sentiment_data:
                symbol, date, cryptobert, vader, textblob, count = row
                
                if any(x is not None for x in [cryptobert, vader, textblob]):
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
                        """, (cryptobert, vader, textblob, count, symbol, date))
                        
                        sentiment_updates += prices_cursor.rowcount
                        
                    except Exception as e:
                        logger.warning(f"Error updating sentiment for {symbol} on {date}: {e}")
                        continue
        
        # Get social media data
        news_cursor.execute("""
            SELECT 
                symbol,
                DATE(created_at) as post_date,
                AVG(CASE WHEN sentiment_score BETWEEN -1 AND 1 THEN sentiment_score END) as avg_social_sentiment,
                COUNT(*) as social_count,
                SUM(CASE WHEN sentiment_score > 0.1 THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment_score < -0.1 THEN 1 ELSE 0 END) as negative_count
            FROM social_media_posts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 60 DAY)
              AND symbol IN (SELECT DISTINCT symbol FROM crypto_prices.ml_features_materialized)
              AND sentiment_score IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY post_date DESC
            LIMIT 1000
        """)
        
        social_data = news_cursor.fetchall()
        print(f"Found {len(social_data)} social media records to integrate")
        
        social_updates = 0
        if social_data:
            for row in social_data:
                symbol, date, avg_sentiment, count, pos_count, neg_count = row
                
                if avg_sentiment is not None:
                    try:
                        prices_cursor.execute("""
                            UPDATE ml_features_materialized
                            SET 
                                social_avg_sentiment = COALESCE(social_avg_sentiment, %s),
                                social_post_count = COALESCE(social_post_count, %s),
                                sentiment_positive = COALESCE(sentiment_positive, %s),
                                sentiment_negative = COALESCE(sentiment_negative, %s),
                                updated_at = NOW()
                            WHERE symbol = %s 
                              AND DATE(created_at) = %s
                        """, (avg_sentiment, count, pos_count, neg_count, symbol, date))
                        
                        social_updates += prices_cursor.rowcount
                        
                    except Exception as e:
                        logger.warning(f"Error updating social for {symbol} on {date}: {e}")
                        continue
        
        # Get crypto news sentiment
        news_cursor.execute("""
            SELECT 
                symbol,
                DATE(created_at) as news_date,
                AVG(sentiment_score) as avg_news_sentiment,
                COUNT(*) as news_count
            FROM crypto_news_data
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 60 DAY)
              AND symbol IN (SELECT DISTINCT symbol FROM crypto_prices.ml_features_materialized)
              AND sentiment_score IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY news_date DESC
            LIMIT 1000
        """)
        
        news_sentiment_data = news_cursor.fetchall()
        print(f"Found {len(news_sentiment_data)} news sentiment records to integrate")
        
        news_updates = 0
        if news_sentiment_data:
            for row in news_sentiment_data:
                symbol, date, avg_news_sentiment, count = row
                
                if avg_news_sentiment is not None:
                    try:
                        prices_cursor.execute("""
                            UPDATE ml_features_materialized
                            SET 
                                news_sentiment = COALESCE(news_sentiment, %s),
                                general_crypto_sentiment_count = COALESCE(general_crypto_sentiment_count, %s),
                                updated_at = NOW()
                            WHERE symbol = %s 
                              AND DATE(created_at) = %s
                        """, (avg_news_sentiment, count, symbol, date))
                        
                        news_updates += prices_cursor.rowcount
                        
                    except Exception as e:
                        logger.warning(f"Error updating news sentiment for {symbol} on {date}: {e}")
                        continue
        
        # Commit all changes
        prices_conn.commit()
        
        print(f"✅ Integration Results:")
        print(f"  Sentiment ML updates: {sentiment_updates}")
        print(f"  Social media updates: {social_updates}")
        print(f"  News sentiment updates: {news_updates}")
        print(f"  Total updates: {sentiment_updates + social_updates + news_updates}")
        
        news_cursor.close()
        prices_cursor.close()
        news_conn.close()
        prices_conn.close()
        
        return sentiment_updates + social_updates + news_updates > 0
        
    except Exception as e:
        logger.error(f"Error integrating sentiment data: {e}")
        return False


def check_current_sentiment_status():
    """Check current sentiment status after integration"""
    try:
        print(f"\n📊 CURRENT SENTIMENT STATUS")
        print("=" * 60)
        
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # Check sentiment coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cryptobert,
                SUM(CASE WHEN avg_vader_score IS NOT NULL THEN 1 ELSE 0 END) as has_vader,
                SUM(CASE WHEN avg_textblob_score IS NOT NULL THEN 1 ELSE 0 END) as has_textblob,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_news,
                SUM(CASE WHEN crypto_sentiment_count > 0 THEN 1 ELSE 0 END) as has_sentiment_count
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        if total > 0:
            print(f"Recent records (7 days): {total:,}")
            print(f"CryptoBERT: {result[1]:,} ({result[1]/total*100:.1f}%)")
            print(f"VADER: {result[2]:,} ({result[2]/total*100:.1f}%)")
            print(f"TextBlob: {result[3]:,} ({result[3]/total*100:.1f}%)")
            print(f"Social sentiment: {result[4]:,} ({result[4]/total*100:.1f}%)")
            print(f"News sentiment: {result[5]:,} ({result[5]/total*100:.1f}%)")
            print(f"Sentiment counts: {result[6]:,} ({result[6]/total*100:.1f}%)")
        
        # Check average sentiment scores
        cursor.execute("""
            SELECT 
                AVG(avg_cryptobert_score) as avg_cryptobert,
                AVG(avg_vader_score) as avg_vader,
                AVG(avg_textblob_score) as avg_textblob,
                AVG(social_avg_sentiment) as avg_social,
                AVG(news_sentiment) as avg_news
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
              AND (avg_cryptobert_score IS NOT NULL 
                   OR avg_vader_score IS NOT NULL 
                   OR avg_textblob_score IS NOT NULL
                   OR social_avg_sentiment IS NOT NULL
                   OR news_sentiment IS NOT NULL)
        """)
        
        result = cursor.fetchone()
        if result and any(x is not None for x in result):
            print(f"\nAverage sentiment scores (7 days):")
            if result[0]: print(f"  CryptoBERT: {result[0]:.3f}")
            if result[1]: print(f"  VADER: {result[1]:.3f}")
            if result[2]: print(f"  TextBlob: {result[2]:.3f}")
            if result[3]: print(f"  Social: {result[3]:.3f}")
            if result[4]: print(f"  News: {result[4]:.3f}")
        
        # Check top symbols with sentiment data
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as records,
                AVG(avg_cryptobert_score) as avg_cb,
                AVG(social_avg_sentiment) as avg_social
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
              AND (avg_cryptobert_score IS NOT NULL OR social_avg_sentiment IS NOT NULL)
            GROUP BY symbol
            ORDER BY records DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"\nTop symbols with sentiment data:")
            print(f"{'Symbol':<8} {'Records':<8} {'CryptoBERT':<10} {'Social':<8}")
            print("-" * 40)
            for row in results:
                symbol = row[0]
                records = row[1]
                cb_score = row[2] if row[2] else 0
                social_score = row[3] if row[3] else 0
                print(f"{symbol:<8} {records:<8} {cb_score:<10.3f} {social_score:<8.3f}")
        
        cursor.close()
        conn.close()
        return total > 0
        
    except Exception as e:
        logger.error(f"Error checking sentiment status: {e}")
        return False


def main():
    """Main function to integrate sentiment data"""
    logger.info("Starting sentiment data integration...")
    
    print("🧠 SENTIMENT DATA INTEGRATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Integrate sentiment data from crypto_news database
    integration_success = integrate_sentiment_data()
    
    # Check results
    status_check = check_current_sentiment_status()
    
    print(f"\n🎯 INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"Data Integration: {'✅ Success' if integration_success else '❌ Failed'}")
    print(f"Status Check: {'✅ Success' if status_check else '❌ Failed'}")
    
    if integration_success:
        print("🎉 Sentiment data integration completed successfully!")
        print("✨ ML features now have sentiment scores from existing data")
    else:
        print("⚠️ Some issues occurred during integration")
    
    print("=" * 70)
    
    return integration_success


if __name__ == "__main__":
    main()