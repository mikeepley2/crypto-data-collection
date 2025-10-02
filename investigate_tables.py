#!/usr/bin/env python3
"""
Database Investigation Script
Investigates specific tables to determine if they contain valuable data
"""

import mysql.connector
from datetime import datetime, timedelta

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

def investigate_table(cursor, table_name):
    """Investigate a specific table for data value and usage"""
    print(f"\n🔍 INVESTIGATING TABLE: {table_name}")
    print("-" * 50)
    
    try:
        # Get table structure
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        print(f"📊 Table Structure ({len(columns)} columns):")
        for col in columns:
            print(f"   • {col[0]} ({col[1]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get date range if possible
        date_columns = []
        for col in columns:
            col_name = col[0].lower()
            if any(date_term in col_name for date_term in ['date', 'time', 'created', 'updated']):
                date_columns.append(col[0])
        
        print(f"📈 Data Summary:")
        print(f"   • Total rows: {row_count:,}")
        
        if date_columns and row_count > 0:
            date_col = date_columns[0]
            cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table_name}")
            date_range = cursor.fetchone()
            if date_range[0] and date_range[1]:
                print(f"   • Date range: {date_range[0]} to {date_range[1]}")
                
                # Check recent data (last 30 days)
                cutoff = datetime.now() - timedelta(days=30)
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {date_col} > %s", (cutoff,))
                recent_count = cursor.fetchone()[0]
                print(f"   • Recent data (30 days): {recent_count:,} rows")
        
        # Sample some data
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_data = cursor.fetchall()
            
            print(f"📋 Sample Data (first 3 rows):")
            for i, row in enumerate(sample_data, 1):
                print(f"   Row {i}: {str(row)[:100]}{'...' if len(str(row)) > 100 else ''}")
        
        return {
            'columns': len(columns),
            'row_count': row_count,
            'has_recent_data': row_count > 0 and date_columns,
            'structure': columns
        }
        
    except Exception as e:
        print(f"❌ Error investigating {table_name}: {e}")
        return None

def main():
    """Main investigation function"""
    print("🔍 DATABASE TABLE INVESTIGATION")
    print("=" * 60)
    
    connection = get_database_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    # Tables that need investigation (large ones)
    tables_to_investigate = [
        'service_monitoring',        # 63.16 MB
        'real_time_sentiment_signals', # 26.09 MB  
        'trading_signals',          # 16.81 MB
        'sentiment_aggregation',    # 16.09 MB
        'hourly_data',             # Large row count
        'onchain_metrics',         # 111k rows
        'macro_indicators'         # 48k rows, 8MB
    ]
    
    investigation_results = {}
    
    for table in tables_to_investigate:
        result = investigate_table(cursor, table)
        investigation_results[table] = result
    
    # Generate recommendations
    print(f"\n" + "=" * 60)
    print("📊 INVESTIGATION SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = {
        'keep': [],
        'archive': [],
        'safe_to_delete': [],
        'needs_migration': []
    }
    
    for table, result in investigation_results.items():
        if result:
            row_count = result['row_count']
            
            if table == 'service_monitoring':
                recommendations['archive'].append((table, "Service monitoring data - can be archived if older than 90 days"))
            elif table == 'real_time_sentiment_signals':
                recommendations['keep'].append((table, "Real-time sentiment data - potentially valuable for ML"))
            elif table == 'trading_signals':
                recommendations['archive'].append((table, "Historical trading signals - archive old data"))
            elif table == 'sentiment_aggregation':
                recommendations['keep'].append((table, "Sentiment aggregation data - may be used by current services"))
            elif table == 'hourly_data':
                recommendations['needs_migration'].append((table, "Hourly data - check if this should be in OHLC format"))
            elif table == 'onchain_metrics':
                recommendations['keep'].append((table, "Onchain metrics - likely used by onchain-data-collector"))
            elif table == 'macro_indicators':
                recommendations['keep'].append((table, "Macro economic data - used by macro-economic collector"))
    
    # Display recommendations
    for category, items in recommendations.items():
        if items:
            print(f"\n{category.upper().replace('_', ' ')}:")
            for table, reason in items:
                icon = "✅" if category == 'keep' else "📦" if category == 'archive' else "🔄" if category == 'needs_migration' else "🗑️"
                print(f"   {icon} {table}: {reason}")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    try:
        main()
        print(f"\n✅ Investigation completed successfully")
    except Exception as e:
        print(f"\n❌ Investigation failed: {e}")
        import traceback
        traceback.print_exc()