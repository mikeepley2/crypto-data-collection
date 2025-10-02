#!/usr/bin/env python3
"""
OHLC Collection Timeline Analysis
Determine if old collectors were responsible for recent data and test current collector
"""

import subprocess
import mysql.connector
from datetime import datetime, timedelta

def analyze_collection_timeline():
    """Analyze when data was last collected vs when we made changes"""
    
    print("🕐 OHLC COLLECTION TIMELINE ANALYSIS")
    print("=" * 50)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Get exact timing of last data collection
            cursor.execute("""
                SELECT MAX(timestamp_iso) as last_collection,
                       COUNT(*) as records_at_that_time
                FROM ohlc_data
            """)
            
            result = cursor.fetchone()
            last_collection, records_at_time = result
            
            print(f"📊 LAST DATA COLLECTION:")
            print(f"   Time: {last_collection}")
            print(f"   Records at that time: {records_at_time}")
            
            if last_collection:
                # Calculate time since last collection
                if isinstance(last_collection, str):
                    last_time = datetime.fromisoformat(last_collection.replace('Z', '+00:00'))
                else:
                    last_time = last_collection
                
                time_since = datetime.now() - last_time.replace(tzinfo=None)
                hours_since = time_since.total_seconds() / 3600
                
                print(f"   Hours ago: {hours_since:.1f}")
                
                # Check how many symbols collected in that last batch
                cursor.execute("""
                    SELECT COUNT(DISTINCT symbol) as symbols_in_last_batch
                    FROM ohlc_data 
                    WHERE timestamp_iso = %s
                """, (last_collection,))
                
                symbols_in_batch = cursor.fetchone()[0]
                print(f"   Symbols in last batch: {symbols_in_batch}")
                
                # Check the pattern of recent collections
                cursor.execute("""
                    SELECT DATE_FORMAT(timestamp_iso, '%Y-%m-%d %H:00:00') as collection_hour,
                           COUNT(*) as records,
                           COUNT(DISTINCT symbol) as symbols
                    FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                    GROUP BY DATE_FORMAT(timestamp_iso, '%Y-%m-%d %H:00:00')
                    ORDER BY collection_hour DESC
                """)
                
                recent_pattern = cursor.fetchall()
                
                print(f"\n📅 RECENT COLLECTION PATTERN (24h):")
                if recent_pattern:
                    print("   Hour               | Records | Symbols")
                    print("   -------------------|---------|--------")
                    for hour, records, symbols in recent_pattern:
                        print(f"   {hour} |   {records:>5} |   {symbols:>3}")
                else:
                    print("   ❌ No collections in last 24 hours")
                
                return last_time, hours_since, symbols_in_batch
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None, 0, 0

def check_when_collectors_archived():
    """Check when we archived the old collectors"""
    
    print(f"\n🗂️  COLLECTOR ARCHIVAL TIMELINE:")
    print("-" * 35)
    
    try:
        # Check current status of old collectors
        cmd = "kubectl get cronjobs -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            archived_collectors = []
            for item in data.get('items', []):
                name = item['metadata']['name']
                if 'ohlc' in name.lower():
                    spec = item.get('spec', {})
                    suspended = spec.get('suspend', False)
                    
                    if suspended:
                        archived_collectors.append(name)
                        print(f"   🗂️  {name}: SUSPENDED")
                    else:
                        print(f"   ▶️  {name}: ACTIVE")
            
            print(f"\n   📊 Archived collectors: {len(archived_collectors)}")
            print(f"   ⏰ Archival time: ~2-3 hours ago (during our session)")
            
            return archived_collectors
            
    except Exception as e:
        print(f"❌ Error checking collectors: {e}")
        return []

def test_current_collector():
    """Test if the current unified-ohlc-collector can actually collect data"""
    
    print(f"\n🧪 TESTING CURRENT COLLECTOR:")
    print("-" * 30)
    
    pod_name = "unified-ohlc-collector-65596d6885-87dvw"
    
    # Check if there are any manual trigger endpoints
    print("🔍 Looking for collection endpoints...")
    
    # Try common endpoints that might trigger collection
    endpoints_to_try = [
        ("/collect", "POST"),
        ("/trigger", "POST"), 
        ("/start", "POST"),
        ("/api/collect", "POST"),
        ("/health", "GET")  # We know this works
    ]
    
    working_endpoints = []
    
    for endpoint, method in endpoints_to_try:
        try:
            if method == "POST":
                cmd = f'''kubectl exec {pod_name} -n crypto-collectors -- python -c "
import urllib.request
import urllib.parse
try:
    data = urllib.parse.urlencode({{}}).encode()
    req = urllib.request.Request('http://localhost:8010{endpoint}', data=data, method='POST')
    response = urllib.request.urlopen(req, timeout=10)
    result = response.read().decode()
    print('POST {endpoint} Response:', result[:200])
    print('SUCCESS')
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
except Exception as e:
    print('Error:', str(e))
"'''
            else:
                cmd = f'''kubectl exec {pod_name} -n crypto-collectors -- python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8010{endpoint}', timeout=5)
    result = response.read().decode()
    print('GET {endpoint} Response:', result[:200])
    print('SUCCESS')
except Exception as e:
    print('Error:', str(e))
"'''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and 'SUCCESS' in result.stdout:
                working_endpoints.append((endpoint, method))
                print(f"   ✅ {method} {endpoint}: WORKS")
                if 'Response:' in result.stdout:
                    response_line = [line for line in result.stdout.split('\n') if 'Response:' in line]
                    if response_line:
                        print(f"      📄 {response_line[0]}")
            else:
                print(f"   ❌ {method} {endpoint}: Failed")
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ {method} {endpoint}: Timeout")
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: Error - {e}")
    
    return working_endpoints

def recommend_collection_strategy(last_time, hours_since, symbols_in_batch, archived_collectors):
    """Recommend the best collection strategy"""
    
    print(f"\n🎯 COLLECTION STRATEGY RECOMMENDATION:")
    print("-" * 45)
    
    print(f"📊 ANALYSIS:")
    print(f"   • Last collection: {hours_since:.1f} hours ago")
    print(f"   • Symbols collected: {symbols_in_batch}")
    print(f"   • Archived collectors: {len(archived_collectors)}")
    print(f"   • Current collector: Finding 32 symbols continuously")
    
    # Determine if the gap correlates with our archival
    if 2 <= hours_since <= 4:
        print(f"\n💡 LIKELY SCENARIO:")
        print(f"   🎯 Timeline matches our collector archival!")
        print(f"   📊 Last data came from old collectors")
        print(f"   🔄 unified-ohlc-collector needs activation")
        
        strategy = "TRIGGER_NEEDED"
    elif hours_since > 6:
        print(f"\n💡 LIKELY SCENARIO:")
        print(f"   📅 Gap predates our changes")
        print(f"   ⏰ May be scheduled collection (every 4-6 hours)")
        print(f"   🔄 unified-ohlc-collector may be waiting for schedule")
        
        strategy = "SCHEDULED"
    else:
        print(f"\n💡 ANALYSIS UNCLEAR:")
        strategy = "INVESTIGATE"
    
    print(f"\n🎯 RECOMMENDATIONS:")
    
    if strategy == "TRIGGER_NEEDED":
        print(f"   1. ⚡ Try to trigger immediate collection")
        print(f"   2. 🔧 Check if collector needs activation flag")
        print(f"   3. 🕐 Consider converting to scheduled (every 4-6 hours)")
        print(f"   4. 📊 Monitor for automatic collection")
        
        print(f"\n   🎯 PREFERRED APPROACH:")
        print(f"   • Convert to SCHEDULED collection (4-6 hour intervals)")
        print(f"   • Matches the data pattern we observed")
        print(f"   • More efficient than continuous running")
        print(f"   • Reduces API rate limit issues")
        
    elif strategy == "SCHEDULED":
        print(f"   1. ⏰ Wait for next scheduled collection")
        print(f"   2. 🔄 Monitor for 4-6 hour collection cycle")
        print(f"   3. 📊 Verify collector activates on schedule")
        
    return strategy

if __name__ == "__main__":
    # Analyze the timeline
    last_time, hours_since, symbols_in_batch = analyze_collection_timeline()
    
    # Check when we archived collectors
    archived_collectors = check_when_collectors_archived()
    
    # Test current collector
    working_endpoints = test_current_collector()
    
    # Recommend strategy
    strategy = recommend_collection_strategy(last_time, hours_since, symbols_in_batch, archived_collectors)
    
    print(f"\n" + "="*60)
    print("🎯 NEXT STEPS:")
    
    if strategy == "TRIGGER_NEEDED":
        print("1. 🔧 Try to manually trigger collection")
        print("2. ⏰ Consider adding to collector-manager schedule")
        print("3. 🎯 Recommend: Schedule every 4 hours (0 */4 * * *)")
    elif strategy == "SCHEDULED":
        print("1. ⏰ Wait for next collection cycle (should be soon)")
        print("2. 📊 Continue monitoring for 2-4 hours")
        print("3. 🔄 Current continuous approach may be correct")
    
    print("="*60)