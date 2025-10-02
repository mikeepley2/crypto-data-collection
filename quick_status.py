#!/usr/bin/env python3
"""
Quick status check of crypto data collection system
"""
import mysql.connector
from datetime import datetime

def quick_status_check():
    """Quick status check"""
    try:
        # Check crypto_prices database
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"🔍 QUICK STATUS CHECK - {timestamp}")
        print("=" * 60)
        
        # Price data status
        cursor.execute("""
            SELECT 
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
            FROM ml_features_materialized
        """)
        
        result = cursor.fetchone()
        latest, recent_1h, recent_24h = result
        
        if latest:
            age_hours = (datetime.now() - latest).total_seconds() / 3600
            status = "✅ HEALTHY" if age_hours < 4 else "⚠️ WARNING" if age_hours < 12 else "🚨 CRITICAL"
            print(f"{status} Price Data: {age_hours:.1f}h old, {recent_1h} (1h), {recent_24h} (24h)")
        else:
            print("❌ Price Data: No data")
        
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
        
        # News status
        news_cursor.execute("""
            SELECT 
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
            FROM crypto_news_data
        """)
        
        result = news_cursor.fetchone()
        latest, recent_1h, recent_24h = result
        
        if latest:
            age_hours = (datetime.now() - latest).total_seconds() / 3600
            status = "✅ HEALTHY" if age_hours < 24 else "⚠️ WARNING" if age_hours < 48 else "🚨 CRITICAL"
            print(f"{status} News Collection: {age_hours:.1f}h old, {recent_1h} (1h), {recent_24h} (24h)")
        else:
            print("❌ News Collection: No data")
        
        # Social status
        news_cursor.execute("""
            SELECT 
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
            FROM social_media_posts
        """)
        
        result = news_cursor.fetchone()
        latest, recent_1h, recent_24h = result
        
        if latest:
            age_hours = (datetime.now() - latest).total_seconds() / 3600
            status = "✅ HEALTHY" if age_hours < 24 else "⚠️ WARNING" if age_hours < 48 else "🚨 CRITICAL"
            print(f"{status} Social Collection: {age_hours:.1f}h old, {recent_1h} (1h), {recent_24h} (24h)")
        else:
            print("❌ Social Collection: No data")
        
        # Sentiment status
        news_cursor.execute("""
            SELECT 
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
            FROM sentiment_data
        """)
        
        result = news_cursor.fetchone()
        latest, recent_1h, recent_24h = result
        
        if latest:
            age_hours = (datetime.now() - latest).total_seconds() / 3600
            status = "✅ HEALTHY" if age_hours < 24 else "⚠️ WARNING" if age_hours < 48 else "🚨 CRITICAL"
            print(f"{status} Sentiment Processing: {age_hours:.1f}h old, {recent_1h} (1h), {recent_24h} (24h)")
        else:
            print("❌ Sentiment Processing: No data")
        
        news_cursor.close()
        news_conn.close()
        
        print("=" * 60)
        print("✅ Status check completed")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    quick_status_check()