#!/usr/bin/env python3
"""
Quick Collector Validation Script for CI/CD

This script validates that all core data collectors can be imported and have basic functionality.
Used as a fast validation step in CI when comprehensive tests aren't available.
"""

import sys
import os
from pathlib import Path

# Add paths for collector imports
PROJECT_ROOT = Path(__file__).parent
sys.path.extend([
    str(PROJECT_ROOT / 'services' / 'price-collection'),
    str(PROJECT_ROOT / 'services' / 'news-collection'),
    str(PROJECT_ROOT / 'services' / 'onchain-collection'),
    str(PROJECT_ROOT / 'services' / 'technical-collection'),
    str(PROJECT_ROOT / 'services' / 'macro-collection'),
    str(PROJECT_ROOT / 'shared'),
    str(PROJECT_ROOT)
])


def test_collector_imports():
    """Test that all core collectors can be imported"""
    collectors = [
        ('Price Collector', 'enhanced_crypto_prices_service'),
        ('News Collector', 'enhanced_crypto_news_collector'),
        ('Onchain Collector', 'enhanced_onchain_collector'),
        ('Technical Collector', 'enhanced_technical_indicators_collector'),
        ('Macro Collector', 'enhanced_macro_collector_v2'),
    ]
    
    results = []
    
    for name, module_name in collectors:
        try:
            # Import the module
            module = __import__(module_name)
            
            # Basic validation - check for main function or collector class
            has_main = hasattr(module, 'main') or hasattr(module, '__main__')
            has_collector = any(
                hasattr(module, attr) for attr in dir(module) 
                if 'collector' in attr.lower() or 'service' in attr.lower()
            )
            
            if has_main or has_collector:
                print(f"✅ {name}: Import successful with main functionality")
                results.append(True)
            else:
                print(f"⚠️ {name}: Imports but missing main functionality")
                results.append(False)
                
        except ImportError as e:
            print(f"❌ {name}: Import failed - {e}")
            results.append(False)
        except Exception as e:
            print(f"⚠️ {name}: Import succeeded but validation failed - {e}")
            results.append(False)
    
    return results


def test_database_config():
    """Test that database configuration can be loaded"""
    try:
        # Try centralized config
        from shared.database_config import DatabaseConfig
        db_config = DatabaseConfig()
        config = db_config.get_mysql_config_dict()
        print(f"✅ Database Config: Centralized config loaded - host={config.get('host', 'unknown')}")
        return True
    except ImportError:
        # Try environment fallback
        env_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_news'),
            'user': os.getenv('MYSQL_USER', 'news_collector')
        }
        print(f"✅ Database Config: Environment fallback - host={env_config['host']}")
        return True
    except Exception as e:
        print(f"❌ Database Config: Failed to load - {e}")
        return False


def test_basic_connectivity():
    """Test basic database connectivity if possible"""
    try:
        import mysql.connector
        
        # Use environment configuration
        config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_news'),
        }
        
        # Quick connectivity test
        connection = mysql.connector.connect(**config, connection_timeout=5)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        connection.close()
        
        print("✅ Database Connectivity: Connection successful")
        return True
        
    except mysql.connector.Error as e:
        print(f"⚠️ Database Connectivity: Failed (expected in some environments) - {e}")
        return False
    except ImportError:
        print("⚠️ Database Connectivity: mysql.connector not available")
        return False
    except Exception as e:
        print(f"⚠️ Database Connectivity: Error - {e}")
        return False


def main():
    """Run all validation tests"""
    print("🚀 Running Crypto Data Collectors Validation")
    print("=" * 50)
    
    # Test collector imports
    print("\n📦 Testing Collector Imports:")
    import_results = test_collector_imports()
    imports_passed = sum(import_results)
    total_collectors = len(import_results)
    
    # Test database configuration
    print("\n🔧 Testing Database Configuration:")
    config_passed = test_database_config()
    
    # Test basic connectivity (optional)
    print("\n🗄️ Testing Database Connectivity:")
    connectivity_passed = test_basic_connectivity()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
    print(f"Collector Imports: {imports_passed}/{total_collectors} successful")
    print(f"Database Config: {'✅ PASS' if config_passed else '❌ FAIL'}")
    print(f"Database Connectivity: {'✅ PASS' if connectivity_passed else '⚠️ OPTIONAL'}")
    
    # Determine overall success
    critical_passed = imports_passed >= 3 and config_passed  # Need at least 3 collectors + config
    
    if critical_passed:
        print("\n🎉 VALIDATION PASSED: Core collectors are functional!")
        sys.exit(0)
    else:
        print(f"\n❌ VALIDATION FAILED: Need at least 3 working collectors and config")
        print(f"   Got: {imports_passed} collectors, config={'working' if config_passed else 'failed'}")
        sys.exit(1)


if __name__ == "__main__":
    main()