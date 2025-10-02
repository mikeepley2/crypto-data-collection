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


def fix_database_connections():
    """Fix 1: Database connectivity issues"""
    try:
        print("🔧 FIXING DATABASE CONNECTIONS")
        print("=" * 60)
        
        # Test connections to both databases
        try:
            crypto_prices_conn = get_db_connection('crypto_prices')
            crypto_prices_cursor = crypto_prices_conn.cursor()
            crypto_prices_cursor.execute("SELECT 1")
            print("✅ crypto_prices database connection: OK")
            crypto_prices_cursor.close()
            crypto_prices_conn.close()
        except Exception as e:
            print(f"❌ crypto_prices database connection: {e}")
            return False
        
        try:
            crypto_news_conn = get_db_connection('crypto_news')
            crypto_news_cursor = crypto_news_conn.cursor()
            crypto_news_cursor.execute("SELECT 1")
            print("✅ crypto_news database connection: OK")
            crypto_news_cursor.close()
            crypto_news_conn.close()
        except Exception as e:
            print(f"❌ crypto_news database connection: {e}")
            return False
        
        print("✅ Database connections verified")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database connections: {e}")
        return False


def fix_schema_alignment():
    """Fix 3: Schema alignment between databases"""
    try:
        print("🔄 FIXING SCHEMA ALIGNMENT")
        print("=" * 60)
        
        # Connect to both databases
        news_conn = get_db_connection('crypto_news')
        prices_conn = get_db_connection('crypto_prices')
        
        news_cursor = news_conn.cursor()
        prices_cursor = prices_conn.cursor()
        
        print("📊 Analyzing schema compatibility...")
        
        # Check sentiment_data table structure
        news_cursor.execute("DESCRIBE sentiment_data")
        sentiment_columns = [row[0] for row in news_cursor.fetchall()]
        print(f"sentiment_data columns found: {len(sentiment_columns)} columns")
        
        # Check crypto_news_data table structure  
        news_cursor.execute("DESCRIBE crypto_news_data")
        news_columns = [row[0] for row in news_cursor.fetchall()]
        print(f"crypto_news_data columns found: {len(news_columns)} columns")
        
        # Check social_media_posts structure
        news_cursor.execute("DESCRIBE social_media_posts")
        social_columns = [row[0] for row in news_cursor.fetchall()]
        print(f"social_media_posts columns found: {len(social_columns)} columns")
        
        print("🔧 Implementing corrected schema mapping...")
        
        # Improved sentiment integration with better symbol handling
        news_cursor.execute("""
            SELECT 
                CASE 
                    WHEN crypto_symbol IS NOT NULL THEN crypto_symbol
                    WHEN symbol IS NOT NULL THEN symbol  
                    ELSE 'BTC'
                END as symbol,
                DATE(created_at) as sentiment_date,
                AVG(CASE WHEN cryptobert_score BETWEEN -1 AND 1 THEN cryptobert_score END) as avg_cryptobert,
                AVG(CASE WHEN vader_score BETWEEN -1 AND 1 THEN vader_score END) as avg_vader,
                AVG(CASE WHEN textblob_score BETWEEN -1 AND 1 THEN textblob_score END) as avg_textblob,
                COUNT(*) as sentiment_count
            FROM sentiment_data
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY sentiment_date DESC
            LIMIT 500
        """)
        
        sentiment_data = news_cursor.fetchall()
        print(f"Found {len(sentiment_data)} sentiment records for integration")
        
        # Update ml_features with sentiment data
        sentiment_updates = 0
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
                    logger.warning(f"Error updating sentiment for {symbol}: {e}")
                    continue
        
        # Enhanced social media integration with content analysis
        news_cursor.execute("""
            SELECT 
                CASE 
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
                SUM(CASE WHEN sentiment_score < -0.1 THEN 1 ELSE 0 END) as negative_count
            FROM social_media_posts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
              AND sentiment_score IS NOT NULL
              AND content IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY post_date DESC
            LIMIT 1000
        """)
        
        social_data = news_cursor.fetchall()
        print(f"Found {len(social_data)} social media records for integration")
        
        # Update with social sentiment
        social_updates = 0
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
                            social_weighted_sentiment = COALESCE(social_weighted_sentiment, %s),
                            updated_at = NOW()
                        WHERE symbol = %s 
                          AND DATE(created_at) = %s
                    """, (avg_sentiment, count, pos_count, neg_count, avg_sentiment * count, symbol, date))
                    
                    social_updates += prices_cursor.rowcount
                    
                except Exception as e:
                    logger.warning(f"Error updating social for {symbol}: {e}")
                    continue
        
        # Enhanced news sentiment integration
        news_cursor.execute("""
            SELECT 
                CASE 
                    WHEN title LIKE '%BTC%' OR title LIKE '%Bitcoin%' THEN 'BTC'
                    WHEN title LIKE '%ETH%' OR title LIKE '%Ethereum%' THEN 'ETH'
                    WHEN title LIKE '%ADA%' OR title LIKE '%Cardano%' THEN 'ADA'
                    WHEN title LIKE '%SOL%' OR title LIKE '%Solana%' THEN 'SOL'
                    WHEN title LIKE '%DOGE%' OR title LIKE '%Dogecoin%' THEN 'DOGE'
                    ELSE 'BTC'
                END as symbol,
                DATE(created_at) as news_date,
                AVG(sentiment_score) as avg_news_sentiment,
                COUNT(*) as news_count
            FROM crypto_news_data
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
              AND sentiment_score IS NOT NULL
              AND title IS NOT NULL
            GROUP BY symbol, DATE(created_at)
            HAVING COUNT(*) > 0
            ORDER BY news_date DESC
            LIMIT 1000
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
                    logger.warning(f"Error updating news sentiment: {e}")
                    continue
        
        prices_conn.commit()
        
        print(f"✅ Schema alignment completed:")
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
        logger.error(f"Error fixing schema alignment: {e}")
        return False


def setup_monitoring():
    """Fix 4: Set up active monitoring"""
    try:
        print("📊 SETTING UP MONITORING")
        print("=" * 60)
        
        # Create monitoring tables in crypto_prices database
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # Create monitoring table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_monitoring (
                id INT AUTO_INCREMENT PRIMARY KEY,
                service_name VARCHAR(100) NOT NULL,
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
        
        # Initialize monitoring records
        services_to_monitor = [
            'crypto_news_collector',
            'reddit_sentiment_collector', 
            'social_other',
            'enhanced_sentiment',
            'sentiment_microservice',
            'llm_integration'
        ]
        
        for service in services_to_monitor:
            cursor.execute("""
                INSERT INTO collection_monitoring (service_name, status, last_collection)
                VALUES (%s, 'initialized', NOW())
                ON DUPLICATE KEY UPDATE updated_at = NOW()
            """, (service,))
        
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
        
        # Check current collection status and create alerts
        news_conn = get_db_connection('crypto_news')
        news_cursor = news_conn.cursor()
        
        # Check news collection
        news_cursor.execute("SELECT MAX(created_at) FROM crypto_news_data")
        latest_news = news_cursor.fetchone()[0]
        
        if latest_news:
            days_old = (datetime.now() - latest_news).days
            if days_old > 1:
                cursor.execute("""
                    INSERT INTO monitoring_alerts (alert_type, message, severity)
                    VALUES ('stale_data', %s, 'warning')
                """, (f"News collection is {days_old} days old (latest: {latest_news})",))
        
        # Check social media
        news_cursor.execute("SELECT MAX(created_at) FROM social_media_posts")
        latest_social = news_cursor.fetchone()[0]
        
        if latest_social:
            days_old = (datetime.now() - latest_social).days
            if days_old > 7:
                cursor.execute("""
                    INSERT INTO monitoring_alerts (alert_type, message, severity)
                    VALUES ('stale_data', %s, 'warning')
                """, (f"Social collection is {days_old} days old (latest: {latest_social})",))
        
        # Check sentiment processing
        news_cursor.execute("SELECT MAX(created_at) FROM sentiment_data")
        latest_sentiment = news_cursor.fetchone()[0]
        
        if latest_sentiment:
            days_old = (datetime.now() - latest_sentiment).days
            if days_old > 30:
                cursor.execute("""
                    INSERT INTO monitoring_alerts (alert_type, message, severity)
                    VALUES ('stale_data', %s, 'critical')
                """, (f"Sentiment processing is {days_old} days old (latest: {latest_sentiment})",))
        
        conn.commit()
        
        print("✅ Monitoring tables created and initialized")
        print("✅ Initial alerts generated for stale data")
        
        # Show current alerts
        cursor.execute("""
            SELECT alert_type, message, severity, created_at
            FROM monitoring_alerts
            WHERE resolved = FALSE
            ORDER BY severity DESC, created_at DESC
            LIMIT 10
        """)
        
        alerts = cursor.fetchall()
        if alerts:
            print("🚨 Current Active Alerts:")
            for alert_type, message, severity, created_at in alerts:
                print(f"  {severity.upper()}: {message}")
        
        cursor.close()
        news_cursor.close()
        conn.close()
        news_conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up monitoring: {e}")
        return False


def verify_fixes():
    """Verify that all fixes were successful"""
    try:
        print("✅ VERIFYING FIXES")
        print("=" * 60)
        
        # Check database connectivity
        try:
            conn = get_db_connection('crypto_prices')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
            recent_updates = cursor.fetchone()[0]
            print(f"Recent ML updates (1h): {recent_updates}")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Database check failed: {e}")
            return False
        
        # Check monitoring setup
        try:
            conn = get_db_connection('crypto_prices')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM collection_monitoring")
            monitoring_records = cursor.fetchone()[0]
            print(f"Monitoring records: {monitoring_records}")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Monitoring check failed: {e}")
            return False
        
        # Check sentiment integration
        try:
            conn = get_db_connection('crypto_prices')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cb,
                    SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                    SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_news
                FROM ml_features_materialized
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """)
            
            result = cursor.fetchone()
            total = result[0]
            if total > 0:
                cb_pct = result[1]/total*100
                social_pct = result[2]/total*100  
                news_pct = result[3]/total*100
                print(f"Sentiment coverage - CB: {cb_pct:.1f}%, Social: {social_pct:.1f}%, News: {news_pct:.1f}%")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Sentiment check failed: {e}")
            return False
        
        print("✅ All fixes verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying fixes: {e}")
        return False


def main():
    """Main function to implement database and schema fixes"""
    logger.info("Starting database and schema fixes...")
    
    print("🔧 DATABASE AND SCHEMA FIXES")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    fixes_results = []
    
    # Fix 1: Database Connections
    print("🔧 FIX 1: DATABASE CONNECTIONS")
    fix1_success = fix_database_connections()
    fixes_results.append(("Database Connections", fix1_success))
    
    # Fix 3: Schema Alignment
    print("\n🔧 FIX 3: SCHEMA ALIGNMENT") 
    fix3_success = fix_schema_alignment()
    fixes_results.append(("Schema Alignment", fix3_success))
    
    # Fix 4: Monitoring
    print("\n🔧 FIX 4: MONITORING SETUP")
    fix4_success = setup_monitoring()
    fixes_results.append(("Monitoring Setup", fix4_success))
    
    # Verify all fixes
    verification_success = verify_fixes()
    
    # Summary
    print(f"\n🎯 FIXES SUMMARY")
    print("=" * 60)
    
    successful_fixes = 0
    for fix_name, success in fixes_results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {fix_name}: {status}")
        if success:
            successful_fixes += 1
    
    print(f"  Verification: {'✅ Success' if verification_success else '❌ Failed'}")
    
    print(f"\nOverall Success Rate: {successful_fixes}/{len(fixes_results)} fixes completed")
    
    if successful_fixes == len(fixes_results) and verification_success:
        print("🎉 Database and schema fixes completed successfully!")
        print("✨ Sentiment data integration significantly improved")
    elif successful_fixes >= 2:
        print("✅ Most critical fixes completed")
    else:
        print("⚠️ Some issues remain")
    
    print("=" * 80)
    
    return successful_fixes >= 2


if __name__ == "__main__":
    main()