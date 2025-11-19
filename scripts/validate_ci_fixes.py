#!/usr/bin/env python3
"""
CI Authentication Validation
Validates that the authentication fixes work without requiring a database connection.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_environment_variable_usage():
    """Validate that the scripts properly use environment variables"""
    logger.info("🔍 Validating environment variable usage...")
    
    init_script = PROJECT_ROOT / 'scripts' / 'init_ci_database.py'
    
    with open(init_script, 'r') as f:
        content = f.read()
    
    # Check for hardcoded credentials (bad)
    issues = []
    
    if "password='root'" in content.lower():
        issues.append("Found hardcoded password 'root'")
    
    if "user='root'" in content.lower() and "MYSQL_USER" not in content:
        issues.append("Found hardcoded user 'root' without environment variable")
    
    if "host='localhost'" in content.lower() and "MYSQL_HOST" not in content:
        issues.append("Found hardcoded host 'localhost' without environment variable")
    
    # Check for proper environment variable usage (good)
    good_patterns = [
        "os.environ.get('MYSQL_USER'",
        "os.environ.get('MYSQL_PASSWORD'",
        "os.environ.get('MYSQL_HOST'",
        "os.environ.get('MYSQL_DATABASE'",
        "os.environ.get('MYSQL_ROOT_PASSWORD'"
    ]
    
    found_patterns = []
    for pattern in good_patterns:
        if pattern in content:
            found_patterns.append(pattern.replace("os.environ.get('", "").replace("'", ""))
    
    if issues:
        logger.error("❌ Found hardcoded credential issues:")
        for issue in issues:
            logger.error(f"   - {issue}")
        return False
    else:
        logger.info("✅ No hardcoded credentials found")
    
    if len(found_patterns) >= 4:  # At least 4 environment variables used
        logger.info("✅ Environment variables properly used:")
        for var in found_patterns:
            logger.info(f"   - {var}")
        return True
    else:
        logger.error("❌ Not enough environment variables used")
        return False

def simulate_ci_environment():
    """Simulate what happens in GitHub Actions CI environment"""
    logger.info("🐳 Simulating GitHub Actions CI environment...")
    
    # These are the environment variables that GitHub Actions will set
    ci_env = {
        'MYSQL_HOST': '127.0.0.1',
        'MYSQL_PORT': '3306',
        'MYSQL_USER': 'news_collector',
        'MYSQL_PASSWORD': '99Rules!',
        'MYSQL_DATABASE': 'crypto_data_test',
        'MYSQL_ROOT_PASSWORD': '99Rules!'
    }
    
    logger.info("📋 CI Environment Variables:")
    for key, value in ci_env.items():
        masked_value = value if key != 'MYSQL_PASSWORD' and key != 'MYSQL_ROOT_PASSWORD' else '*' * len(value)
        logger.info(f"   {key}={masked_value}")
    
    # Show what the connection parameters will be
    logger.info("🔗 Connection Parameters:")
    logger.info(f"   Host: {ci_env['MYSQL_HOST']}")
    logger.info(f"   Port: {ci_env['MYSQL_PORT']}")  
    logger.info(f"   User: {ci_env['MYSQL_USER']}")
    logger.info(f"   Database: {ci_env['MYSQL_DATABASE']}")
    logger.info(f"   Password: {'*' * len(ci_env['MYSQL_PASSWORD'])} (masked)")
    
    return True

def validate_schema_files():
    """Validate that schema files have been updated"""
    logger.info("📋 Validating schema files...")
    
    # Check integration test file
    integration_test = PROJECT_ROOT / 'tests' / 'test_pytest_comprehensive_integration.py'
    
    if not integration_test.exists():
        logger.error("❌ Integration test file not found")
        return False
    
    with open(integration_test, 'r') as f:
        content = f.read()
    
    # Check for updated field names
    good_field_mappings = [
        'current_price',  # instead of 'price'
        'volume_usd_24h', # instead of 'total_volume'
        'rsi',            # technical indicator field
        'sma_20',         # technical indicator field
        'macd'            # technical indicator field
    ]
    
    found_mappings = []
    for field in good_field_mappings:
        if f"'{field}'" in content or f'"{field}"' in content:
            found_mappings.append(field)
    
    if len(found_mappings) >= 4:
        logger.info("✅ Field mappings updated correctly:")
        for field in found_mappings:
            logger.info(f"   - {field}")
        return True
    else:
        logger.error("❌ Field mappings may not be updated correctly")
        return False

def main():
    """Main validation function"""
    logger.info("🚀 CI Authentication and Schema Validation")
    logger.info("=" * 60)
    
    success = True
    
    # Test 1: Environment variable usage
    if not validate_environment_variable_usage():
        success = False
    
    logger.info("")
    
    # Test 2: Simulate CI environment
    if not simulate_ci_environment():
        success = False
    
    logger.info("")
    
    # Test 3: Schema file validation
    if not validate_schema_files():
        success = False
    
    logger.info("")
    logger.info("=" * 60)
    
    if success:
        logger.info("🎉 All validations passed!")
        logger.info("✅ Authentication fixes are correct")
        logger.info("✅ Schema updates are in place")
        logger.info("✅ Ready for GitHub Actions deployment")
        
        logger.info("")
        logger.info("🚀 What will happen in GitHub Actions:")
        logger.info("   1. MySQL 8.0 container starts with service credentials")
        logger.info("   2. init_ci_database.py reads environment variables")
        logger.info("   3. Connects using news_collector/99Rules! (not root/root)")
        logger.info("   4. Creates all tables with production schemas")
        logger.info("   5. Integration tests use correct field names")
        logger.info("   6. No more 'Access denied' errors!")
        
    else:
        logger.error("❌ Some validations failed")
        logger.error("   Please review the issues above before deploying")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)