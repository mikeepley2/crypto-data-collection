#!/usr/bin/env python3
"""
Local Database Setup Test
Tests the database initialization scripts locally before CI deployment.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"✅ Docker available: {result.stdout.strip()}")
            return True
        else:
            logger.error("❌ Docker command failed")
            return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Docker command timed out")
        return False
    except FileNotFoundError:
        logger.error("❌ Docker not found. Please install Docker to test locally.")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking Docker: {e}")
        return False

def start_mysql_container():
    """Start a MySQL container for testing"""
    logger.info("🐳 Starting MySQL container for testing...")
    
    container_name = "crypto-test-mysql"
    mysql_password = "99Rules!"
    mysql_user = "news_collector"
    mysql_database = "crypto_data_test"
    
    # Stop and remove existing container if it exists
    subprocess.run(['docker', 'stop', container_name], capture_output=True)
    subprocess.run(['docker', 'rm', container_name], capture_output=True)
    
    # Start new MySQL container
    cmd = [
        'docker', 'run', '-d',
        '--name', container_name,
        '-p', '3308:3306',  # Use port 3308 to avoid conflicts
        '-e', f'MYSQL_ROOT_PASSWORD={mysql_password}',
        '-e', f'MYSQL_USER={mysql_user}',
        '-e', f'MYSQL_PASSWORD={mysql_password}',
        '-e', f'MYSQL_DATABASE={mysql_database}',
        'mysql:8.0'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info(f"✅ MySQL container started: {result.stdout.strip()}")
            
            # Wait for MySQL to be ready
            logger.info("⏳ Waiting for MySQL to be ready...")
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    health_check = subprocess.run([
                        'docker', 'exec', container_name,
                        'mysql', '-u', 'root', f'-p{mysql_password}',
                        '-e', 'SELECT 1'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if health_check.returncode == 0:
                        logger.info("✅ MySQL is ready!")
                        return True
                    else:
                        time.sleep(2)
                        if attempt % 5 == 0:
                            logger.info(f"⏳ Still waiting... (attempt {attempt + 1}/{max_attempts})")
                except subprocess.TimeoutExpired:
                    time.sleep(2)
                    if attempt % 5 == 0:
                        logger.info(f"⏳ Still waiting... (attempt {attempt + 1}/{max_attempts})")
            
            logger.error("❌ MySQL failed to become ready within timeout")
            return False
            
        else:
            logger.error(f"❌ Failed to start MySQL container: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Docker command timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error starting MySQL container: {e}")
        return False

def run_database_initialization():
    """Run the database initialization script"""
    logger.info("🏗️ Running database initialization...")
    
    # Set environment variables for local testing
    env = os.environ.copy()
    env.update({
        'MYSQL_HOST': '127.0.0.1',
        'MYSQL_PORT': '3308',
        'MYSQL_USER': 'news_collector',
        'MYSQL_PASSWORD': '99Rules!',
        'MYSQL_DATABASE': 'crypto_data_test',
        'MYSQL_ROOT_PASSWORD': '99Rules!'
    })
    
    init_script = PROJECT_ROOT / 'scripts' / 'init_ci_database.py'
    
    try:
        result = subprocess.run([
            sys.executable, str(init_script)
        ], capture_output=True, text=True, timeout=120, env=env)
        
        if result.returncode == 0:
            logger.info("✅ Database initialization completed successfully")
            logger.info("📋 Initialization output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"   {line}")
            return True
        else:
            logger.error("❌ Database initialization failed")
            logger.error("📋 Error output:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(f"   {line}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Database initialization timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error running database initialization: {e}")
        return False

def run_database_tests():
    """Run the database test script"""
    logger.info("🧪 Running database tests...")
    
    # Set environment variables for local testing
    env = os.environ.copy()
    env.update({
        'MYSQL_HOST': '127.0.0.1',
        'MYSQL_PORT': '3308',
        'MYSQL_USER': 'news_collector',
        'MYSQL_PASSWORD': '99Rules!',
        'MYSQL_DATABASE': 'crypto_data_test'
    })
    
    test_script = PROJECT_ROOT / 'scripts' / 'test_ci_database.py'
    
    try:
        result = subprocess.run([
            sys.executable, str(test_script)
        ], capture_output=True, text=True, timeout=60, env=env)
        
        if result.returncode == 0:
            logger.info("✅ Database tests completed successfully")
            logger.info("📋 Test output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"   {line}")
            return True
        else:
            logger.error("❌ Database tests failed")
            logger.error("📋 Test output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.error(f"   {line}")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(f"   {line}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Database tests timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error running database tests: {e}")
        return False

def run_sample_integration_tests():
    """Run a sample of the integration tests that were previously failing"""
    logger.info("🧪 Running sample integration tests...")
    
    # Set environment variables for local testing
    env = os.environ.copy()
    env.update({
        'MYSQL_HOST': '127.0.0.1',
        'MYSQL_PORT': '3308',
        'MYSQL_USER': 'news_collector',
        'MYSQL_PASSWORD': '99Rules!',
        'MYSQL_DATABASE': 'crypto_data_test'
    })
    
    # Run just a few key integration tests
    test_file = PROJECT_ROOT / 'tests' / 'test_pytest_comprehensive_integration.py'
    
    try:
        # Run specific test methods that were previously failing
        result = subprocess.run([
            sys.executable, '-m', 'pytest', str(test_file),
            '-v',
            '-k', 'test_price_data_fields or test_onchain_data_fields or test_technical_data_fields',
            '--tb=short'
        ], capture_output=True, text=True, timeout=120, env=env, cwd=str(PROJECT_ROOT))
        
        if result.returncode == 0:
            logger.info("✅ Sample integration tests passed")
            logger.info("📋 Test results:")
            for line in result.stdout.split('\n'):
                if line.strip() and ('PASSED' in line or 'FAILED' in line or 'ERROR' in line):
                    logger.info(f"   {line}")
            return True
        else:
            logger.error("❌ Sample integration tests failed")
            logger.error("📋 Test output:")
            for line in result.stdout.split('\n')[-20:]:  # Last 20 lines
                if line.strip():
                    logger.error(f"   {line}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Integration tests timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error running integration tests: {e}")
        return False

def cleanup_container():
    """Clean up the test MySQL container"""
    logger.info("🧹 Cleaning up test container...")
    
    container_name = "crypto-test-mysql"
    
    try:
        # Stop container
        subprocess.run(['docker', 'stop', container_name], capture_output=True, timeout=30)
        # Remove container
        subprocess.run(['docker', 'rm', container_name], capture_output=True, timeout=30)
        logger.info("✅ Test container cleaned up")
    except Exception as e:
        logger.warning(f"⚠️ Error cleaning up container: {e}")

def main():
    """Main test function"""
    logger.info("🚀 Local Database Setup Test")
    logger.info("=" * 60)
    
    success = True
    
    try:
        # Step 1: Check Docker
        if not check_docker():
            logger.error("❌ Docker is required for local testing")
            logger.info("💡 Alternative: Test directly against your local MySQL instance")
            logger.info("   Set these environment variables:")
            logger.info("   MYSQL_HOST=127.0.0.1")
            logger.info("   MYSQL_PORT=3306")
            logger.info("   MYSQL_USER=your_user")
            logger.info("   MYSQL_PASSWORD=your_password")
            logger.info("   MYSQL_DATABASE=crypto_data_test")
            logger.info("   Then run: python scripts/init_ci_database.py")
            logger.info("   Then run: python scripts/test_ci_database.py")
            return False
        
        # Step 2: Start MySQL container
        if not start_mysql_container():
            success = False
            return success
        
        # Step 3: Run database initialization
        if not run_database_initialization():
            success = False
        
        # Step 4: Run database tests
        if success and not run_database_tests():
            success = False
        
        # Step 5: Run sample integration tests
        if success and not run_sample_integration_tests():
            success = False
        
        if success:
            logger.info("🎉 All local tests passed!")
            logger.info("✅ Your changes are ready for GitHub Actions CI")
        else:
            logger.error("❌ Some tests failed. Please fix issues before CI deployment.")
        
    finally:
        cleanup_container()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)