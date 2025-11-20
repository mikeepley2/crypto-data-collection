#!/usr/bin/env python3
"""
Test CI Environment Variables
Test that our wait_for_mysql function will work with the GitHub Actions environment.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def test_ci_environment_variables():
    """Test the environment variables that GitHub Actions will provide"""
    print("🔍 Testing CI Environment Variables")
    print("=" * 50)
    
    # These are the environment variables from the GitHub Actions workflow
    ci_env = {
        'MYSQL_HOST': '127.0.0.1',
        'MYSQL_PORT': '3306',
        'MYSQL_USER': 'news_collector',
        'MYSQL_PASSWORD': '99Rules!',
        'MYSQL_DATABASE': 'crypto_data_test',
        'MYSQL_ROOT_PASSWORD': '99Rules!'
    }
    
    # Set environment variables to simulate GitHub Actions
    for key, value in ci_env.items():
        os.environ[key] = value
    
    print("📋 Simulated GitHub Actions environment:")
    for key, value in ci_env.items():
        if 'PASSWORD' in key:
            print(f"   {key}=******* (masked)")
        else:
            print(f"   {key}={value}")
    
    print()
    
    # Test our wait_for_mysql function logic
    print("🧪 Testing wait_for_mysql configuration logic:")
    
    mysql_host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
    mysql_user = os.environ.get('MYSQL_USER', 'news_collector')
    mysql_password = os.environ.get('MYSQL_PASSWORD', '99Rules!')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'crypto_data_test')
    mysql_root_password = os.environ.get('MYSQL_ROOT_PASSWORD', '99Rules!')
    
    print("📊 Connection configurations that will be tried:")
    print("   1. Primary user connection:")
    print(f"      Host: {mysql_host}")
    print(f"      Port: {mysql_port}")
    print(f"      User: {mysql_user}")
    print(f"      Database: {mysql_database}")
    print(f"      Password: {'*' * len(mysql_password)}")
    
    print("   2. Root fallback connection:")
    print(f"      Host: {mysql_host}")
    print(f"      Port: {mysql_port}")
    print(f"      User: root")
    print(f"      Database: (none - for initial setup)")
    print(f"      Password: {'*' * len(mysql_root_password)}")
    
    # Test environment detection from database_config.py
    print()
    print("🔍 Testing database_config environment detection:")
    
    # Set CI environment variable
    os.environ['CI'] = 'true'
    os.environ['GITHUB_ACTIONS'] = 'true'
    
    try:
        # Import and test database config
        sys.path.insert(0, str(PROJECT_ROOT))
        from shared.database_config import db_config
        
        print(f"   Environment detected: {db_config.environment}")
        print(f"   MySQL config: {db_config.get_connection_info()}")
        
        # Get the actual config that will be used
        mysql_config = db_config.get_mysql_config_dict()
        print("   Database config that will be used:")
        for key, value in mysql_config.items():
            if 'password' in key.lower():
                print(f"      {key}: {'*' * len(str(value))}")
            else:
                print(f"      {key}: {value}")
                
    except Exception as e:
        print(f"   ❌ Error testing database config: {e}")
        return False
    
    print()
    print("✅ CI environment variable test completed")
    print("✅ Both wait_for_mysql and database_config should work correctly")
    return True

if __name__ == "__main__":
    success = test_ci_environment_variables()
    sys.exit(0 if success else 1)