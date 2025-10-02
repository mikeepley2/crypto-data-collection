#!/usr/bin/env python3
"""
FINAL OHLC COLLECTOR STATUS REPORT
Comprehensive assessment after troubleshooting and configuration updates
"""

import subprocess
import mysql.connector
import json
from datetime import datetime

def final_collector_assessment():
    """Provide final assessment of OHLC collector status"""
    
    print("📋 FINAL OHLC COLLECTOR STATUS REPORT")
    print("=" * 55)
    print(f"🕐 Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Deployment Status
    print(f"\n1️⃣ DEPLOYMENT STATUS:")
    print("-" * 25)
    
    try:
        cmd = "kubectl get deployment unified-ohlc-collector -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            deployment = json.loads(result.stdout)
            status = deployment.get('status', {})
            
            replicas = status.get('replicas', 0)
            ready_replicas = status.get('readyReplicas', 0)
            
            print(f"   ✅ Deployment: unified-ohlc-collector")
            print(f"   📊 Status: {ready_replicas}/{replicas} replicas ready")
            
            if ready_replicas == replicas and replicas > 0:
                deployment_healthy = True
                print("   🟢 Health: HEALTHY")
            else:
                deployment_healthy = False
                print("   🔴 Health: UNHEALTHY")
        else:
            deployment_healthy = False
            print("   ❌ Failed to get deployment status")
    except:
        deployment_healthy = False
        print("   ❌ Error checking deployment")
    
    # 2. Configuration Status  
    print(f"\n2️⃣ CONFIGURATION STATUS:")
    print("-" * 30)
    
    try:
        cmd = "kubectl describe deployment unified-ohlc-collector -n crypto-collectors"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            output = result.stdout
            
            env_vars = []
            lines = output.split('\n')
            in_env_section = False
            
            for line in lines:
                if 'Environment:' in line:
                    in_env_section = True
                    continue
                elif in_env_section and line.strip() and not line.startswith('  Mounts:'):
                    if line.startswith('    '):
                        env_vars.append(line.strip())
                elif 'Mounts:' in line:
                    in_env_section = False
            
            print("   📋 Environment Variables:")
            database_config_found = False
            
            for env in env_vars:
                print(f"     {env}")
                if any(db_var in env for db_var in ['DATABASE_HOST', 'DATABASE_USER', 'OHLC_TABLE']):
                    database_config_found = True
            
            if database_config_found:
                print("   🟢 Database Configuration: PRESENT")
            else:
                print("   🔴 Database Configuration: MISSING")
        else:
            print("   ❌ Failed to get configuration")
            database_config_found = False
    except:
        print("   ❌ Error checking configuration")
        database_config_found = False
    
    # 3. Database Status
    print(f"\n3️⃣ DATABASE STATUS:")
    print("-" * 23)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    database_healthy = False
    recent_data = False
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("SHOW TABLES LIKE 'ohlc_data'")
            table_exists = cursor.fetchone() is not None
            print(f"   📊 ohlc_data table: {'✅ EXISTS' if table_exists else '❌ MISSING'}")
            
            if table_exists:
                # Check total records
                cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                total = cursor.fetchone()[0]
                print(f"   📈 Total records: {total:,}")
                
                # Check recent data (last hour)
                cursor.execute("""
                    SELECT COUNT(*) FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """)
                last_hour = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """)
                last_24h = cursor.fetchone()[0]
                
                print(f"   🕐 Last hour: {last_hour} records")
                print(f"   📅 Last 24h: {last_24h} records")
                
                if last_hour > 0:
                    recent_data = True
                    print("   🟢 Recent Data: FRESH")
                else:
                    print("   🔴 Recent Data: STALE")
                
                database_healthy = True
            else:
                print("   🔴 Table Status: MISSING")
    except Exception as e:
        print(f"   ❌ Database Error: {e}")
    
    # 4. Collection Activity
    print(f"\n4️⃣ COLLECTION ACTIVITY:")
    print("-" * 30)
    
    try:
        # Get current pod name
        cmd = "kubectl get pods -n crypto-collectors -l app=unified-ohlc-collector -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            
            if pods:
                pod_name = pods[0]['metadata']['name']
                print(f"   📦 Active Pod: {pod_name}")
                
                # Get recent logs
                cmd = f"kubectl logs {pod_name} -n crypto-collectors --tail=20"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if result.returncode == 0:
                    logs = result.stdout.lower()
                    
                    collection_found = 'found' in logs and 'symbols' in logs
                    insertion_found = any(word in logs for word in ['inserted', 'saved', 'stored', 'database'])
                    errors_found = any(word in logs for word in ['error', 'failed', 'exception'])
                    
                    print(f"   🔍 Data Discovery: {'✅ YES' if collection_found else '❌ NO'}")
                    print(f"   💾 Data Insertion: {'✅ YES' if insertion_found else '❌ NO'}")
                    print(f"   ⚠️  Errors Present: {'🔴 YES' if errors_found else '✅ NO'}")
                    
                    collection_active = collection_found and not errors_found
                else:
                    print("   ❌ Failed to get logs")
                    collection_active = False
            else:
                print("   ❌ No active pods found")
                collection_active = False
        else:
            print("   ❌ Failed to get pod information")
            collection_active = False
    except:
        print("   ❌ Error checking collection activity")
        collection_active = False
    
    # 5. Overall Assessment
    print(f"\n5️⃣ OVERALL ASSESSMENT:")
    print("-" * 30)
    
    checks = [
        ("Deployment Health", deployment_healthy),
        ("Database Configuration", database_config_found),
        ("Database Connectivity", database_healthy),
        ("Recent Data Present", recent_data),
        ("Collection Activity", collection_active)
    ]
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    print("   📋 Health Checks:")
    for check_name, status in checks:
        icon = "✅" if status else "❌"
        print(f"     {icon} {check_name}")
    
    health_score = (passed / total) * 100
    print(f"\n   🎯 Overall Score: {health_score:.0f}% ({passed}/{total})")
    
    # 6. Recommendations
    print(f"\n6️⃣ RECOMMENDATIONS:")
    print("-" * 25)
    
    if health_score >= 80:
        print("   🟢 STATUS: GOOD")
        print("   📝 System appears to be working correctly")
        if not recent_data:
            print("   ⏰ Wait for collection cycle to complete")
    elif health_score >= 60:
        print("   🟡 STATUS: NEEDS ATTENTION") 
        print("   📝 Some issues detected:")
        if not database_config_found:
            print("     - Add database environment variables")
        if not collection_active:
            print("     - Check collector logs for errors")
        if not recent_data:
            print("     - Monitor for new data insertion")
    else:
        print("   🔴 STATUS: CRITICAL")
        print("   📝 Major issues require immediate attention:")
        if not deployment_healthy:
            print("     - Fix deployment issues")
        if not database_healthy:
            print("     - Restore database connectivity")
        if not collection_active:
            print("     - Debug collector application")
    
    return health_score >= 60

if __name__ == "__main__":
    healthy = final_collector_assessment()
    
    print(f"\n✨ ASSESSMENT COMPLETE")
    print("=" * 30)
    
    if healthy:
        print("🎉 Unified OHLC Collector shows good health indicators")
        print("🔄 Continue monitoring for data collection activity")
    else:
        print("⚠️  Unified OHLC Collector needs additional troubleshooting")
        print("🛠️  Review recommendations above for next steps")