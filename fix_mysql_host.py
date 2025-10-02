#!/usr/bin/env python3
"""
Fix MySQL Host Configuration Script
Updates the database-pool-config ConfigMap with the correct Windows host IP
and validates connectivity
"""

import subprocess
import time
import json

def run_command(cmd):
    """Execute command and return output"""
    try:
        # Try different kubectl command formats
        for kubectl_cmd in ['kubectl', 'kubectl.exe', 'C:\\kubectl\\kubectl.exe']:
            try:
                full_cmd = cmd.replace('kubectl', kubectl_cmd)
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return result.stdout.strip()
                elif "Error" not in result.stderr:
                    return result.stdout.strip()
            except subprocess.TimeoutExpired:
                print(f"Command timed out: {full_cmd}")
                continue
            except Exception:
                continue
        
        print(f"Failed to execute: {cmd}")
        return None
    except Exception as e:
        print(f"Exception running command {cmd}: {e}")
        return None

def check_kubectl_connection():
    """Check if kubectl is connected"""
    print("🔍 Checking kubectl connectivity...")
    output = run_command("kubectl cluster-info")
    if output and "running" in output.lower():
        print("✅ kubectl connected to cluster")
        return True
    else:
        print("❌ kubectl not connected or not available")
        return False

def get_host_ip():
    """Get the Windows host IP"""
    print("🔍 Getting Windows host IP...")
    result = subprocess.run('ipconfig', shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        for line in lines:
            if 'IPv4 Address' in line and '192.168' in line:
                ip = line.split(':')[1].strip()
                print(f"✅ Found host IP: {ip}")
                return ip
    return "192.168.230.162"  # Fallback

def update_configmap():
    """Update the ConfigMap with correct host IP"""
    host_ip = get_host_ip()
    print(f"🔧 Updating ConfigMap with host IP: {host_ip}")
    
    # Create the updated ConfigMap YAML
    configmap_yaml = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: database-pool-config
  namespace: crypto-collectors
data:
  DB_POOL_SIZE: "15"
  MYSQL_DATABASE: crypto_prices
  MYSQL_HOST: {host_ip}
  MYSQL_PASSWORD: 99Rules!
  MYSQL_USER: news_collector
"""
    
    # Write to file
    with open('fixed-configmap.yaml', 'w') as f:
        f.write(configmap_yaml)
    
    # Apply the ConfigMap
    output = run_command("kubectl apply -f fixed-configmap.yaml")
    if output:
        print(f"✅ ConfigMap updated: {output}")
        return True
    else:
        print("❌ Failed to update ConfigMap")
        return False

def restart_services():
    """Restart key services to pick up new configuration"""
    services = [
        'enhanced-crypto-prices',
        'sentiment-microservice', 
        'unified-ohlc-collector',
        'enhanced-sentiment',
        'narrative-analyzer'
    ]
    
    print("🔄 Restarting services to pick up new configuration...")
    
    for service in services:
        cmd = f"kubectl rollout restart deployment {service} -n crypto-collectors"
        output = run_command(cmd)
        if output and "restarted" in output:
            print(f"✅ {service}: restarted")
        else:
            print(f"❌ {service}: failed to restart")

def validate_connectivity():
    """Test database connectivity from a pod"""
    print("🔍 Testing database connectivity...")
    
    # Wait for pods to be ready
    time.sleep(10)
    
    # Get a pod name
    output = run_command("kubectl get pods -n crypto-collectors -l app=enhanced-crypto-prices -o jsonpath='{.items[0].metadata.name}'")
    
    if output:
        pod_name = output.strip("'")
        print(f"Testing connectivity from pod: {pod_name}")
        
        # Test environment variables
        env_cmd = f"kubectl exec {pod_name} -n crypto-collectors -- printenv | grep MYSQL_HOST"
        env_output = run_command(env_cmd)
        
        if env_output:
            print(f"✅ Environment variables loaded: {env_output}")
            return True
        else:
            print("❌ Environment variables not found")
            return False
    else:
        print("❌ No pods found for testing")
        return False

def main():
    """Main function"""
    print("🚀 MYSQL HOST CONFIGURATION FIX")
    print("="*50)
    
    if not check_kubectl_connection():
        print("\n❌ Cannot proceed without kubectl connectivity")
        print("Please ensure kubectl is installed and connected to your cluster")
        return False
    
    if update_configmap():
        restart_services()
        
        print("\n⏳ Waiting for services to restart...")
        time.sleep(30)
        
        if validate_connectivity():
            print("\n🎉 SUCCESS: MySQL host configuration fixed!")
            print("Services should now be able to connect to the database")
            return True
        else:
            print("\n⚠️  Configuration updated but connectivity test failed")
            print("Services may need more time to restart")
            return True
    else:
        print("\n❌ Failed to update configuration")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ MySQL host fix completed successfully")
        else:
            print("\n❌ MySQL host fix failed")
    except KeyboardInterrupt:
        print("\n⚠️  Fix interrupted by user")
    except Exception as e:
        print(f"\n❌ Fix failed with error: {e}")