#!/usr/bin/env python3
"""
Database Table Analysis and Cleanup Script
Analyzes all database tables to identify unused collection tables for cleanup
"""

import subprocess
import mysql.connector
import os
from datetime import datetime, timedelta
import json

def get_database_connection():
    """Get a connection to the MySQL database"""
    try:
        connection = mysql.connector.connect(
            host='192.168.230.162',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices',
            charset='utf8mb4'
        )
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def analyze_database_structure():
    """Analyze the database structure and table usage"""
    print("🔍 DATABASE STRUCTURE ANALYSIS")
    print("=" * 60)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Get all tables in the database
        cursor.execute("SHOW TABLES")
        all_tables = [table[0] for table in cursor.fetchall()]
        
        print(f"\n📊 Total tables found: {len(all_tables)}")
        
        # Categorize tables by name patterns
        table_categories = {
            'price_data': [],
            'ohlc_data': [],
            'sentiment': [],
            'news': [],
            'technical': [],
            'social': [],
            'macro': [],
            'onchain': [],
            'ml_features': [],
            'other': []
        }
        
        for table in all_tables:
            table_lower = table.lower()
            categorized = False
            
            for category in table_categories.keys():
                if category in table_lower:
                    table_categories[category].append(table)
                    categorized = True
                    break
            
            if not categorized:
                # Additional pattern matching
                if any(pattern in table_lower for pattern in ['price', 'cost', 'rate']):
                    table_categories['price_data'].append(table)
                elif any(pattern in table_lower for pattern in ['news', 'article', 'headline']):
                    table_categories['news'].append(table)
                elif any(pattern in table_lower for pattern in ['sentiment', 'emotion', 'feeling']):
                    table_categories['sentiment'].append(table)
                elif any(pattern in table_lower for pattern in ['reddit', 'twitter', 'social']):
                    table_categories['social'].append(table)
                elif any(pattern in table_lower for pattern in ['rsi', 'macd', 'sma', 'ema', 'bollinger']):
                    table_categories['technical'].append(table)
                elif any(pattern in table_lower for pattern in ['gdp', 'inflation', 'fed', 'economic']):
                    table_categories['macro'].append(table)
                else:
                    table_categories['other'].append(table)
        
        # Display categorized tables
        for category, tables in table_categories.items():
            if tables:
                print(f"\n📂 {category.upper()} TABLES ({len(tables)}):")
                for table in sorted(tables):
                    print(f"   • {table}")
        
        return all_tables, table_categories, cursor, connection
        
    except Exception as e:
        print(f"❌ Error analyzing database structure: {e}")
        connection.close()
        return None

def analyze_table_usage(cursor, tables):
    """Analyze table usage patterns - size, last update, record counts"""
    print(f"\n🔍 TABLE USAGE ANALYSIS")
    print("=" * 60)
    
    table_info = {}
    
    for table in tables:
        try:
            # Get table size and row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            # Get table size
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'DB Size in MB'
                FROM information_schema.tables 
                WHERE table_schema = 'crypto_prices' AND table_name = '{table}'
            """)
            size_result = cursor.fetchone()
            size_mb = size_result[0] if size_result else 0
            
            # Try to get creation time and last update
            cursor.execute(f"""
                SELECT create_time, update_time 
                FROM information_schema.tables 
                WHERE table_schema = 'crypto_prices' AND table_name = '{table}'
            """)
            time_result = cursor.fetchone()
            created = time_result[0] if time_result and time_result[0] else 'Unknown'
            updated = time_result[1] if time_result and time_result[1] else 'Unknown'
            
            # Try to find timestamp columns and get latest data
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            
            timestamp_columns = []
            for col in columns:
                col_name = col[0].lower()
                if any(ts in col_name for ts in ['timestamp', 'created', 'updated', 'date', 'time']):
                    timestamp_columns.append(col[0])
            
            latest_data = 'Unknown'
            if timestamp_columns:
                try:
                    ts_col = timestamp_columns[0]
                    cursor.execute(f"SELECT MAX({ts_col}) FROM {table}")
                    latest_result = cursor.fetchone()
                    if latest_result and latest_result[0]:
                        latest_data = latest_result[0]
                except:
                    pass
            
            table_info[table] = {
                'row_count': row_count,
                'size_mb': float(size_mb) if size_mb else 0,
                'created': created,
                'updated': updated,
                'latest_data': latest_data,
                'timestamp_columns': timestamp_columns
            }
            
        except Exception as e:
            print(f"⚠️  Error analyzing table {table}: {e}")
            table_info[table] = {
                'row_count': 0,
                'size_mb': 0,
                'created': 'Error',
                'updated': 'Error',
                'latest_data': 'Error',
                'timestamp_columns': []
            }
    
    return table_info

def identify_current_collectors():
    """Identify which tables are currently used by active collectors"""
    print(f"\n🔍 ACTIVE COLLECTOR TABLE USAGE")
    print("=" * 60)
    
    # Based on our monitoring, these are the active collectors and their likely table usage
    active_collector_tables = {
        'unified-ohlc-collector': ['ohlc_data', 'crypto_prices', 'price_data'],
        'enhanced-crypto-prices': ['crypto_prices', 'price_data', 'ohlc_data'],
        'crypto-news-collector': ['crypto_news', 'news_data', 'headlines'],
        'onchain-data-collector': ['onchain_data', 'blockchain_metrics', 'transaction_data'],
        'enhanced-sentiment': ['sentiment_analysis', 'sentiment_scores', 'crypto_sentiment'],
        'reddit-sentiment-collector': ['reddit_sentiment', 'social_sentiment', 'reddit_data'],
        'narrative-analyzer': ['news_narrative', 'narrative_analysis', 'market_themes'],
        'macro-economic': ['macro_data', 'economic_indicators', 'fred_data'],
        'technical-indicators': ['technical_indicators', 'ta_data', 'chart_analysis'],
        'materialized-updater': ['materialized_data', 'ml_features', 'processed_data'],
        'stock-news-collector': ['stock_news', 'financial_news'],
        'stock-sentiment-collector': ['stock_sentiment', 'equity_sentiment']
    }
    
    # Flatten the list of likely active tables
    likely_active_tables = set()
    for collector, tables in active_collector_tables.items():
        likely_active_tables.update(tables)
    
    print("📊 Tables likely used by active collectors:")
    for table in sorted(likely_active_tables):
        print(f"   ✅ {table}")
    
    return likely_active_tables, active_collector_tables

def find_unused_tables(all_tables, table_info, likely_active_tables):
    """Identify potentially unused tables for cleanup"""
    print(f"\n🔍 UNUSED TABLE IDENTIFICATION")
    print("=" * 60)
    
    # Criteria for potentially unused tables:
    # 1. Not in likely active tables list
    # 2. Empty or very small (< 1000 rows)
    # 3. No recent data (older than 30 days)
    # 4. Small size (< 10 MB)
    
    potentially_unused = []
    definitely_unused = []
    needs_investigation = []
    
    cutoff_date = datetime.now() - timedelta(days=30)
    
    for table in all_tables:
        info = table_info.get(table, {})
        row_count = info.get('row_count', 0)
        size_mb = info.get('size_mb', 0)
        latest_data = info.get('latest_data', 'Unknown')
        
        # Check if table is in likely active list
        is_likely_active = any(table.lower() in active.lower() or active.lower() in table.lower() 
                             for active in likely_active_tables)
        
        # Check if data is recent
        has_recent_data = False
        if isinstance(latest_data, datetime):
            has_recent_data = latest_data > cutoff_date
        elif latest_data != 'Unknown' and latest_data != 'Error':
            try:
                # Try to parse the date string
                if isinstance(latest_data, str):
                    parsed_date = datetime.strptime(latest_data.split()[0], '%Y-%m-%d')
                    has_recent_data = parsed_date > cutoff_date
            except:
                pass
        
        # Categorize tables
        if not is_likely_active:
            if row_count == 0:
                definitely_unused.append({
                    'table': table,
                    'reason': 'Empty table (0 rows)',
                    'info': info
                })
            elif row_count < 100 and size_mb < 1:
                definitely_unused.append({
                    'table': table,
                    'reason': f'Very small table ({row_count} rows, {size_mb} MB)',
                    'info': info
                })
            elif not has_recent_data and size_mb < 10:
                potentially_unused.append({
                    'table': table,
                    'reason': f'No recent data and small size ({row_count} rows, {size_mb} MB)',
                    'info': info
                })
            else:
                needs_investigation.append({
                    'table': table,
                    'reason': f'Not in active list but has data ({row_count} rows, {size_mb} MB)',
                    'info': info
                })
    
    # Display results
    print(f"🗑️  DEFINITELY UNUSED TABLES ({len(definitely_unused)}):")
    total_size_to_free = 0
    for item in definitely_unused:
        size = item['info'].get('size_mb', 0)
        total_size_to_free += size
        print(f"   🔴 {item['table']}: {item['reason']}")
    
    print(f"\n⚠️  POTENTIALLY UNUSED TABLES ({len(potentially_unused)}):")
    potential_size_to_free = 0
    for item in potentially_unused:
        size = item['info'].get('size_mb', 0)
        potential_size_to_free += size
        print(f"   🟡 {item['table']}: {item['reason']}")
    
    print(f"\n🔍 NEEDS INVESTIGATION ({len(needs_investigation)}):")
    for item in needs_investigation:
        print(f"   🟠 {item['table']}: {item['reason']}")
    
    print(f"\n💾 SPACE SAVINGS:")
    print(f"   Definitely unused: {total_size_to_free:.2f} MB")
    print(f"   Potentially unused: {potential_size_to_free:.2f} MB")
    print(f"   Total potential savings: {total_size_to_free + potential_size_to_free:.2f} MB")
    
    return definitely_unused, potentially_unused, needs_investigation

def generate_cleanup_script(definitely_unused, potentially_unused):
    """Generate SQL cleanup scripts"""
    print(f"\n📝 GENERATING CLEANUP SCRIPTS")
    print("=" * 60)
    
    # Backup script
    backup_script = "#!/bin/bash\n"
    backup_script += "# Database backup script before cleanup\n"
    backup_script += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    backup_script += "echo 'Creating database backup before cleanup...'\n"
    backup_script += "mysqldump -h 192.168.230.162 -u news_collector -p99Rules! crypto_prices > crypto_prices_backup_$(date +%Y%m%d_%H%M%S).sql\n"
    backup_script += "echo 'Backup completed!'\n"
    
    # Cleanup script for definitely unused tables
    cleanup_script = "-- Database cleanup script\n"
    cleanup_script += f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    cleanup_script += "-- CAUTION: Review carefully before executing!\n\n"
    cleanup_script += "USE crypto_prices;\n\n"
    
    if definitely_unused:
        cleanup_script += "-- DEFINITELY UNUSED TABLES (Safe to drop)\n"
        for item in definitely_unused:
            table = item['table']
            reason = item['reason']
            cleanup_script += f"-- {table}: {reason}\n"
            cleanup_script += f"DROP TABLE IF EXISTS `{table}`;\n\n"
    
    if potentially_unused:
        cleanup_script += "-- POTENTIALLY UNUSED TABLES (Review before uncommenting)\n"
        for item in potentially_unused:
            table = item['table']
            reason = item['reason']
            cleanup_script += f"-- {table}: {reason}\n"
            cleanup_script += f"-- DROP TABLE IF EXISTS `{table}`;\n\n"
    
    # Write scripts to files
    with open('database_backup.sh', 'w') as f:
        f.write(backup_script)
    
    with open('database_cleanup.sql', 'w') as f:
        f.write(cleanup_script)
    
    print("✅ Generated cleanup scripts:")
    print("   📁 database_backup.sh - Run this first to backup database")
    print("   📁 database_cleanup.sql - Review and execute to clean up tables")
    
    return backup_script, cleanup_script

def main():
    """Main analysis function"""
    print("🗄️  DATABASE TABLE CLEANUP ANALYSIS")
    print("=" * 70)
    
    # Analyze database structure
    analysis_result = analyze_database_structure()
    if not analysis_result:
        return
    
    all_tables, table_categories, cursor, connection = analysis_result
    
    try:
        # Analyze table usage
        table_info = analyze_table_usage(cursor, all_tables)
        
        # Identify current collectors
        likely_active_tables, active_collector_tables = identify_current_collectors()
        
        # Find unused tables
        definitely_unused, potentially_unused, needs_investigation = find_unused_tables(
            all_tables, table_info, likely_active_tables
        )
        
        # Generate cleanup scripts
        generate_cleanup_script(definitely_unused, potentially_unused)
        
        # Summary
        print(f"\n" + "=" * 70)
        print("📊 CLEANUP ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"Total tables analyzed: {len(all_tables)}")
        print(f"Definitely unused: {len(definitely_unused)}")
        print(f"Potentially unused: {len(potentially_unused)}")
        print(f"Need investigation: {len(needs_investigation)}")
        print(f"Likely active: {len(likely_active_tables)}")
        
        total_size = sum(info.get('size_mb', 0) for info in table_info.values())
        unused_size = sum(item['info'].get('size_mb', 0) for item in definitely_unused + potentially_unused)
        
        print(f"\nDatabase size: {total_size:.2f} MB")
        print(f"Potential cleanup: {unused_size:.2f} MB ({unused_size/total_size*100:.1f}%)")
        
        print(f"\n⚠️  NEXT STEPS:")
        print("1. Review the generated database_cleanup.sql file")
        print("2. Run database_backup.sh to create a backup")
        print("3. Execute the cleanup script in stages")
        print("4. Monitor collectors to ensure no issues")
        
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    try:
        main()
        print(f"\n✅ Database analysis completed successfully")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()