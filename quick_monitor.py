#!/usr/bin/env python3
"""
Quick OHLC Monitor
Watch for the next scheduled collection
"""

import mysql.connector
import time
from datetime import datetime

def monitor_next_collection():
    """Monitor for the next OHLC collection"""
    
    print("OHLC Collection Monitor - Next collection expected at 12:00!")
    print("=" * 60)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    # Get baseline
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ohlc_data")
            baseline = cursor.fetchone()[0]
        
        print(f"Baseline: {baseline:,} records")
        print("Monitoring for new data...")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                time.sleep(30)  # Check every 30 seconds
                
                with mysql.connector.connect(**db_config) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                    current = cursor.fetchone()[0]
                    
                    now = datetime.now().strftime('%H:%M:%S')
                    
                    if current > baseline:
                        new_records = current - baseline
                        print(f"NEW DATA DETECTED! +{new_records} records at {now}")
                        
                        # Get latest records
                        cursor.execute("""
                            SELECT symbol, timestamp_iso 
                            FROM ohlc_data 
                            ORDER BY id DESC 
                            LIMIT 5
                        """)
                        latest = cursor.fetchall()
                        
                        print("Latest records:")
                        for symbol, timestamp in latest:
                            print(f"  {symbol}: {timestamp}")
                        
                        baseline = current
                        print(f"New baseline: {current:,} records")
                        print()
                    else:
                        print(f"{now} - Waiting... ({current:,} records)")
        
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            
            # Final check
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                final = cursor.fetchone()[0]
                
                if final > baseline:
                    print(f"Final result: +{final - baseline} new records collected!")
                else:
                    print("No new data collected during monitoring")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitor_next_collection()