#!/usr/bin/env python3
"""
Emergency Diagnostic and Recovery Script
Comprehensive diagnosis when all services fail auto-resolution
"""

import subprocess
import mysql.connector
from datetime import datetime
import json

def emergency_diagnostic():
    """Run comprehensive emergency diagnostics"""
    
    print("🚨 EMERGENCY DIAGNOSTIC - COLLECTION SYSTEM FAILURE")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    issues_found = []
    
    # 1. Check collector manager health
    print("\n1. COLLECTOR MANAGER DIAGNOSIS:")
    print("-" * 40)
    
    try:
        # Get collector manager pod
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '-l', 'app=collector-manager', '--no-headers'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split()
                    name = parts[0]
                    ready = parts[1]
                    status = parts[2]
                    print(f"Pod: {name}")
                    print(f"Ready: {ready} | Status: {status}")
                    
                    if status != 'Running' or '1/1' not in ready:
                        issues_found.append(f"Collector manager unhealthy: {status}")
        else:
            issues_found.append("Cannot get collector manager status")
            print("❌ Cannot get collector manager pods")
            
    except Exception as e:
        issues_found.append(f"Collector manager check failed: {e}")
        print(f"❌ Error: {e}")
    
    # 2. Check collector manager logs for errors
    print("\n2. COLLECTOR MANAGER LOGS:")
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
            print(f"Checking logs for: {manager_pod}")
            
            # Get recent logs
            log_result = subprocess.run([
                'kubectl', 'logs', manager_pod, '-n', 'crypto-collectors', '--tail=10'
            ], capture_output=True, text=True, timeout=15)
            
            if log_result.returncode == 0:
                print("Recent logs:")
                print(log_result.stdout)
                
                # Check for common error patterns
                if 'error' in log_result.stdout.lower():
                    issues_found.append("Errors found in collector manager logs")
                if 'failed' in log_result.stdout.lower():
                    issues_found.append("Failures found in collector manager logs")
            else:
                issues_found.append("Cannot retrieve collector manager logs")
                
    except Exception as e:
        issues_found.append(f"Log check failed: {e}")
        print(f"❌ Error checking logs: {e}")
    
    # 3. Check database connectivity
    print("\n3. DATABASE CONNECTIVITY:")
    print("-" * 40)
    
    db_configs = [
        {'name': 'crypto_prices', 'database': 'crypto_prices'},
        {'name': 'crypto_news', 'database': 'crypto_news'}
    ]
    
    for db_config in db_configs:
        try:
            config = {
                'host': 'host.docker.internal',
                'user': 'news_collector',
                'password': '99Rules!',
                'database': db_config['database'],
                'charset': 'utf8mb4',
                'connect_timeout': 5
            }
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    print(f"✅ {db_config['name']}: Connected successfully")
                else:
                    issues_found.append(f"Database {db_config['name']} query failed")
                    print(f"❌ {db_config['name']}: Query failed")
                    
        except Exception as e:
            issues_found.append(f"Database {db_config['name']} connection failed: {e}")
            print(f"❌ {db_config['name']}: {e}")
    
    # 4. Check service endpoints directly
    print("\n4. SERVICE ENDPOINT TESTING:")
    print("-" * 40)
    
    # Test key services directly
    services_to_test = [
        ('enhanced-crypto-prices', 8001),
        ('crypto-news-collector', 8000),
        ('technical-indicators', 8000)
    ]
    
    try:
        # Get any running pod to test from
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '--field-selector=status.phase=Running', '-o', 'name'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            pods = result.stdout.strip().split('\n')
            if pods and pods[0]:
                test_pod = pods[0].replace('pod/', '')
                print(f"Testing from pod: {test_pod}")
                
                for service, port in services_to_test:
                    try:
                        test_result = subprocess.run([
                            'kubectl', 'exec', test_pod, '-n', 'crypto-collectors', '--',
                            'curl', '-s', '--max-time', '5',
                            f'http://{service}.crypto-collectors.svc.cluster.local:{port}/health'
                        ], capture_output=True, text=True, timeout=10)
                        
                        if test_result.returncode == 0 and 'healthy' in test_result.stdout:
                            print(f"✅ {service}: Responding")
                        else:
                            print(f"❌ {service}: Not responding properly")
                            issues_found.append(f"Service {service} not responding")
                            
                    except Exception as e:
                        print(f"❌ {service}: Test failed - {e}")
                        issues_found.append(f"Service {service} test failed")
                        
    except Exception as e:
        print(f"❌ Cannot test service endpoints: {e}")
        issues_found.append("Service endpoint testing failed")
    
    # 5. Check ConfigMap
    print("\n5. CONFIGMAP STATUS:")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            'kubectl', 'get', 'configmap', 'collector-manager-config',
            '-n', 'crypto-collectors', '-o', 'json'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ ConfigMap exists")
            
            # Check if it contains our fixed configuration
            config_data = json.loads(result.stdout)
            config_content = config_data.get('data', {}).get('k8s_collectors_config.json', '')
            
            if 'enhanced-crypto-prices' in config_content:
                print("✅ ConfigMap contains correct service names")
            else:
                print("❌ ConfigMap may have incorrect configuration")
                issues_found.append("ConfigMap configuration incorrect")
                
        else:
            print("❌ ConfigMap not found")
            issues_found.append("ConfigMap missing")
            
    except Exception as e:
        print(f"❌ ConfigMap check failed: {e}")
        issues_found.append("ConfigMap check failed")
    
    # Summary and recommendations
    print("\n" + "=" * 70)
    print("🔍 DIAGNOSTIC SUMMARY:")
    print("=" * 70)
    
    if not issues_found:
        print("✅ No critical issues found - this may be a timing/data issue")
        print("\n💡 RECOMMENDED ACTIONS:")
        print("1. Wait 5-10 minutes for natural data collection")
        print("2. Check if services are on different collection schedules")
        print("3. Review service logs for specific errors")
    else:
        print("❌ CRITICAL ISSUES FOUND:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 EMERGENCY RECOVERY ACTIONS:")
        
        if any('collector manager' in issue.lower() for issue in issues_found):
            print("1. RESTART COLLECTOR MANAGER:")
            print("   kubectl rollout restart deployment/collector-manager -n crypto-collectors")
        
        if any('database' in issue.lower() for issue in issues_found):
            print("2. CHECK DATABASE STATUS:")
            print("   - Verify MySQL is running on host.docker.internal:3306")
            print("   - Check database credentials and connectivity")
        
        if any('configmap' in issue.lower() for issue in issues_found):
            print("3. REAPPLY CONFIGURATION:")
            print("   kubectl apply -f collector-manager-configmap.yaml")
            print("   kubectl rollout restart deployment/collector-manager -n crypto-collectors")
        
        if any('service' in issue.lower() for issue in issues_found):
            print("4. RESTART ALL COLLECTION SERVICES:")
            print("   kubectl rollout restart deployment/enhanced-crypto-prices -n crypto-collectors")
            print("   kubectl rollout restart deployment/crypto-news-collector -n crypto-collectors")
            print("   kubectl rollout restart deployment/technical-indicators -n crypto-collectors")
    
    return issues_found

if __name__ == "__main__":
    emergency_diagnostic()