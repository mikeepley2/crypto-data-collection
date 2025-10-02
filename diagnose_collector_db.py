#!/usr/bin/env python3
"""
Check Database Connection from Collector Perspective
Verify if the database can be accessed and if data is being written
"""

import mysql.connector
from datetime import datetime, timedelta

def check_database_from_collector_perspective():
    """Check database access like the collector would"""
    
    print("🔍 DATABASE CONNECTION CHECK (Collector Perspective)")
    print("=" * 60)
    
    # Check if the collector can access the database
    db_configs = [
        # Default localhost (same as our checks)
        {
            'name': 'localhost',
            'host': 'localhost',
            'user': 'root',
            'password': '99Rules!',
            'database': 'crypto_prices'
        },
        # Kubernetes internal service (how collector might connect)
        {
            'name': 'mysql service',
            'host': 'mysql.crypto-collectors.svc.cluster.local',
            'user': 'root', 
            'password': '99Rules!',
            'database': 'crypto_prices'
        }
    ]
    
    for config in db_configs:
        config_name = config.pop('name')
        print(f"\n📊 Testing: {config_name}")
        print("-" * 30)
        
        try:
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                # Check if ohlc_data table exists
                cursor.execute("SHOW TABLES LIKE 'ohlc_data'")
                table_exists = cursor.fetchone() is not None
                print(f"   ohlc_data table exists: {'✅' if table_exists else '❌'}")
                
                if table_exists:
                    # Check record count
                    cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                    count = cursor.fetchone()[0]
                    print(f"   Total records: {count:,}")
                    
                    # Check latest record
                    cursor.execute("""
                        SELECT symbol, timestamp_iso 
                        FROM ohlc_data 
                        ORDER BY timestamp_iso DESC 
                        LIMIT 1
                    """)
                    latest = cursor.fetchone()
                    if latest:
                        symbol, timestamp = latest
                        print(f"   Latest: {symbol} at {timestamp}")
                    
                    # Try to insert a test record
                    try:
                        test_insert = """
                            INSERT INTO ohlc_data 
                            (symbol, coin_id, timestamp_unix, timestamp_iso, 
                             open_price, high_price, low_price, close_price, volume)
                            VALUES 
                            ('TEST', 'test', 1234567890, '2025-09-30 18:30:00', 
                             1.0, 1.1, 0.9, 1.05, 1000.0)
                        """
                        cursor.execute(test_insert)
                        conn.commit()
                        print("   Test insert: ✅ SUCCESS")
                        
                        # Clean up test record
                        cursor.execute("DELETE FROM ohlc_data WHERE symbol = 'TEST'")
                        conn.commit()
                        
                    except Exception as e:
                        print(f"   Test insert: ❌ FAILED - {e}")
                
                print(f"   Connection: ✅ SUCCESS")
                return True
                
        except Exception as e:
            print(f"   Connection: ❌ FAILED - {e}")
    
    return False

def check_recent_collection_patterns():
    """Check recent collection patterns to understand the issue"""
    
    print(f"\n📈 RECENT COLLECTION ANALYSIS")
    print("-" * 40)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check collection pattern over last few hours
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(timestamp_iso, '%Y-%m-%d %H:00:00') as hour,
                    COUNT(*) as records,
                    COUNT(DISTINCT symbol) as symbols
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 12 HOUR)
                GROUP BY DATE_FORMAT(timestamp_iso, '%Y-%m-%d %H:00:00')
                ORDER BY hour DESC
            """)
            
            results = cursor.fetchall()
            
            if results:
                print("📊 HOURLY COLLECTION PATTERN (Last 12 hours):")
                print("   Hour                | Records | Symbols")
                print("   -------------------|---------|--------")
                
                for hour, records, symbols in results:
                    print(f"   {hour} |   {records:>5} |   {symbols:>3}")
                
                # Identify gap
                latest_hour = results[0][0] if results else None
                current_hour = datetime.now().strftime('%Y-%m-%d %H:00:00')
                
                if latest_hour and latest_hour < current_hour:
                    gap_hours = (datetime.strptime(current_hour, '%Y-%m-%d %H:00:00') - 
                               datetime.strptime(latest_hour, '%Y-%m-%d %H:00:00')).total_seconds() / 3600
                    print(f"\n   ⚠️  DATA GAP: {gap_hours:.1f} hours since last collection")
                else:
                    print(f"\n   ✅ Recent data found")
            else:
                print("❌ No recent data found in last 12 hours")
            
            # Check what symbols were collected recently
            cursor.execute("""
                SELECT symbol, COUNT(*) as records, MAX(timestamp_iso) as latest
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY symbol
                ORDER BY records DESC
                LIMIT 10
            """)
            
            symbols = cursor.fetchall()
            
            if symbols:
                print(f"\n🎯 TOP SYMBOLS COLLECTED (Last 24h):")
                print("   Symbol | Records | Latest")
                print("   -------|---------|-------")
                
                for symbol, records, latest in symbols:
                    print(f"   {symbol:>6} |   {records:>5} | {latest}")
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")

def check_collector_configuration():
    """Check if we can determine collector configuration"""
    
    print(f"\n⚙️  COLLECTOR CONFIGURATION CHECK")
    print("-" * 40)
    
    # Check if there are any ConfigMaps that might contain database config
    try:
        import subprocess
        
        cmd = "kubectl get configmaps -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            configmaps = []
            for item in data.get('items', []):
                name = item['metadata']['name']
                if 'ohlc' in name.lower() or 'unified' in name.lower():
                    configmaps.append(name)
            
            if configmaps:
                print(f"📋 Found relevant ConfigMaps:")
                for cm in configmaps:
                    print(f"   - {cm}")
            else:
                print("📋 No OHLC-related ConfigMaps found")
                print("   Collector likely uses hardcoded database connection")
        
    except Exception as e:
        print(f"❌ ConfigMap check error: {e}")

if __name__ == "__main__":
    print("🎯 COLLECTOR DATABASE CONNECTION DIAGNOSIS")
    print("=" * 60)
    
    db_accessible = check_database_from_collector_perspective()
    check_recent_collection_patterns()
    check_collector_configuration()
    
    print(f"\n✨ Diagnosis Complete!")
    
    if db_accessible:
        print("🎯 Database is accessible - issue may be with collector logic")
    else:
        print("⚠️  Database connection issues detected")