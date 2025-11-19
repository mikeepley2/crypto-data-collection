#!/usr/bin/env python3
"""
Test Fixes Verification Script
Verify that all fixes for CI/CD test failures work correctly
"""

import sys
import importlib
import traceback
from pathlib import Path

def test_imports():
    """Test all problematic imports"""
    print("🧪 Testing import fixes...")
    
    success = True
    
    # Test 1: Base collector template imports
    try:
        from tests.test_base_collector import MockCollector, create_mock_config
        config = create_mock_config()
        collector = MockCollector(config)
        print("✅ Base collector imports: SUCCESS")
    except Exception as e:
        print(f"❌ Base collector imports: FAILED - {e}")
        traceback.print_exc()
        success = False
    
    # Test 2: Enhanced sentiment ML imports
    try:
        from services.enhanced_sentiment_ml_analysis import MLSentimentCollectorConfig
        print("✅ Enhanced sentiment ML imports: SUCCESS")
    except Exception as e:
        print(f"❌ Enhanced sentiment ML imports: FAILED - {e}")
        success = False
    
    # Test 3: Enhanced technical calculator imports  
    try:
        from services.enhanced_technical_calculator import TechnicalCalculatorConfig
        print("✅ Enhanced technical calculator imports: SUCCESS")
    except Exception as e:
        print(f"❌ Enhanced technical calculator imports: FAILED - {e}")
        success = False
    
    # Test 4: Enhanced news collector imports
    try:
        from services.enhanced_news_collector import EnhancedNewsCollectorConfig
        print("✅ Enhanced news collector imports: SUCCESS")
    except Exception as e:
        print(f"❌ Enhanced news collector imports: FAILED - {e}")
        success = False
    
    # Test 5: Smart model manager imports
    try:
        from shared.smart_model_manager import SmartModelManager, ModelSource
        manager = SmartModelManager()
        print(f"✅ Smart model manager imports: SUCCESS (Environment: {manager.environment.value})")
    except Exception as e:
        print(f"❌ Smart model manager imports: FAILED - {e}")
        success = False
    
    return success

def test_config_creation():
    """Test CollectorConfig creation with proper parameters"""
    print("\n🔧 Testing CollectorConfig creation...")
    
    try:
        from base_collector_template import CollectorConfig, LogLevel
        
        # Test creating config with all required parameters
        config = CollectorConfig(
            # Database configuration
            mysql_host="localhost",
            mysql_port=3306,
            mysql_user="test_user",
            mysql_password="test_password", 
            mysql_database="test_db",
            
            # Collection configuration
            collection_interval=60,
            backfill_batch_size=100,
            max_retry_attempts=3,
            api_timeout=30,
            api_rate_limit=60,
            
            # Date configuration
            collector_beginning_date="2023-01-01",
            backfill_lookback_days=30,
            
            # Logging configuration
            log_level=LogLevel.INFO,
            log_format="json",
            enable_audit_logging=True,
            
            # Service configuration
            service_name="test-collector",
            service_version="1.0.0-test",
            health_check_interval=30,
            
            # Rate limiting and circuit breaker
            enable_rate_limiting=True,
            api_rate_limit_per_minute=60,
            circuit_breaker_failure_threshold=5,
            circuit_breaker_timeout=60,
            
            # Data validation and quality
            enable_data_validation=True,
            enable_duplicate_detection=True,
            data_retention_days=90,
            
            # Performance and optimization
            connection_pool_size=10,
            query_timeout=30,
            batch_commit_size=100,
            
            # Alerting and notifications
            enable_alerting=True,
            alert_webhook_url=None,
            alert_error_threshold=5
        )
        
        print(f"✅ CollectorConfig creation: SUCCESS (service: {config.service_name})")
        return True
        
    except Exception as e:
        print(f"❌ CollectorConfig creation: FAILED - {e}")
        traceback.print_exc()
        return False

def test_dependencies():
    """Test that required dependencies are available"""
    print("\n📦 Testing dependencies...")
    
    success = True
    
    required_packages = [
        ("schedule", "schedule"),
        ("websockets", "websockets"),
        ("fastapi", "fastapi"),
        ("mysql.connector", "mysql-connector-python"),
        ("prometheus_client", "prometheus-client")
    ]
    
    for module, package in required_packages:
        try:
            importlib.import_module(module)
            print(f"✅ {package}: AVAILABLE")
        except ImportError:
            print(f"❌ {package}: MISSING")
            success = False
    
    return success

def main():
    """Run all verification tests"""
    print("🚀 Starting Test Fixes Verification")
    print("=" * 50)
    
    all_success = True
    
    # Test imports
    import_success = test_imports()
    all_success &= import_success
    
    # Test config creation
    config_success = test_config_creation()
    all_success &= config_success
    
    # Test dependencies
    dep_success = test_dependencies()
    all_success &= dep_success
    
    print("\n" + "=" * 50)
    if all_success:
        print("🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("✅ Tests should now pass in CI/CD")
    else:
        print("💥 SOME FIXES STILL HAVE ISSUES")
        print("❌ Additional work needed before tests pass")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())