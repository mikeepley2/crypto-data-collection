#!/usr/bin/env python3
"""
Quick check for new OHLC data
Check if the collector is now inserting data after configuration update
"""

import mysql.connector
from datetime import datetime

def check_for_new_data():
    """Check if new data has been inserted recently"""
    
    print("🔍 CHECKING FOR NEW OHLC DATA")
    print("=" * 40)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check data from last 5 minutes
            cursor.execute("""
                SELECT COUNT(*) FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
            """)
            last_5min = cursor.fetchone()[0]
            print(f"📊 Last 5 minutes: {last_5min} records")
            
            # Check data from last hour
            cursor.execute("""
                SELECT COUNT(*) FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)
            last_hour = cursor.fetchone()[0]
            print(f"📊 Last hour: {last_hour} records")
            
            # Check most recent record
            cursor.execute("""
                SELECT symbol, timestamp_iso, open_price, close_price
                FROM ohlc_data 
                ORDER BY id DESC 
                LIMIT 1
            """)
            latest = cursor.fetchone()
            
            if latest:
                symbol, timestamp, open_price, close_price = latest
                print(f"🔄 Latest record:")
                print(f"   Symbol: {symbol}")
                print(f"   Time: {timestamp}")
                print(f"   OHLC: O={open_price} C={close_price}")
                
                # Check if this is very recent (last few minutes)
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                
                time_diff = datetime.now() - timestamp.replace(tzinfo=None)
                minutes_ago = time_diff.total_seconds() / 60
                
                if minutes_ago < 5:
                    print(f"   Status: ✅ VERY FRESH ({minutes_ago:.1f} min ago)")
                    return True
                elif minutes_ago < 60:
                    print(f"   Status: ⚠️  Recent ({minutes_ago:.1f} min ago)")
                    return False
                else:
                    print(f"   Status: ❌ Old ({minutes_ago/60:.1f} hours ago)")
                    return False
            else:
                print("❌ No records found")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fresh_data = check_for_new_data()
    
    if fresh_data:
        print("\n🎉 SUCCESS: Fresh data detected!")
        print("🎯 Collector is now working properly")
    else:
        print("\n⚠️  No fresh data yet")
        print("🔄 Collector may need more time or additional fixes")