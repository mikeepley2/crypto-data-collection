#!/usr/bin/env python3
"""
Quick Collector Status Check
Fast analysis to identify which collectors need attention
"""

import mysql.connector
from datetime import datetime, date, timedelta

def quick_collector_check():
    """Quick check of all collector tables"""
    
    db_config = {
        'host': '172.22.32.1',
        'user': 'news_collector', 
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    print("🚀 QUICK COLLECTOR STATUS CHECK")
    print("=" * 40)
    
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        
        # Check what tables exist
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📊 Found {len(tables)} tables in database")
        
        # Focus on key collector tables
        key_tables = [
            'price_data_real',
            'technical_indicators', 
            'onchain_data',
            'crypto_news',
            'stock_sentiment',
            'macro_indicators'
        ]
        
        print(f"\n🔍 Checking key collector tables...")
        
        results = {}
        
        for table in key_tables:
            if table in tables:
                print(f"\n📋 {table}:")
                
                # Get basic counts
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total_count = cursor.fetchone()[0]
                print(f"   Total records: {total_count:,}")
                
                if total_count > 0:
                    # Check recent data (last 24 hours)
                    try:
                        if table == 'macro_indicators':
                            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE date >= CURDATE() - INTERVAL 1 DAY")
                        elif table == 'crypto_news':
                            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE published_at >= NOW() - INTERVAL 1 DAY")
                        else:
                            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE timestamp_iso >= NOW() - INTERVAL 1 DAY")
                        
                        recent_count = cursor.fetchone()[0]
                        print(f"   Recent (24h): {recent_count:,}")
                        
                        if recent_count == 0:
                            print(f"   ❌ NO RECENT DATA - Collector may be down")
                        else:
                            print(f"   ✅ Active - Recent data found")
                            
                    except Exception as e:
                        print(f"   ⚠️  Cannot check recent data: {e}")
                
                    # Check unique symbols if applicable
                    try:
                        if table in ['price_data_real', 'technical_indicators', 'onchain_data', 'stock_sentiment']:
                            cursor.execute(f"SELECT COUNT(DISTINCT symbol) FROM {table}")
                            symbol_count = cursor.fetchone()[0]
                            print(f"   Symbols: {symbol_count}")
                        elif table == 'crypto_news':
                            cursor.execute(f"SELECT COUNT(DISTINCT symbols) FROM {table} WHERE symbols IS NOT NULL")
                            symbol_count = cursor.fetchone()[0]
                            print(f"   Symbol mentions: {symbol_count}")
                    except:
                        pass
                
                results[table] = {
                    'total_records': total_count,
                    'recent_records': recent_count if 'recent_count' in locals() else 0,
                    'status': 'active' if recent_count > 0 else 'inactive'
                }
                
            else:
                print(f"\n📋 {table}: ❌ TABLE NOT FOUND")
                results[table] = {'status': 'missing'}
        
        # Summary
        print(f"\n📊 SUMMARY")
        print("=" * 20)
        
        active_collectors = sum(1 for r in results.values() if r.get('status') == 'active')
        inactive_collectors = sum(1 for r in results.values() if r.get('status') == 'inactive')
        missing_collectors = sum(1 for r in results.values() if r.get('status') == 'missing')
        
        print(f"✅ Active collectors: {active_collectors}")
        print(f"❌ Inactive collectors: {inactive_collectors}")
        print(f"🚫 Missing collectors: {missing_collectors}")
        
        print(f"\n🎯 PRIORITY ACTIONS:")
        
        # Prioritize actions
        for table, result in results.items():
            if result.get('status') == 'missing':
                print(f"🚨 HIGH: Create {table} table and collector")
            elif result.get('status') == 'inactive':
                print(f"⚠️  MEDIUM: Restart {table} collector - no recent data")
            elif result.get('total_records', 0) < 1000:
                print(f"📈 LOW: Enhance {table} - low data volume")
        
        db.close()
        return results
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

if __name__ == "__main__":
    quick_collector_check()