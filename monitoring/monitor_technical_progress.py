#!/usr/bin/env python3
"""
Monitor Technical Calculator Progress
Real-time monitoring of technical indicator calculation
"""

import time
import sys
import os
sys.path.append('.')

from shared.database_config import get_db_connection

def monitor_technical_progress():
    """Monitor technical calculator progress"""
    print("🔍 Technical Calculator Progress Monitor")
    print("📍 Checking progress every 30 seconds...")
    print("📢 Press Ctrl+C to stop monitoring\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get current stats
            cursor.execute("SELECT COUNT(*) FROM technical_indicators")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM technical_indicators WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
            recent_updates = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(updated_at) FROM technical_indicators")
            latest_update = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM technical_indicators WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
            recent_symbols = cursor.fetchone()[0]
            
            # Display report
            print(f"📊 Technical Calculator Status (Check #{iteration})")
            print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📈 Total records: {total_records:,}")
            print(f"🔄 Updates (1h): {recent_updates:,}")
            print(f"🎯 Symbols updated (1h): {recent_symbols}")
            print(f"⌚ Latest update: {latest_update}")
            
            if recent_updates > 0:
                print("✅ Technical calculator is ACTIVE")
            else:
                print("⚠️  No recent updates detected")
            
            print("-" * 50)
            
            conn.close()
            
            # Wait 30 seconds
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitoring stopped by user")
        print(f"📊 Completed {iteration} progress checks")

if __name__ == "__main__":
    monitor_technical_progress()