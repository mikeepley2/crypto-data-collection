#!/usr/bin/env python3
"""
Database Connectivity Recovery Script
Fix MySQL connection issues for all collection services
"""

import subprocess
import time

def fix_database_connectivity():
    """Fix database connectivity issues"""
    
    print("🔧 DATABASE CONNECTIVITY RECOVERY")
    print("=" * 50)
    
    # Step 1: Check if MySQL is running locally
    print("\n1. CHECKING LOCAL MYSQL STATUS:")
    print("-" * 40)
    
    try:
        # Check if MySQL service is running on Windows
        result = subprocess.run([
            'sc', 'query', 'MySQL80'
        ], capture_output=True, text=True, timeout=10)
        
        if 'RUNNING' in result.stdout:
            print("✅ MySQL service is running locally")
        else:
            print("❌ MySQL service not running locally")
            print("💡 Starting MySQL service...")
            
            # Try to start MySQL service
            try:
                start_result = subprocess.run([
                    'net', 'start', 'MySQL80'
                ], capture_output=True, text=True, timeout=30)
                
                if start_result.returncode == 0:
                    print("✅ MySQL service started successfully")
                else:
                    print(f"❌ Failed to start MySQL: {start_result.stderr}")
                    
            except Exception as e:
                print(f"❌ Error starting MySQL: {e}")
                
    except Exception as e:
        print(f"❌ Cannot check MySQL service status: {e}")
    
    # Step 2: Test database connectivity from a pod
    print("\n2. TESTING DATABASE CONNECTIVITY FROM KUBERNETES:")
    print("-" * 40)
    
    try:
        # Get a running pod to test from
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '--field-selector=status.phase=Running', '-o', 'name'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            pods = result.stdout.strip().split('\n')
            if pods and pods[0]:
                test_pod = pods[0].replace('pod/', '')
                print(f"Testing from pod: {test_pod}")
                
                # Test MySQL connectivity
                test_result = subprocess.run([
                    'kubectl', 'exec', test_pod, '-n', 'crypto-collectors', '--',
                    'nc', '-zv', 'host.docker.internal', '3306'
                ], capture_output=True, text=True, timeout=15)
                
                if test_result.returncode == 0:
                    print("✅ Database connectivity successful from pod")
                else:
                    print("❌ Database connectivity failed from pod")
                    print("🔧 Attempting connectivity fixes...")
                    
                    # Try alternative approaches
                    print("\n   Trying to restart network components...")
                    
                    # Restart collector manager (sometimes fixes connectivity)
                    restart_result = subprocess.run([
                        'kubectl', 'rollout', 'restart', 'deployment/collector-manager',
                        '-n', 'crypto-collectors'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if restart_result.returncode == 0:
                        print("✅ Collector manager restarted")
                    else:
                        print("❌ Failed to restart collector manager")
                        
    except Exception as e:
        print(f"❌ Error testing connectivity: {e}")
    
    # Step 3: Restart all collection services to refresh connections
    print("\n3. RESTARTING ALL COLLECTION SERVICES:")
    print("-" * 40)
    
    services_to_restart = [
        'enhanced-crypto-prices',
        'crypto-news-collector', 
        'stock-news-collector',
        'technical-indicators',
        'macro-economic',
        'social-other',
        'onchain-data-collector'
    ]
    
    for service in services_to_restart:
        try:
            print(f"🔄 Restarting {service}...")
            result = subprocess.run([
                'kubectl', 'rollout', 'restart', f'deployment/{service}',
                '-n', 'crypto-collectors'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ {service} restarted successfully")
            else:
                print(f"❌ Failed to restart {service}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error restarting {service}: {e}")
    
    # Step 4: Wait for services to come back up
    print("\n4. WAITING FOR SERVICES TO STABILIZE:")
    print("-" * 40)
    
    print("⏳ Waiting 60 seconds for all services to restart and stabilize...")
    for i in range(6):
        time.sleep(10)
        print(f"   {(i+1)*10}/60 seconds...")
    
    # Step 5: Test database connectivity again
    print("\n5. VERIFYING RECOVERY:")
    print("-" * 40)
    
    try:
        # Get current collector manager pod
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '-l', 'app=collector-manager', '--field-selector=status.phase=Running',
            '-o', 'jsonpath={.items[0].metadata.name}'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            manager_pod = result.stdout.strip()
            print(f"Testing with new collector manager: {manager_pod}")
            
            # Test database connectivity again
            test_result = subprocess.run([
                'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
                'nc', '-zv', 'host.docker.internal', '3306'
            ], capture_output=True, text=True, timeout=15)
            
            if test_result.returncode == 0:
                print("✅ Database connectivity restored!")
                
                # Try a manual collection trigger
                print("🧪 Testing manual collection trigger...")
                trigger_result = subprocess.run([
                    'kubectl', 'exec', manager_pod, '-n', 'crypto-collectors', '--',
                    'curl', '-s', '-X', 'POST', 'http://localhost:8000/services/enhanced-crypto-prices/collect',
                    '-H', 'Content-Type: application/json', '-d', '{}'
                ], capture_output=True, text=True, timeout=30)
                
                if '"status":"success"' in trigger_result.stdout:
                    print("✅ Manual collection trigger successful!")
                    print("🎉 Recovery appears successful!")
                else:
                    print("❌ Manual trigger failed, may need more time")
                    
            else:
                print("❌ Database connectivity still failing")
                
    except Exception as e:
        print(f"❌ Error during verification: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 RECOVERY ACTIONS COMPLETED")
    print("=" * 50)
    print("💡 NEXT STEPS:")
    print("1. Wait 5-10 minutes for automatic scheduling to resume")
    print("2. Run: python quick_status_check.py")
    print("3. If issues persist, check MySQL service on host system")
    print("4. Restart monitoring: python simple_collection_monitor.py")

if __name__ == "__main__":
    fix_database_connectivity()