#!/usr/bin/env python3
"""
Automated Data Migration and Table Cleanup Script
Automatically migrates data and renames old tables
"""

import mysql.connector
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_automated_migration():
    """Execute automated data migration and cleanup"""
    
    print("🚀 AUTOMATED CRYPTO DATA MIGRATION AND CLEANUP")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Database connection
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    migration_results = []
    
    print("\n🔄 EXECUTING DATA MIGRATIONS")
    print("=" * 40)
    
    # Migration 1: price_data -> hourly_data
    print("\n1. MIGRATING price_data -> hourly_data")
    print("-" * 40)
    
    try:
        config = db_config.copy()
        config['database'] = 'crypto_prices'
        
        with mysql.connector.connect(**config) as conn:
            cursor = conn.cursor()
            
            # Check source table
            cursor.execute("SELECT COUNT(*) FROM price_data")
            source_count = cursor.fetchone()[0]
            print(f"   Source records: {source_count:,}")
            
            # Get common columns between price_data and hourly_data
            cursor.execute("SHOW COLUMNS FROM price_data")
            price_data_cols = [col[0] for col in cursor.fetchall()]
            
            cursor.execute("SHOW COLUMNS FROM hourly_data")
            hourly_data_cols = [col[0] for col in cursor.fetchall()]
            
            print(f"   price_data columns: {', '.join(price_data_cols[:5])}...")
            print(f"   hourly_data columns: {', '.join(hourly_data_cols)}")
            
            # Find mappable columns (price_data might have close -> hourly_data needs close)
            # price_data has: symbol, high_24h, low_24h, open_24h, close, volume_usd_24h, timestamp
            # hourly_data has: symbol, timestamp, open, high, low, close, volume
            
            migration_sql = """
                INSERT IGNORE INTO hourly_data (symbol, timestamp, open, high, low, close, volume)
                SELECT 
                    symbol,
                    timestamp,
                    COALESCE(open_24h, close) as open,
                    COALESCE(high_24h, close) as high, 
                    COALESCE(low_24h, close) as low,
                    close,
                    COALESCE(volume_usd_24h, 0) as volume
                FROM price_data 
                WHERE symbol IS NOT NULL 
                AND timestamp IS NOT NULL
                AND close IS NOT NULL
            """
            
            print("   🔄 Executing migration...")
            cursor.execute(migration_sql)
            migrated_count = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Migrated {migrated_count:,} records to hourly_data")
            migration_results.append(('price_data -> hourly_data', migrated_count, 'SUCCESS'))
            
    except Exception as e:
        print(f"   ❌ Migration failed: {e}")
        migration_results.append(('price_data -> hourly_data', 0, f'FAILED: {e}'))
    
    # Migration 2: ohlc_data -> hourly_data
    print("\n2. MIGRATING ohlc_data -> hourly_data")
    print("-" * 40)
    
    try:
        config['database'] = 'crypto_prices'
        
        with mysql.connector.connect(**config) as conn:
            cursor = conn.cursor()
            
            # Check if ohlc_data exists and get its structure
            cursor.execute("SELECT COUNT(*) FROM ohlc_data")
            source_count = cursor.fetchone()[0]
            print(f"   Source records: {source_count:,}")
            
            cursor.execute("SHOW COLUMNS FROM ohlc_data")
            ohlc_cols = [col[0] for col in cursor.fetchall()]
            print(f"   ohlc_data columns: {', '.join(ohlc_cols[:7])}")
            
            # OHLC data should have standard OHLC columns
            migration_sql = """
                INSERT IGNORE INTO hourly_data (symbol, timestamp, open, high, low, close, volume)
                SELECT 
                    symbol,
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    COALESCE(volume, 0) as volume
                FROM ohlc_data 
                WHERE symbol IS NOT NULL 
                AND timestamp IS NOT NULL
            """
            
            print("   🔄 Executing migration...")
            cursor.execute(migration_sql)
            migrated_count = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Migrated {migrated_count:,} records from ohlc_data")
            migration_results.append(('ohlc_data -> hourly_data', migrated_count, 'SUCCESS'))
            
    except Exception as e:
        print(f"   ❌ Migration failed: {e}")
        migration_results.append(('ohlc_data -> hourly_data', 0, f'FAILED: {e}'))
    
    # Migration 3: sentiment_data -> crypto_sentiment_data
    print("\n3. MIGRATING sentiment_data -> crypto_sentiment_data")
    print("-" * 50)
    
    try:
        config['database'] = 'crypto_news'
        
        with mysql.connector.connect(**config) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM sentiment_data")
            source_count = cursor.fetchone()[0]
            print(f"   Source records: {source_count:,}")
            
            if source_count > 0:
                # Get common columns
                cursor.execute("SHOW COLUMNS FROM sentiment_data")
                sentiment_cols = [col[0] for col in cursor.fetchall()]
                
                cursor.execute("SHOW COLUMNS FROM crypto_sentiment_data")
                crypto_sentiment_cols = [col[0] for col in cursor.fetchall()]
                
                common_cols = list(set(sentiment_cols) & set(crypto_sentiment_cols))
                print(f"   Common columns: {', '.join(common_cols[:5])}")
                
                if common_cols:
                    columns_str = ', '.join(f'`{col}`' for col in common_cols)
                    
                    migration_sql = f"""
                        INSERT IGNORE INTO crypto_sentiment_data ({columns_str})
                        SELECT {columns_str} FROM sentiment_data
                    """
                    
                    print("   🔄 Executing migration...")
                    cursor.execute(migration_sql)
                    migrated_count = cursor.rowcount
                    conn.commit()
                    
                    print(f"   ✅ Migrated {migrated_count:,} records to crypto_sentiment_data")
                    migration_results.append(('sentiment_data -> crypto_sentiment_data', migrated_count, 'SUCCESS'))
                else:
                    print("   ⚠️  No common columns found")
                    migration_results.append(('sentiment_data -> crypto_sentiment_data', 0, 'SKIPPED: No common columns'))
            else:
                print("   ℹ️  No data to migrate")
                migration_results.append(('sentiment_data -> crypto_sentiment_data', 0, 'SKIPPED: Empty table'))
                
    except Exception as e:
        print(f"   ❌ Migration failed: {e}")
        migration_results.append(('sentiment_data -> crypto_sentiment_data', 0, f'FAILED: {e}'))
    
    # Table Renaming
    print(f"\n🏷️  RENAMING OLD TABLES")
    print("=" * 30)
    
    tables_to_rename = [
        ('crypto_prices', 'price_data'),
        ('crypto_prices', 'ohlc_data'),
        ('crypto_news', 'sentiment_data')
    ]
    
    for db_name, table_name in tables_to_rename:
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if cursor.fetchone():
                    
                    # Check if _old version already exists
                    cursor.execute(f"SHOW TABLES LIKE '{table_name}_old'")
                    if cursor.fetchone():
                        print(f"  ⚠️  {db_name}.{table_name}_old already exists, skipping")
                        continue
                    
                    # Rename table
                    cursor.execute(f"RENAME TABLE `{table_name}` TO `{table_name}_old`")
                    print(f"  ✅ Renamed {db_name}.{table_name} -> {table_name}_old")
                    
                else:
                    print(f"  ℹ️  {db_name}.{table_name} doesn't exist, skipping")
                    
        except Exception as e:
            print(f"  ❌ Failed to rename {db_name}.{table_name}: {e}")
    
    # Summary
    print(f"\n📋 MIGRATION SUMMARY")
    print("=" * 30)
    
    for migration, count, status in migration_results:
        status_icon = "✅" if status == 'SUCCESS' else "⚠️" if 'SKIP' in status else "❌"
        print(f"  {status_icon} {migration:30} | {count:>8,} records | {status}")
    
    print(f"\n✨ MIGRATION AND CLEANUP COMPLETE!")
    print("🎯 Data consolidated into enhanced tables")
    print("📊 Old tables preserved with '_old' suffix")
    print("🚀 System now using optimized table structure")
    
    return migration_results


if __name__ == "__main__":
    execute_automated_migration()