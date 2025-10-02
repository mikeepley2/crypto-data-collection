#!/usr/bin/env python3
"""
Direct LLM Integration Testing
==============================

Test the LLM integration services directly by running them as Python scripts.
This bypasses Docker/Kubernetes for direct validation.
"""

import asyncio
import subprocess
import time
import sys
import os
import signal
from pathlib import Path

class DirectTestRunner:
    def __init__(self):
        self.processes = []
        self.base_port = 8040
        
    def start_service(self, script_name: str, port: int):
        """Start a service directly using uvicorn"""
        try:
            print(f"🚀 Starting {script_name} on port {port}...")
            
            # Set environment variables
            env = os.environ.copy()
            if script_name == "llm_client":
                env["AITEST_OLLAMA_ENDPOINT"] = "http://localhost:8050"
            elif script_name == "enhanced_sentiment":
                env["LLM_CLIENT_ENDPOINT"] = "http://localhost:8040"
                env["CRYPTOBERT_ENDPOINT"] = "http://localhost:8000"
            elif script_name == "narrative_analyzer":
                env["LLM_CLIENT_ENDPOINT"] = "http://localhost:8040"
            
            # Start uvicorn process
            proc = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                f"{script_name}:app", 
                "--host", "0.0.0.0", 
                "--port", str(port),
                "--reload"
            ], env=env)
            
            self.processes.append(proc)
            time.sleep(3)  # Give it time to start
            
            # Check if process is still running
            if proc.poll() is None:
                print(f"✅ {script_name} started successfully on port {port}")
                return True
            else:
                print(f"❌ {script_name} failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting {script_name}: {e}")
            return False
    
    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
        print("✅ All services stopped")
    
    def test_health_endpoint(self, port: int, service_name: str):
        """Test a service health endpoint"""
        try:
            import requests
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {service_name} health check: {data.get('status', 'OK')}")
                return True
            else:
                print(f"❌ {service_name} health check failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {service_name} health check error: {e}")
            return False
    
    def run_basic_tests(self):
        """Run basic functionality tests"""
        print("\n🧪 Running basic functionality tests...")
        
        # Test LLM Client models endpoint
        try:
            import requests
            response = requests.get("http://localhost:8040/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ LLM Models available: {list(data.get('configured', {}).keys())}")
            else:
                print(f"❌ Models endpoint failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Models endpoint error: {e}")
        
        # Test sentiment enhancement
        try:
            test_data = {
                "text": "Bitcoin is showing strong bullish momentum with institutional adoption!",
                "original_score": 0.8
            }
            response = requests.post("http://localhost:8040/enhance-sentiment", 
                                   json=test_data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Sentiment enhancement working: {result.get('result', {}).get('enhanced_emotion', 'N/A')}")
            else:
                print(f"❌ Sentiment enhancement failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Sentiment enhancement error: {e}")
    
    def run_full_test_suite(self):
        """Run the complete test suite"""
        try:
            print("🧠 Direct LLM Integration Test Suite")
            print("=" * 50)
            
            # Start services
            services = [
                ("llm_client", 8040),
                ("enhanced_sentiment", 8038),
                ("narrative_analyzer", 8039)
            ]
            
            started_services = []
            for script, port in services:
                if self.start_service(script, port):
                    started_services.append((script, port))
                else:
                    print(f"⚠️ Skipping {script} due to startup failure")
            
            if not started_services:
                print("❌ No services started successfully")
                return False
            
            # Wait a bit for all services to be ready
            print("\n⏳ Waiting for services to be ready...")
            time.sleep(10)
            
            # Test health endpoints
            print("\n🏥 Testing health endpoints...")
            for script, port in started_services:
                self.test_health_endpoint(port, script)
            
            # Run functionality tests
            if any(port == 8040 for _, port in started_services):
                self.run_basic_tests()
            else:
                print("⚠️ Skipping functionality tests - LLM client not running")
            
            print("\n✅ Test suite completed!")
            print("\n📝 Services are running and can be tested manually:")
            for script, port in started_services:
                print(f"   • {script}: http://localhost:{port}")
            
            print("\n⌨️ Press Ctrl+C to stop all services and exit")
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupted by user")
            
            return True
            
        except Exception as e:
            print(f"❌ Test suite error: {e}")
            return False
        finally:
            self.stop_all_services()

def main():
    """Main entry point"""
    # Check if we're in the right directory
    if not (Path("llm_client.py").exists() and Path("enhanced_sentiment.py").exists()):
        print("❌ Error: Required service files not found in current directory")
        print("   Please ensure llm_client.py and enhanced_sentiment.py are present")
        return 1
    
    # Check if required packages are installed
    try:
        import requests
        import uvicorn
        import fastapi
    except ImportError as e:
        print(f"❌ Error: Required package not installed: {e}")
        print("   Please install with: pip install requests uvicorn fastapi")
        return 1
    
    runner = DirectTestRunner()
    success = runner.run_full_test_suite()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())