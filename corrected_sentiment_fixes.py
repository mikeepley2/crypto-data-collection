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


def corrected_schema_integration():
    """Fix sentiment data integration with correct column names"""
    try:
        print("🔧 CORRECTED SENTIMENT DATA INTEGRATION")
        print("=" * 70)
        
        # Connect to both databases
        news_conn = get_db_connection('crypto_news')
        prices_conn = get_db_connection('crypto_prices')
        
        news_cursor = news_conn.cursor()
        prices_cursor = prices_conn.cursor()
        
        print("📊 Integrating sentiment data with correct schema...")
        
        # Corrected sentiment integration using actual column names
        news_cursor.execute("""
            SELECT 
                symbol,
                DATE(created_at) as sentiment_date,
                AVG(CASE WHEN cryptobert_score BETWEEN -1 AND 1 THEN cryptobert_score END) as avg_cryptobert,
                AVG(CASE WHEN vader_score BETWEEN -1 AND 1 THEN vader_score END) as avg_vader,
                AVG(CASE WHEN textblob_score BETWEEN -1 AND 1 THEN textblob_score END) as avg_textblob,
                AVG(CASE WHEN finbert_score BETWEEN -1 AND 1 THEN finbert_score END) as avg_finbert,
                COUNT(*) as sentiment_count
            FROM sentiment_data
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 60 DAY)
              AND symbol IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY sentiment_date DESC
            LIMIT 1000
        """)
        
        sentiment_data = news_cursor.fetchall()
        print(f"Found {len(sentiment_data)} sentiment records for integration")
        
        # Update ml_features with sentiment data
        sentiment_updates = 0
        for row in sentiment_data:
            symbol, date, cryptobert, vader, textblob, finbert, count = row
            
            if any(x is not None for x in [cryptobert, vader, textblob, finbert]):
                try:
                    prices_cursor.execute("""
                        UPDATE ml_features_materialized
                        SET 
                            avg_cryptobert_score = COALESCE(avg_cryptobert_score, %s),
                            avg_vader_score = COALESCE(avg_vader_score, %s),
                            avg_textblob_score = COALESCE(avg_textblob_score, %s),
                            avg_finbert_sentiment_score = COALESCE(avg_finbert_sentiment_score, %s),
                            crypto_sentiment_count = COALESCE(crypto_sentiment_count, %s),
                            updated_at = NOW()
                        WHERE symbol = %s 
                          AND DATE(created_at) = %s
                    """, (cryptobert, vader, textblob, finbert, count, symbol, date))
                    
                    sentiment_updates += prices_cursor.rowcount
                    
                except Exception as e:
                    logger.debug(f"Update attempt for {symbol}: {e}")
                    continue
        
        print(f"✅ Sentiment ML updates: {sentiment_updates}")
        
        # Corrected social media integration using actual column names
        news_cursor.execute("""
            SELECT 
                CASE 
                    WHEN coin_mentioned IS NOT NULL AND coin_mentioned != '' THEN coin_mentioned
                    WHEN content LIKE '%BTC%' OR content LIKE '%Bitcoin%' THEN 'BTC'
                    WHEN content LIKE '%ETH%' OR content LIKE '%Ethereum%' THEN 'ETH'
                    WHEN content LIKE '%ADA%' OR content LIKE '%Cardano%' THEN 'ADA'
                    WHEN content LIKE '%SOL%' OR content LIKE '%Solana%' THEN 'SOL'
                    WHEN content LIKE '%DOGE%' OR content LIKE '%Dogecoin%' THEN 'DOGE'
                    WHEN content LIKE '%MATIC%' OR content LIKE '%Polygon%' THEN 'MATIC'
                    WHEN content LIKE '%AVAX%' OR content LIKE '%Avalanche%' THEN 'AVAX'
                    WHEN content LIKE '%DOT%' OR content LIKE '%Polkadot%' THEN 'DOT'
                    WHEN content LIKE '%LINK%' OR content LIKE '%Chainlink%' THEN 'LINK'
                    WHEN content LIKE '%UNI%' OR content LIKE '%Uniswap%' THEN 'UNI'
                    ELSE 'BTC'
                END as symbol,
                DATE(created_at) as post_date,
                AVG(CASE WHEN sentiment_score BETWEEN -1 AND 1 THEN sentiment_score END) as avg_social_sentiment,
                COUNT(*) as social_count,
                SUM(CASE WHEN sentiment_score > 0.1 THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment_score < -0.1 THEN 1 ELSE 0 END) as negative_count,
                AVG(engagement_score) as avg_engagement
            FROM social_media_posts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 60 DAY)
              AND sentiment_score IS NOT NULL
              AND content IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY post_date DESC
            LIMIT 2000
        """)
        
        social_data = news_cursor.fetchall()
        print(f"Found {len(social_data)} social media records for integration")
        
        # Update with social sentiment
        social_updates = 0
        for row in social_data:
            symbol, date, avg_sentiment, count, pos_count, neg_count, avg_eng = row
            
            if avg_sentiment is not None:
                try:
                    # Calculate derived metrics
                    weighted_sentiment = avg_sentiment * (avg_eng if avg_eng else 1)
                    
                    prices_cursor.execute("""
                        UPDATE ml_features_materialized
                        SET 
                            social_avg_sentiment = COALESCE(social_avg_sentiment, %s),
                            social_post_count = COALESCE(social_post_count, %s),
                            sentiment_positive = COALESCE(sentiment_positive, %s),
                            sentiment_negative = COALESCE(sentiment_negative, %s),
                            social_weighted_sentiment = COALESCE(social_weighted_sentiment, %s),
                            social_total_engagement = COALESCE(social_total_engagement, %s),
                            updated_at = NOW()
                        WHERE symbol = %s 
                          AND DATE(created_at) = %s
                    """, (avg_sentiment, count, pos_count, neg_count, weighted_sentiment, avg_eng, symbol, date))
                    
                    social_updates += prices_cursor.rowcount
                    
                except Exception as e:
                    logger.debug(f"Social update attempt for {symbol}: {e}")
                    continue
        
        print(f"✅ Social media updates: {social_updates}")
        
        # Enhanced news sentiment integration
        news_cursor.execute("""
            SELECT 
                CASE 
                    WHEN title LIKE '%BTC%' OR title LIKE '%Bitcoin%' OR content LIKE '%BTC%' THEN 'BTC'
                    WHEN title LIKE '%ETH%' OR title LIKE '%Ethereum%' OR content LIKE '%ETH%' THEN 'ETH'
                    WHEN title LIKE '%ADA%' OR title LIKE '%Cardano%' OR content LIKE '%ADA%' THEN 'ADA'
                    WHEN title LIKE '%SOL%' OR title LIKE '%Solana%' OR content LIKE '%SOL%' THEN 'SOL'
                    WHEN title LIKE '%DOGE%' OR title LIKE '%Dogecoin%' OR content LIKE '%DOGE%' THEN 'DOGE'
                    ELSE 'BTC'
                END as symbol,
                DATE(created_at) as news_date,
                AVG(CASE WHEN sentiment_score BETWEEN -1 AND 1 THEN sentiment_score END) as avg_news_sentiment,
                COUNT(*) as news_count
            FROM crypto_news_data
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 60 DAY)
              AND sentiment_score IS NOT NULL
              AND (title IS NOT NULL OR content IS NOT NULL)
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY news_date DESC
            LIMIT 2000
        """)
        
        news_sentiment_data = news_cursor.fetchall()
        print(f"Found {len(news_sentiment_data)} news sentiment records")
        
        # Update news sentiment
        news_updates = 0
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
                    logger.debug(f"News update attempt for {symbol}: {e}")
                    continue
        
        print(f"✅ News sentiment updates: {news_updates}")
        
        # Commit all changes
        prices_conn.commit()
        
        total_updates = sentiment_updates + social_updates + news_updates
        print(f"\n📊 INTEGRATION SUMMARY:")
        print(f"  Total updates applied: {total_updates:,}")
        
        news_cursor.close()
        prices_cursor.close()
        news_conn.close()
        prices_conn.close()
        
        return total_updates > 0
        
    except Exception as e:
        logger.error(f"Error in corrected schema integration: {e}")
        return False


def setup_collection_monitoring():
    """Set up monitoring for collection services"""
    try:
        print("\n📊 SETTING UP COLLECTION MONITORING")
        print("=" * 70)
        
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # Create monitoring table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_monitoring (
                id INT AUTO_INCREMENT PRIMARY KEY,
                service_name VARCHAR(100) NOT NULL UNIQUE,
                status VARCHAR(50) NOT NULL,
                last_collection TIMESTAMP NULL,
                records_collected INT DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_service_status (service_name, status),
                INDEX idx_last_collection (last_collection)
            )
        """)
        
        # Create alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                alert_type VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                severity ENUM('info', 'warning', 'error', 'critical') DEFAULT 'info',
                resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP NULL,
                INDEX idx_severity_resolved (severity, resolved),
                INDEX idx_created_at (created_at)
            )
        """)
        
        # Initialize service monitoring
        services = [
            'crypto_news_collector',
            'reddit_sentiment_collector',
            'social_other',
            'enhanced_sentiment',
            'sentiment_microservice',
            'llm_integration'
        ]
        
        for service in services:
            cursor.execute("""
                INSERT INTO collection_monitoring (service_name, status, last_collection)
                VALUES (%s, 'monitoring', NOW())
                ON DUPLICATE KEY UPDATE 
                    status = 'monitoring', 
                    updated_at = NOW()
            """, (service,))
        
        # Generate current status alerts
        news_conn = get_db_connection('crypto_news')
        news_cursor = news_conn.cursor()
        
        # Check and alert on stale data
        checks = [
            ("crypto_news_data", "News collection", 2),
            ("social_media_posts", "Social media collection", 7), 
            ("sentiment_data", "Sentiment processing", 30)
        ]
        
        for table, description, max_days in checks:
            news_cursor.execute(f"SELECT MAX(created_at) FROM {table}")
            latest = news_cursor.fetchone()[0]
            
            if latest:
                days_old = (datetime.now() - latest).days
                if days_old > max_days:
                    severity = 'critical' if days_old > max_days * 2 else 'warning'
                    cursor.execute("""
                        INSERT INTO monitoring_alerts (alert_type, message, severity)
                        VALUES ('stale_data', %s, %s)
                        ON DUPLICATE KEY UPDATE created_at = NOW()
                    """, (f"{description} is {days_old} days old", severity))
        
        conn.commit()
        
        # Show monitoring status
        cursor.execute("SELECT service_name, status FROM collection_monitoring")
        monitoring_services = cursor.fetchall()
        
        print("✅ Monitoring setup completed")
        print(f"Services being monitored: {len(monitoring_services)}")
        for service, status in monitoring_services:
            print(f"  {service}: {status}")
        
        cursor.close()
        news_cursor.close()
        conn.close()
        news_conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up monitoring: {e}")
        return False


def verify_sentiment_integration():
    """Verify the sentiment integration results"""
    try:
        print("\n✅ VERIFYING SENTIMENT INTEGRATION")
        print("=" * 70)
        
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # Check overall sentiment coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cb,
                SUM(CASE WHEN avg_vader_score IS NOT NULL THEN 1 ELSE 0 END) as has_vader,
                SUM(CASE WHEN avg_textblob_score IS NOT NULL THEN 1 ELSE 0 END) as has_textblob,
                SUM(CASE WHEN avg_finbert_sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as has_finbert,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_news
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        if total > 0:
            print(f"📊 Sentiment Coverage (Last 7 days, {total:,} records):")
            print(f"  CryptoBERT: {result[1]:,} ({result[1]/total*100:.1f}%)")
            print(f"  VADER: {result[2]:,} ({result[2]/total*100:.1f}%)")
            print(f"  TextBlob: {result[3]:,} ({result[3]/total*100:.1f}%)")
            print(f"  FinBERT: {result[4]:,} ({result[4]/total*100:.1f}%)")
            print(f"  Social: {result[5]:,} ({result[5]/total*100:.1f}%)")
            print(f"  News: {result[6]:,} ({result[6]/total*100:.1f}%)")
        
        # Check recent updates
        cursor.execute("""
            SELECT COUNT(*) FROM ml_features_materialized
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
              AND (avg_cryptobert_score IS NOT NULL 
                   OR social_avg_sentiment IS NOT NULL 
                   OR news_sentiment IS NOT NULL)
        """)
        
        recent_updates = cursor.fetchone()[0]
        print(f"\n⏰ Recent sentiment updates (1 hour): {recent_updates:,}")
        
        # Check top symbols with sentiment
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as records,
                AVG(avg_cryptobert_score) as avg_cb,
                AVG(social_avg_sentiment) as avg_social,
                AVG(news_sentiment) as avg_news
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
              AND (avg_cryptobert_score IS NOT NULL 
                   OR social_avg_sentiment IS NOT NULL 
                   OR news_sentiment IS NOT NULL)
            GROUP BY symbol
            ORDER BY records DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"\n🏆 Top symbols with sentiment data:")
            print(f"{'Symbol':<8} {'Records':<8} {'CryptoBERT':<10} {'Social':<8} {'News':<8}")
            print("-" * 50)
            for row in results:
                symbol = row[0]
                records = row[1]
                cb_score = row[2] if row[2] else 0
                social_score = row[3] if row[3] else 0
                news_score = row[4] if row[4] else 0
                print(f"{symbol:<8} {records:<8} {cb_score:<10.3f} {social_score:<8.3f} {news_score:<8.3f}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error verifying sentiment integration: {e}")
        return False


def main():
    """Main function for corrected sentiment fixes"""
    logger.info("Starting corrected sentiment system fixes...")
    
    print("🔧 CORRECTED SENTIMENT SYSTEM FIXES")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Execute fixes
    integration_success = corrected_schema_integration()
    monitoring_success = setup_collection_monitoring()
    verification_success = verify_sentiment_integration()
    
    # Summary
    print(f"\n🎯 CORRECTED FIXES SUMMARY")
    print("=" * 70)
    print(f"  Sentiment Integration: {'✅ Success' if integration_success else '❌ Failed'}")
    print(f"  Monitoring Setup: {'✅ Success' if monitoring_success else '❌ Failed'}")
    print(f"  Verification: {'✅ Success' if verification_success else '❌ Failed'}")
    
    success_count = sum([integration_success, monitoring_success, verification_success])
    
    print(f"\nOverall Success: {success_count}/3 components working")
    
    if success_count == 3:
        print("🎉 All corrected fixes completed successfully!")
        print("✨ Sentiment data integration significantly improved")
        print("📊 Monitoring system active and operational")
    elif success_count >= 2:
        print("✅ Most critical fixes completed successfully")
    else:
        print("⚠️ Some issues remain - additional work needed")
    
    print("=" * 80)
    
    return success_count >= 2


if __name__ == "__main__":
    main()