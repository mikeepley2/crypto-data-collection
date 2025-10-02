#!/usr/bin/env python3
"""
Check where price data is being stored and why materialized updater isn't processing it
"""
import mysql.connector

print("🔍 PRICE DATA FLOW INVESTIGATION")
print("=" * 60)

try:
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Check all price-related tables for recent data
    tables_to_check = ['price_data', 'price_data_real', 'crypto_assets']
    
    for table in tables_to_check:
        try:
            # Try different timestamp columns
            for time_col in ['created_at', 'timestamp', 'last_updated', 'date_updated']:
                try:
                    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '%{time_col}%'")
                    if cursor.fetchone():
                        cursor.execute(f"""
                            SELECT COUNT(*), MAX({time_col})
                            FROM {table} 
                            WHERE {time_col} >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                        """)
                        count, latest = cursor.fetchone()
                        print(f"📊 {table} ({time_col}): {count} records in last hour, latest: {latest}")
                        
                        if count > 0:
                            # Show sample data
                            cursor.execute(f"""
                                SELECT symbol, {time_col}
                                FROM {table} 
                                WHERE {time_col} >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                                ORDER BY {time_col} DESC
                                LIMIT 5
                            """)
                            samples = cursor.fetchall()
                            print(f"   Recent samples: {samples}")
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Error checking {table}: {e}")
    
    # Check what the materialized updater is looking for
    print(f"\n🔧 MATERIALIZED UPDATER DATA SOURCE:")
    
    # Check if there's a gap between collection and processing
    cursor.execute("""
        SELECT 
            'price_data' as source,
            COUNT(*) as total,
            MAX(created_at) as latest_created
        FROM price_data
        UNION ALL
        SELECT 
            'ml_features_materialized' as source,
            COUNT(*) as total,
            MAX(created_at) as latest_created
        FROM ml_features_materialized
    """)
    
    results = cursor.fetchall()
    print("Data sources comparison:")
    for source, total, latest in results:
        print(f"   {source}: {total:,} records, latest: {latest}")
    
    # Check why materialized updater might not be processing
    print(f"\n🤔 POTENTIAL ISSUES:")
    print(f"1. Materialized updater might be looking at wrong table")
    print(f"2. TNX error might be blocking processing")
    print(f"3. Data might be going to different database")
    print(f"4. Processing might be waiting for trigger")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n💡 NEXT STEPS:")
print(f"1. Check materialized updater logs for data source")
print(f"2. Verify price collection target table")
print(f"3. Check if manual trigger needed")
print(f"4. Fix TNX error that might be blocking")