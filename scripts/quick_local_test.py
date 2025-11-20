#!/usr/bin/env python3
"""
Quick Local Database Test
Simple test script for existing MySQL installations.
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

def main():
    """Quick test with existing MySQL setup"""
    logger.info("🚀 Quick Local Database Test")
    logger.info("=" * 50)
    
    # Check if environment variables are set
    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("💡 Set these environment variables first:")
        logger.info("   export MYSQL_HOST=127.0.0.1")
        logger.info("   export MYSQL_PORT=3306")  
        logger.info("   export MYSQL_USER=your_mysql_user")
        logger.info("   export MYSQL_PASSWORD=your_mysql_password")
        logger.info("   export MYSQL_DATABASE=crypto_data_test")
        logger.info("   export MYSQL_ROOT_PASSWORD=your_root_password")
        logger.info("")
        logger.info("Then run this script again.")
        return False
    
    logger.info("✅ Environment variables found")
    
    # Test 1: Database initialization
    logger.info("🏗️ Testing database initialization...")
    init_script = PROJECT_ROOT / 'scripts' / 'init_ci_database.py'
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, str(init_script)
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            logger.info("✅ Database initialization successful")
        else:
            logger.error("❌ Database initialization failed")
            logger.error("Error output:")
            for line in result.stderr.split('\n')[:10]:  # First 10 lines
                if line.strip():
                    logger.error(f"   {line}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running initialization: {e}")
        return False
    
    # Test 2: Database connectivity test
    logger.info("🧪 Testing database connectivity...")
    test_script = PROJECT_ROOT / 'scripts' / 'test_ci_database.py'
    
    try:
        result = subprocess.run([
            sys.executable, str(test_script)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info("✅ Database tests passed")
        else:
            logger.error("❌ Database tests failed")
            logger.error("Error output:")
            for line in result.stderr.split('\n')[:10]:  # First 10 lines
                if line.strip():
                    logger.error(f"   {line}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        return False
    
    logger.info("🎉 All tests passed! Ready for GitHub Actions.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)