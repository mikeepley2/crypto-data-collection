#!/usr/bin/env python3
"""
Check onchain data collection status and validate schema/data
"""

import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import os
import json

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "172.22.32.1"),
        user=os.getenv("MYSQL_USER", "news_collector"),
        password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
        database=os.getenv("MYSQL_DATABASE", "crypto_prices")
    )

def check_onchain_table_exists():
    """Check if onchain_data table exists and get schema"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'onchain_data'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("❌ onchain_data table does not exist")
            return False, None
            
        # Get table schema
        cursor.execute("DESCRIBE onchain_data")
        columns = cursor.fetchall()
        
        print("✅ onchain_data table exists")
        print(f"📊 Table has {len(columns)} columns:")
        
        column_info = []
        for col in columns:
            field, data_type, null, key, default, extra = col
            column_info.append({
                'field': field,
                'type': data_type,
                'null': null,
                'key': key,
                'default': default,
                'extra': extra
            })
            print(f"   {field}: {data_type} {'(PK)' if key == 'PRI' else ''}")
            
        db.close()
        return True, column_info
        
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        return False, None

def check_recent_data():
    """Check for recent onchain data collection"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check total records
        cursor.execute("SELECT COUNT(*) as total_records FROM onchain_data")
        total_records = cursor.fetchone()['total_records']
        print(f"\n📈 Total onchain records: {total_records:,}")
        
        if total_records == 0:
            print("⚠️  No data found in onchain_data table")
            db.close()
            return
            
        # Check date range
        cursor.execute("""
            SELECT 
                MIN(timestamp_iso) as earliest_date,
                MAX(timestamp_iso) as latest_date,
                MIN(collected_at) as first_collection,
                MAX(collected_at) as last_collection
            FROM onchain_data
        """)
        date_range = cursor.fetchone()
        
        print(f"📅 Data range: {date_range['earliest_date']} to {date_range['latest_date']}")
        print(f"🕒 Collection range: {date_range['first_collection']} to {date_range['last_collection']}")
        
        # Check recent activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) as recent_records 
            FROM onchain_data 
            WHERE collected_at >= NOW() - INTERVAL 24 HOUR
        """)
        recent_records = cursor.fetchone()['recent_records']
        
        if recent_records > 0:
            print(f"✅ Recent collection active: {recent_records} records in last 24h")
        else:
            print(f"⚠️  No recent collection: 0 records in last 24h")
            
        # Check symbols being collected
        cursor.execute("""
            SELECT symbol, COUNT(*) as record_count, MAX(collected_at) as last_collection
            FROM onchain_data 
            GROUP BY symbol 
            ORDER BY record_count DESC 
            LIMIT 10
        """)
        symbols = cursor.fetchall()
        
        print(f"\n🪙 Top symbols being collected:")
        for symbol in symbols:
            print(f"   {symbol['symbol']}: {symbol['record_count']:,} records (last: {symbol['last_collection']})")
            
        # Check data completeness for recent records
        cursor.execute("""
            SELECT 
                COUNT(*) as total_recent,
                COUNT(circulating_supply) as has_supply,
                COUNT(market_cap) as has_mcap,
                COUNT(transaction_count) as has_tx_count,
                COUNT(active_addresses) as has_addresses
            FROM onchain_data 
            WHERE collected_at >= NOW() - INTERVAL 7 DAY
        """)
        completeness = cursor.fetchone()
        
        if completeness['total_recent'] > 0:
            print(f"\n📊 Data completeness (last 7 days):")
            print(f"   Total records: {completeness['total_recent']}")
            print(f"   Supply data: {completeness['has_supply']}/{completeness['total_recent']} ({completeness['has_supply']/completeness['total_recent']*100:.1f}%)")
            print(f"   Market cap: {completeness['has_mcap']}/{completeness['total_recent']} ({completeness['has_mcap']/completeness['total_recent']*100:.1f}%)")
            print(f"   Transaction count: {completeness['has_tx_count']}/{completeness['total_recent']} ({completeness['has_tx_count']/completeness['total_recent']*100:.1f}%)")
            print(f"   Active addresses: {completeness['has_addresses']}/{completeness['total_recent']} ({completeness['has_addresses']/completeness['total_recent']*100:.1f}%)")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error checking recent data: {e}")

def check_column_usage():
    """Check which columns are being populated"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get all columns
        cursor.execute("DESCRIBE onchain_data")
        all_columns = [row['Field'] for row in cursor.fetchall()]
        
        # Check column usage
        column_stats = {}
        for col in all_columns:
            if col in ['id', 'timestamp_iso', 'collected_at', 'symbol']:
                continue  # Skip always-present columns
                
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT({col}) as non_null_records,
                    COUNT(DISTINCT {col}) as unique_values
                FROM onchain_data 
                WHERE collected_at >= NOW() - INTERVAL 7 DAY
            """)
            stats = cursor.fetchone()
            
            if stats['total_records'] > 0:
                fill_rate = stats['non_null_records'] / stats['total_records'] * 100
                column_stats[col] = {
                    'fill_rate': fill_rate,
                    'unique_values': stats['unique_values'],
                    'non_null': stats['non_null_records']
                }
        
        print(f"\n🔍 Column usage analysis (last 7 days):")
        sorted_columns = sorted(column_stats.items(), key=lambda x: x[1]['fill_rate'], reverse=True)
        
        for col, stats in sorted_columns:
            if stats['fill_rate'] > 0:
                print(f"   {col}: {stats['fill_rate']:.1f}% filled ({stats['non_null']:,} records, {stats['unique_values']:,} unique)")
            
        # Identify completely empty columns
        empty_columns = [col for col, stats in column_stats.items() if stats['fill_rate'] == 0]
        if empty_columns:
            print(f"\n⚠️  Empty columns (not being populated):")
            for col in empty_columns:
                print(f"   {col}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error checking column usage: {e}")

def check_backfill_status():
    """Check if automated backfilling has occurred"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check for data patterns that indicate backfilling
        cursor.execute("""
            SELECT 
                DATE(timestamp_iso) as data_date,
                COUNT(*) as record_count,
                COUNT(DISTINCT symbol) as symbol_count,
                MIN(collected_at) as first_collection,
                MAX(collected_at) as last_collection
            FROM onchain_data 
            GROUP BY DATE(timestamp_iso)
            ORDER BY data_date DESC
            LIMIT 30
        """)
        daily_data = cursor.fetchall()
        
        print(f"\n📅 Daily collection pattern (last 30 days):")
        
        recent_days = 0
        backfill_detected = False
        
        for day in daily_data:
            data_date = day['data_date']
            record_count = day['record_count']
            symbol_count = day['symbol_count']
            collection_span = (day['last_collection'] - day['first_collection']).total_seconds() / 3600 if day['last_collection'] != day['first_collection'] else 0
            
            print(f"   {data_date}: {record_count:,} records, {symbol_count} symbols (collected over {collection_span:.1f}h)")
            
            # Check if this looks like backfill (many records collected in short time)
            if record_count > 50 and collection_span < 1:
                backfill_detected = True
                
            recent_days += 1
            
        if backfill_detected:
            print(f"✅ Backfilling activity detected (high volume collections)")
        else:
            print(f"⚠️  No obvious backfilling pattern detected")
            
        # Check for gaps in data
        cursor.execute("""
            SELECT COUNT(DISTINCT DATE(timestamp_iso)) as days_with_data
            FROM onchain_data 
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        days_with_data = cursor.fetchone()['days_with_data']
        
        print(f"\n📈 Data coverage: {days_with_data}/30 days have data in last month")
        
        if days_with_data < 25:
            print(f"⚠️  Potential data gaps detected")
        else:
            print(f"✅ Good data coverage")
            
        db.close()
        
    except Exception as e:
        print(f"❌ Error checking backfill status: {e}")

def main():
    """Main validation function"""
    print("=" * 80)
    print("ONCHAIN DATA COLLECTION VALIDATION")
    print("=" * 80)
    print(f"Validation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check table existence and schema
    table_exists, columns = check_onchain_table_exists()
    
    if not table_exists:
        print("\n❌ Cannot validate data - table does not exist")
        return
        
    # Check recent data collection
    check_recent_data()
    
    # Check column usage
    check_column_usage()
    
    # Check backfill status
    check_backfill_status()
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()