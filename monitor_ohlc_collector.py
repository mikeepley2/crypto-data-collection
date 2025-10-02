#!/usr/bin/env python3
"""
Unified OHLC Collector Health Check
Comprehensive monitoring of the unified-ohlc-collector deployment
"""

import subprocess
import mysql.connector
import json
from datetime import datetime, timedelta

def check_deployment_status():
    """Check the Kubernetes deployment status"""
    
    print("🔍 DEPLOYMENT STATUS CHECK")
    print("=" * 40)
    
    try:
        # Get deployment status
        cmd = "kubectl get deployment unified-ohlc-collector -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            deployment = json.loads(result.stdout)
            
            # Extract status information
            spec = deployment.get('spec', {})
            status = deployment.get('status', {})
            
            replicas = spec.get('replicas', 0)
            ready_replicas = status.get('readyReplicas', 0)
            available_replicas = status.get('availableReplicas', 0)
            
            print(f"📋 Deployment: unified-ohlc-collector")
            print(f"   Desired Replicas: {replicas}")
            print(f"   Ready Replicas: {ready_replicas}")
            print(f"   Available Replicas: {available_replicas}")
            
            if ready_replicas == replicas and available_replicas == replicas:
                print("   Status: ✅ HEALTHY")
                return True
            else:
                print("   Status: ❌ NOT HEALTHY")
                return False
        else:
            print(f"❌ Failed to get deployment status: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking deployment: {e}")
        return False

def check_pod_logs():
    """Check recent logs from the collector pod"""
    
    print(f"\n📊 POD LOGS CHECK")
    print("-" * 25)
    
    try:
        # Get pod name
        cmd = "kubectl get pods -n crypto-collectors -l app=unified-ohlc-collector -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            
            if not pods:
                print("❌ No pods found for unified-ohlc-collector")
                return False
            
            pod_name = pods[0]['metadata']['name']
            pod_status = pods[0]['status']['phase']
            
            print(f"🔍 Pod: {pod_name}")
            print(f"   Status: {pod_status}")
            
            # Get recent logs (last 50 lines)
            cmd = f"kubectl logs {pod_name} -n crypto-collectors --tail=50"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                logs = result.stdout
                lines = logs.split('\n')[-10:]  # Last 10 lines
                
                print(f"   Recent Logs (last 10 lines):")
                for line in lines:
                    if line.strip():
                        print(f"     {line}")
                
                # Look for signs of active collection
                collection_indicators = ['collected', 'inserted', 'processed', 'success']
                error_indicators = ['error', 'failed', 'exception', 'traceback']
                
                has_collection = any(indicator in logs.lower() for indicator in collection_indicators)
                has_errors = any(indicator in logs.lower() for indicator in error_indicators)
                
                if has_collection and not has_errors:
                    print("   Logs Status: ✅ COLLECTING DATA")
                    return True
                elif has_errors:
                    print("   Logs Status: ⚠️  ERRORS DETECTED")
                    return False
                else:
                    print("   Logs Status: ⚠️  NO CLEAR COLLECTION ACTIVITY")
                    return False
            else:
                print(f"❌ Failed to get logs: {result.stderr}")
                return False
        else:
            print(f"❌ Failed to get pods: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking logs: {e}")
        return False

def check_database_activity():
    """Check database for recent OHLC data collection"""
    
    print(f"\n💾 DATABASE ACTIVITY CHECK")
    print("-" * 30)
    
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
            
            # Check total records
            cursor.execute("SELECT COUNT(*) FROM ohlc_data")
            total_records = cursor.fetchone()[0]
            print(f"📊 Total OHLC records: {total_records:,}")
            
            # Check recent data (last hour)
            cursor.execute("""
                SELECT COUNT(*) FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)
            last_hour = cursor.fetchone()[0]
            print(f"🕐 Last hour: {last_hour} records")
            
            # Check recent data (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)
            last_24h = cursor.fetchone()[0]
            print(f"📅 Last 24 hours: {last_24h} records")
            
            # Check most recent record
            cursor.execute("""
                SELECT symbol, timestamp_iso, open_price, close_price, volume
                FROM ohlc_data 
                ORDER BY timestamp_iso DESC 
                LIMIT 1
            """)
            latest = cursor.fetchone()
            
            if latest:
                symbol, timestamp, open_price, close_price, volume = latest
                print(f"🔄 Latest record:")
                print(f"   Symbol: {symbol}")
                print(f"   Time: {timestamp}")
                print(f"   OHLC: O={open_price} C={close_price}")
                print(f"   Volume: {volume}")
                
                # Check how recent the latest data is
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now() - timedelta(days=1)  # Fallback
                
                time_diff = datetime.now() - timestamp.replace(tzinfo=None)
                minutes_ago = time_diff.total_seconds() / 60
                
                if minutes_ago < 60:
                    print(f"   Freshness: ✅ {minutes_ago:.1f} minutes ago")
                    collection_active = True
                elif minutes_ago < 1440:  # 24 hours
                    print(f"   Freshness: ⚠️  {minutes_ago/60:.1f} hours ago")
                    collection_active = False
                else:
                    print(f"   Freshness: ❌ {minutes_ago/1440:.1f} days ago")
                    collection_active = False
            else:
                print("❌ No records found in ohlc_data table")
                collection_active = False
            
            # Check data diversity (multiple symbols)
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol) as symbol_count
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)
            symbol_count = cursor.fetchone()[0]
            print(f"🎯 Symbols collected (24h): {symbol_count}")
            
            if symbol_count > 10:
                print("   Diversity: ✅ GOOD COVERAGE")
            elif symbol_count > 5:
                print("   Diversity: ⚠️  LIMITED COVERAGE")
            else:
                print("   Diversity: ❌ POOR COVERAGE")
            
            return collection_active and symbol_count > 5
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def monitor_collection_rate():
    """Monitor the real-time collection rate"""
    
    print(f"\n⏱️  COLLECTION RATE MONITORING")
    print("-" * 35)
    
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
            
            # Get collection rate for different time windows
            time_windows = [
                ("5 minutes", 5),
                ("15 minutes", 15),
                ("1 hour", 60),
                ("6 hours", 360)
            ]
            
            for window_name, minutes in time_windows:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL {minutes} MINUTE)
                """)
                count = cursor.fetchone()[0]
                rate_per_minute = count / minutes if minutes > 0 else 0
                
                print(f"📊 {window_name:>10}: {count:>4} records ({rate_per_minute:.1f}/min)")
            
            # Expected rate calculation
            # Assuming we collect major cryptos every few minutes
            expected_min_rate = 0.5  # At least 0.5 records per minute
            
            cursor.execute("""
                SELECT COUNT(*) FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 15 MINUTE)
            """)
            recent_count = cursor.fetchone()[0]
            actual_rate = recent_count / 15
            
            print(f"\n🎯 RATE ANALYSIS:")
            print(f"   Expected: ≥{expected_min_rate}/min")
            print(f"   Actual: {actual_rate:.2f}/min")
            
            if actual_rate >= expected_min_rate:
                print("   Status: ✅ COLLECTING AT GOOD RATE")
                return True
            else:
                print("   Status: ⚠️  COLLECTION RATE LOW")
                return False
                
    except Exception as e:
        print(f"❌ Rate monitoring error: {e}")
        return False

def overall_health_assessment(deployment_ok, logs_ok, db_ok, rate_ok):
    """Provide overall health assessment"""
    
    print(f"\n🏥 OVERALL HEALTH ASSESSMENT")
    print("=" * 40)
    
    checks = [
        ("Deployment Status", deployment_ok),
        ("Pod Logs", logs_ok),
        ("Database Activity", db_ok),
        ("Collection Rate", rate_ok)
    ]
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    print("📋 HEALTH CHECKS:")
    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {check_name}")
    
    health_percentage = (passed / total) * 100
    
    print(f"\n🎯 OVERALL HEALTH: {health_percentage:.0f}% ({passed}/{total})")
    
    if health_percentage >= 90:
        print("🟢 STATUS: EXCELLENT - Collector running optimally")
    elif health_percentage >= 75:
        print("🟡 STATUS: GOOD - Minor issues detected")
    elif health_percentage >= 50:
        print("🟠 STATUS: WARNING - Multiple issues need attention")
    else:
        print("🔴 STATUS: CRITICAL - Collector needs immediate attention")
    
    return health_percentage >= 75

if __name__ == "__main__":
    print("🎯 UNIFIED OHLC COLLECTOR HEALTH CHECK")
    print("=" * 50)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all health checks
    deployment_ok = check_deployment_status()
    logs_ok = check_pod_logs()
    db_ok = check_database_activity()
    rate_ok = monitor_collection_rate()
    
    # Overall assessment
    healthy = overall_health_assessment(deployment_ok, logs_ok, db_ok, rate_ok)
    
    print(f"\n✨ Health Check Complete!")
    
    if healthy:
        print("🎉 unified-ohlc-collector is running successfully!")
    else:
        print("⚠️  Issues detected - review the checks above")