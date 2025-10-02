#!/usr/bin/env python3
"""
Quick Setup and Launch Script for Continuous Collection Monitor
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing required dependencies...")
    
    packages = [
        'mysql-connector-python',
        'asyncio'
    ]
    
    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"⚠️  {package} might already be installed")

def check_kubectl():
    """Verify kubectl is available"""
    try:
        subprocess.run(['kubectl', 'version', '--client'], 
                      check=True, capture_output=True)
        print("✅ kubectl is available")
        return True
    except subprocess.CalledProcessError:
        print("❌ kubectl not found - please ensure it's installed and in PATH")
        return False

def main():
    print("🚀 CONTINUOUS COLLECTION MONITOR - SETUP")
    print("=" * 50)
    
    # Check prerequisites
    if not check_kubectl():
        return
    
    # Install dependencies
    install_dependencies()
    
    print("\n🎯 Starting Continuous Collection Monitor...")
    print("=" * 50)
    
    # Launch monitor
    try:
        subprocess.run([sys.executable, 'continuous_collection_monitor.py'])
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()