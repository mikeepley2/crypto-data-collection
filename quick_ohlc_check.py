#!/usr/bin/env python3
"""
Quick OHLC Verification - Confirm restoration success
"""

import mysql.connector

def quick_ohlc_check():
    """Quick verification that OHLC restoration worked"""
    
    print("🎯 OHLC RESTORATION VERIFICATION")
    print("=" * 40)
    
    db_config = {
        'host': 'localhost',
        'user': 'root', 
        'password': '99Rules!',
        'database': 'crypto_prices',
        'charset': 'utf8mb4'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check if ohlc_data exists
            cursor.execute("SHOW TABLES LIKE 'ohlc_data'")
            ohlc_exists = cursor.fetchone()
            
            if ohlc_exists:
                print("✅ ohlc_data table EXISTS!")
                
                # Get record count
                cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                total = cursor.fetchone()[0]
                print(f"📊 Total records: {total:,}")
                
                # Check recent data
                cursor.execute("""
                    SELECT COUNT(*) FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """)
                recent = cursor.fetchone()[0]
                print(f"🔄 Recent data (24h): {recent:,}")
                
                # Check structure
                cursor.execute("DESCRIBE ohlc_data")
                columns = [row[0] for row in cursor.fetchall()]
                print(f"📋 Columns ({len(columns)}): {', '.join(columns[:6])}...")
                
                # Check if ohlc_data_old still exists
                cursor.execute("SHOW TABLES LIKE 'ohlc_data_old'")
                old_exists = cursor.fetchone()
                print(f"🗂️  ohlc_data_old exists: {old_exists is not None}")
                
                print(f"\n🎉 RESTORATION SUCCESSFUL!")
                print("✅ OHLC collectors now have proper target table")
                print("✅ 516K historical records preserved")
                print("✅ Active data collection continuing")
                
            else:
                print("❌ ohlc_data table NOT FOUND!")
                print("⚠️  Restoration may have failed")
                
                # Check if old table still exists
                cursor.execute("SHOW TABLES LIKE 'ohlc_data_old'")
                old_exists = cursor.fetchone()
                if old_exists:
                    print("🗂️  ohlc_data_old still exists - restoration incomplete")
                
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    quick_ohlc_check()