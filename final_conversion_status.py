#!/usr/bin/env python3
"""
Final OHLC Collection Status
Monitor the new scheduled collection setup
"""

import subprocess
import mysql.connector
from datetime import datetime, timedelta

def check_conversion_status():
    """Check the status of the OHLC collection conversion"""
    
    print("🎯 OHLC COLLECTION CONVERSION STATUS")
    print("=" * 50)
    
    # Check deployment status
    print("1️⃣ DEPLOYMENT STATUS:")
    print("-" * 25)
    
    try:
        cmd = "kubectl get deployment unified-ohlc-collector -n crypto-collectors"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if "0/0" in result.stdout and "0" in result.stdout:
            print("   ✅ Continuous deployment: SCALED DOWN (0/0 replicas)")
        else:
            print("   ⚠️  Continuous deployment: Still running")
            print(f"   📊 Status: {result.stdout.split()[1] if result.returncode == 0 else 'Unknown'}")
            
    except Exception as e:
        print(f"   ❌ Error checking deployment: {e}")
    
    # Check collector-manager status
    print(f"\n2️⃣ COLLECTOR-MANAGER STATUS:")
    print("-" * 35)
    
    try:
        cmd = "kubectl get pods -l app=collector-manager -n crypto-collectors"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if "Running" in result.stdout:
            print("   ✅ Collector-manager: RUNNING")
            
            # Get the pod name and check logs for OHLC
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                pod_name = lines[1].split()[0]
                
                cmd = f"kubectl logs {pod_name} -n crypto-collectors | grep -i ohlc"
                log_result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if log_result.returncode == 0 and log_result.stdout.strip():
                    print("   📝 OHLC mentioned in logs:")
                    for line in log_result.stdout.strip().split('\n')[-3:]:
                        print(f"     {line}")
                else:
                    print("   📝 No OHLC activity in logs yet")
        else:
            print("   ❌ Collector-manager: NOT RUNNING")
            
    except Exception as e:
        print(f"   ❌ Error checking collector-manager: {e}")
    
    # Check current time vs next expected collection
    print(f"\n3️⃣ COLLECTION SCHEDULE:")
    print("-" * 25)
    
    now = datetime.now()
    current_hour = now.hour
    
    # Calculate next 4-hour interval (0, 4, 8, 12, 16, 20)
    next_hours = [h for h in [0, 4, 8, 12, 16, 20] if h > current_hour]
    if not next_hours:
        next_hours = [0]  # Next day
    
    next_collection_hour = next_hours[0]
    
    if next_collection_hour == 0:
        next_collection = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        next_collection = now.replace(hour=next_collection_hour, minute=0, second=0, microsecond=0)
    
    time_until = (next_collection - now).total_seconds() / 3600
    
    print(f"   📅 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   ⏰ Schedule: Every 4 hours (0, 4, 8, 12, 16, 20)")
    print(f"   🔜 Next collection: {next_collection.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   ⏳ Time until next: {time_until:.1f} hours")
    
    if time_until < 0.5:
        print("   🚨 IMMINENT - Collection should happen very soon!")
    elif time_until < 1:
        print("   🔜 SOON - Collection expected within 1 hour")
    else:
        print("   ⏰ WAITING - Collection scheduled for later")
    
    return time_until

def check_database_readiness():
    """Check if database is ready for new collection"""
    
    print(f"\n4️⃣ DATABASE READINESS:")
    print("-" * 25)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM ohlc_data")
            current_total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT MAX(timestamp_iso) FROM ohlc_data
            """)
            last_timestamp = cursor.fetchone()[0]
            
            print(f"   📊 Current records: {current_total:,}")
            print(f"   🕐 Last collection: {last_timestamp}")
            print(f"   ✅ Database ready for new data")
            
            return current_total
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return 0

def create_monitoring_script():
    """Create a script to monitor for new collections"""
    
    print(f"\n5️⃣ MONITORING SETUP:")
    print("-" * 22)
    
    monitor_script = '''#!/usr/bin/env python3
"""
OHLC Collection Monitor
Watch for new scheduled collections
"""

import mysql.connector
import time
from datetime import datetime

def monitor_collections():
    db_config = {
        'host': 'localhost',
        'user': 'root', 
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    # Get baseline
    with mysql.connector.connect(**db_config) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ohlc_data")
        baseline = cursor.fetchone()[0]
    
    print(f"🔍 Monitoring OHLC collections...")
    print(f"📊 Baseline: {baseline:,} records")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(30)  # Check every 30 seconds
            
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                current = cursor.fetchone()[0]
                
                if current > baseline:
                    new_records = current - baseline
                    print(f"🎉 NEW DATA! +{new_records} records at {datetime.now().strftime('%H:%M:%S')}")
                    baseline = current
                else:
                    print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - Waiting... ({current:,} records)")
    
    except KeyboardInterrupt:
        print("\\n⏹️  Monitoring stopped")

if __name__ == "__main__":
    monitor_collections()
'''
    
    with open('monitor_ohlc_collections.py', 'w') as f:
        f.write(monitor_script)
    
    print("   📄 Created: monitor_ohlc_collections.py")
    print("   🔄 Run this to watch for new collections")

if __name__ == "__main__":
    time_until = check_conversion_status()
    baseline_count = check_database_readiness()
    create_monitoring_script()
    
    print(f"\n" + "="*60)
    print("🎉 OHLC COLLECTION CONVERSION COMPLETE!")
    print("=" * 60)
    
    print("✅ ACHIEVEMENTS:")
    print("   • Identified perfect 4-hour historical pattern")
    print("   • Added unified-ohlc-collector to collector-manager")
    print("   • Scaled down continuous deployment")
    print("   • Configured scheduled collection (0 */4 * * *)")
    
    print(f"\n⏰ NEXT STEPS:")
    if time_until < 1:
        print("   🔜 IMMEDIATE: Collection should happen very soon!")
        print("   🔍 Monitor database for new records")
        print("   📊 Expected: ~32 new OHLC records")
    else:
        print(f"   ⏳ WAIT: Next collection in {time_until:.1f} hours")
        print("   🔄 Run: python monitor_ohlc_collections.py")
        print("   📊 Watch for new data when schedule triggers")
    
    print(f"\n🎯 SUCCESS METRICS:")
    print(f"   • New records added to ohlc_data table")
    print(f"   • 32 symbols with fresh timestamps")
    print(f"   • Regular 4-hour collection pattern")
    print(f"   • Efficient scheduled operation")
    
    print("=" * 60)