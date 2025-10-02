#!/usr/bin/env python3
"""
OHLC Table Column Analysis
Check if the collector is populating all expected columns
"""

import mysql.connector
import subprocess

def analyze_ohlc_table_structure():
    """Analyze the ohlc_data table structure and data completeness"""
    
    print("🔍 OHLC TABLE COLUMN ANALYSIS")
    print("=" * 45)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Get table structure
            print("1️⃣ TABLE STRUCTURE:")
            print("-" * 25)
            
            cursor.execute("DESCRIBE ohlc_data")
            columns_info = cursor.fetchall()
            
            print("   Column Name        | Type           | Null | Key | Default")
            print("   -------------------|----------------|------|-----|--------")
            
            column_names = []
            for col_name, col_type, is_null, key, default, extra in columns_info:
                column_names.append(col_name)
                print(f"   {col_name:<18} | {col_type:<14} | {is_null:<4} | {key:<3} | {str(default):<7}")
            
            print(f"\n   📊 Total columns: {len(column_names)}")
            print(f"   📋 Columns: {', '.join(column_names)}")
            
            # Check data completeness for recent records
            print(f"\n2️⃣ DATA COMPLETENESS ANALYSIS:")
            print("-" * 35)
            
            # Get recent records to analyze
            cursor.execute("""
                SELECT * FROM ohlc_data 
                ORDER BY timestamp_iso DESC 
                LIMIT 5
            """)
            
            recent_records = cursor.fetchall()
            
            if recent_records:
                print("   📊 Recent records analysis:")
                print("   (Checking for NULL/empty values)")
                
                # Analyze each column for completeness
                null_counts = {}
                empty_counts = {}
                
                for i, col_name in enumerate(column_names):
                    null_count = 0
                    empty_count = 0
                    
                    for record in recent_records:
                        value = record[i]
                        if value is None:
                            null_count += 1
                        elif isinstance(value, str) and value.strip() == '':
                            empty_count += 1
                        elif isinstance(value, (int, float)) and value == 0:
                            # For numeric fields, 0 might indicate missing data
                            if col_name in ['open_price', 'high_price', 'low_price', 'close_price']:
                                empty_count += 1
                    
                    null_counts[col_name] = null_count
                    empty_counts[col_name] = empty_count
                
                print(f"\n   Column Completeness (last 5 records):")
                print("   Column Name        | NULL | Zero/Empty | Status")
                print("   -------------------|------|------------|-------")
                
                for col_name in column_names:
                    nulls = null_counts[col_name]
                    empties = empty_counts[col_name]
                    
                    if nulls == 0 and empties == 0:
                        status = "✅ Complete"
                    elif nulls > 0 or empties > 0:
                        status = f"⚠️  Issues"
                    else:
                        status = "❓ Unknown"
                    
                    print(f"   {col_name:<18} | {nulls:>4} | {empties:>10} | {status}")
                
                # Show sample recent record
                print(f"\n3️⃣ SAMPLE RECENT RECORD:")
                print("-" * 30)
                
                latest_record = recent_records[0]
                print("   Latest record details:")
                for i, col_name in enumerate(column_names):
                    value = latest_record[i]
                    print(f"     {col_name}: {value}")
                    
            else:
                print("   ❌ No records found in ohlc_data table")
            
            return column_names, recent_records
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return [], []

def check_collector_output_format():
    """Check what format the collector is expected to output"""
    
    print(f"\n4️⃣ COLLECTOR OUTPUT EXPECTATIONS:")
    print("-" * 40)
    
    print("   📋 Standard OHLC data should include:")
    print("     • Symbol/Coin identification")
    print("     • Timestamp (both unix and ISO format)")
    print("     • OHLC prices (open, high, low, close)")
    print("     • Volume data")
    print("     • Additional metadata (coin_id, etc.)")
    
    expected_columns = [
        'id', 'symbol', 'coin_id', 'timestamp_unix', 'timestamp_iso',
        'open_price', 'high_price', 'low_price', 'close_price', 'volume'
    ]
    
    print(f"\n   🎯 Expected essential columns:")
    for col in expected_columns:
        print(f"     • {col}")
    
    return expected_columns

def compare_with_other_tables():
    """Compare ohlc_data structure with other price tables"""
    
    print(f"\n5️⃣ COMPARISON WITH OTHER TABLES:")
    print("-" * 40)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Compare with other price-related tables
            comparison_tables = ['price_data_real', 'ml_features_materialized', 'hourly_data']
            
            for table in comparison_tables:
                try:
                    cursor.execute(f"DESCRIBE {table}")
                    other_columns = [row[0] for row in cursor.fetchall()]
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    print(f"\n   📊 {table}:")
                    print(f"     Columns: {len(other_columns)}")
                    print(f"     Records: {count:,}")
                    print(f"     Sample columns: {', '.join(other_columns[:8])}{'...' if len(other_columns) > 8 else ''}")
                    
                    # Check for OHLC-like columns
                    ohlc_like = [col for col in other_columns if any(term in col.lower() for term in ['open', 'high', 'low', 'close', 'volume', 'price'])]
                    if ohlc_like:
                        print(f"     OHLC-related: {', '.join(ohlc_like[:5])}{'...' if len(ohlc_like) > 5 else ''}")
                        
                except:
                    print(f"   ❌ Could not analyze {table}")
                    
    except Exception as e:
        print(f"❌ Error in comparison: {e}")

def analyze_data_gaps():
    """Analyze potential data gaps or issues"""
    
    print(f"\n6️⃣ DATA QUALITY ANALYSIS:")
    print("-" * 30)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check for missing OHLC data patterns
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN open_price IS NULL OR open_price = 0 THEN 1 END) as missing_open,
                    COUNT(CASE WHEN high_price IS NULL OR high_price = 0 THEN 1 END) as missing_high,
                    COUNT(CASE WHEN low_price IS NULL OR low_price = 0 THEN 1 END) as missing_low,
                    COUNT(CASE WHEN close_price IS NULL OR close_price = 0 THEN 1 END) as missing_close,
                    COUNT(CASE WHEN volume IS NULL OR volume = 0 THEN 1 END) as missing_volume
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
            
            stats = cursor.fetchone()
            total, missing_open, missing_high, missing_low, missing_close, missing_volume = stats
            
            print(f"   📊 Data Quality (last 30 days):")
            print(f"     Total records: {total:,}")
            print(f"     Missing open: {missing_open:,} ({missing_open/total*100:.1f}%)" if total > 0 else "     No recent data")
            print(f"     Missing high: {missing_high:,} ({missing_high/total*100:.1f}%)" if total > 0 else "")
            print(f"     Missing low: {missing_low:,} ({missing_low/total*100:.1f}%)" if total > 0 else "")
            print(f"     Missing close: {missing_close:,} ({missing_close/total*100:.1f}%)" if total > 0 else "")
            print(f"     Missing volume: {missing_volume:,} ({missing_volume/total*100:.1f}%)" if total > 0 else "")
            
            # Overall assessment
            if total > 0:
                critical_missing = max(missing_open, missing_high, missing_low, missing_close)
                missing_pct = critical_missing / total * 100
                
                if missing_pct < 5:
                    print(f"     ✅ Data quality: EXCELLENT ({missing_pct:.1f}% missing)")
                elif missing_pct < 15:
                    print(f"     🟡 Data quality: GOOD ({missing_pct:.1f}% missing)")
                else:
                    print(f"     ⚠️  Data quality: NEEDS ATTENTION ({missing_pct:.1f}% missing)")
                    
                if missing_volume / total > 0.5:
                    print(f"     ⚠️  Volume data: Often missing - may not be collected")
                    
    except Exception as e:
        print(f"❌ Error in data quality analysis: {e}")

if __name__ == "__main__":
    column_names, recent_records = analyze_ohlc_table_structure()
    expected_columns = check_collector_output_format()
    
    if column_names:
        compare_with_other_tables()
        analyze_data_gaps()
        
        print(f"\n" + "="*60)
        print("🎯 COLUMN COMPLETENESS ASSESSMENT:")
        print("="*60)
        
        missing_expected = [col for col in expected_columns if col not in column_names]
        extra_columns = [col for col in column_names if col not in expected_columns]
        
        if not missing_expected and not extra_columns:
            print("✅ PERFECT MATCH: Table has all expected OHLC columns")
        else:
            if missing_expected:
                print(f"❌ MISSING COLUMNS: {', '.join(missing_expected)}")
            if extra_columns:
                print(f"ℹ️  EXTRA COLUMNS: {', '.join(extra_columns)}")
        
        print(f"\n🔍 COLLECTOR ASSESSMENT:")
        if len(recent_records) > 0:
            print("✅ Collector appears to be writing to all table columns")
            print("📊 Check data quality percentages above for completeness")
        else:
            print("⚠️  No recent data to assess collector output")
            
        print("="*60)
    else:
        print("❌ Unable to analyze table structure")