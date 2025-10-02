#!/usr/bin/env python3
"""
Data Collection Tables Inventory
Complete overview of all tables used for data collection with record counts
"""

import mysql.connector
from datetime import datetime

def show_all_data_collection_tables():
    """Show all tables used for data collection with record counts"""
    
    print("📊 DATA COLLECTION TABLES INVENTORY")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Database connection
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    # Define all data collection tables by category
    data_collection_tables = {
        'crypto_prices': {
            'Primary Active Tables': {
                'ml_features_materialized': 'Primary ML features table (117 columns) - Enhanced crypto prices writes here',
                'crypto_onchain_data': 'Onchain metrics data - Active collection',
                'hourly_data': 'VIEW of ml_features_materialized providing OHLCV format'
            },
            'Reference/Historical Tables': {
                'price_data_real': 'Comprehensive historical price data (49 columns)',
                'technical_indicators': 'Technical analysis indicators',
                'macro_indicators': 'Macro economic indicators'
            },
            'Archived Tables': {
                'price_data_old': 'Previous basic price data (archived)',
                'ohlc_data_old': 'Previous OHLC data (archived)'
            },
            'Compatibility Views': {
                'crypto_prices': 'VIEW mapping to price_data for service compatibility',
                'onchain_metrics': 'VIEW mapping to crypto_onchain_data for service compatibility'
            }
        },
        'crypto_news': {
            'Primary Active Tables': {
                'crypto_news_data': 'Crypto-specific news articles',
                'news_data': 'General financial news data',
                'crypto_sentiment_data': 'Crypto sentiment analysis results',
                'social_media_posts': 'Social media content collection',
                'social_sentiment_data': 'Social media sentiment analysis'
            },
            'Secondary Tables': {
                'macro_economic_data': 'Macro economic data collection',
                'technical_indicators': 'Technical indicators (news database copy)'
            },
            'Archived Tables': {
                'sentiment_data_old': 'Previous sentiment data (archived)'
            },
            'Compatibility Views': {
                'crypto_news': 'VIEW mapping to crypto_news_data',
                'stock_news': 'VIEW mapping to news_data',
                'reddit_posts': 'VIEW mapping to social_media_posts',
                'stock_sentiment_data': 'VIEW mapping to social_sentiment_data'
            }
        }
    }
    
    grand_total_records = 0
    all_tables_summary = []
    
    for db_name, categories in data_collection_tables.items():
        print(f"\n🗄️  DATABASE: {db_name.upper()}")
        print("=" * 50)
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                db_total = 0
                
                for category, tables in categories.items():
                    print(f"\n📋 {category}:")
                    print("-" * 40)
                    
                    category_total = 0
                    
                    for table_name, description in tables.items():
                        try:
                            # Check if it's a view or table
                            cursor.execute(f"""
                                SELECT TABLE_TYPE 
                                FROM information_schema.TABLES 
                                WHERE TABLE_SCHEMA = '{db_name}' 
                                AND TABLE_NAME = '{table_name}'
                            """)
                            
                            table_info = cursor.fetchone()
                            if not table_info:
                                print(f"  ❌ {table_name:25} | NOT FOUND")
                                continue
                                
                            table_type = table_info[0]
                            type_icon = "👁️" if table_type == 'VIEW' else "📊"
                            
                            # Get record count
                            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                            record_count = cursor.fetchone()[0]
                            
                            # Check for recent data (last 24 hours)
                            recent_data = "?"
                            try:
                                # Try common timestamp columns
                                timestamp_cols = ['timestamp', 'timestamp_iso', 'created_at', 'updated_at', 'collected_at']
                                
                                for ts_col in timestamp_cols:
                                    try:
                                        cursor.execute(f"""
                                            SELECT COUNT(*) FROM `{table_name}` 
                                            WHERE `{ts_col}` >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                                        """)
                                        recent_count = cursor.fetchone()[0]
                                        if recent_count > 0:
                                            recent_data = f"{recent_count} (24h)"
                                            break
                                        else:
                                            recent_data = "0"
                                    except:
                                        continue
                            except:
                                recent_data = "N/A"
                            
                            print(f"  {type_icon} {table_name:25} | {record_count:>12,} records | Recent: {recent_data}")
                            print(f"      {description}")
                            
                            # Add to totals (only for actual tables, not views)
                            if table_type != 'VIEW':
                                category_total += record_count
                                db_total += record_count
                                
                            all_tables_summary.append({
                                'database': db_name,
                                'table': table_name,
                                'type': table_type,
                                'records': record_count,
                                'category': category,
                                'description': description,
                                'recent': recent_data
                            })
                            
                        except Exception as e:
                            print(f"  ❌ {table_name:25} | ERROR: {e}")
                    
                    if category_total > 0:
                        print(f"\n  📊 {category} Total: {category_total:,} records")
                
                print(f"\n🎯 {db_name.upper()} DATABASE TOTAL: {db_total:,} records")
                grand_total_records += db_total
                
        except Exception as e:
            print(f"❌ Error connecting to {db_name}: {e}")
    
    # Summary Section
    print(f"\n📈 SUMMARY STATISTICS")
    print("=" * 40)
    
    # Count by type
    tables_count = len([t for t in all_tables_summary if t['type'] == 'BASE TABLE'])
    views_count = len([t for t in all_tables_summary if t['type'] == 'VIEW'])
    
    print(f"Total Tables: {tables_count}")
    print(f"Total Views: {views_count}")
    print(f"Grand Total Records: {grand_total_records:,}")
    
    # Top 10 largest tables
    print(f"\n🏆 TOP 10 LARGEST TABLES:")
    print("-" * 35)
    
    largest_tables = sorted([t for t in all_tables_summary if t['type'] == 'BASE TABLE'], 
                           key=lambda x: x['records'], reverse=True)[:10]
    
    for i, table in enumerate(largest_tables, 1):
        print(f"{i:2d}. {table['database']}.{table['table']:25} | {table['records']:>10,} records")
    
    # Active collection summary
    print(f"\n🔄 ACTIVE DATA COLLECTION:")
    print("-" * 30)
    
    active_tables = [t for t in all_tables_summary if t['recent'] not in ['0', 'N/A', '?'] and '24h' in str(t['recent'])]
    
    if active_tables:
        total_recent = 0
        for table in active_tables:
            recent_str = str(table['recent']).replace(' (24h)', '')
            try:
                recent_num = int(recent_str)
                total_recent += recent_num
                print(f"  ✅ {table['database']}.{table['table']:25} | {recent_num:>6} records/24h")
            except:
                print(f"  ✅ {table['database']}.{table['table']:25} | Active")
        
        print(f"\n📊 Total Recent Collection Rate: {total_recent:,} records/24h")
    else:
        print("  ⚠️  No tables showing recent data collection")
    
    # Database breakdown
    print(f"\n📊 DATABASE BREAKDOWN:")
    print("-" * 25)
    
    db_totals = {}
    for table in all_tables_summary:
        if table['type'] == 'BASE TABLE':
            db_totals[table['database']] = db_totals.get(table['database'], 0) + table['records']
    
    for db_name, total in sorted(db_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (total / grand_total_records * 100) if grand_total_records > 0 else 0
        print(f"  {db_name:15} | {total:>10,} records ({percentage:5.1f}%)")
    
    print(f"\n✨ Data Collection Tables Inventory Complete!")
    print(f"🎯 Your system manages {grand_total_records:,} total records across {tables_count} tables")

if __name__ == "__main__":
    show_all_data_collection_tables()