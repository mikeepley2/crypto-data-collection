#!/usr/bin/env python3
"""
Quick evaluation with correct column names
"""
import mysql.connector
from datetime import datetime

def check_recent_data():
    print("🔍 RECENT DATA COLLECTION CHECK")
    print("=" * 50)
    
    try:
        # Check crypto_prices
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        # Check ml_features_materialized schema
        cursor.execute("SHOW COLUMNS FROM ml_features_materialized LIKE '%datetime%'")
        datetime_cols = cursor.fetchall()
        print(f"DateTime columns: {[col[0] for col in datetime_cols]}")
        
        # Check recent materialized data
        cursor.execute("""
            SELECT COUNT(*), MAX(created_at), MAX(updated_at)
            FROM ml_features_materialized 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
        """)
        result = cursor.fetchone()
        print(f"ML Features (6h): {result[0]} records, latest created: {result[1]}, latest updated: {result[2]}")
        
        # Check what's actually being collected recently
        cursor.execute("""
            SELECT symbol, COUNT(*) as count, MAX(created_at) as latest
            FROM ml_features_materialized 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 HOUR)
            GROUP BY symbol
            ORDER BY latest DESC
            LIMIT 10
        """)
        results = cursor.fetchall()
        print(f"\nTop 10 recently updated symbols (12h):")
        for symbol, count, latest in results:
            print(f"   {symbol}: {count} records, latest: {latest}")
        
        cursor.close()
        conn.close()
        
        # Check news database for actual recent collection
        news_conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_news'
        )
        news_cursor = news_conn.cursor()
        
        # Check if news was actually collected today
        news_cursor.execute("""
            SELECT COUNT(*), MAX(created_at)
            FROM crypto_news_data 
            WHERE created_at >= CURDATE()
        """)
        result = news_cursor.fetchone()
        print(f"\nNews today: {result[0]} records, latest: {result[1]}")
        
        # Check very recent news
        news_cursor.execute("""
            SELECT COUNT(*), MAX(created_at)
            FROM crypto_news_data 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        """)
        result = news_cursor.fetchone()
        print(f"News (2h): {result[0]} records, latest: {result[1]}")
        
        news_cursor.close()
        news_conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_service_collection_status():
    print("\n🚀 ACTIVE COLLECTION STATUS")
    print("=" * 50)
    
    try:
        # Let's see what cronjobs have run recently
        print("Recent completed collection jobs should show data...")
        
        # Check if price collection is working
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        # Check crypto_assets for recent price data
        cursor.execute("""
            SELECT COUNT(*), MAX(timestamp)
            FROM crypto_assets 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        result = cursor.fetchone()
        print(f"Raw price data (1h): {result[0]} records, latest: {result[1]}")
        
        cursor.execute("""
            SELECT COUNT(*), MAX(timestamp)
            FROM crypto_assets 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
        """)
        result = cursor.fetchone()
        print(f"Raw price data (6h): {result[0]} records, latest: {result[1]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking collection: {e}")

if __name__ == "__main__":
    check_recent_data()
    check_service_collection_status()