#!/usr/bin/env python3
"""
Fix collector manager configuration to use correct service names and ports
"""

import json
import subprocess
import sys
from datetime import datetime

def get_current_config():
    """Get current collector configuration from the running pod"""
    try:
        result = subprocess.run([
            'kubectl', 'exec', '-it', 'collector-manager-746b9798f6-bq88f', 
            '-n', 'crypto-collectors', '--', 
            'cat', '/app/k8s_collectors_config.json'
        ], capture_output=True, text=True, check=True)
        
        # Clean up any terminal formatting
        config_text = result.stdout.strip()
        if 'k8s_collectors_config.json' in config_text:
            config_text = config_text.split('\n', 1)[1]
        
        return json.loads(config_text)
    except Exception as e:
        print(f"Error getting current config: {e}")
        return None

def fix_configuration():
    """Fix the collector configuration with correct service names and ports"""
    
    print("🔧 Fixing collector manager configuration...")
    
    # Get current config
    config = get_current_config()
    if not config:
        print("❌ Failed to get current configuration")
        return False
    
    print(f"📋 Current config has {len(config['services'])} services")
    
    # Service corrections needed
    corrections = {
        'crypto-prices': {
            'name': 'enhanced-crypto-prices',
            'url': 'http://enhanced-crypto-prices.crypto-collectors.svc.cluster.local:8001',
            'port': 8001
        }
    }
    
    # Apply corrections
    for service in config['services']:
        service_name = service['name']
        if service_name in corrections:
            correction = corrections[service_name]
            print(f"🔄 Fixing {service_name} → {correction['name']} (port {correction['port']})")
            service['name'] = correction['name']
            service['url'] = correction['url']
            service['port'] = correction['port']
    
    # Disable the crashing realtime-materialized-updater for now
    for service in config['services']:
        if service['name'] == 'realtime-materialized-updater':
            print(f"⏸️  Disabling realtime-materialized-updater (crashing)")
            service['enabled'] = False
    
    # Write corrected config to file
    corrected_config_file = 'corrected_k8s_collectors_config.json'
    with open(corrected_config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"💾 Corrected config saved to {corrected_config_file}")
    
    # Copy corrected config to the collector manager pod
    try:
        print("📤 Uploading corrected config to collector manager...")
        
        # Copy file to pod
        subprocess.run([
            'kubectl', 'cp', corrected_config_file,
            'crypto-collectors/collector-manager-746b9798f6-bq88f:/app/k8s_collectors_config.json'
        ], check=True)
        
        print("✅ Configuration uploaded successfully")
        
        # Restart collector manager to pick up new config
        print("🔄 Restarting collector manager...")
        subprocess.run([
            'kubectl', 'rollout', 'restart', 'deployment/collector-manager',
            '-n', 'crypto-collectors'
        ], check=True)
        
        print("✅ Collector manager restart initiated")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def test_services():
    """Test that key services are responding on correct endpoints"""
    
    print("\n🧪 Testing service endpoints...")
    
    services_to_test = [
        ('enhanced-crypto-prices', 'http://enhanced-crypto-prices.crypto-collectors.svc.cluster.local:8001/health'),
        ('crypto-news-collector', 'http://crypto-news-collector.crypto-collectors.svc.cluster.local:8000/health'),
        ('stock-news-collector', 'http://stock-news-collector.crypto-collectors.svc.cluster.local:8000/health'),
        ('onchain-data-collector', 'http://onchain-data-collector.crypto-collectors.svc.cluster.local:8000/health'),
        ('technical-indicators', 'http://technical-indicators.crypto-collectors.svc.cluster.local:8000/health'),
        ('macro-economic', 'http://macro-economic.crypto-collectors.svc.cluster.local:8000/health'),
    ]
    
    for service_name, url in services_to_test:
        try:
            result = subprocess.run([
                'kubectl', 'exec', '-it', 'collector-manager-746b9798f6-bq88f',
                '-n', 'crypto-collectors', '--',
                'curl', '-s', '--max-time', '5', url
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and 'healthy' in result.stdout:
                print(f"✅ {service_name}: Healthy")
            else:
                print(f"❌ {service_name}: Not responding properly")
                
        except Exception as e:
            print(f"❌ {service_name}: Error testing - {e}")

if __name__ == "__main__":
    print("🚀 Collector Configuration Fix Tool")
    print("=" * 50)
    
    # Fix configuration
    if fix_configuration():
        print("\n⏳ Waiting for collector manager to restart...")
        import time
        time.sleep(10)
        
        # Test services
        test_services()
        
        print("\n✅ Configuration fix completed!")
        print("📊 The collector manager should now:")
        print("   • Connect to enhanced-crypto-prices on port 8001")
        print("   • Skip the crashing realtime-materialized-updater")
        print("   • Schedule all other collectors properly")
        
    else:
        print("❌ Configuration fix failed")
        sys.exit(1)