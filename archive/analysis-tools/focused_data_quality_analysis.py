#!/usr/bin/env python3
"""
Focused Data Quality Analysis - Current Database Schema
Analyzes existing data sources and identifies priority areas
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from shared.database_config import get_db_connection

def get_available_tables():
    """Get list of available tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SHOW TABLES')
    tables = [table[0] for table in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return tables

def analyze_table_structure(table_name):
    """Get table structure and sample data"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get table structure
        cursor.execute(f'DESCRIBE {table_name}')
        columns = cursor.fetchall()
        
        # Get record count
        cursor.execute(f'SELECT COUNT(*) as count FROM {table_name}')
        count = cursor.fetchone()['count']
        
        # Get date range if possible
        date_columns = ['date', 'timestamp', 'created_at', 'published_at', 'collection_date']
        date_info = None
        
        for date_col in date_columns:
            if any(col['Field'] == date_col for col in columns):
                try:
                    cursor.execute(f'SELECT MIN({date_col}) as earliest, MAX({date_col}) as latest FROM {table_name}')
                    date_info = cursor.fetchone()
                    date_info['date_column'] = date_col
                    break
                except:
                    continue
        
        return {
            'columns': columns,
            'count': count,
            'date_info': date_info
        }
    
    except Exception as e:
        return {'error': str(e)}
    finally:
        cursor.close()
        conn.close()

def analyze_data_quality():
    """Comprehensive data quality analysis"""
    print("🔍 COMPREHENSIVE DATA QUALITY ANALYSIS")
    print("="*60)
    
    tables = get_available_tables()
    print(f"\n📋 Found {len(tables)} tables in database\n")
    
    priority_issues = []
    data_sources = {}
    
    for table in sorted(tables):
        print(f"📊 Analyzing {table}...")
        analysis = analyze_table_structure(table)
        
        if 'error' in analysis:
            print(f"   ❌ Error: {analysis['error']}")
            priority_issues.append({
                'table': table,
                'severity': 'HIGH',
                'issue': 'Table access error',
                'details': analysis['error']
            })
            continue
        
        count = analysis['count']
        date_info = analysis['date_info']
        
        print(f"   📈 Records: {count:,}")
        
        # Check for empty tables
        if count == 0:
            priority_issues.append({
                'table': table,
                'severity': 'HIGH',
                'issue': 'Empty table',
                'details': 'No data found'
            })
            print("   🔴 EMPTY TABLE - HIGH PRIORITY")
            continue
        
        # Check date range and freshness
        if date_info and date_info['earliest'] and date_info['latest']:
            earliest = date_info['earliest']
            latest = date_info['latest']
            date_col = date_info['date_column']
            
            print(f"   📅 Date range: {earliest} to {latest} ({date_col})")
            
            # Calculate data freshness
            if isinstance(latest, datetime):
                gap_hours = (datetime.now() - latest).total_seconds() / 3600
                print(f"   ⏰ Data freshness: {gap_hours:.1f} hours ago")
                
                # Flag stale data
                if gap_hours > 24:
                    severity = 'HIGH' if gap_hours > 72 else 'MEDIUM'
                    priority_issues.append({
                        'table': table,
                        'severity': severity,
                        'issue': 'Stale data',
                        'details': f'{gap_hours:.1f} hours since last update'
                    })
                    status = "🔴" if severity == 'HIGH' else "🟡"
                    print(f"   {status} STALE DATA - {severity} PRIORITY")
                else:
                    print("   ✅ Data is fresh")
            
        else:
            print("   ⚠️  No date column found")
        
        # Store analysis results
        data_sources[table] = {
            'count': count,
            'date_info': date_info,
            'columns': len(analysis['columns'])
        }
        
        print()
    
    # Summary analysis
    print("\n" + "="*60)
    print("📊 DATA QUALITY SUMMARY")
    print("="*60)
    
    # Total data volume
    total_records = sum(data['count'] for data in data_sources.values())
    print(f"\n📈 Total Records: {total_records:,}")
    
    # Top tables by volume
    print(f"\n🏆 Largest Tables:")
    sorted_tables = sorted(data_sources.items(), key=lambda x: x[1]['count'], reverse=True)
    for table, data in sorted_tables[:5]:
        print(f"   {table}: {data['count']:,} records")
    
    # Priority issues summary
    print(f"\n🚨 PRIORITY ISSUES ({len(priority_issues)} found):")
    
    if not priority_issues:
        print("   ✅ No critical issues found!")
    else:
        high_priority = [i for i in priority_issues if i['severity'] == 'HIGH']
        medium_priority = [i for i in priority_issues if i['severity'] == 'MEDIUM']
        
        if high_priority:
            print(f"\n   🔴 HIGH PRIORITY ({len(high_priority)}):")
            for issue in high_priority:
                print(f"      • {issue['table']}: {issue['issue']}")
                print(f"        {issue['details']}")
        
        if medium_priority:
            print(f"\n   🟡 MEDIUM PRIORITY ({len(medium_priority)}):")
            for issue in medium_priority:
                print(f"      • {issue['table']}: {issue['issue']}")
                print(f"        {issue['details']}")
    
    # Recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    
    if high_priority:
        print("   1. 🔴 Address HIGH priority issues immediately:")
        for issue in high_priority[:3]:  # Top 3 high priority
            print(f"      - Fix {issue['table']}: {issue['issue']}")
    
    if medium_priority:
        print("   2. 🟡 Schedule MEDIUM priority fixes:")
        for issue in medium_priority[:3]:  # Top 3 medium priority
            print(f"      - Update {issue['table']}: {issue['issue']}")
    
    if not priority_issues:
        print("   ✅ All data sources appear healthy!")
        print("   🔄 Focus on: Regular monitoring and maintenance")
    
    # Data collection status
    fresh_tables = []
    stale_tables = []
    
    for table, data in data_sources.items():
        if data['date_info'] and data['date_info']['latest']:
            latest = data['date_info']['latest']
            if isinstance(latest, datetime):
                gap_hours = (datetime.now() - latest).total_seconds() / 3600
                if gap_hours <= 24:
                    fresh_tables.append(table)
                else:
                    stale_tables.append(table)
    
    print(f"\n📊 COLLECTION STATUS:")
    print(f"   ✅ Fresh data: {len(fresh_tables)} tables")
    print(f"   ⚠️  Stale data: {len(stale_tables)} tables")
    
    if fresh_tables:
        print(f"\n   🟢 Active collection: {', '.join(fresh_tables[:5])}")
    
    if stale_tables:
        print(f"\n   🔴 Needs attention: {', '.join(stale_tables[:5])}")
    
    print("\n" + "="*60)
    
    return {
        'tables': data_sources,
        'priority_issues': priority_issues,
        'total_records': total_records,
        'fresh_tables': fresh_tables,
        'stale_tables': stale_tables
    }

def detailed_onchain_analysis():
    """Detailed analysis of onchain data specifically"""
    print("\n🔍 DETAILED ONCHAIN DATA ANALYSIS")
    print("="*40)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check onchain data details
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT coin_symbol) as unique_symbols,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest,
                COUNT(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 END) as has_addresses,
                COUNT(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 END) as has_transactions
            FROM crypto_onchain_data
        """)
        
        stats = cursor.fetchone()
        print(f"📊 Onchain Data Statistics:")
        print(f"   Total records: {stats['total_records']:,}")
        print(f"   Unique symbols: {stats['unique_symbols']}")
        print(f"   Date range: {stats['earliest']} to {stats['latest']}")
        print(f"   Has addresses: {stats['has_addresses']:,} records")
        print(f"   Has transactions: {stats['has_transactions']:,} records")
        
        # Check recent coverage
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as records,
                COUNT(DISTINCT coin_symbol) as symbols
            FROM crypto_onchain_data
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)
        
        recent = cursor.fetchall()
        print(f"\n📅 Recent Coverage (Last 7 days):")
        for day in recent:
            print(f"   {day['date']}: {day['records']} records, {day['symbols']} symbols")
        
        if stats['latest']:
            gap_hours = (datetime.now() - stats['latest']).total_seconds() / 3600
            status = "✅" if gap_hours < 12 else "⚠️" if gap_hours < 24 else "🔴"
            print(f"\n{status} Data freshness: {gap_hours:.1f} hours ago")
        
    except Exception as e:
        print(f"❌ Error analyzing onchain data: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    results = analyze_data_quality()
    detailed_onchain_analysis()