#!/usr/bin/env python3
"""
Test OHLC Collector Endpoints
Try to trigger collection or get more information from the collector
"""

import subprocess
import json

def test_collector_endpoints():
    """Test various endpoints on the unified-ohlc-collector"""
    
    print("🔍 TESTING OHLC COLLECTOR ENDPOINTS")
    print("=" * 45)
    
    pod_name = "unified-ohlc-collector-65596d6885-87dvw"
    
    endpoints_to_test = [
        "/health",
        "/status", 
        "/collect",
        "/trigger",
        "/start",
        "/run",
        "/ohlc",
        "/api/collect",
        "/api/ohlc",
        "/docs"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        print(f"\n🌐 Testing: {endpoint}")
        
        cmd = f'''kubectl exec {pod_name} -n crypto-collectors -- python -c "
import urllib.request
import json
try:
    response = urllib.request.urlopen('http://localhost:8010{endpoint}')
    data = response.read().decode()
    try:
        parsed = json.loads(data)
        print('JSON Response:', parsed)
    except:
        print('Text Response:', data[:200])
    print('STATUS: SUCCESS')
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
except Exception as e:
    print('Error:', str(e))
"'''
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if 'SUCCESS' in output:
                    working_endpoints.append(endpoint)
                    print(f"   ✅ WORKING")
                    if 'Response:' in output:
                        print(f"   📄 {output}")
                else:
                    print(f"   ❌ Failed: {output}")
            else:
                print(f"   ❌ Command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 SUMMARY:")
    print(f"Working endpoints: {len(working_endpoints)}")
    for endpoint in working_endpoints:
        print(f"   ✅ {endpoint}")
    
    return working_endpoints

def trigger_collection_if_possible():
    """Try to trigger collection using any working endpoints"""
    
    print(f"\n🚀 ATTEMPTING TO TRIGGER COLLECTION")
    print("-" * 40)
    
    pod_name = "unified-ohlc-collector-65596d6885-87dvw"
    
    # Try different HTTP methods on potential trigger endpoints
    trigger_attempts = [
        ("/collect", "POST"),
        ("/trigger", "POST"),
        ("/start", "POST"),
        ("/collect", "GET"),
        ("/api/collect", "POST")
    ]
    
    for endpoint, method in trigger_attempts:
        print(f"\n🎯 Trying {method} {endpoint}")
        
        if method == "POST":
            cmd = f'''kubectl exec {pod_name} -n crypto-collectors -- python -c "
import urllib.request
import json
try:
    req = urllib.request.Request('http://localhost:8010{endpoint}', method='POST')
    response = urllib.request.urlopen(req)
    data = response.read().decode()
    print('Response:', data)
    print('SUCCESS')
except Exception as e:
    print('Error:', str(e))
"'''
        else:
            cmd = f'''kubectl exec {pod_name} -n crypto-collectors -- python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8010{endpoint}')
    data = response.read().decode()
    print('Response:', data)
    print('SUCCESS')
except Exception as e:
    print('Error:', str(e))
"'''
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and 'SUCCESS' in result.stdout:
                print(f"   ✅ {method} {endpoint} worked!")
                print(f"   📄 {result.stdout}")
                return True
            else:
                print(f"   ❌ Failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n⚠️  No trigger endpoints found")
    return False

if __name__ == "__main__":
    working_endpoints = test_collector_endpoints()
    
    if working_endpoints:
        triggered = trigger_collection_if_possible()
        
        if triggered:
            print(f"\n🎉 Collection may have been triggered!")
            print("🔄 Check database for new records")
        else:
            print(f"\n🤔 Collector is healthy but may be on internal schedule")
            print("⏰ Continue monitoring for automatic collection")
    else:
        print(f"\n❌ No working endpoints found")
        print("🔧 Collector may need different configuration")