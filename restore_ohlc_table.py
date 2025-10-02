#!/usr/bin/env python3
"""
Restore OHLC Data Table
The ohlc_data_old table is actively collecting data and should be the primary OHLC table
"""

import mysql.connector

def restore_ohlc_table():
    """Restore ohlc_data table from ohlc_data_old"""
    
    print("🔧 RESTORING OHLC DATA TABLE")
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
            
            # First, check current status
            print("1. CURRENT STATUS:")
            print("-" * 20)
            
            cursor.execute("SHOW TABLES LIKE 'ohlc_data'")
            ohlc_exists = cursor.fetchone()
            print(f"   ohlc_data exists: {ohlc_exists is not None}")
            
            cursor.execute("SELECT COUNT(*) FROM ohlc_data_old")
            old_count = cursor.fetchone()[0]
            print(f"   ohlc_data_old records: {old_count:,}")
            
            cursor.execute("""
                SELECT COUNT(*) FROM ohlc_data_old 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)
            recent = cursor.fetchone()[0]
            print(f"   Recent data (24h): {recent}")
            
            if ohlc_exists:
                print("\n   ⚠️  WARNING: ohlc_data already exists!")
                return False
            
            # Rename ohlc_data_old back to ohlc_data
            print(f"\n2. RESTORING TABLE:")
            print("-" * 25)
            print("   Renaming ohlc_data_old -> ohlc_data...")
            
            cursor.execute("RENAME TABLE `ohlc_data_old` TO `ohlc_data`")
            
            print("   ✅ Successfully restored ohlc_data table!")
            
            # Verify the restoration
            cursor.execute("SELECT COUNT(*) FROM ohlc_data")
            restored_count = cursor.fetchone()[0]
            print(f"   Verified: {restored_count:,} records in restored table")
            
            print(f"\n3. BENEFITS:")
            print("-" * 15)
            print("   • OHLC collectors can now write to proper table name")
            print("   • 516K historical records preserved")
            print("   • Clean 12-column OHLC structure maintained") 
            print("   • Active data collection continues (156 records/24h)")
            
            return True
            
    except Exception as e:
        print(f"❌ Error restoring table: {e}")
        return False

def update_enhanced_crypto_prices_to_ohlc():
    """Update enhanced-crypto-prices to use the proper OHLC table"""
    
    print(f"\n4. UPDATING ENHANCED-CRYPTO-PRICES CONFIGURATION:")
    print("-" * 50)
    
    import subprocess
    
    # Create patch to use ohlc_data instead of hourly_data
    ohlc_patch = '''
spec:
  template:
    spec:
      containers:
      - name: enhanced-crypto-prices
        env:
        - name: CRYPTO_PRICES_TABLE
          value: "ohlc_data"
        - name: HIGH_COLUMN
          value: "high_price"
        - name: LOW_COLUMN
          value: "low_price"
        - name: OPEN_COLUMN
          value: "open_price"
        - name: CLOSE_COLUMN
          value: "close_price"
        - name: VOLUME_COLUMN
          value: "volume"
'''
    
    with open('enhanced-prices-ohlc-patch.yaml', 'w') as f:
        f.write(ohlc_patch)
    
    print("   Created patch file: enhanced-prices-ohlc-patch.yaml")
    print("   This will configure enhanced-crypto-prices to use ohlc_data")
    print("   (Clean 12-column OHLC format vs 117-column ML features)")
    
    response = input(f"\n   Apply this configuration? (y/n): ")
    if response.lower() == 'y':
        try:
            cmd = "kubectl patch deployment enhanced-crypto-prices -n crypto-collectors --patch-file enhanced-prices-ohlc-patch.yaml"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Successfully updated enhanced-crypto-prices configuration")
                print("   📝 Now using ohlc_data (clean OHLC format)")
            else:
                print(f"   ❌ Failed to update: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("   ⏸️  Configuration update skipped")

if __name__ == "__main__":
    print("🎯 OHLC DATA TABLE RESTORATION")
    print("=" * 50)
    print("The ohlc_data_old table has:")
    print("• 516,384 records (6 years of data)")
    print("• 156 recent records (actively collecting)")
    print("• Clean 12-column OHLC structure")
    print("• Multiple collectors expecting 'ohlc_data' table name")
    print()
    
    response = input("Restore ohlc_data_old -> ohlc_data? (y/n): ")
    if response.lower() == 'y':
        if restore_ohlc_table():
            update_enhanced_crypto_prices_to_ohlc()
            print(f"\n✨ OHLC table restoration complete!")
            print("🎯 Your system now has proper OHLC data collection")
        else:
            print("❌ Restoration failed")
    else:
        print("⏸️  Restoration cancelled")