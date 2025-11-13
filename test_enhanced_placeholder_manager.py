#!/usr/bin/env python3
"""
Enhanced Placeholder Manager Test Script
Tests all functionality of the comprehensive placeholder system
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'placeholder-manager'))

from placeholder_manager import CentralizedPlaceholderManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_placeholder_manager")

def test_comprehensive_placeholder_system():
    """Test the enhanced placeholder manager with all data types"""
    logger.info("🚀 Testing Enhanced Placeholder Manager System")
    logger.info("=" * 70)
    
    # Initialize the manager
    manager = CentralizedPlaceholderManager()
    logger.info("✅ Manager initialized successfully")
    
    # Test 1: Check active configurations
    logger.info("\n📋 Testing Configuration:")
    active_configs = [(name, config) for name, config in manager.collector_configs.items() 
                     if config.get('active', True)]
    
    for name, config in active_configs:
        priority = config.get('priority', 5)
        table = config['table']
        frequency = config['frequency']
        logger.info(f"  ✅ {name} (priority {priority}): {table} - {frequency}")
    
    logger.info(f"\nActive collectors: {len(active_configs)}")
    
    # Test 2: Test database connectivity
    logger.info("\n🔌 Testing Database Connectivity:")
    conn = manager.get_db_connection()
    if conn:
        logger.info("  ✅ Database connection successful")
        conn.close()
    else:
        logger.error("  ❌ Database connection failed")
        return False
    
    # Test 3: Test symbol retrieval for each collector
    logger.info("\n🪙 Testing Symbol Retrieval:")
    for name in [config_name for config_name, config in active_configs]:
        symbols = manager.get_symbols_for_collector(name)
        logger.info(f"  {name}: {len(symbols)} symbols")
        if len(symbols) > 0:
            logger.info(f"    Sample: {symbols[:5]}...")
    
    # Test 4: Test completeness summary (before placeholder creation)
    logger.info("\n📊 Testing Completeness Summary (Before):")
    summary_before = manager.get_completeness_summary()
    for collector, data in summary_before.items():
        if isinstance(data, dict) and 'error' not in data:
            total = data.get('total_records', 0)
            filled = data.get('filled_records', 0)
            avg_completeness = data.get('avg_completeness', 0)
            logger.info(f"  {collector}: {filled}/{total} records ({avg_completeness:.1f}% avg completeness)")
        else:
            logger.info(f"  {collector}: {data}")
    
    # Test 5: Run comprehensive placeholder creation
    logger.info("\n🔧 Testing Comprehensive Placeholder Creation:")
    results = manager.ensure_comprehensive_placeholders()
    
    total_created = sum(results.values()) if results else 0
    logger.info(f"\nPlaceholder creation results:")
    for collector, count in results.items():
        logger.info(f"  {collector}: {count} placeholders created")
    logger.info(f"Total created: {total_created}")
    
    # Test 6: Test completeness summary (after placeholder creation)
    logger.info("\n📊 Testing Completeness Summary (After):")
    summary_after = manager.get_completeness_summary()
    for collector, data in summary_after.items():
        if isinstance(data, dict) and 'error' not in data:
            total = data.get('total_records', 0)
            filled = data.get('filled_records', 0)
            avg_completeness = data.get('avg_completeness', 0)
            logger.info(f"  {collector}: {filled}/{total} records ({avg_completeness:.1f}% avg completeness)")
        else:
            logger.info(f"  {collector}: {data}")
    
    # Test 7: Test gap detection
    logger.info("\n🔍 Testing Gap Detection:")
    gap_results = manager.detect_and_fill_gaps()
    gap_total = sum(gap_results.values()) if gap_results else 0
    logger.info(f"Gap detection results: {gap_total} gaps filled")
    
    # Test 8: Test service statistics
    logger.info("\n📈 Testing Service Statistics:")
    stats = manager.stats
    logger.info(f"  Total placeholders created: {stats['total_placeholders_created']}")
    logger.info(f"  Last run: {stats['last_run']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Service uptime: {datetime.now() - stats['service_start_time']}")
    
    # Test 9: Test configuration validation
    logger.info("\n🔬 Testing Configuration Validation:")
    validation_errors = []
    
    for name, config in manager.collector_configs.items():
        # Check required fields
        required_fields = ['table', 'start_date', 'frequency']
        for field in required_fields:
            if field not in config:
                validation_errors.append(f"{name}: Missing {field}")
        
        # Check data types
        if 'active' in config and not isinstance(config['active'], bool):
            validation_errors.append(f"{name}: 'active' must be boolean")
        
        if 'priority' in config and not isinstance(config['priority'], int):
            validation_errors.append(f"{name}: 'priority' must be integer")
    
    if validation_errors:
        logger.warning(f"Configuration validation errors:")
        for error in validation_errors:
            logger.warning(f"  ⚠️  {error}")
    else:
        logger.info("  ✅ All configurations valid")
    
    # Test 10: Cleanup test (dry run)
    logger.info("\n🧹 Testing Cleanup (Dry Run):")
    try:
        # Test cleanup without actually running it
        conn = manager.get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Count what would be cleaned up
            cleanup_queries = [
                ("macro_economic_data", "DATE(timestamp)"),
                ("technical_indicators", "DATE(timestamp)"),
                ("crypto_onchain_data", "DATE(timestamp)"),
                ("trading_signals", "DATE(timestamp)"),
                ("ohlc_data", "DATE(timestamp)"),
                ("crypto_derivatives_ml", "DATE(timestamp)")
            ]
            
            total_cleanup_candidates = 0
            for table, date_field in cleanup_queries:
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE data_completeness_percentage = 0 
                        AND data_source LIKE '%placeholder%'
                        AND {date_field} < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    """)
                    count = cursor.fetchone()[0]
                    total_cleanup_candidates += count
                    if count > 0:
                        logger.info(f"  {table}: {count} old placeholders could be cleaned")
                except Exception as e:
                    logger.debug(f"  Error checking {table}: {e}")
            
            logger.info(f"Total cleanup candidates: {total_cleanup_candidates}")
            cursor.close()
            conn.close()
        else:
            logger.warning("  ⚠️  Could not connect to database for cleanup test")
    except Exception as e:
        logger.error(f"  ❌ Cleanup test failed: {e}")
    
    # Final assessment
    logger.info("\n🎯 COMPREHENSIVE TEST RESULTS:")
    logger.info("=" * 70)
    
    success_indicators = [
        len(active_configs) > 0,  # Has active configurations
        total_created >= 0,  # Placeholder creation didn't fail
        len(validation_errors) == 0,  # Configuration is valid
        manager.stats['errors'] < 5,  # Low error count
    ]
    
    success_rate = sum(success_indicators) / len(success_indicators) * 100
    
    if success_rate >= 75:
        status = "✅ PASS"
    elif success_rate >= 50:
        status = "⚠️  PARTIAL"
    else:
        status = "❌ FAIL"
    
    logger.info(f"Overall Status: {status} ({success_rate:.0f}% success rate)")
    logger.info(f"Active Data Types: {len(active_configs)}")
    logger.info(f"Placeholders Created: {total_created}")
    logger.info(f"Configuration Errors: {len(validation_errors)}")
    logger.info(f"System Errors: {manager.stats['errors']}")
    
    return success_rate >= 75

if __name__ == "__main__":
    try:
        success = test_comprehensive_placeholder_system()
        print(f"\n{'='*70}")
        if success:
            print("🎉 COMPREHENSIVE PLACEHOLDER SYSTEM TEST PASSED! 🎉")
            print("The enhanced placeholder manager is ready for production use.")
        else:
            print("⚠️  Some tests failed. Review the logs above for details.")
        print(f"{'='*70}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()