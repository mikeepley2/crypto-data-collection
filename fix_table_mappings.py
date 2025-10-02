#!/usr/bin/env python3
"""
Fix Table Mappings - Create views/aliases for services to use correct tables
"""

import mysql.connector
from datetime import datetime

def fix_table_mappings():
    """Create views to map service expectations to actual tables"""
    
    print("🔧 FIXING TABLE MAPPINGS")
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
    
    # Table mappings: expected_name -> actual_table
    table_mappings = {
        'crypto_prices': {
            # Services expect 'crypto_prices' but we need to find what table has price data
            # Services expect 'onchain_metrics' but actual table is 'crypto_onchain_data'
            'onchain_metrics': 'crypto_onchain_data'
        },
        'crypto_news': {
            # Services expect 'crypto_news' but actual table is 'crypto_news_data'  
            'crypto_news': 'crypto_news_data',
            # Services expect 'stock_sentiment_data' but actual table is 'sentiment_data'
            'stock_sentiment_data': 'sentiment_data'
        }
    }
    
    for db_name, mappings in table_mappings.items():
        print(f"\n📊 DATABASE: {db_name}")
        print("-" * 30)
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                for expected_table, actual_table in mappings.items():
                    try:
                        # Check if actual table exists
                        cursor.execute(f"SELECT COUNT(*) FROM {actual_table}")
                        count = cursor.fetchone()[0]
                        
                        # Drop view if it exists (in case we're re-running)
                        try:
                            cursor.execute(f"DROP VIEW IF EXISTS {expected_table}")
                            print(f"  🗑️  Dropped existing view: {expected_table}")
                        except:
                            pass
                        
                        # Create view mapping expected name to actual table
                        cursor.execute(f"CREATE VIEW {expected_table} AS SELECT * FROM {actual_table}")
                        
                        print(f"  ✅ Created view: {expected_table} -> {actual_table} ({count:,} records)")
                        
                    except Exception as e:
                        print(f"  ❌ Failed to create view {expected_table}: {e}")
                
                # Commit changes
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error with database {db_name}: {e}")
    
    # Now let's figure out what to do about crypto_prices table
    print(f"\n🔍 INVESTIGATING PRICE DATA:")
    print("-" * 30)
    
    try:
        config = db_config.copy()
        config['database'] = 'crypto_prices'
        
        with mysql.connector.connect(**config) as conn:
            cursor = conn.cursor()
            
            # Look for tables that might contain price data
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            
            price_tables = [t for t in tables if 'price' in t.lower() or 'ohlc' in t.lower()]
            
            print(f"Tables that might contain price data: {price_tables}")
            
            for table in price_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    # Try to get recent data
                    try:
                        cursor.execute(f"""
                            SELECT COUNT(*) as recent_count, MAX(timestamp) as latest 
                            FROM {table} 
                            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                        """)
                        result = cursor.fetchone()
                        recent_count = result[0] if result else 0
                        latest = result[1] if result else None
                        
                        print(f"  📊 {table}: {count:,} total, {recent_count} recent, latest: {latest}")
                        
                    except:
                        print(f"  📊 {table}: {count:,} total (no timestamp column)")
                        
                except Exception as e:
                    print(f"  ❌ Error checking {table}: {e}")
                    
    except Exception as e:
        print(f"❌ Error investigating price data: {e}")
    
    # Check for missing tables that need to be created or mapped
    print(f"\n📋 CHECKING OTHER MISSING TABLES:")
    print("-" * 40)
    
    missing_tables = {
        'crypto_news': ['stock_news', 'reddit_posts'],
        'crypto_prices': ['crypto_prices']  # We'll figure this out
    }
    
    for db_name, tables in missing_tables.items():
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                for table in tables:
                    # Check if there are similar tables
                    cursor.execute("SHOW TABLES")
                    all_tables = [t[0] for t in cursor.fetchall()]
                    
                    # Look for similar table names
                    similar = [t for t in all_tables if table.replace('_', '') in t.replace('_', '') or t.replace('_', '') in table.replace('_', '')]
                    
                    if similar:
                        print(f"  💡 {table} missing, similar tables: {similar}")
                    else:
                        print(f"  ❌ {table} missing, no similar tables found")
                        
        except Exception as e:
            print(f"❌ Error checking {db_name}: {e}")
    
    print(f"\n🎯 NEXT STEPS:")
    print("-" * 20)
    print("1. Views created for existing table mappings")
    print("2. Need to identify correct price data table") 
    print("3. May need to create missing tables (stock_news, reddit_posts)")
    print("4. Test services with new mappings")

if __name__ == "__main__":
    fix_table_mappings()