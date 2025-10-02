#!/usr/bin/env python3
"""
Verify Table Mappings are Working
Check if the views we created are accessible and contain data
"""

import mysql.connector
from datetime import datetime, timedelta

def verify_table_mappings():
    """Test the database views we created"""
    
    print("🔍 VERIFYING TABLE MAPPINGS")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Database connection config
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    # Views we created
    views_to_test = {
        'crypto_prices': [
            'crypto_prices',  # -> price_data
            'onchain_metrics'  # -> crypto_onchain_data
        ],
        'crypto_news': [
            'crypto_news',  # -> crypto_news_data
            'stock_news',  # -> news_data
            'stock_sentiment_data',  # -> social_sentiment_data
            'reddit_posts'  # -> social_media_posts
        ]
    }
    
    for db_name, views in views_to_test.items():
        print(f"\n📊 DATABASE: {db_name}")
        print("-" * 30)
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                for view_name in views:
                    try:
                        # Test basic SELECT
                        cursor.execute(f"SELECT COUNT(*) FROM `{view_name}`")
                        total_count = cursor.fetchone()[0]
                        
                        # Test recent data (last 24 hours)
                        recent_count = 0
                        latest_timestamp = None
                        
                        # Check for timestamp columns
                        cursor.execute(f"SHOW COLUMNS FROM `{view_name}`")
                        columns = [col[0] for col in cursor.fetchall()]
                        
                        timestamp_cols = [col for col in columns if 'timestamp' in col.lower() 
                                        or 'time' in col.lower() 
                                        or 'date' in col.lower() 
                                        or col.lower() in ['created_at', 'updated_at']]
                        
                        if timestamp_cols:
                            ts_col = timestamp_cols[0]
                            try:
                                cursor.execute(f"""
                                    SELECT COUNT(*) as recent_count, MAX(`{ts_col}`) as latest 
                                    FROM `{view_name}` 
                                    WHERE `{ts_col}` >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                                """)
                                result = cursor.fetchone()
                                recent_count = result[0] if result else 0
                                latest_timestamp = result[1] if result else None
                            except Exception as e:
                                print(f"    ⚠️  Error getting recent data for {view_name}: {e}")
                        
                        # Status indicator
                        status = "🟢" if recent_count > 0 else "🔴"
                        
                        print(f"  {status} {view_name:20} | Total: {total_count:>8,} | Recent: {recent_count:>6} | Latest: {latest_timestamp}")
                        
                    except Exception as e:
                        print(f"  ❌ {view_name:20} | ERROR: {e}")
                
        except Exception as e:
            print(f"❌ Error connecting to {db_name}: {e}")
    
    # Test specific expected queries that collectors might use
    print(f"\n🧪 TESTING COLLECTOR-STYLE QUERIES")
    print("-" * 40)
    
    test_queries = [
        {
            'db': 'crypto_prices',
            'name': 'Price Data Query',
            'query': "SELECT symbol, close, timestamp FROM crypto_prices ORDER BY timestamp DESC LIMIT 5"
        },
        {
            'db': 'crypto_prices', 
            'name': 'Onchain Metrics Query',
            'query': "SELECT symbol, metric_value, timestamp FROM onchain_metrics ORDER BY timestamp DESC LIMIT 5"
        },
        {
            'db': 'crypto_news',
            'name': 'Crypto News Query', 
            'query': "SELECT title, source, timestamp FROM crypto_news ORDER BY timestamp DESC LIMIT 3"
        },
        {
            'db': 'crypto_news',
            'name': 'Stock News Query',
            'query': "SELECT title, source, timestamp FROM stock_news ORDER BY timestamp DESC LIMIT 3"
        }
    ]
    
    for test in test_queries:
        try:
            config = db_config.copy()
            config['database'] = test['db']
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                cursor.execute(test['query'])
                results = cursor.fetchall()
                
                if results:
                    print(f"  ✅ {test['name']:20} | {len(results)} rows returned")
                    # Show first result as sample
                    if len(results) > 0:
                        print(f"     Sample: {results[0]}")
                else:
                    print(f"  ⚠️  {test['name']:20} | No data returned")
                    
        except Exception as e:
            print(f"  ❌ {test['name']:20} | Error: {e}")
    
    print(f"\n🎯 RECOMMENDATIONS")
    print("-" * 30)
    print("1. Views created successfully - collectors should now find expected tables")
    print("2. Wait 5-10 minutes for collectors to pick up new mappings")
    print("3. Monitor collection progress with monitoring script")
    print("4. Check for new data flowing into the tables")

if __name__ == "__main__":
    verify_table_mappings()