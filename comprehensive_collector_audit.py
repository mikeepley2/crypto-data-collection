#!/usr/bin/env python3

import mysql.connector
from datetime import datetime

def check_all_collectors():
    """Check all collection services and their recent data"""
    
    print("🔍 COMPREHENSIVE COLLECTOR AUDIT")
    print(f"⏰ Current time: {datetime.now()}")
    print("=" * 80)
    
    # Connection details for different databases
    db_configs = {
        'crypto_prices': {
            'host': 'host.docker.internal',
            'database': 'crypto_prices',
            'user': 'news_collector',
            'password': '99Rules!'
        },
        'crypto_news': {
            'host': 'host.docker.internal',
            'database': 'crypto_news',
            'user': 'news_collector',
            'password': '99Rules!'
        }
    }
    
    # Define what to check in each database
    checks = {
        'crypto_prices': [
            ('price_data', 'Price Collection', 'timestamp'),
            ('sentiment_data', 'Sentiment Collection', 'timestamp'),
            ('social_media_posts', 'Social Media Collection', 'timestamp'),
            ('technical_indicators', 'Technical Indicators', 'timestamp'),
            ('macro_indicators', 'Macro Economic Data', 'timestamp'),
            ('crypto_onchain_data', 'Onchain Data', 'timestamp'),
        ],
        'crypto_news': [
            ('crypto_news_data', 'Crypto News', 'created_at'),
            ('stock_market_news_data', 'Stock News', 'created_at'),
            ('crypto_sentiment_data', 'Crypto Sentiment', 'created_at'),
            ('stock_market_sentiment_data', 'Stock Sentiment', 'created_at'),
            ('social_media_posts', 'Social Posts', 'created_at'),
            ('social_sentiment_data', 'Social Sentiment', 'created_at'),
        ]
    }
    
    for db_name, config in db_configs.items():
        print(f"\n📊 DATABASE: {db_name.upper()}")
        print("-" * 40)
        
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
            for table_name, display_name, timestamp_col in checks[db_name]:
                try:
                    # Check if table exists
                    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                    if not cursor.fetchone():
                        print(f"⚠️  {display_name:25} | Table doesn't exist")
                        continue
                    
                    # Check total records
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = cursor.fetchone()[0]
                    
                    # Check recent records (try different timestamp column names)
                    recent_count = 0
                    latest_time = None
                    
                    for ts_col in [timestamp_col, 'timestamp', 'created_at', 'updated_at']:
                        try:
                            cursor.execute(f"""
                                SELECT COUNT(*) as count, MAX({ts_col}) as latest 
                                FROM {table_name} 
                                WHERE {ts_col} > DATE_SUB(NOW(), INTERVAL 2 HOUR)
                            """)
                            result = cursor.fetchone()
                            recent_count = result[0] or 0
                            latest_time = result[1]
                            break
                        except:
                            continue
                    
                    # Status assessment
                    if recent_count > 100:
                        status = "✅ EXCELLENT"
                    elif recent_count > 10:
                        status = "🟡 MODERATE"
                    elif recent_count > 0:
                        status = "🟠 LOW"
                    else:
                        status = "❌ STALE"
                    
                    # Display results
                    latest_str = str(latest_time) if latest_time else "No data"
                    print(f"{status} {display_name:25} | Total: {total_count:8,} | Recent 2h: {recent_count:4} | Latest: {latest_str}")
                    
                except Exception as e:
                    print(f"❌ {display_name:25} | Error: {str(e)[:50]}...")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to connect to {db_name}: {e}")
    
    print("\n" + "=" * 80)
    print("📋 LEGEND:")
    print("✅ EXCELLENT: >100 records in last 2 hours")
    print("🟡 MODERATE:  10-100 records in last 2 hours") 
    print("🟠 LOW:       1-10 records in last 2 hours")
    print("❌ STALE:     0 records in last 2 hours")
    print("=" * 80)

if __name__ == "__main__":
    check_all_collectors()