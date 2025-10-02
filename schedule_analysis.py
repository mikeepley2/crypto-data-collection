#!/usr/bin/env python3
"""
OHLC Collection Schedule Analysis
Determine the exact collection schedule and predict next collection
"""

import mysql.connector
from datetime import datetime, timedelta

def analyze_collection_schedule():
    """Analyze the historical collection pattern to predict schedule"""
    
    print("⏰ OHLC COLLECTION SCHEDULE ANALYSIS")
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
            
            # Get the last 10 collection timestamps to identify pattern
            cursor.execute("""
                SELECT DISTINCT timestamp_iso, COUNT(*) as records
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 48 HOUR)
                GROUP BY timestamp_iso
                ORDER BY timestamp_iso DESC
                LIMIT 10
            """)
            
            collections = cursor.fetchall()
            
            print("📊 RECENT COLLECTION HISTORY:")
            print("   Timestamp           | Records | Hours Since")
            print("   -------------------|---------|------------")
            
            intervals = []
            
            for i, (timestamp, records) in enumerate(collections):
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                
                hours_since = (datetime.now() - dt.replace(tzinfo=None)).total_seconds() / 3600
                
                print(f"   {timestamp} |   {records:>5} | {hours_since:>8.1f}h")
                
                # Calculate intervals between collections
                if i < len(collections) - 1:
                    next_timestamp = collections[i + 1][0]
                    if isinstance(next_timestamp, str):
                        next_dt = datetime.fromisoformat(next_timestamp.replace('Z', '+00:00'))
                    else:
                        next_dt = next_timestamp
                    
                    interval = (dt.replace(tzinfo=None) - next_dt.replace(tzinfo=None)).total_seconds() / 3600
                    intervals.append(interval)
            
            # Analyze intervals
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                
                print(f"\n📈 INTERVAL ANALYSIS:")
                print(f"   Collection intervals: {[f'{i:.1f}h' for i in intervals]}")
                print(f"   Average interval: {avg_interval:.1f} hours")
                
                # Determine the schedule pattern
                if 3.5 <= avg_interval <= 4.5:
                    schedule_type = "Every 4 hours"
                    cron_pattern = "0 */4 * * *"
                    next_expected = 4
                elif 5.5 <= avg_interval <= 6.5:
                    schedule_type = "Every 6 hours"
                    cron_pattern = "0 */6 * * *"
                    next_expected = 6
                elif 2.8 <= avg_interval <= 3.2:
                    schedule_type = "Every 3 hours"
                    cron_pattern = "0 */3 * * *"
                    next_expected = 3
                else:
                    schedule_type = f"Every {avg_interval:.1f} hours (irregular)"
                    cron_pattern = "Custom schedule"
                    next_expected = avg_interval
                
                print(f"\n🎯 DETECTED SCHEDULE:")
                print(f"   Pattern: {schedule_type}")
                print(f"   Cron: {cron_pattern}")
                
                # Predict next collection
                last_collection = collections[0][0]
                if isinstance(last_collection, str):
                    last_dt = datetime.fromisoformat(last_collection.replace('Z', '+00:00'))
                else:
                    last_dt = last_collection
                
                next_collection = last_dt.replace(tzinfo=None) + timedelta(hours=next_expected)
                time_until_next = (next_collection - datetime.now()).total_seconds() / 3600
                
                print(f"\n🔮 NEXT COLLECTION PREDICTION:")
                print(f"   Expected time: {next_collection.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Hours from now: {time_until_next:.1f}h")
                
                if time_until_next < 0:
                    print(f"   🚨 OVERDUE by {abs(time_until_next):.1f} hours!")
                    status = "OVERDUE"
                elif time_until_next < 1:
                    print(f"   🔜 IMMINENT - expected within 1 hour!")
                    status = "IMMINENT"
                elif time_until_next < 2:
                    print(f"   ⏰ SOON - expected within 2 hours")
                    status = "SOON"
                else:
                    print(f"   ⏳ WAITING - expected in {time_until_next:.1f} hours")
                    status = "WAITING"
                
                return schedule_type, cron_pattern, next_collection, status
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None, None, "ERROR"

def recommend_action(schedule_type, cron_pattern, next_collection, status):
    """Recommend what action to take based on schedule analysis"""
    
    print(f"\n🎯 RECOMMENDATION:")
    print("-" * 25)
    
    if status == "OVERDUE":
        print(f"🚨 ISSUE DETECTED:")
        print(f"   • Collection is overdue!")
        print(f"   • unified-ohlc-collector may not be writing data")
        print(f"   • Need to investigate why collection isn't happening")
        
        print(f"\n⚡ IMMEDIATE ACTIONS:")
        print(f"   1. Check if collector needs manual trigger")
        print(f"   2. Verify database write permissions")
        print(f"   3. Consider adding to collector-manager schedule")
        print(f"   4. Test manual collection endpoint")
        
        action = "INVESTIGATE"
        
    elif status in ["IMMINENT", "SOON"]:
        print(f"✅ NORMAL SCHEDULE:")
        print(f"   • Collection appears to be on {schedule_type} schedule")
        print(f"   • Next collection expected {status.lower()}")
        print(f"   • unified-ohlc-collector likely working correctly")
        
        print(f"\n⏳ RECOMMENDED APPROACH:")
        print(f"   1. Wait for next scheduled collection")
        print(f"   2. Monitor database for new records")
        print(f"   3. Verify collection happens on time")
        
        action = "WAIT_AND_MONITOR"
        
    else:
        print(f"⏰ SCHEDULED COLLECTION:")
        print(f"   • Pattern: {schedule_type}")
        print(f"   • Next expected: {next_collection}")
        print(f"   • Status: {status}")
        
        action = "MONITOR"
    
    print(f"\n🔧 COLLECTION STRATEGY DECISION:")
    
    if "4 hour" in schedule_type:
        print(f"   🎯 RECOMMENDED: Keep as SCHEDULED collection")
        print(f"   📋 Add to collector-manager with cron: {cron_pattern}")
        print(f"   ⚡ Convert from continuous to scheduled")
        print(f"   💡 Benefits: Lower resource usage, batch efficiency")
        
        strategy = "CONVERT_TO_SCHEDULED"
    else:
        print(f"   🔄 RECOMMENDED: Investigate current approach")
        print(f"   📊 Pattern may be market-driven or API-limited")
        
        strategy = "INVESTIGATE_PATTERN"
    
    return action, strategy

if __name__ == "__main__":
    schedule_type, cron_pattern, next_collection, status = analyze_collection_schedule()
    
    if schedule_type:
        action, strategy = recommend_action(schedule_type, cron_pattern, next_collection, status)
        
        print(f"\n" + "="*60)
        print("🎯 FINAL RECOMMENDATION:")
        
        if strategy == "CONVERT_TO_SCHEDULED":
            print("✨ OPTIMAL APPROACH: Convert to Scheduled Collection")
            print("   • Add unified-ohlc-collector to collector-manager")
            print(f"   • Schedule: {cron_pattern} ({schedule_type})")
            print("   • Stop continuous running, use triggered collection")
            print("   • More efficient and predictable")
            
        elif action == "INVESTIGATE":
            print("🔧 IMMEDIATE ACTION: Investigate Collection Issue")
            print("   • Collection is overdue - needs troubleshooting")
            print("   • unified-ohlc-collector may need activation")
            
        else:
            print("⏳ CURRENT ACTION: Wait and Monitor")
            print("   • Collection should happen automatically")
            print(f"   • Expected: {next_collection}")
            
        print("="*60)
    else:
        print("❌ Unable to determine collection schedule")