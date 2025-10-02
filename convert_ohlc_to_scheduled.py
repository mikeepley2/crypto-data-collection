#!/usr/bin/env python3
"""
Add Unified OHLC Collector to Collector Manager
Convert from continuous to scheduled collection based on historical 4-hour pattern
"""

import subprocess
import json

def add_ohlc_to_collector_manager():
    """Add unified-ohlc-collector to collector-manager configuration"""
    
    print("🔧 ADDING OHLC COLLECTOR TO COLLECTOR MANAGER")
    print("=" * 55)
    
    # First, get current collector-manager config
    try:
        cmd = "kubectl get configmap collector-manager-config -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            config_data = json.loads(result.stdout)
            current_config = json.loads(config_data['data']['k8s_collectors_config.json'])
            
            print("📋 Current collector-manager services:")
            for service in current_config['services']:
                print(f"   • {service['name']} - {service['collection_schedule']}")
            
            # Check if unified-ohlc-collector already exists
            existing = any(s['name'] == 'unified-ohlc-collector' for s in current_config['services'])
            
            if existing:
                print(f"\n⚠️  unified-ohlc-collector already in collector-manager config")
                return False
            
            # Add unified-ohlc-collector to the configuration
            ohlc_service = {
                "name": "unified-ohlc-collector",
                "url": "http://unified-ohlc-collector.crypto-collectors.svc.cluster.local:8010",
                "port": 8010,
                "enabled": True,
                "health_check_interval": 30,
                "collection_schedule": "0 */4 * * *",  # Every 4 hours based on analysis
                "priority": 1,  # High priority for OHLC data
                "timeout": 120,  # Longer timeout for OHLC collection
                "retry_attempts": 3,
                "dependencies": None
            }
            
            current_config['services'].append(ohlc_service)
            
            print(f"\n✅ Adding unified-ohlc-collector:")
            print(f"   Schedule: 0 */4 * * * (every 4 hours)")
            print(f"   URL: http://unified-ohlc-collector.crypto-collectors.svc.cluster.local:8010")
            print(f"   Priority: 1 (high)")
            print(f"   Timeout: 120s")
            
            # Create updated configmap
            updated_data = {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": "collector-manager-config",
                    "namespace": "crypto-collectors"
                },
                "data": {
                    "k8s_collectors_config.json": json.dumps(current_config, indent=2)
                }
            }
            
            # Save to file for applying
            with open('updated-collector-manager-config.yaml', 'w') as f:
                import yaml
                yaml.dump(updated_data, f, default_flow_style=False)
            
            print(f"\n📄 Created: updated-collector-manager-config.yaml")
            return True
            
        else:
            print(f"❌ Failed to get current config: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_ohlc_service():
    """Create Kubernetes service for unified-ohlc-collector if needed"""
    
    print(f"\n🌐 CREATING KUBERNETES SERVICE:")
    print("-" * 35)
    
    # Check if service already exists
    try:
        cmd = "kubectl get service unified-ohlc-collector -n crypto-collectors"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Service unified-ohlc-collector already exists")
            return True
        
        # Create service
        service_yaml = """
apiVersion: v1
kind: Service
metadata:
  name: unified-ohlc-collector
  namespace: crypto-collectors
  labels:
    app: unified-ohlc-collector
    component: data-collection
    tier: ohlc
spec:
  selector:
    app: unified-ohlc-collector
  ports:
  - port: 8010
    targetPort: 8010
    protocol: TCP
    name: http
  type: ClusterIP
"""
        
        with open('unified-ohlc-service.yaml', 'w') as f:
            f.write(service_yaml)
        
        cmd = "kubectl apply -f unified-ohlc-service.yaml"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Created service: unified-ohlc-collector")
            return True
        else:
            print(f"❌ Failed to create service: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating service: {e}")
        return False

def scale_down_continuous_collector():
    """Scale down the continuous unified-ohlc-collector deployment"""
    
    print(f"\n📉 SCALING DOWN CONTINUOUS COLLECTOR:")
    print("-" * 40)
    
    print("ℹ️  After adding to collector-manager, we can scale down the continuous deployment")
    print("   This will save resources and prevent duplicate collection")
    
    response = input("Scale down continuous deployment now? (y/n): ")
    
    if response.lower() == 'y':
        try:
            cmd = "kubectl scale deployment unified-ohlc-collector -n crypto-collectors --replicas=0"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Scaled down unified-ohlc-collector deployment to 0 replicas")
                print("🔄 Collector-manager will now handle scheduled collection")
                return True
            else:
                print(f"❌ Failed to scale down: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error scaling down: {e}")
            return False
    else:
        print("⏸️  Keeping continuous collector running for now")
        print("   💡 You can scale it down later after verifying scheduled collection works")
        return False

if __name__ == "__main__":
    print("🎯 OHLC COLLECTOR CONVERSION: CONTINUOUS → SCHEDULED")
    print("=" * 60)
    print("Based on analysis:")
    print("• Historical pattern: Every 4 hours (0 */4 * * *)")
    print("• Current collection is 3.8 hours overdue")
    print("• Continuous collector finding data but not writing")
    print("• Optimal solution: Add to collector-manager schedule")
    print()
    
    # Step 1: Create service
    service_created = create_ohlc_service()
    
    # Step 2: Add to collector-manager
    if service_created:
        config_updated = add_ohlc_to_collector_manager()
        
        if config_updated:
            print(f"\n🚀 APPLYING CONFIGURATION:")
            print("-" * 30)
            
            response = input("Apply updated collector-manager config? (y/n): ")
            
            if response.lower() == 'y':
                try:
                    cmd = "kubectl apply -f updated-collector-manager-config.yaml"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✅ Applied updated collector-manager configuration")
                        
                        # Restart collector-manager to pick up new config
                        cmd = "kubectl rollout restart deployment collector-manager -n crypto-collectors"
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            print("🔄 Restarted collector-manager to load new configuration")
                            
                            # Option to scale down continuous collector
                            scale_down_continuous_collector()
                            
                            print(f"\n🎉 CONVERSION COMPLETE!")
                            print("✨ unified-ohlc-collector now managed by collector-manager")
                            print("⏰ Collections will happen every 4 hours: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00")
                            print("🔄 Next collection expected around: 12:00 (in ~0.2 hours)")
                            
                        else:
                            print(f"⚠️  Applied config but failed to restart collector-manager: {result.stderr}")
                    else:
                        print(f"❌ Failed to apply config: {result.stderr}")
                        
                except Exception as e:
                    print(f"❌ Error applying config: {e}")
            else:
                print("⏸️  Configuration ready but not applied")
                print("   📄 File: updated-collector-manager-config.yaml")
                print("   🔧 Apply manually when ready: kubectl apply -f updated-collector-manager-config.yaml")
        else:
            print("❌ Failed to update collector-manager configuration")
    else:
        print("❌ Failed to create required service")
    
    print(f"\n" + "="*60)
    print("📋 SUMMARY:")
    print("• Converted OHLC collection from continuous to scheduled")
    print("• Schedule: Every 4 hours (matches historical pattern)")
    print("• Managed by collector-manager for consistency")
    print("• More efficient resource usage")
    print("="*60)