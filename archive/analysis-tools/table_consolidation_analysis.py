#!/usr/bin/env python3
"""
Table Consolidation Analysis and Execution Script
Analyzes database tables, identifies duplicates, and creates consolidation plan
"""

import sys
import os
sys.path.append('/mnt/e/git/crypto-data-collection')
from shared.table_config import *

# Table Analysis Results from Database Inventory
DATABASE_TABLES = {
    # Core approved tables according to centralized config
    "crypto_assets": {"records": 362, "status": "approved", "config_key": "ASSETS"},
    "crypto_onchain_data": {"records": 79845, "status": "approved", "config_key": "ONCHAIN_DATA"},
    "crypto_news": {"records": 147675, "status": "approved", "config_key": "NEWS"},
    "technical_indicators": {"records": 3815288, "status": "approved", "config_key": "INDICATORS"},
    "macro_indicators": {"records": 49959, "status": "approved", "config_key": "MACRO"},
    "sentiment_aggregation": {"records": 67721, "status": "approved", "config_key": "SENTIMENT"},
    "ml_features_materialized": {"records": 3753076, "status": "approved", "config_key": "FEATURES"},
    "trading_signals": {"records": 132045, "status": "approved", "config_key": "SIGNALS"},
    "trade_recommendations": {"records": 86615, "status": "approved", "config_key": "RECOMMENDATIONS"},
    "ohlc_data": {"records": 524659, "status": "approved", "config_key": "OHLC"},
    
    # Tables currently used by collectors but not in centralized config
    "price_data_real": {"records": 4698205, "status": "collector_target", "used_by": "enhanced-crypto-prices"},
    "real_time_sentiment_signals": {"records": 113853, "status": "collector_target", "used_by": "enhanced-sentiment-collector"},
    
    # Duplicate/Enhanced tables that need consolidation
    "crypto_onchain_data_enhanced_backup_20251104_224552": {
        "records": 25544, 
        "status": "duplicate", 
        "merge_into": "crypto_onchain_data",
        "date_range": "2025-09-03 to 2025-09-27"
    },
    
    # Archive tables (empty, can be dropped)
    "crypto_news_archive": {"records": 0, "status": "archive_empty"},
    "news_data_archive": {"records": 0, "status": "archive_empty"},
    "reddit_posts_archive": {"records": 0, "status": "archive_empty"},
    "social_media_posts_archive": {"records": 0, "status": "archive_empty"},
    "stock_market_news_data_archive": {"records": 0, "status": "archive_empty"},
    "stock_news_archive": {"records": 0, "status": "archive_empty"},
    
    # Old/Backup tables that need archiving
    "price_data_old": {"records": 71905, "status": "needs_archive"},
    "ml_trading_signals_old": {"records": 2729, "status": "needs_archive"},
    "technical_indicators_backup_20251104_214228": {"records": 1000, "status": "needs_archive"},
    "technical_indicators_backup_20251104_214305": {"records": 1000, "status": "needs_archive"},
    "technical_indicators_corrupted_backup": {"records": 120962, "status": "needs_archive"},
    "assets_archived": {"records": 315, "status": "needs_archive"},
    
    # Views with errors (need fixing)
    "crypto_prices": {"status": "view_broken"},
    "onchain_metrics": {"status": "view_broken"},
    
    # Working tables
    "service_monitoring": {"records": 223673, "status": "operational"},
    "market_conditions_history": {"records": 0, "status": "operational"},
    "enhanced_trading_signals": {"records": 0, "status": "operational"},
    "social_sentiment_metrics": {"records": 0, "status": "operational"},
    "portfolio_optimizations": {"records": 0, "status": "operational"},
    "backtesting_results": {"records": 0, "status": "operational"},
    "backtesting_trades": {"records": 0, "status": "operational"}
}

# Current Collector Table Usage
COLLECTOR_TABLE_USAGE = {
    "crypto-news-collector": {
        "target_table": "crypto_news",
        "status": "correct",
        "config_match": True
    },
    "enhanced-crypto-prices": {
        "target_table": "price_data_real",
        "status": "incorrect",
        "config_match": False,
        "should_target": "technical_indicators"
    },
    "onchain-collector": {
        "target_table": "crypto_onchain_data",
        "status": "correct", 
        "config_match": True
    },
    "macro-collector": {
        "target_table": "macro_indicators",
        "status": "correct",
        "config_match": True
    },
    "enhanced-sentiment-collector": {
        "target_table": "real_time_sentiment_signals",
        "status": "incorrect",
        "config_match": False,
        "should_target": "sentiment_aggregation"
    },
    "technical-calculator": {
        "target_table": "technical_indicators",
        "status": "correct",
        "config_match": True
    }
}

def analyze_table_discrepancies():
    """Analyze differences between actual usage and centralized config"""
    print("🔍 TABLE USAGE ANALYSIS")
    print("=" * 60)
    
    print("\n✅ CORRECTLY CONFIGURED COLLECTORS:")
    for collector, config in COLLECTOR_TABLE_USAGE.items():
        if config["config_match"]:
            print(f"   {collector} -> {config['target_table']}")
    
    print("\n❌ INCORRECTLY CONFIGURED COLLECTORS:")
    for collector, config in COLLECTOR_TABLE_USAGE.items():
        if not config["config_match"]:
            print(f"   {collector}")
            print(f"      Current: {config['target_table']}")
            print(f"      Should be: {config['should_target']}")
    
    print("\n🔄 DUPLICATE TABLES REQUIRING CONSOLIDATION:")
    for table, info in DATABASE_TABLES.items():
        if info["status"] == "duplicate":
            print(f"   {table} ({info['records']:,} records) -> {info['merge_into']}")
            print(f"      Date range: {info['date_range']}")
    
    print("\n🗃️ TABLES TO ARCHIVE:")
    for table, info in DATABASE_TABLES.items():
        if info["status"] == "needs_archive":
            print(f"   {table} ({info['records']:,} records) -> {table}_Archive")
    
    print("\n🗑️ EMPTY ARCHIVE TABLES TO DROP:")
    for table, info in DATABASE_TABLES.items():
        if info["status"] == "archive_empty":
            print(f"   {table}")

def generate_consolidation_sql():
    """Generate SQL commands for table consolidation"""
    print("\n🔧 SQL CONSOLIDATION COMMANDS")
    print("=" * 60)
    
    print("\n-- STEP 1: Consolidate duplicate data")
    print("-- Merge crypto_onchain_data_enhanced_backup into crypto_onchain_data")
    print("""
INSERT IGNORE INTO crypto_onchain_data 
SELECT * FROM crypto_onchain_data_enhanced_backup_20251104_224552 
WHERE timestamp NOT IN (
    SELECT timestamp FROM crypto_onchain_data 
    WHERE coin_symbol = crypto_onchain_data_enhanced_backup_20251104_224552.coin_symbol
);
""")
    
    print("\n-- STEP 2: Archive old tables")
    archive_tables = [table for table, info in DATABASE_TABLES.items() if info["status"] == "needs_archive"]
    for table in archive_tables:
        print(f"RENAME TABLE `{table}` TO `{table}_Archive`;")
    
    print("\n-- STEP 3: Drop empty archive tables")
    empty_archives = [table for table, info in DATABASE_TABLES.items() if info["status"] == "archive_empty"]
    for table in empty_archives:
        print(f"DROP TABLE IF EXISTS `{table}`;")
    
    print("\n-- STEP 4: Fix broken views")
    print("""
-- Fix crypto_prices view to point to technical_indicators
DROP VIEW IF EXISTS crypto_prices;
CREATE VIEW crypto_prices AS 
SELECT symbol, current_price, price_change_24h, volume_usd_24h, market_cap, timestamp_iso as timestamp
FROM technical_indicators 
WHERE current_price IS NOT NULL;

-- Fix onchain_metrics view  
DROP VIEW IF EXISTS onchain_metrics;
CREATE VIEW onchain_metrics AS
SELECT coin_symbol as symbol, market_cap, volume_24h, circulating_supply, timestamp
FROM crypto_onchain_data
WHERE market_cap IS NOT NULL;
""")

def generate_collector_updates():
    """Generate commands to update collector configurations"""
    print("\n🔄 COLLECTOR CONFIGURATION UPDATES")
    print("=" * 60)
    
    print("\n-- Update enhanced-crypto-prices to target technical_indicators")
    print("""
kubectl patch deployment enhanced-crypto-prices -n crypto-data-collection --type='merge' -p='{"spec":{"template":{"spec":{"containers":[{"name":"enhanced-crypto-prices","env":[{"name":"CRYPTO_PRICES_TABLE","value":"technical_indicators"}]}]}}}}'
""")
    
    print("\n-- Update enhanced-sentiment-collector to target sentiment_aggregation")  
    print("""
kubectl patch deployment enhanced-sentiment-collector -n crypto-data-collection --type='merge' -p='{"spec":{"template":{"spec":{"containers":[{"name":"enhanced-sentiment-collector","env":[{"name":"SENTIMENT_TABLE","value":"sentiment_aggregation"}]}]}}}}'
""")

def generate_validation_script():
    """Generate updated validation script with correct table names"""
    print("\n✅ UPDATED VALIDATION SCRIPT")
    print("=" * 60)
    
    validation_script = """
#!/usr/bin/env python3
import mysql.connector
import os
from datetime import datetime, timedelta

# Database connection using centralized config
conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST', 'host.docker.internal'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_USER', 'news_collector'),
    password=os.getenv('MYSQL_PASSWORD', '99Rules!'),
    database=os.getenv('MYSQL_DATABASE', 'crypto_prices')
)

cursor = conn.cursor()
recent_threshold = datetime.now() - timedelta(hours=24)

print("📊 COLLECTOR HEALTH VALIDATION (Updated)")
print("=" * 60)

# Check each collector's target table with correct names
collectors = {
    "crypto-news-collector": "crypto_news",
    "enhanced-crypto-prices": "technical_indicators", 
    "onchain-collector": "crypto_onchain_data",
    "macro-collector": "macro_indicators", 
    "enhanced-sentiment-collector": "sentiment_aggregation",
    "technical-calculator": "technical_indicators"
}

health_scores = {}
for collector, table in collectors.items():
    try:
        # Get recent record count
        cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE timestamp_iso >= %s", (recent_threshold,))
        recent_count = cursor.fetchone()[0]
        
        # Get total records
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        total_count = cursor.fetchone()[0]
        
        # Get latest timestamp
        cursor.execute(f"SELECT MAX(timestamp_iso) FROM `{table}`")
        latest = cursor.fetchone()[0]
        
        # Calculate health score
        hours_ago = (datetime.now() - latest).total_seconds() / 3600 if latest else 999
        score = max(0, 100 - (hours_ago * 10))  # Lose 10 points per hour old
        
        health_scores[collector] = score
        
        print(f"\\n{collector}:")
        print(f"  Table: {table}")
        print(f"  Total Records: {total_count:,}")
        print(f"  Recent (24h): {recent_count:,}")
        print(f"  Latest: {latest}")
        print(f"  Health Score: {score:.1f}/100")
        
    except Exception as e:
        print(f"\\n{collector}: ERROR - {e}")
        health_scores[collector] = 0

cursor.close()
conn.close()

overall_health = sum(health_scores.values()) / len(health_scores)
print(f"\\n🎯 OVERALL HEALTH SCORE: {overall_health:.1f}/100")
"""
    
    with open('updated_collector_validation.py', 'w') as f:
        f.write(validation_script)
    
    print("✅ Validation script saved as 'updated_collector_validation.py'")

def main():
    """Run complete table consolidation analysis"""
    print("🚀 CRYPTO DATA COLLECTION - TABLE CONSOLIDATION PLAN")
    print("=" * 80)
    
    analyze_table_discrepancies()
    generate_consolidation_sql()
    generate_collector_updates() 
    generate_validation_script()
    
    print("\n📋 EXECUTION SUMMARY")
    print("=" * 60)
    print("1. ✅ Execute SQL consolidation commands")
    print("2. 🔄 Update collector configurations") 
    print("3. ♻️  Restart affected collectors")
    print("4. ✅ Run updated validation script")
    print("5. 📊 Verify improved health scores")
    
    print("\n⚠️  IMPORTANT: Backup database before executing consolidation!")

if __name__ == "__main__":
    main()