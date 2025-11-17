#!/usr/bin/env python3
"""
Final Endpoint Testing Validation

Validates that all template endpoints are properly tested and working.
"""

import sys
import time
from pathlib import Path

# Add current directory to Python path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

def test_endpoint_functionality():
    """Test all endpoint functionality directly"""
    print("🧪 Testing Endpoint Functionality...")
    
    try:
        from tests.test_comprehensive_endpoints import ComprehensiveTestCollector
        from fastapi.testclient import TestClient
        
        collector = ComprehensiveTestCollector()
        client = TestClient(collector.app)
        
        # Define all required template endpoints
        required_endpoints = [
            ("/health", "GET", "Health check endpoint"),
            ("/ready", "GET", "Readiness check endpoint"),
            ("/status", "GET", "Service status endpoint"),
            ("/metrics", "GET", "Metrics endpoint"),
            ("/collect", "POST", "Trigger collection endpoint"),
            ("/start", "POST", "Start service endpoint"),
            ("/stop", "POST", "Stop service endpoint"),
            ("/restart", "POST", "Restart service endpoint"),
            ("/config", "GET", "Get configuration endpoint"),
            ("/config", "PUT", "Update configuration endpoint"),
            ("/logs", "GET", "Get logs endpoint"),
            ("/backfill", "POST", "Backfill missing data endpoint"),
            ("/data-quality", "GET", "Data quality report endpoint"),
            ("/performance", "GET", "Performance metrics endpoint"),
            ("/alert", "POST", "Send alert notification endpoint"),
            ("/validate-data", "POST", "Validate data structure endpoint"),
            ("/circuit-breaker-status", "GET", "Circuit breaker status endpoint")
        ]
        
        passed = 0
        total = len(required_endpoints)
        results = []
        
        print(f"\n📋 Testing {total} template endpoints...")
        
        for endpoint, method, description in required_endpoints:
            try:
                if method == "GET":
                    response = client.get(endpoint)
                elif method == "POST":
                    # Provide appropriate JSON payloads for POST endpoints
                    if endpoint == "/backfill":
                        response = client.post(endpoint, json={"start_date": "2025-01-01T00:00:00"})
                    elif endpoint == "/alert":
                        response = client.post(endpoint, json={
                            "alert_type": "test", "severity": "low", 
                            "message": "test", "service": "test"
                        })
                    elif endpoint == "/validate-data":
                        response = client.post(endpoint, json={"test": "data"})
                    else:
                        response = client.post(endpoint, json={})
                elif method == "PUT":
                    response = client.put(endpoint, json={"test": "value"})
                
                if response.status_code == 200:
                    passed += 1
                    status = "✅ PASS"
                    results.append((endpoint, method, description, "PASS", response.status_code))
                    print(f"  {status} {method} {endpoint}: {response.status_code}")
                else:
                    status = "❌ FAIL"
                    results.append((endpoint, method, description, "FAIL", response.status_code))
                    print(f"  {status} {method} {endpoint}: {response.status_code}")
                    
            except Exception as e:
                status = "❌ ERROR"
                results.append((endpoint, method, description, "ERROR", str(e)))
                print(f"  {status} {method} {endpoint}: {e}")
        
        print(f"\n📊 Results: {passed}/{total} endpoints passed ({(passed/total)*100:.1f}%)")
        
        return passed == total, results
        
    except ImportError as e:
        print(f"❌ Cannot import test collector: {e}")
        return False, []


def test_error_handling():
    """Test error handling functionality"""
    print("\n🛡️  Testing Error Handling...")
    
    try:
        from tests.test_comprehensive_endpoints import ComprehensiveTestCollector
        from fastapi.testclient import TestClient
        
        collector = ComprehensiveTestCollector()
        client = TestClient(collector.app)
        
        error_tests = [
            ("/invalid-endpoint", "GET", 404, "Invalid endpoint returns 404"),
            ("/health", "POST", 405, "Health endpoint rejects POST"),
            ("/collect", "GET", 405, "Collect endpoint rejects GET"),
        ]
        
        passed = 0
        total = len(error_tests)
        
        for endpoint, method, expected_code, description in error_tests:
            try:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint)
                
                if response.status_code == expected_code:
                    passed += 1
                    print(f"  ✅ {description}: {response.status_code}")
                else:
                    print(f"  ❌ {description}: got {response.status_code}, expected {expected_code}")
                    
            except Exception as e:
                print(f"  ❌ {description}: ERROR - {e}")
        
        print(f"\n📊 Error handling: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        return passed == total
        
    except ImportError as e:
        print(f"❌ Cannot test error handling: {e}")
        return False


def test_performance():
    """Test basic performance requirements"""
    print("\n⚡ Testing Performance...")
    
    try:
        from tests.test_comprehensive_endpoints import ComprehensiveTestCollector
        from fastapi.testclient import TestClient
        
        collector = ComprehensiveTestCollector()
        client = TestClient(collector.app)
        
        # Test health endpoint performance
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200 and duration < 1.0:
            print(f"  ✅ Health endpoint performance: {duration:.3f}s (< 1.0s)")
            performance_ok = True
        else:
            print(f"  ❌ Health endpoint performance: {duration:.3f}s (>= 1.0s)")
            performance_ok = False
        
        # Test concurrent requests
        import threading
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        concurrent_duration = end_time - start_time
        success_count = sum(1 for code in results if code == 200)
        
        if success_count == 5 and concurrent_duration < 2.0:
            print(f"  ✅ Concurrent requests: {success_count}/5 succeeded in {concurrent_duration:.3f}s")
            concurrent_ok = True
        else:
            print(f"  ❌ Concurrent requests: {success_count}/5 succeeded in {concurrent_duration:.3f}s")
            concurrent_ok = False
        
        return performance_ok and concurrent_ok
        
    except ImportError as e:
        print(f"❌ Cannot test performance: {e}")
        return False


def test_content_validation():
    """Test response content validation"""
    print("\n📝 Testing Content Validation...")
    
    try:
        from tests.test_comprehensive_endpoints import ComprehensiveTestCollector
        from fastapi.testclient import TestClient
        import json
        from datetime import datetime
        
        collector = ComprehensiveTestCollector()
        client = TestClient(collector.app)
        
        validation_tests = [
            ("/health", "status", str, "Health endpoint has status field"),
            ("/health", "timestamp", str, "Health endpoint has timestamp field"),
            ("/status", "service", str, "Status endpoint has service field"),
            ("/metrics", "collector_metrics", dict, "Metrics endpoint has collector_metrics"),
            ("/config", "configuration", dict, "Config endpoint has configuration"),
        ]
        
        passed = 0
        total = len(validation_tests)
        
        for endpoint, field, expected_type, description in validation_tests:
            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    if field in data and isinstance(data[field], expected_type):
                        passed += 1
                        print(f"  ✅ {description}")
                    else:
                        print(f"  ❌ {description}: field missing or wrong type")
                else:
                    print(f"  ❌ {description}: endpoint returned {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {description}: ERROR - {e}")
        
        # Test timestamp format
        try:
            response = client.get("/health")
            data = response.json()
            timestamp = data.get("timestamp")
            datetime.fromisoformat(timestamp)
            passed += 1
            print(f"  ✅ Timestamp format validation: {timestamp}")
            total += 1
        except Exception as e:
            print(f"  ❌ Timestamp format validation: ERROR - {e}")
            total += 1
        
        print(f"\n📊 Content validation: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        return passed == total
        
    except ImportError as e:
        print(f"❌ Cannot test content validation: {e}")
        return False


def generate_coverage_report(results):
    """Generate final coverage report"""
    print("\n📊 ENDPOINT TESTING COVERAGE REPORT")
    print("=" * 60)
    
    print(f"\n📋 Template Endpoint Coverage:")
    for endpoint, method, description, status, code in results:
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"  {status_symbol} {method:4} {endpoint:20} - {description}")
    
    passed_count = sum(1 for _, _, _, status, _ in results if status == "PASS")
    total_count = len(results)
    coverage_percentage = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\n📈 Coverage Statistics:")
    print(f"  • Total endpoints tested: {total_count}")
    print(f"  • Endpoints passing: {passed_count}")
    print(f"  • Coverage percentage: {coverage_percentage:.1f}%")
    
    return coverage_percentage


def main():
    """Main validation function"""
    print("🚀 COMPREHENSIVE ENDPOINT TESTING VALIDATION")
    print("=" * 60)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    # Run all tests
    endpoint_test_passed, endpoint_results = test_endpoint_functionality()
    error_handling_passed = test_error_handling()
    performance_passed = test_performance()
    content_validation_passed = test_content_validation()
    
    # Generate report
    coverage_percentage = generate_coverage_report(endpoint_results)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n🏁 FINAL RESULTS")
    print("=" * 60)
    print(f"⏱️  Total test duration: {duration:.2f} seconds")
    print(f"🎯 Template endpoint coverage: {coverage_percentage:.1f}%")
    print(f"🧪 Endpoint functionality: {'✅ PASS' if endpoint_test_passed else '❌ FAIL'}")
    print(f"🛡️  Error handling: {'✅ PASS' if error_handling_passed else '❌ FAIL'}")
    print(f"⚡ Performance: {'✅ PASS' if performance_passed else '❌ FAIL'}")
    print(f"📝 Content validation: {'✅ PASS' if content_validation_passed else '❌ FAIL'}")
    
    all_passed = (endpoint_test_passed and error_handling_passed and 
                  performance_passed and content_validation_passed)
    
    print(f"\n🎉 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n✨ CONGRATULATIONS!")
        print("🏆 All template endpoints are comprehensively tested and working!")
        print("📊 Your endpoint testing coverage is complete!")
        print("🚀 Ready for production use!")
    else:
        print("\n⚠️  ATTENTION NEEDED")
        print("🔧 Some tests failed and need to be addressed")
        print("📋 Review the failed tests above and fix issues")
    
    print("\n" + "=" * 60)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())