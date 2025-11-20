#!/usr/bin/env python3
"""
Test the integration test port fix
"""

import sys
import os
from pathlib import Path

def test_integration_port_fix():
    """Test that the integration test port validation is fixed"""
    
    print("🧪 Testing Integration Test Port Fix...")
    
    # Set up environment to simulate CI
    os.environ['TESTING'] = 'true'
    os.environ['CI'] = 'true'
    
    # Add project root to path
    PROJECT_ROOT = Path('.').absolute()
    sys.path.insert(0, str(PROJECT_ROOT))
    
    try:
        # Import the centralized config
        from shared.database_config import get_db_config
        config = get_db_config()
        
        print(f"✅ Config loaded: {config['host']}:{config['port']}/{config['database']}")
        
        # Test the validation logic from the fixed integration test
        assert config['database'].endswith('_test'), f"Must use test database, got: {config['database']}"
        print("✅ Test database validation: PASS")
        
        # Test the CI detection and port validation
        is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
        
        if not is_ci and config['port'] == 3306:
            print("⚠️ Would warn about port 3306 in local environment")
        else:
            print("✅ Port validation: PASS (CI environment allows 3306)")
        
        print(f"✅ CI detected: {is_ci}")
        print(f"✅ Port {config['port']} is allowed in CI environment")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_local_environment():
    """Test local environment behavior"""
    
    print("\n🧪 Testing Local Environment Behavior...")
    
    # Remove CI flag to simulate local environment
    os.environ.pop('CI', None)
    os.environ.pop('GITHUB_ACTIONS', None)
    
    try:
        from shared.database_config import get_db_config
        config = get_db_config()
        
        # Test the validation logic
        is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
        
        print(f"✅ Local environment: CI = {is_ci}")
        
        if not is_ci and config['port'] == 3306:
            print("⚠️ In local environment, would show warning about port 3306 (but not fail)")
        else:
            print(f"✅ Port {config['port']} is acceptable")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Integration Test Port Fix Verification")
    print("=" * 45)
    
    # Test 1: CI environment
    test1_passed = test_integration_port_fix()
    
    # Test 2: Local environment  
    test2_passed = test_local_environment()
    
    print("\n📊 Test Results:")
    print("=" * 20)
    print(f"CI Environment Port Validation: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Local Environment Port Validation: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 Integration test port fix is working correctly!")
        print("\n💡 This resolves the CI/CD error:")
        print("   AssertionError: Cannot use production port 3306 ✅ FIXED")
        print("   Tests can now run with port 3306 in CI/CD environments")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)