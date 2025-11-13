#!/usr/bin/env python3
"""
Collector Service Manager
Starts and manages crypto data collectors as background services
Alternative to K8s when cluster is not available
"""

import subprocess
import time
import os
import sys
import signal
from pathlib import Path

def find_running_collectors():
    """Find any running collector processes"""
    try:
        # Check for running Python processes with collector scripts
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        collectors = {}
        for line in lines:
            if 'python' in line and 'collector' in line:
                if 'macro_collector.py' in line:
                    pid = line.split()[1]
                    collectors['macro'] = pid
                elif 'onchain_collector.py' in line:
                    pid = line.split()[1]
                    collectors['onchain'] = pid
                    
        return collectors
    except:
        return {}

def start_collector(name, script_path, log_path):
    """Start a collector as background process"""
    try:
        print(f"🚀 Starting {name} collector...")
        
        # Ensure the script exists
        if not os.path.exists(script_path):
            print(f"❌ Script not found: {script_path}")
            return None
            
        # Start the process
        with open(log_path, 'w') as log_file:
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=log_file, stderr=subprocess.STDOUT, 
               preexec_fn=os.setsid)  # Create new process group
            
        print(f"   ✅ Started with PID: {process.pid}")
        print(f"   📄 Logs: {log_path}")
        return process.pid
        
    except Exception as e:
        print(f"   ❌ Failed to start {name}: {e}")
        return None

def stop_collector(name, pid):
    """Stop a collector process"""
    try:
        print(f"🛑 Stopping {name} collector (PID: {pid})...")
        os.killpg(int(pid), signal.SIGTERM)
        time.sleep(2)
        print(f"   ✅ Stopped {name}")
        return True
    except:
        print(f"   ⚠️  Could not stop {name} (PID: {pid})")
        return False

def main():
    print("🔧 CRYPTO DATA COLLECTOR SERVICE MANAGER")
    print("=" * 50)
    
    # Get the repository root
    repo_root = Path(__file__).parent.absolute()
    os.chdir(repo_root)
    
    # Define collector configurations
    collectors = {
        'macro': {
            'script': 'services/macro-collection/macro_collector.py',
            'log': '/tmp/macro_collector.log',
            'description': 'Macro Economic Indicators (every 1 hour)'
        },
        'onchain': {
            'script': 'services/onchain-collection/onchain_collector.py', 
            'log': '/tmp/onchain_collector.log',
            'description': 'Blockchain Metrics (every 6 hours)'
        }
    }
    
    # Check what's currently running
    running = find_running_collectors()
    print(f"📊 Current Status:")
    
    for name, config in collectors.items():
        if name in running:
            print(f"   {name:8}: 🟢 RUNNING (PID: {running[name]})")
        else:
            print(f"   {name:8}: 🔴 STOPPED")
    
    print()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            print("🚀 STARTING COLLECTORS...")
            for name, config in collectors.items():
                if name not in running:
                    pid = start_collector(name, config['script'], config['log'])
                    if pid:
                        time.sleep(1)  # Stagger starts
                else:
                    print(f"⚠️  {name} already running (PID: {running[name]})")
                    
        elif command == 'stop':
            print("🛑 STOPPING COLLECTORS...")
            for name in running:
                stop_collector(name, running[name])
                
        elif command == 'restart':
            print("🔄 RESTARTING COLLECTORS...")
            # Stop first
            for name in running:
                stop_collector(name, running[name])
            time.sleep(2)
            # Start all
            for name, config in collectors.items():
                pid = start_collector(name, config['script'], config['log'])
                if pid:
                    time.sleep(1)
                    
        elif command == 'status':
            print("📋 DETAILED STATUS:")
            running = find_running_collectors()
            for name, config in collectors.items():
                print(f"\n{name.upper()} COLLECTOR:")
                print(f"   Description: {config['description']}")
                print(f"   Script: {config['script']}")
                print(f"   Log: {config['log']}")
                if name in running:
                    print(f"   Status: 🟢 RUNNING (PID: {running[name]})")
                    # Show recent log lines
                    try:
                        with open(config['log'], 'r') as f:
                            lines = f.readlines()[-3:]
                            if lines:
                                print("   Recent logs:")
                                for line in lines:
                                    print(f"     {line.strip()}")
                    except:
                        pass
                else:
                    print(f"   Status: 🔴 STOPPED")
                    
        else:
            print(f"❌ Unknown command: {command}")
            
    else:
        print("📋 USAGE:")
        print("   python collector_manager.py start    # Start all stopped collectors")
        print("   python collector_manager.py stop     # Stop all running collectors") 
        print("   python collector_manager.py restart  # Restart all collectors")
        print("   python collector_manager.py status   # Show detailed status")
        print()
        print("📊 COLLECTOR SCHEDULES:")
        for name, config in collectors.items():
            print(f"   {name:8}: {config['description']}")
        print()
        print("📄 LOG FILES:")
        for name, config in collectors.items():
            print(f"   {name:8}: tail -f {config['log']}")

if __name__ == "__main__":
    main()