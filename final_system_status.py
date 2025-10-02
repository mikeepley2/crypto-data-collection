#!/usr/bin/env python3
"""
Final System Status After OHLC Restoration
Complete overview of the corrected data collection system
"""

import mysql.connector
from datetime import datetime

def final_status_check():
    """Complete status check after OHLC restoration"""
    
    print("🎯 FINAL SYSTEM STATUS - POST OHLC RESTORATION")
    print("=" * 55)
    
    db_configs = [
        {'name': 'crypto_prices', 'host': 'localhost', 'user': 'root', 'password': '99Rules!', 'database': 'crypto_prices'},
        {'name': 'crypto_news', 'host': 'localhost', 'user': 'root', 'password': '99Rules!', 'database': 'crypto_news'}
    ]
    
    total_records = 0
    active_tables = []
    
    for db_config in db_configs:
        db_name = db_config['name']
        print(f"\n📊 {db_name.upper()} DATABASE:")
        print("-" * 25)
        
        try:
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                db_total = 0
                db_active = 0
                
                for table in sorted(tables):
                    # Skip views and old tables for main count
                    if '_view' in table or table.endswith('_old'):
                        continue
                        
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                        count = cursor.fetchone()[0]
                        
                        # Check for recent data (24h)
                        cursor.execute(f"DESCRIBE `{table}`")
                        columns = [row[0] for row in cursor.fetchall()]
                        
                        recent_count = 0
                        time_col = None
                        for col in ['timestamp_iso', 'timestamp', 'created_at', 'date_time']:
                            if col in columns:
                                time_col = col
                                break
                        
                        if time_col:
                            cursor.execute(f"""
                                SELECT COUNT(*) FROM `{table}` 
                                WHERE `{time_col}` >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                            """)
                            recent_count = cursor.fetchone()[0]
                        
                        # Display table info
                        status = "🔴 inactive"
                        if recent_count > 0:
                            status = f"✅ {recent_count:,}/24h"
                            db_active += recent_count
                            active_tables.append((f"{db_name}.{table}", count, recent_count))
                        
                        print(f"  {table:<30} | {count:>10,} records | {status}")
                        db_total += count
                        
                    except Exception as e:
                        print(f"  {table:<30} | ERROR: {e}")
                
                print(f"\n  📊 {db_name} TOTAL: {db_total:,} records | {db_active:,} active/24h")
                total_records += db_total
                
        except Exception as e:
            print(f"❌ Error connecting to {db_name}: {e}")
    
    # Summary
    print(f"\n🏆 SYSTEM SUMMARY:")
    print("=" * 30)
    print(f"📊 Total Records: {total_records:,}")
    print(f"🔄 Active Collection Rate: {sum(r[2] for r in active_tables):,} records/24h")
    
    # Highlight OHLC restoration
    print(f"\n🎯 OHLC RESTORATION RESULTS:")
    print("-" * 35)
    ohlc_found = False
    for table_name, count, recent in active_tables:
        if 'ohlc_data' in table_name and not table_name.endswith('_old'):
            print(f"✅ {table_name}: {count:,} records, {recent:,}/24h ACTIVE")
            ohlc_found = True
    
    if ohlc_found:
        print("🎉 OHLC data collection RESTORED and ACTIVE!")
    else:
        print("⚠️  OHLC table not found in active collection")
    
    # Top collectors
    print(f"\n🔄 TOP DATA COLLECTORS:")
    print("-" * 30)
    sorted_active = sorted(active_tables, key=lambda x: x[2], reverse=True)
    for i, (table, count, recent) in enumerate(sorted_active[:5], 1):
        print(f"{i}. {table:<35} | {recent:>6,}/24h")
    
    print(f"\n✨ System Status Check Complete!")
    print(f"🎯 {len(active_tables)} tables actively collecting data")

if __name__ == "__main__":
    final_status_check()