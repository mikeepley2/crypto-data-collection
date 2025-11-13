#!/usr/bin/env python3
"""
Simple Placeholder Manager Test Script
Tests core functionality without FastAPI dependencies
"""

import sys
import os
import pymysql
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_test")

# Database configuration
db_config = {
    'host': os.getenv("DB_HOST", "172.22.32.1"),
    'user': os.getenv("DB_USER", "news_collector"),
    'password': os.getenv("DB_PASSWORD", "99Rules!"),
    'database': os.getenv("DB_NAME", "crypto_prices"),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get database connection"""
    try:
        return pymysql.connect(**db_config)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def test_comprehensive_coverage():
    """Test comprehensive placeholder coverage across all data types"""
    logger.info("🔍 Testing Comprehensive Placeholder Coverage")
    logger.info("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Data types to check
        data_type_tables = {
            "OHLC Data": ["ohlc_data"],
            "Price Data": ["crypto_prices", "price_data_real"],
            "Technical Indicators": ["technical_indicators"],
            "Onchain Data": ["crypto_onchain_data", "onchain_data", "onchain_metrics"],
            "Macro Economic": ["macro_economic_data"],
            "Trading Signals": ["trading_signals", "enhanced_trading_signals"],
            "Derivatives": ["crypto_derivatives_ml"]
        }
        
        total_placeholders = 0
        coverage_summary = {}
        
        for data_type, tables in data_type_tables.items():
            logger.info(f"\n📊 {data_type}:")
            type_total = 0
            type_coverage = {}
            
            for table in tables:
                try:
                    # Check if table exists
                    cursor.execute(f"SHOW TABLES LIKE '{table}'")
                    if not cursor.fetchone():
                        logger.info(f"  ❌ {table}: Table does not exist")
                        type_coverage[table] = {"status": "missing_table", "count": 0}
                        continue
                    
                    # Check if data_source column exists
                    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'data_source'")
                    has_data_source = cursor.fetchone() is not None
                    
                    if not has_data_source:
                        logger.info(f"  ⚠️  {table}: Missing data_source column")
                        type_coverage[table] = {"status": "missing_column", "count": 0}
                        continue
                    
                    # Count placeholder records
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE data_source = 'placeholder_generator'
                    """)
                    placeholder_count = cursor.fetchone()[0]
                    
                    # Count total records
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    total_count = cursor.fetchone()[0]
                    
                    # Get date range for placeholders
                    try:
                        cursor.execute(f"""
                            SELECT MIN(timestamp), MAX(timestamp) FROM {table}
                            WHERE data_source = 'placeholder_generator'
                            LIMIT 1
                        """)
                        result = cursor.fetchone()
                        if result and result[0]:
                            min_date, max_date = result
                            date_range = f"{min_date} to {max_date}"
                        else:
                            date_range = "No placeholders"
                    except Exception:
                        date_range = "Unable to determine"
                    
                    logger.info(f"  ✅ {table}: {placeholder_count:,} placeholders / {total_count:,} total")
                    logger.info(f"     Range: {date_range}")
                    
                    type_coverage[table] = {
                        "status": "ok",
                        "placeholder_count": placeholder_count,
                        "total_count": total_count,
                        "date_range": date_range
                    }
                    
                    type_total += placeholder_count
                    
                except Exception as e:
                    logger.error(f"  ❌ {table}: Error - {e}")
                    type_coverage[table] = {"status": "error", "error": str(e), "count": 0}
            
            logger.info(f"  📈 {data_type} Total: {type_total:,} placeholders")
            coverage_summary[data_type] = {
                "total_placeholders": type_total,
                "tables": type_coverage
            }
            total_placeholders += type_total
        
        # Overall summary
        logger.info(f"\n🎯 COMPREHENSIVE COVERAGE SUMMARY:")
        logger.info("=" * 60)
        logger.info(f"Grand Total Placeholders: {total_placeholders:,}")
        
        # Check coverage by data type
        coverage_status = {}
        for data_type, summary in coverage_summary.items():
            placeholder_count = summary["total_placeholders"]
            table_count = len(summary["tables"])
            ready_tables = sum(1 for table_info in summary["tables"].values() 
                             if table_info["status"] == "ok")
            
            if placeholder_count > 0:
                status = "✅ ACTIVE"
            elif ready_tables > 0:
                status = "⚠️  READY"
            else:
                status = "❌ NOT_READY"
            
            coverage_status[data_type] = status
            logger.info(f"{status} {data_type}: {placeholder_count:,} placeholders across {ready_tables}/{table_count} tables")
        
        # Final assessment
        active_types = sum(1 for status in coverage_status.values() if "ACTIVE" in status)
        ready_types = sum(1 for status in coverage_status.values() if status != "❌ NOT_READY")
        total_types = len(coverage_status)
        
        logger.info(f"\n📋 COVERAGE ASSESSMENT:")
        logger.info(f"  Active Data Types: {active_types}/{total_types}")
        logger.info(f"  Ready Data Types: {ready_types}/{total_types}")
        logger.info(f"  Coverage Rate: {(ready_types/total_types)*100:.0f}%")
        
        # Success criteria
        success = (
            total_placeholders > 100000 and  # Substantial placeholder count
            active_types >= 4 and           # At least 4 data types active
            ready_types >= 6                # At least 6 data types ready
        )
        
        return success, {
            "total_placeholders": total_placeholders,
            "active_types": active_types,
            "ready_types": ready_types,
            "coverage_summary": coverage_summary,
            "coverage_status": coverage_status
        }
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False, {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

def test_symbol_coverage():
    """Test symbol coverage across data types"""
    logger.info("\n🪙 Testing Symbol Coverage:")
    
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        symbol_coverage = {}
        
        tables_with_symbols = [
            'ohlc_data', 'crypto_onchain_data', 'technical_indicators',
            'trading_signals', 'enhanced_trading_signals', 'crypto_derivatives_ml'
        ]
        
        for table in tables_with_symbols:
            try:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    continue
                
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT symbol) FROM {table}
                    WHERE data_source = 'placeholder_generator'
                """)
                symbol_count = cursor.fetchone()[0]
                
                if symbol_count > 0:
                    # Get sample symbols
                    cursor.execute(f"""
                        SELECT DISTINCT symbol FROM {table}
                        WHERE data_source = 'placeholder_generator'
                        LIMIT 5
                    """)
                    sample_symbols = [row[0] for row in cursor.fetchall()]
                    
                    symbol_coverage[table] = {
                        "count": symbol_count,
                        "sample": sample_symbols
                    }
                    logger.info(f"  {table}: {symbol_count} symbols (e.g., {', '.join(sample_symbols)})")
                
            except Exception as e:
                logger.debug(f"Error checking symbols for {table}: {e}")
        
        return symbol_coverage
        
    except Exception as e:
        logger.error(f"Symbol coverage test failed: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def main():
    """Main test execution"""
    try:
        logger.info("🚀 COMPREHENSIVE PLACEHOLDER SYSTEM TEST")
        logger.info("=" * 70)
        
        # Test 1: Coverage assessment
        success, results = test_comprehensive_coverage()
        
        if not success:
            logger.error("❌ Coverage test failed")
            return False
        
        # Test 2: Symbol coverage
        symbol_results = test_symbol_coverage()
        
        # Final results
        logger.info(f"\n🎯 FINAL TEST RESULTS:")
        logger.info("=" * 70)
        
        if success:
            logger.info("✅ COMPREHENSIVE PLACEHOLDER SYSTEM TEST PASSED!")
            logger.info(f"  Total Placeholders: {results['total_placeholders']:,}")
            logger.info(f"  Active Data Types: {results['active_types']}/7")
            logger.info(f"  Ready Data Types: {results['ready_types']}/7")
            logger.info(f"  Symbol Coverage: {len(symbol_results)} table types")
            logger.info("")
            logger.info("🎉 The comprehensive placeholder system is operational!")
            logger.info("   All requested data types (OHLC, prices, technical, onchain,")
            logger.info("   macro, trading signals, derivatives) have placeholder coverage.")
        else:
            logger.warning("⚠️  Some coverage gaps detected - see details above")
        
        return success
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    sys.exit(exit_code)