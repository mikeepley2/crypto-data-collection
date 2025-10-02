#!/usr/bin/env python3
"""
Lightweight continuous monitoring for crypto data collection system
"""
import mysql.connector
import time
from datetime import datetime

def monitor_once():
    """Single monitoring check"""
    try:
        # Check crypto_prices database
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        # Quick health check
        cursor.execute("""
            SELECT 
                'Price Data' as service,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
            FROM ml_features_materialized
            UNION ALL
            SELECT 
                'OHLC Data' as service,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
            FROM ohlc_data
        """)
        
        results = cursor.fetchall()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n[{timestamp}] SYSTEM STATUS:")
        for service, latest, recent_1h in results:
            if latest:
                age_hours = (datetime.now() - latest).total_seconds() / 3600
                status = "✅" if age_hours < 4 else "⚠️" if age_hours < 12 else "🚨"
                print(f"  {status} {service}: {age_hours:.1f}h old, {recent_1h} recent")
            else:
                print(f"  ❌ {service}: No data")
        
        cursor.close()
        conn.close()
        
        # Check crypto_news database
        news_conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_news'
        )
        news_cursor = news_conn.cursor()
        
        news_cursor.execute("""
            SELECT 
                'News' as service,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
            FROM crypto_news_data
            UNION ALL
            SELECT 
                'Social' as service,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
            FROM social_media_posts
            UNION ALL
            SELECT 
                'Sentiment' as service,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
            FROM sentiment_data
        """)
        
        news_results = news_cursor.fetchall()
        for service, latest, recent_1h in news_results:
            if latest:
                age_hours = (datetime.now() - latest).total_seconds() / 3600
                status = "✅" if age_hours < 24 else "⚠️" if age_hours < 48 else "🚨"
                print(f"  {status} {service}: {age_hours:.1f}h old, {recent_1h} recent")
            else:
                print(f"  ❌ {service}: No data")
        
        news_cursor.close()
        news_conn.close()
        
        print("  " + "="*50)
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring error: {e}")

def main():
    """Main monitoring loop"""
    print("🔄 Starting lightweight continuous monitoring...")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n--- Cycle #{cycle} ---")
            monitor_once()
            time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
            break
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    main()