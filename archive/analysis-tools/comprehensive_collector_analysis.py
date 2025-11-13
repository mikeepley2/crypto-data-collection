#!/usr/bin/env python3
"""
Comprehensive Collector Table Analysis
Verify single-source-of-truth for all collector table types and identify any duplicates
"""
import mysql.connector
import sys
from contextlib import contextmanager
from collections import defaultdict
import pandas as pd

# Database credentials from K8s config
MYSQL_HOST = "172.22.32.1"
MYSQL_PORT = 3306
MYSQL_USER = "news_collector"
MYSQL_PASSWORD = "99Rules!"

@contextmanager
def mysql_connection(database=None):
    """Context manager for MySQL connections"""
    connection = None
    try:
        config = {
            'host': MYSQL_HOST,
            'port': MYSQL_PORT,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'autocommit': True,
            'charset': 'utf8mb4',
            'use_unicode': True
        }
        if database:
            config['database'] = database
            
        connection = mysql.connector.connect(**config)
        yield connection
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()

def analyze_collector_tables():
    """Analyze all collector table types for duplicates and completeness"""
    
    print("🔍 COMPREHENSIVE COLLECTOR TABLE ANALYSIS")
    print("=" * 80)
    
    # Define collector table patterns
    table_patterns = {
        'onchain': ['onchain', 'chain'],
        'ohlc': ['ohlc', 'candlestick', 'candle'],
        'macro': ['macro', 'economic'],
        'technical': ['technical', 'indicator'],
        'sentiment': ['sentiment'],
        'ml_features': ['ml_feature', 'feature'],
        'price': ['price_data'],
        'news': ['news'],
        'social': ['social'],
        'market': ['market']
    }
    
    with mysql_connection() as conn:
        cursor = conn.cursor()
        
        # Get all databases
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall() if row[0] not in 
                    ['information_schema', 'performance_schema', 'mysql', 'sys']]
        
        print(f"📊 Analyzing databases: {', '.join(databases)}")
        
        # Find all tables across all databases
        cursor.execute("""
        SELECT 
            table_schema,
            table_name,
            table_rows,
            ROUND((data_length + index_length) / 1024 / 1024, 2) as size_mb,
            create_time,
            update_time
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
        ORDER BY table_schema, table_name
        """)
        
        all_tables = cursor.fetchall()
        
        # Categorize tables by type
        categorized_tables = defaultdict(list)
        
        for table_info in all_tables:
            db_name, table_name, rows, size_mb, created, updated = table_info
            table_lower = table_name.lower()
            
            # Skip old/backup tables for now
            if any(suffix in table_lower for suffix in ['_old', '_backup', '_archive', '_corrupted']):
                continue
                
            # Categorize table
            categorized = False
            for category, patterns in table_patterns.items():
                for pattern in patterns:
                    if pattern in table_lower:
                        categorized_tables[category].append({
                            'database': db_name,
                            'table': table_name,
                            'full_name': f"{db_name}.{table_name}",
                            'rows': rows or 0,
                            'size_mb': size_mb or 0,
                            'created': created,
                            'updated': updated
                        })
                        categorized = True
                        break
                if categorized:
                    break
        
        # Analyze each category
        duplicates_found = {}
        primary_tables = {}
        
        for category, tables in categorized_tables.items():
            print(f"\n🎯 CATEGORY: {category.upper()}")
            print("-" * 60)
            
            if len(tables) == 0:
                print(f"  ❌ No {category} tables found")
                continue
            elif len(tables) == 1:
                table = tables[0]
                print(f"  ✅ Single table: {table['full_name']}")
                print(f"     📊 Rows: {table['rows']:,} | Size: {table['size_mb']:.1f} MB")
                primary_tables[category] = table
            else:
                print(f"  ⚠️  Multiple {category} tables found:")
                
                # Sort by row count to identify primary
                tables_sorted = sorted(tables, key=lambda x: x['rows'], reverse=True)
                
                for i, table in enumerate(tables_sorted):
                    marker = "🏆 PRIMARY" if i == 0 else "🔄 DUPLICATE"
                    print(f"     {marker}: {table['full_name']}")
                    print(f"        📊 Rows: {table['rows']:,} | Size: {table['size_mb']:.1f} MB")
                    
                    if i == 0:
                        primary_tables[category] = table
                
                duplicates_found[category] = tables_sorted[1:]  # All except primary
        
        cursor.close()
        
        # Summary
        print(f"\n📋 ANALYSIS SUMMARY")
        print("=" * 50)
        
        print(f"\n✅ PRIMARY TABLES IDENTIFIED:")
        for category, table in primary_tables.items():
            print(f"  🎯 {category}: {table['full_name']} ({table['rows']:,} rows)")
        
        if duplicates_found:
            print(f"\n⚠️  DUPLICATE TABLES FOUND:")
            for category, duplicates in duplicates_found.items():
                print(f"  🔄 {category}:")
                for dup in duplicates:
                    print(f"     - {dup['full_name']} ({dup['rows']:,} rows)")
        else:
            print(f"\n🎉 No duplicate tables found - Single source of truth achieved!")
        
        return primary_tables, duplicates_found

def check_data_completeness(primary_tables, duplicates_found):
    """Check for missing data in primary tables that might exist in duplicates"""
    
    print(f"\n🔍 DATA COMPLETENESS ANALYSIS")
    print("=" * 60)
    
    missing_data_found = {}
    
    for category, duplicates in duplicates_found.items():
        if category not in primary_tables:
            continue
            
        primary = primary_tables[category]
        print(f"\n📊 Checking {category} completeness:")
        print(f"  🏆 Primary: {primary['full_name']} ({primary['rows']:,} rows)")
        
        # For each duplicate, check if it has data not in primary
        for duplicate in duplicates:
            print(f"  🔍 Analyzing: {duplicate['full_name']} ({duplicate['rows']:,} rows)")
            
            # We'll need to check schemas and data overlaps - this is table-specific
            # For now, we'll identify potentially missing data based on row counts
            if duplicate['rows'] > 0:
                print(f"     ⚠️  Contains {duplicate['rows']:,} rows - needs migration check")
                if category not in missing_data_found:
                    missing_data_found[category] = []
                missing_data_found[category].append(duplicate)
            else:
                print(f"     ✅ Empty table - safe to remove")
    
    return missing_data_found

if __name__ == "__main__":
    try:
        print("🚀 Starting comprehensive collector table analysis...")
        
        # Analyze table structure
        primary_tables, duplicates_found = analyze_collector_tables()
        
        # Check for missing data
        missing_data = check_data_completeness(primary_tables, duplicates_found)
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print("-" * 30)
        
        if duplicates_found:
            print("📋 Actions needed:")
            for category, duplicates in duplicates_found.items():
                print(f"  🔄 {category}:")
                for dup in duplicates:
                    if dup['rows'] > 0:
                        print(f"     1. Migrate unique data from {dup['full_name']}")
                        print(f"     2. Archive table as {dup['table']}_old")
                    else:
                        print(f"     1. Archive empty table {dup['full_name']} as {dup['table']}_old")
        else:
            print("🎉 System is already optimized with single source of truth!")
        
        print(f"\n✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)