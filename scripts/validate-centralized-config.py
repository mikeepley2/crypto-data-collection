#!/usr/bin/env python3
"""
Centralized Configuration Deployment Validator
Validates that the centralized configuration system is properly set up before deployment
"""

import sys
import os
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_file_exists(file_path: str, description: str) -> bool:
    """Validate that a required file exists"""
    if os.path.exists(file_path):
        logger.info(f"✅ {description}: {file_path}")
        return True
    else:
        logger.error(f"❌ {description} missing: {file_path}")
        return False

def validate_import(module_path: str, description: str) -> bool:
    """Validate that a module can be imported"""
    try:
        exec(f"import {module_path}")
        logger.info(f"✅ {description} import successful")
        return True
    except ImportError as e:
        logger.error(f"❌ {description} import failed: {e}")
        return False

def validate_table_configuration() -> bool:
    """Validate centralized table configuration"""
    logger.info("🔍 Validating centralized table configuration...")
    
    try:
        # Import table configuration
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from shared.table_config import (
            CRYPTO_TABLES, TECHNICAL_TABLES, ML_TABLES, 
            get_master_onchain_table, validate_table_usage
        )
        
        # Validate core tables exist
        required_tables = {
            "ONCHAIN_DATA": "crypto_onchain_data",
            "ASSETS": "crypto_assets"
        }
        
        for key, expected_name in required_tables.items():
            if key not in CRYPTO_TABLES:
                logger.error(f"❌ Missing required table key: {key}")
                return False
                
            actual_name = CRYPTO_TABLES[key]
            if actual_name != expected_name:
                logger.error(f"❌ Table name mismatch: {key} = {actual_name}, expected {expected_name}")
                return False
                
            logger.info(f"✅ Table validated: {key} = {actual_name}")
        
        # Test master onchain table function
        master_table = get_master_onchain_table()
        if master_table != "crypto_onchain_data":
            logger.error(f"❌ Master onchain table mismatch: {master_table}")
            return False
        logger.info(f"✅ Master onchain table: {master_table}")
        
        # Test table validation function
        approved_result = validate_table_usage("crypto_onchain_data")
        if approved_result["status"] != "approved":
            logger.error(f"❌ Table validation failed for approved table: {approved_result}")
            return False
        logger.info("✅ Table validation function working for approved tables")
        
        unknown_result = validate_table_usage("invalid_table_name")
        if unknown_result["status"] != "unknown":
            logger.error(f"❌ Table validation failed for unknown table: {unknown_result}")
            return False
        logger.info("✅ Table validation function working for unknown tables")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Table configuration validation failed: {e}")
        return False

def validate_database_configuration() -> bool:
    """Validate centralized database configuration"""
    logger.info("🔍 Validating centralized database configuration...")
    
    try:
        # Import database configuration
        from shared.database_config import (
            get_db_config, test_db_connection, get_db_connection
        )
        
        # Test configuration loading
        config = get_db_config()
        required_keys = ['host', 'port', 'user', 'password', 'database']
        
        for key in required_keys:
            if key not in config:
                logger.error(f"❌ Missing database config key: {key}")
                return False
        
        logger.info("✅ Database configuration keys present")
        
        # Test database connectivity (if possible)
        try:
            if test_db_connection():
                logger.info("✅ Database connectivity test passed")
            else:
                logger.warning("⚠️ Database connectivity test failed (may be expected in some environments)")
        except Exception as e:
            logger.warning(f"⚠️ Database connectivity test failed: {e} (may be expected in some environments)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database configuration validation failed: {e}")
        return False

def validate_environment_variables() -> bool:
    """Validate required environment variables"""
    logger.info("🔍 Validating environment variables...")
    
    # Optional environment variables (may be set via K8s secrets)
    optional_vars = [
        "COINGECKO_API_KEY",
        "FRED_API_KEY", 
        "GUARDIAN_API_KEY",
        "OPENAI_API_KEY",
        "DB_HOST",
        "DB_USER",
        "DB_PASSWORD"
    ]
    
    missing_vars = []
    present_vars = []
    
    for var in optional_vars:
        if os.getenv(var):
            present_vars.append(var)
        else:
            missing_vars.append(var)
    
    if present_vars:
        logger.info(f"✅ Environment variables present: {', '.join(present_vars)}")
    
    if missing_vars:
        logger.warning(f"⚠️ Environment variables missing (may be set via K8s secrets): {', '.join(missing_vars)}")
    
    return True

def validate_project_structure() -> bool:
    """Validate required project structure"""
    logger.info("🔍 Validating project structure...")
    
    required_files = [
        ("shared/table_config.py", "Centralized table configuration"),
        ("shared/database_config.py", "Centralized database configuration"),
        ("CENTRALIZED_CONFIG_INSTRUCTIONS.md", "Configuration instructions"),
        ("README.md", "Main README")
    ]
    
    all_present = True
    for file_path, description in required_files:
        if not validate_file_exists(file_path, description):
            all_present = False
    
    return all_present

def main():
    """Run all validation checks"""
    logger.info("🚀 Starting centralized configuration deployment validation...")
    logger.info("=" * 80)
    
    # Track validation results
    validations = [
        ("Project Structure", validate_project_structure),
        ("Table Configuration", validate_table_configuration),
        ("Database Configuration", validate_database_configuration),
        ("Environment Variables", validate_environment_variables)
    ]
    
    results = []
    for name, validator in validations:
        logger.info(f"\n📋 {name} Validation:")
        logger.info("-" * 40)
        
        try:
            result = validator()
            results.append((name, result))
            
            if result:
                logger.info(f"✅ {name} validation: PASSED")
            else:
                logger.error(f"❌ {name} validation: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {name} validation: ERROR - {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 VALIDATION SUMMARY:")
    logger.info("=" * 80)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{name:25}: {status}")
        if result:
            passed += 1
    
    logger.info("-" * 80)
    logger.info(f"Total: {passed}/{total} validations passed")
    
    if passed == total:
        logger.info("🎉 ALL VALIDATIONS PASSED - Ready for deployment!")
        return 0
    else:
        logger.error("🚨 VALIDATION FAILURES - DO NOT DEPLOY until all issues are resolved!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)