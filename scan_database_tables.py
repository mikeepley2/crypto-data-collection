#!/usr/bin/env python3
"""
Scan databases for tables with the most data and analyze collector configurations
"""

import mysql.connector
from datetime import datetime, timedelta
import os
import json

def scan_database_tables():
    """Scan all tables in both databases and find the ones with most data"""
    
    print("🔍 SCANNING DATABASE TABLES FOR DATA")
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
    
    databases = ['crypto_prices', 'crypto_news']
    all_table_data = {}
    
    for db_name in databases:
        print(f"\n📊 DATABASE: {db_name}")
        print("-" * 40)
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SHOW TABLES")
                tables = [t[0] for t in cursor.fetchall()]
                
                table_info = {}
                
                for table in tables:
                    try:
                        # Get total count
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                        total_count = cursor.fetchone()[0]
                        
                        # Try to get recent data (last 24 hours)
                        recent_count = 0
                        latest_timestamp = None
                        
                        # Check for common timestamp columns
                        cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                        columns = [col[0] for col in cursor.fetchall()]
                        
                        timestamp_cols = [col for col in columns if 'timestamp' in col.lower() 
                                        or 'time' in col.lower() 
                                        or 'date' in col.lower() 
                                        or col.lower() in ['created_at', 'updated_at']]
                        
                        if timestamp_cols:
                            # Use the first timestamp column found
                            ts_col = timestamp_cols[0]
                            try:
                                cursor.execute(f"""
                                    SELECT COUNT(*) as recent_count, MAX(`{ts_col}`) as latest 
                                    FROM `{table}` 
                                    WHERE `{ts_col}` >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                                """)
                                result = cursor.fetchone()
                                recent_count = result[0] if result else 0
                                latest_timestamp = result[1] if result else None
                            except Exception as e:
                                print(f"    ⚠️  Error getting recent data for {table}: {e}")
                        
                        table_info[table] = {
                            'total_count': total_count,
                            'recent_count': recent_count,
                            'latest_timestamp': latest_timestamp,
                            'timestamp_columns': timestamp_cols,
                            'all_columns': columns
                        }
                        
                        print(f"  📋 {table:25} | Total: {total_count:>8,} | Recent: {recent_count:>6} | Latest: {latest_timestamp}")
                        
                    except Exception as e:
                        print(f"  ❌ Error scanning {table}: {e}")
                
                all_table_data[db_name] = table_info
                
        except Exception as e:
            print(f"❌ Error connecting to {db_name}: {e}")
    
    # Now analyze the data to find the best tables
    print(f"\n🎯 ANALYSIS: TABLES WITH MOST DATA")
    print("=" * 60)
    
    for db_name, tables in all_table_data.items():
        print(f"\n📊 {db_name.upper()} - TOP TABLES BY DATA VOLUME:")
        print("-" * 50)
        
        # Sort by total count
        sorted_tables = sorted(tables.items(), key=lambda x: x[1]['total_count'], reverse=True)
        
        for table_name, info in sorted_tables[:10]:  # Top 10
            recent_indicator = "🟢" if info['recent_count'] > 0 else "🔴"
            print(f"  {recent_indicator} {table_name:25} | {info['total_count']:>8,} total | {info['recent_count']:>6} recent")
    
    # Check what collectors are expecting
    print(f"\n🔧 CHECKING COLLECTOR CONFIGURATIONS")
    print("=" * 50)
    
    # Look for collector configuration files
    config_files = []
    
    # Common places to find collector configs
    search_paths = [
        'src/',
        'config/',
        'collectors/',
        '.'
    ]
    
    for root_path in search_paths:
        if os.path.exists(root_path):
            for root, dirs, files in os.walk(root_path):
                for file in files:
                    if (file.endswith('.py') and 'collector' in file.lower()) or \
                       (file.endswith('.json') and 'config' in file.lower()) or \
                       (file.endswith('.yaml') and ('config' in file.lower() or 'collector' in file.lower())):
                        config_files.append(os.path.join(root, file))
    
    print(f"Found {len(config_files)} potential collector config files:")
    for f in config_files[:20]:  # Show first 20
        print(f"  📄 {f}")
    
    # Look for table references in collector files
    print(f"\n🔍 SEARCHING FOR TABLE REFERENCES IN COLLECTORS")
    print("-" * 50)
    
    table_references = {}
    
    for config_file in config_files[:10]:  # Check first 10 files
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for common table names
                common_tables = [
                    'crypto_prices', 'crypto_news', 'stock_news', 'reddit_posts',
                    'onchain_metrics', 'technical_indicators', 'macro_indicators',
                    'sentiment_data', 'crypto_news_data', 'crypto_onchain_data'
                ]
                
                found_tables = []
                for table in common_tables:
                    if table in content:
                        found_tables.append(table)
                
                if found_tables:
                    table_references[config_file] = found_tables
                    print(f"  📄 {os.path.basename(config_file):30} | References: {', '.join(found_tables)}")
                    
        except Exception as e:
            print(f"  ❌ Error reading {config_file}: {e}")
    
    # Generate recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 30)
    
    recommendations = []
    
    # Find the tables with most data for each category
    crypto_price_tables = []
    news_tables = []
    onchain_tables = []
    sentiment_tables = []
    
    for db_name, tables in all_table_data.items():
        for table_name, info in tables.items():
            if 'price' in table_name.lower() or 'ohlc' in table_name.lower():
                crypto_price_tables.append((table_name, info['total_count'], db_name))
            elif 'news' in table_name.lower():
                news_tables.append((table_name, info['total_count'], db_name))
            elif 'onchain' in table_name.lower() or 'chain' in table_name.lower():
                onchain_tables.append((table_name, info['total_count'], db_name))
            elif 'sentiment' in table_name.lower():
                sentiment_tables.append((table_name, info['total_count'], db_name))
    
    # Sort by data volume
    crypto_price_tables.sort(key=lambda x: x[1], reverse=True)
    news_tables.sort(key=lambda x: x[1], reverse=True)
    onchain_tables.sort(key=lambda x: x[1], reverse=True)
    sentiment_tables.sort(key=lambda x: x[1], reverse=True)
    
    print("\n🎯 RECOMMENDED TABLE MAPPINGS:")
    print("-" * 40)
    
    if crypto_price_tables:
        best_price_table = crypto_price_tables[0]
        print(f"💰 PRICE DATA: {best_price_table[0]} ({best_price_table[1]:,} records in {best_price_table[2]})")
        recommendations.append(f"crypto_prices -> {best_price_table[0]}")
    
    if news_tables:
        best_news_table = news_tables[0]
        print(f"📰 NEWS DATA: {best_news_table[0]} ({best_news_table[1]:,} records in {best_news_table[2]})")
        recommendations.append(f"crypto_news -> {best_news_table[0]}")
    
    if onchain_tables:
        best_onchain_table = onchain_tables[0]
        print(f"⛓️  ONCHAIN DATA: {best_onchain_table[0]} ({best_onchain_table[1]:,} records in {best_onchain_table[2]})")
        recommendations.append(f"onchain_metrics -> {best_onchain_table[0]}")
    
    if sentiment_tables:
        best_sentiment_table = sentiment_tables[0]
        print(f"😊 SENTIMENT DATA: {best_sentiment_table[0]} ({best_sentiment_table[1]:,} records in {best_sentiment_table[2]})")
        recommendations.append(f"stock_sentiment_data -> {best_sentiment_table[0]}")
    
    return all_table_data, table_references, recommendations

if __name__ == "__main__":
    scan_database_tables()