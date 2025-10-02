#!/usr/bin/env python3
"""
Kubernetes Collection Diagnostic - Test services through kubectl port-forward
"""
import subprocess
import requests
import json
import time
import pymysql
from datetime import datetime, timedelta
import threading
import signal
import sys

class PortForwardManager:
    def __init__(self):
        self.processes = []
        self.ports = {}
        
    def setup_port_forward(self, service, namespace, local_port, remote_port):
        """Set up port forwarding for a service"""
        try:
            cmd = [
                "kubectl", "port-forward", 
                f"service/{service}", 
                f"{local_port}:{remote_port}",
                "-n", namespace
            ]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self.processes.append(process)
            self.ports[service] = local_port
            
            # Give it a moment to establish
            time.sleep(2)
            return process
            
        except Exception as e:
            print(f"❌ Failed to set up port forward for {service}: {e}")
            return None
    
    def cleanup(self):
        """Clean up all port forwards"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass

def test_direct_kubernetes_access():
    """Test services directly through kubectl exec"""
    print("\n🔍 TESTING DIRECT KUBERNETES ACCESS:")
    print("-" * 50)
    
    services = [
        ("enhanced-crypto-prices", "enhanced-crypto-prices"),
        ("crypto-news-collector", "crypto-news-collector"),
        ("technical-indicators", "technical-indicators"),
        ("collector-manager", "collector-manager")
    ]
    
    for service_name, pod_prefix in services:
        try:
            print(f"\n🎯 Testing {service_name}...")
            
            # Get pod name
            cmd = ["kubectl", "get", "pods", "-n", "crypto-collectors", 
                   "--selector", f"app={service_name}", "-o", "name"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"  ❌ Failed to find pod: {result.stderr}")
                continue
                
            pod_names = result.stdout.strip().split('\n')
            if not pod_names or not pod_names[0]:
                print(f"  ❌ No running pods found")
                continue
                
            pod_name = pod_names[0].replace('pod/', '')
            print(f"  📦 Found pod: {pod_name}")
            
            # Test health endpoint
            health_cmd = [
                "kubectl", "exec", pod_name, "-n", "crypto-collectors", "--",
                "curl", "-s", "http://localhost:8000/health"
            ]
            
            health_result = subprocess.run(health_cmd, capture_output=True, text=True, timeout=10)
            if health_result.returncode == 0:
                print(f"  ✅ Health check: {health_result.stdout}")
            else:
                print(f"  ❌ Health check failed: {health_result.stderr}")
            
        except Exception as e:
            print(f"  ❌ Error testing {service_name}: {e}")

def test_database_from_cluster():
    """Test database access from within a cluster pod"""
    print("\n🔍 TESTING DATABASE FROM CLUSTER:")
    print("-" * 50)
    
    try:
        # Get a pod to test from
        cmd = ["kubectl", "get", "pods", "-n", "crypto-collectors", 
               "--selector", "app=enhanced-crypto-prices", "-o", "name"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print("❌ Failed to find test pod")
            return
            
        pod_names = result.stdout.strip().split('\n')
        if not pod_names or not pod_names[0]:
            print("❌ No running pods found for testing")
            return
            
        pod_name = pod_names[0].replace('pod/', '')
        print(f"📦 Testing from pod: {pod_name}")
        
        # Test database connection
        db_test_cmd = [
            "kubectl", "exec", pod_name, "-n", "crypto-collectors", "--",
            "python3", "-c", """
import pymysql
import os
from datetime import datetime, timedelta

try:
    connection = pymysql.connect(
        host=os.getenv('DB_HOST', 'host.docker.internal'),
        port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'rootpassword'),
        database='crypto_prices',
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM crypto_prices WHERE timestamp > %s', 
                      (datetime.now() - timedelta(hours=1),))
        recent = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM crypto_prices')
        total = cursor.fetchone()[0]
        
        print(f'DB_CONNECTION_SUCCESS: Recent={recent}, Total={total}')
    
    connection.close()
    
except Exception as e:
    print(f'DB_CONNECTION_FAILED: {e}')
"""
        ]
        
        db_result = subprocess.run(db_test_cmd, capture_output=True, text=True, timeout=30)
        if db_result.returncode == 0:
            print(f"  Database test result: {db_result.stdout}")
        else:
            print(f"  ❌ Database test failed: {db_result.stderr}")
            
    except Exception as e:
        print(f"❌ Error testing database from cluster: {e}")

def test_collection_manually():
    """Manually trigger collection from within pods"""
    print("\n🔍 MANUAL COLLECTION TEST:")
    print("-" * 50)
    
    services = ["enhanced-crypto-prices", "crypto-news-collector", "technical-indicators"]
    
    for service in services:
        try:
            print(f"\n🎯 Testing manual collection for {service}...")
            
            # Get pod name
            cmd = ["kubectl", "get", "pods", "-n", "crypto-collectors", 
                   "--selector", f"app={service}", "-o", "name"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"  ❌ Failed to find pod")
                continue
                
            pod_names = result.stdout.strip().split('\n')
            if not pod_names or not pod_names[0]:
                print(f"  ❌ No running pods found")
                continue
                
            pod_name = pod_names[0].replace('pod/', '')
            
            # Try to trigger collection
            collect_cmd = [
                "kubectl", "exec", pod_name, "-n", "crypto-collectors", "--",
                "curl", "-X", "POST", "-s", "http://localhost:8000/collect"
            ]
            
            collect_result = subprocess.run(collect_cmd, capture_output=True, text=True, timeout=60)
            if collect_result.returncode == 0:
                print(f"  ✅ Collection triggered: {collect_result.stdout[:200]}...")
            else:
                print(f"  ❌ Collection failed: {collect_result.stderr}")
                
        except Exception as e:
            print(f"  ❌ Error testing {service}: {e}")

def main():
    print("🚀 KUBERNETES COLLECTION DIAGNOSTIC")
    print("=" * 60)
    print("🎯 Testing services within Kubernetes cluster")
    print()
    
    # Test database access from cluster
    test_database_from_cluster()
    
    # Test direct kubernetes access
    test_direct_kubernetes_access()
    
    # Test manual collection
    test_collection_manually()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()