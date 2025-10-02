#!/usr/bin/env python3
"""
Fix RSS Feed User-Agent and Database Connectivity Issues
"""

import subprocess
import json
import time
from datetime import datetime

def patch_news_collectors():
    """Patch news collectors with better User-Agent headers and retry logic"""
    
    print("🔧 Fixing RSS Feed and Database Issues")
    print("=" * 50)
    
    # News collector patches
    patches = [
        {
            "name": "crypto-news-collector",
            "deployment": "crypto-news-collector",
            "env_patches": [
                {"name": "USER_AGENT", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"},
                {"name": "REQUEST_DELAY", "value": "2"},
                {"name": "RETRY_ATTEMPTS", "value": "3"},
                {"name": "RSS_TIMEOUT", "value": "30"},
                {"name": "DATABASE_RETRY_ATTEMPTS", "value": "5"},
                {"name": "DATABASE_RETRY_DELAY", "value": "2"}
            ]
        },
        {
            "name": "stock-news-collector", 
            "deployment": "stock-news-collector",
            "env_patches": [
                {"name": "USER_AGENT", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"},
                {"name": "REQUEST_DELAY", "value": "3"},
                {"name": "RETRY_ATTEMPTS", "value": "3"},
                {"name": "RSS_TIMEOUT", "value": "30"},
                {"name": "DATABASE_RETRY_ATTEMPTS", "value": "5"},
                {"name": "DATABASE_RETRY_DELAY", "value": "2"}
            ]
        }
    ]
    
    for patch in patches:
        print(f"\n🔄 Patching {patch['name']}...")
        
        # Create environment patch
        env_patch = []
        for env_var in patch['env_patches']:
            env_patch.append({
                "name": env_var["name"],
                "value": env_var["value"]
            })
        
        # Build the patch command
        patch_json = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": patch['name'],
                            "env": env_patch
                        }]
                    }
                }
            }
        }
        
        # Write patch to file
        patch_file = f"{patch['name']}-fix-patch.json"
        with open(patch_file, 'w') as f:
            json.dump(patch_json, f, indent=2)
        
        try:
            # Apply the patch
            result = subprocess.run([
                'kubectl', 'patch', 'deployment', patch['deployment'],
                '-n', 'crypto-collectors',
                '--type', 'strategic',
                '--patch-file', patch_file
            ], capture_output=True, text=True, check=True)
            
            print(f"✅ Patched {patch['name']} successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to patch {patch['name']}: {e}")
            print(f"Error output: {e.stderr}")

def fix_database_connectivity():
    """Fix database connectivity issues"""
    
    print("\n🔌 Fixing Database Connectivity...")
    
    # Restart MySQL-dependent services to refresh connections
    services_to_restart = [
        "technical-indicators",
        "macro-economic", 
        "social-other",
        "crypto-sentiment-collector",
        "stock-sentiment-collector"
    ]
    
    for service in services_to_restart:
        try:
            print(f"🔄 Restarting {service}...")
            subprocess.run([
                'kubectl', 'rollout', 'restart', f'deployment/{service}',
                '-n', 'crypto-collectors'
            ], check=True)
            print(f"✅ Restarted {service}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to restart {service}: {e}")

def wait_for_collections():
    """Wait for collections to start working"""
    
    print("\n⏳ Waiting for collectors to start working...")
    
    # Wait 3 minutes for services to restart and begin collection
    for i in range(18):  # 18 * 10 seconds = 3 minutes
        time.sleep(10)
        print(f"   Waiting... {(i+1)*10}/180 seconds")

def test_collections():
    """Test collections through collector manager"""
    
    print("\n🧪 Testing Collections...")
    
    # Get the current collector manager pod
    try:
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '-l', 'app=collector-manager',
            '-o', 'jsonpath={.items[0].metadata.name}'
        ], capture_output=True, text=True, check=True)
        
        collector_manager_pod = result.stdout.strip()
        print(f"📋 Using collector manager pod: {collector_manager_pod}")
        
        # Test collections
        test_services = [
            "enhanced-crypto-prices",
            "crypto-news-collector", 
            "stock-news-collector",
            "technical-indicators",
            "macro-economic",
            "social-other"
        ]
        
        successful_tests = 0
        for service in test_services:
            try:
                print(f"   Testing {service}...")
                result = subprocess.run([
                    'kubectl', 'exec', '-it', collector_manager_pod,
                    '-n', 'crypto-collectors', '--',
                    'curl', '-s', '-X', 'POST',
                    f'http://localhost:8000/services/{service}/collect',
                    '-H', 'Content-Type: application/json',
                    '-d', '{}'
                ], capture_output=True, text=True, timeout=30)
                
                if '"status":"success"' in result.stdout:
                    print(f"   ✅ {service}: Working")
                    successful_tests += 1
                else:
                    print(f"   ❌ {service}: Failed")
                    
            except Exception as e:
                print(f"   ❌ {service}: Error - {e}")
        
        print(f"\n📊 Test Results: {successful_tests}/{len(test_services)} services working")
        return successful_tests
        
    except Exception as e:
        print(f"❌ Failed to test collections: {e}")
        return 0

if __name__ == "__main__":
    print("🚀 RSS Feed and Database Connectivity Fix")
    print("=" * 60)
    
    # Fix RSS feeds
    patch_news_collectors()
    
    # Fix database connectivity
    fix_database_connectivity()
    
    # Wait for changes to take effect
    wait_for_collections()
    
    # Test the fixes
    working_services = test_collections()
    
    print(f"\n{'='*60}")
    if working_services >= 4:
        print("✅ Collection system fixes successful!")
        print("📊 Most collectors should now be working properly")
    else:
        print("⚠️  Collection system partially fixed")
        print("📊 Some services may need additional troubleshooting")
    
    print("\n📋 Next Steps:")
    print("   1. Run comprehensive audit in 10 minutes to verify fixes")
    print("   2. Monitor automatic scheduling for next 30 minutes") 
    print("   3. Check data collection rates return to normal")