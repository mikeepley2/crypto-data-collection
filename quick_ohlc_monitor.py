#!/usr/bin/env python3
"""
Quick OHLC Data Checker
Check for immediate database changes while monitoring runs
"""

import mysql.connector
import time
from datetime import datetime

def quick_data_check():
    """Quick check for any new OHLC data"""
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check current total
            cursor.execute("SELECT COUNT(*) FROM ohlc_data")
            total = cursor.fetchone()[0]
            
            # Check very recent data (last 2 minutes)
            cursor.execute("""
                SELECT COUNT(*) FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 2 MINUTE)
            """)
            last_2min = cursor.fetchone()[0]
            
            # Check latest record details
            cursor.execute("""
                SELECT id, symbol, timestamp_iso, open_price, close_price
                FROM ohlc_data 
                ORDER BY id DESC 
                LIMIT 1
            """)
            latest = cursor.fetchone()
            
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | Total: {total:,} | Last 2min: {last_2min}")
            
            if latest:
                record_id, symbol, timestamp, open_price, close_price = latest
                print(f"   Latest: ID={record_id} | {symbol} | {timestamp} | O={open_price}")
            
            return total, last_2min
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0, 0

if __name__ == "__main__":
    print("🔍 QUICK OHLC DATA MONITORING")
    print("=" * 40)
    print("Press Ctrl+C to stop")
    
    baseline = None
    
    try:
        while True:
            total, recent = quick_data_check()
            
            if baseline is None:
                baseline = total
                print(f"📊 Baseline set: {baseline:,} records")
            
            if total > baseline:
                new_records = total - baseline
                print(f"🎉 NEW DATA! +{new_records} records added!")
                
            if recent > 0:
                print(f"🟢 Fresh activity: {recent} records in last 2 minutes")
            
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Quick monitoring stopped")
        if baseline:
            final_total, _ = quick_data_check()
            if final_total > baseline:
                print(f"✨ Total new records added: {final_total - baseline}")
            else:
                print("📊 No new records detected")