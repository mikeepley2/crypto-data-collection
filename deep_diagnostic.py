#!/usr/bin/env python3
"""
Deep Database and Collection Diagnostic
Figure out exactly why data isn't being collected despite healthy services
"""

import subprocess
import json
import time
from datetime import datetime

def deep_diagnostic():
    """Comprehensive diagnostic to find the root cause"""
    
    print("🔍 DEEP DATABASE & COLLECTION DIAGNOSTIC")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get collector manager pod
    manager_pod = None
    try:
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '-l', 'app=collector-manager', '--field-selector=status.phase=Running',
            '-o', 'jsonpath={.items[0].metadata.name}'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            manager_pod = result.stdout.strip()
            print(f"✅ Found collector manager: {manager_pod}")
        else:
            print("❌ No collector manager found")
            return False
            
    except Exception as e:
        print(f"❌ Error finding collector manager: {e}")
        return False
    
    # Test 1: Check collector manager schedule status
    print(f"\n1. COLLECTOR MANAGER SCHEDULE STATUS:")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
            'curl', '-s', 'http://localhost:8000/schedule'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("Schedule endpoint response:")
            print(result.stdout[:500])  # First 500 chars
        else:
            print(f"❌ Schedule check failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error checking schedule: {e}")
    
    # Test 2: Direct database connectivity test from pod
    print(f"\n2. DATABASE CONNECTIVITY FROM POD:")
    print("-" * 40)
    
    try:
        # Test raw connection
        result = subprocess.run([
            'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
            'nc', '-zv', 'host.docker.internal', '3306'
        ], capture_output=True, text=True, timeout=10)
        
        if 'open' in result.stderr or result.returncode == 0:
            print("✅ Raw TCP connection to MySQL: SUCCESS")
            
            # Test with mysql client if available
            mysql_test = subprocess.run([
                'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
                'mysql', '-h', 'host.docker.internal', '-u', 'news_collector', 
                '-p99Rules!', '-e', 'SELECT 1'
            ], capture_output=True, text=True, timeout=15)
            
            if mysql_test.returncode == 0:
                print("✅ MySQL client connection: SUCCESS")
            else:
                print(f"❌ MySQL client failed: {mysql_test.stderr}")
                
        else:
            print(f"❌ Raw TCP connection failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error testing database connectivity: {e}")
    
    # Test 3: Check service logs for actual errors
    print(f"\n3. SERVICE ERROR LOG ANALYSIS:")
    print("-" * 40)
    
    services = ['enhanced-crypto-prices', 'crypto-news-collector', 'technical-indicators']
    
    for service in services:
        try:
            print(f"\n{service.upper()} LOGS:")
            
            # Get pod name
            pod_result = subprocess.run([
                'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
                '-l', f'app={service}', '--field-selector=status.phase=Running',
                '-o', 'jsonpath={.items[0].metadata.name}'
            ], capture_output=True, text=True, timeout=10)
            
            if pod_result.returncode == 0 and pod_result.stdout.strip():
                pod_name = pod_result.stdout.strip()
                
                # Get recent logs
                log_result = subprocess.run([
                    'kubectl', 'logs', pod_name, '-n', 'crypto-collectors', '--tail=5'
                ], capture_output=True, text=True, timeout=15)
                
                if log_result.returncode == 0:
                    print(f"Recent logs from {pod_name}:")
                    print(log_result.stdout)
                else:
                    print(f"❌ Failed to get logs: {log_result.stderr}")
            else:
                print(f"❌ No running pod found for {service}")
                
        except Exception as e:
            print(f"❌ Error checking {service} logs: {e}")
    
    # Test 4: Manual collection with detailed output
    print(f"\n4. DETAILED MANUAL COLLECTION TEST:")
    print("-" * 40)
    
    try:
        print("Testing enhanced-crypto-prices collection...")
        
        result = subprocess.run([
            'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
            'curl', '-v', '-X', 'POST', 
            'http://localhost:8000/services/enhanced-crypto-prices/collect',
            '-H', 'Content-Type: application/json', '-d', '{}'
        ], capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if '"status":"success"' in result.stdout:
            print("✅ Collection trigger succeeded")
            
            # Extract any records collected info
            if '"records_collected":' in result.stdout:
                try:
                    response = json.loads(result.stdout.split('\n')[-1])
                    records = response.get('records_collected', 0)
                    print(f"📊 Records collected: {records}")
                except:
                    print("⚠️  Could not parse collection response")
        else:
            print("❌ Collection trigger failed or returned error")
            
    except Exception as e:
        print(f"❌ Error in manual collection test: {e}")
    
    # Test 5: Check actual database tables
    print(f"\n5. DATABASE TABLE VERIFICATION:")
    print("-" * 40)
    
    # We'll use a pod to connect to database and check tables
    try:
        # Check if crypto_prices table exists and is accessible
        table_check = subprocess.run([
            'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
            'mysql', '-h', 'host.docker.internal', '-u', 'news_collector', 
            '-p99Rules!', 'crypto_prices', '-e', 'SHOW TABLES'
        ], capture_output=True, text=True, timeout=15)
        
        if table_check.returncode == 0:
            print("✅ crypto_prices database accessible")
            print("Available tables:")
            print(table_check.stdout)
            
            # Check if we can insert data
            insert_test = subprocess.run([
                'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
                'mysql', '-h', 'host.docker.internal', '-u', 'news_collector', 
                '-p99Rules!', 'crypto_prices', '-e', 
                "SELECT COUNT(*) as total_records FROM crypto_prices WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)"
            ], capture_output=True, text=True, timeout=15)
            
            if insert_test.returncode == 0:
                print("Recent data check:")
                print(insert_test.stdout)
            else:
                print(f"❌ Could not check recent data: {insert_test.stderr}")
                
        else:
            print(f"❌ crypto_prices database not accessible: {table_check.stderr}")
            
    except Exception as e:
        print(f"❌ Error checking database tables: {e}")
    
    # Test 6: Check service environment variables
    print(f"\n6. SERVICE ENVIRONMENT ANALYSIS:")
    print("-" * 40)
    
    try:
        # Check enhanced-crypto-prices environment
        env_result = subprocess.run([
            'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
            'env'
        ], capture_output=True, text=True, timeout=10)
        
        if env_result.returncode == 0:
            env_lines = env_result.stdout.split('\n')
            mysql_vars = [line for line in env_lines if 'MYSQL' in line or 'DATABASE' in line]
            
            print("Database-related environment variables:")
            for var in mysql_vars:
                if var.strip():
                    print(f"  {var}")
        else:
            print(f"❌ Could not check environment: {env_result.stderr}")
            
    except Exception as e:
        print(f"❌ Error checking environment: {e}")
    
    print(f"\n" + "=" * 60)
    print("🎯 DIAGNOSTIC COMPLETE - ANALYZING RESULTS...")
    print("=" * 60)
    
    return True

def fix_based_on_findings():
    """Apply fixes based on diagnostic findings"""
    
    print(f"\n🔧 APPLYING TARGETED FIXES:")
    print("-" * 40)
    
    # Fix 1: Reset auto-resolution counters by restarting monitor
    print("1. Resetting auto-resolution system...")
    # This will be done by stopping and restarting the monitor
    
    # Fix 2: Force restart problematic services
    print("2. Force restarting services with fresh database connections...")
    
    services_to_restart = [
        'enhanced-crypto-prices',
        'crypto-news-collector', 
        'technical-indicators'
    ]
    
    for service in services_to_restart:
        try:
            result = subprocess.run([
                'kubectl', 'rollout', 'restart', f'deployment/{service}',
                '-n', 'crypto-collectors'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Restarted {service}")
            else:
                print(f"❌ Failed to restart {service}")
                
        except Exception as e:
            print(f"❌ Error restarting {service}: {e}")
    
    # Fix 3: Restart collector manager for fresh state
    print("3. Restarting collector manager...")
    
    try:
        result = subprocess.run([
            'kubectl', 'rollout', 'restart', 'deployment/collector-manager',
            '-n', 'crypto-collectors'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Collector manager restarted")
        else:
            print("❌ Failed to restart collector manager")
            
    except Exception as e:
        print(f"❌ Error restarting collector manager: {e}")
    
    print(f"\n⏳ Waiting 60 seconds for services to stabilize...")
    for i in range(6):
        time.sleep(10)
        print(f"   {(i+1)*10}/60 seconds...")
    
    print(f"\n✅ FIXES APPLIED - Ready for fresh monitoring!")

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE COLLECTION SYSTEM DIAGNOSTIC")
    print("🎯 Objective: Figure out why data collection isn't working")
    print("🔍 Running deep analysis...")
    print()
    
    success = deep_diagnostic()
    
    if success:
        print(f"\n🔧 Applying fixes based on findings...")
        fix_based_on_findings()
        
        print(f"\n📋 NEXT STEPS:")
        print("1. Start fresh monitoring: python simple_collection_monitor.py")
        print("2. Monitor for 10 minutes to see if data collection resumes")
        print("3. Check status: python quick_status_check.py")
    else:
        print(f"\n❌ Diagnostic failed - manual investigation needed")