#!/usr/bin/env python3
"""
Fix Collector Table Mappings
Create views to map expected table names to actual tables with data
"""

import mysql.connector
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_collector_table_mappings():
    """Create database views to fix table name mismatches"""
    
    print("🔧 FIXING COLLECTOR TABLE MAPPINGS")
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
    
    # Table mappings based on scan results
    # Format: {database: {expected_table: actual_table}}
    table_mappings = {
        'crypto_prices': {
            # Price data is working correctly - enhanced-crypto-prices writes to 'price_data'
            # Onchain data is working correctly - onchain-data-collector writes to 'crypto_onchain_data'
            # But some services might expect different names
            'crypto_prices': 'price_data',  # If any service expects 'crypto_prices' table
            'onchain_metrics': 'crypto_onchain_data'  # Map expected 'onchain_metrics' to actual table
        },
        'crypto_news': {
            # News collection issue - need to map expected names to actual tables
            'crypto_news': 'crypto_news_data',  # Services expect 'crypto_news' but data is in 'crypto_news_data'
            'stock_news': 'news_data',  # Services expect 'stock_news' but general news is in 'news_data'
            'sentiment_data': 'crypto_sentiment_data',  # Map generic to specific sentiment data
            'stock_sentiment_data': 'social_sentiment_data'  # Map to social sentiment data
        }
    }
    
    # Track successful and failed mappings
    results = {
        'successful_views': [],
        'failed_views': [],
        'errors': []
    }
    
    for db_name, mappings in table_mappings.items():
        print(f"\n📊 FIXING DATABASE: {db_name}")
        print("-" * 40)
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                for expected_table, actual_table in mappings.items():
                    try:
                        # First, verify the actual table exists and has data
                        cursor.execute(f"SELECT COUNT(*) FROM `{actual_table}`")
                        count = cursor.fetchone()[0]
                        
                        if count == 0:
                            print(f"  ⚠️  {actual_table} exists but has no data, skipping view creation")
                            continue
                        
                        # Check if expected table already exists as a table (not view)
                        cursor.execute(f"""
                            SELECT TABLE_TYPE 
                            FROM information_schema.TABLES 
                            WHERE TABLE_SCHEMA = '{db_name}' 
                            AND TABLE_NAME = '{expected_table}'
                        """)
                        existing = cursor.fetchone()
                        
                        if existing and existing[0] == 'BASE TABLE':
                            print(f"  ℹ️  {expected_table} already exists as table, skipping")
                            continue
                        
                        # Drop existing view if it exists
                        try:
                            cursor.execute(f"DROP VIEW IF EXISTS `{expected_table}`")
                        except Exception as e:
                            logger.debug(f"Could not drop view {expected_table}: {e}")
                        
                        # Create view mapping expected name to actual table
                        create_view_sql = f"CREATE VIEW `{expected_table}` AS SELECT * FROM `{actual_table}`"
                        cursor.execute(create_view_sql)
                        
                        print(f"  ✅ Created view: {expected_table} -> {actual_table} ({count:,} records)")
                        results['successful_views'].append(f"{db_name}.{expected_table} -> {actual_table}")
                        
                    except Exception as e:
                        error_msg = f"Failed to create view {expected_table} -> {actual_table}: {e}"
                        print(f"  ❌ {error_msg}")
                        results['failed_views'].append(f"{db_name}.{expected_table}")
                        results['errors'].append(error_msg)
                
                # Commit changes
                conn.commit()
                
        except Exception as e:
            error_msg = f"Error with database {db_name}: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
    
    # Handle missing tables that might need to be created
    print(f"\n🔍 CHECKING FOR MISSING TABLES")
    print("-" * 40)
    
    missing_table_checks = {
        'crypto_news': ['reddit_posts'],  # This table might be truly missing
    }
    
    for db_name, tables_to_check in missing_table_checks.items():
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                for table_name in tables_to_check:
                    # Check if there's a similar table we can map to
                    cursor.execute("SHOW TABLES")
                    all_tables = [t[0] for t in cursor.fetchall()]
                    
                    # Look for tables containing 'reddit' or 'social'
                    reddit_tables = [t for t in all_tables if 'reddit' in t.lower() or 'social' in t.lower()]
                    
                    if reddit_tables:
                        # Use the table with most data
                        best_table = None
                        max_count = 0
                        
                        for candidate in reddit_tables:
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM `{candidate}`")
                                count = cursor.fetchone()[0]
                                if count > max_count:
                                    max_count = count
                                    best_table = candidate
                            except:
                                continue
                        
                        if best_table and max_count > 0:
                            try:
                                cursor.execute(f"DROP VIEW IF EXISTS `{table_name}`")
                                cursor.execute(f"CREATE VIEW `{table_name}` AS SELECT * FROM `{best_table}`")
                                print(f"  ✅ Created view: {table_name} -> {best_table} ({max_count:,} records)")
                                results['successful_views'].append(f"{db_name}.{table_name} -> {best_table}")
                            except Exception as e:
                                print(f"  ❌ Failed to create {table_name} view: {e}")
                        else:
                            print(f"  ⚠️  No suitable table found for {table_name}")
                    else:
                        print(f"  ⚠️  No reddit/social tables found for {table_name}")
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error checking missing tables in {db_name}: {e}")
    
    # Print summary
    print(f"\n📋 SUMMARY")
    print("=" * 30)
    print(f"✅ Successfully created {len(results['successful_views'])} views:")
    for view in results['successful_views']:
        print(f"   - {view}")
    
    if results['failed_views']:
        print(f"\n❌ Failed to create {len(results['failed_views'])} views:")
        for view in results['failed_views']:
            print(f"   - {view}")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Restart collectors to pick up new table mappings")
    print("2. Monitor collection progress")
    print("3. Check if data starts flowing to the mapped tables")
    
    return results

def restart_collectors():
    """Restart Kubernetes collectors to pick up new table mappings"""
    print(f"\n🔄 RESTARTING COLLECTORS")
    print("-" * 30)
    
    import subprocess
    
    # List of collectors to restart
    collectors = [
        'crypto-news-collector',
        'stock-news-collector', 
        'onchain-data-collector',
        'social-other',
        'crypto-sentiment-collector',
        'stock-sentiment-collector'
    ]
    
    for collector in collectors:
        try:
            # Restart the deployment
            cmd = f"kubectl rollout restart deployment {collector} -n crypto-collectors"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ Restarted {collector}")
            else:
                print(f"  ❌ Failed to restart {collector}: {result.stderr}")
                
        except Exception as e:
            print(f"  ❌ Error restarting {collector}: {e}")

if __name__ == "__main__":
    # Fix table mappings
    results = fix_collector_table_mappings()
    
    # Restart collectors if views were created successfully
    if results['successful_views']:
        restart_collectors()
        print(f"\n✨ Table mapping fixes complete!")
        print("🔍 Monitor the simple_collection_monitor.py to see if data collection resumes")
    else:
        print(f"\n⚠️  No views were created. Please check the errors above.")