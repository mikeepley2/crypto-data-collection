#!/usr/bin/env python3
"""
Table Structure Analysis - Check existing tables vs service expectations
"""

import mysql.connector
from datetime import datetime

def analyze_table_structure():
    """Analyze existing database tables vs service expectations"""
    
    print("🔍 TABLE STRUCTURE ANALYSIS")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Database connection config
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    # Check both databases
    databases = ['crypto_news', 'crypto_prices']
    
    for db_name in databases:
        print(f"\n📊 DATABASE: {db_name}")
        print("-" * 40)
        
        try:
            # Connect to specific database
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                print(f"Tables found: {len(tables)}")
                
                for table_tuple in tables:
                    table_name = table_tuple[0]
                    
                    # Get table info
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    # Get recent records
                    try:
                        # Try common timestamp columns
                        timestamp_cols = ['timestamp', 'created_at', 'published_date', 'published_at']
                        recent_count = 0
                        latest_time = None
                        
                        for col in timestamp_cols:
                            try:
                                cursor.execute(f"""
                                    SELECT COUNT(*) as recent_count, MAX({col}) as latest 
                                    FROM {table_name} 
                                    WHERE {col} >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                                """)
                                result = cursor.fetchone()
                                if result and result[0] > 0:
                                    recent_count = result[0]
                                    latest_time = result[1]
                                    break
                            except:
                                continue
                        
                        # Format latest time
                        latest_str = str(latest_time)[:19] if latest_time else "Unknown"
                        
                        print(f"  📋 {table_name:<25} | {count:>8,} total | {recent_count:>4} recent | {latest_str}")
                        
                    except Exception as e:
                        print(f"  📋 {table_name:<25} | {count:>8,} total | Error getting recent data")
                
        except Exception as e:
            print(f"❌ Error accessing {db_name}: {e}")
    
    # Now check what the monitoring script expects
    print(f"\n🎯 SERVICE EXPECTATIONS:")
    print("-" * 40)
    
    # These are the tables our monitoring scripts are looking for
    expected_tables = {
        'crypto_prices': [
            'crypto_prices',
            'technical_indicators', 
            'macro_indicators',
            'onchain_metrics'
        ],
        'crypto_news': [
            'crypto_news',
            'stock_news',
            'reddit_posts',
            'crypto_sentiment_data',
            'stock_sentiment_data'
        ]
    }
    
    for db_name, expected in expected_tables.items():
        print(f"\n📊 Expected in {db_name}:")
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                # Check if expected tables exist
                for table in expected:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  ✅ {table:<25} | EXISTS ({count:,} records)")
                    except Exception as e:
                        print(f"  ❌ {table:<25} | MISSING or ERROR: {str(e)[:50]}")
                        
                        # Try to find similar table names
                        cursor.execute("SHOW TABLES")
                        all_tables = [t[0] for t in cursor.fetchall()]
                        similar = [t for t in all_tables if table.replace('_', '') in t.replace('_', '') or t.replace('_', '') in table.replace('_', '')]
                        if similar:
                            print(f"    💡 Similar tables found: {', '.join(similar)}")
                
        except Exception as e:
            print(f"❌ Error checking {db_name}: {e}")

if __name__ == "__main__":
    analyze_table_structure()