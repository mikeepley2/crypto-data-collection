#!/usr/bin/env python3
"""
Data Migration and Table Cleanup Script
1. Migrate data from smaller tables to enhanced comprehensive tables
2. Rename old tables with '_old' suffix for cleanup
"""

import mysql.connector
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_data_migration_opportunities():
    """Analyze what data needs to be migrated between tables"""
    
    print("DATA MIGRATION ANALYSIS")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Database connection
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    migration_opportunities = []
    
    # Check crypto_prices database
    print("\n📊 CRYPTO_PRICES DATABASE ANALYSIS:")
    print("-" * 40)
    
    try:
        config = db_config.copy()
        config['database'] = 'crypto_prices'
        
        with mysql.connector.connect(**config) as conn:
            cursor = conn.cursor()
            
            # Analyze price tables
            price_tables = {
                'price_data': {'target': 'hourly_data', 'priority': 'HIGH'},
                'price_data_real': {'target': 'KEEP', 'priority': 'COMPREHENSIVE'},
                'hourly_data': {'target': 'KEEP', 'priority': 'ACTIVE'},
                'ml_features_materialized': {'target': 'ANALYZE', 'priority': 'ML'},
                'ohlc_data': {'target': 'hourly_data', 'priority': 'MEDIUM'},
                'technical_indicators': {'target': 'ANALYZE', 'priority': 'TECHNICAL'}
            }
            
            for table_name, info in price_tables.items():
                try:
                    # Get table info
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    total_count = cursor.fetchone()[0]
                    
                    # Check recent data
                    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
                    columns = [col[0] for col in cursor.fetchall()]
                    
                    timestamp_cols = [col for col in columns if 'timestamp' in col.lower() or 'time' in col.lower()]
                    
                    recent_count = 0
                    latest_timestamp = None
                    
                    if timestamp_cols:
                        ts_col = timestamp_cols[0]
                        try:
                            cursor.execute(f"""
                                SELECT COUNT(*) as recent_count, MAX(`{ts_col}`) as latest 
                                FROM `{table_name}` 
                                WHERE `{ts_col}` >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                            """)
                            result = cursor.fetchone()
                            recent_count = result[0] if result else 0
                            latest_timestamp = result[1] if result else None
                        except:
                            pass
                    
                    # Determine migration action
                    status = "ACTIVE" if recent_count > 0 else "HISTORICAL"
                    action = "KEEP" if info['target'] == 'KEEP' else f"MIGRATE to {info['target']}"
                    
                    print(f"  {table_name:25} | {total_count:>10,} | {recent_count:>6} recent | {status:>10} | {action}")
                    
                    # Add to migration opportunities
                    if info['target'] not in ['KEEP', 'ANALYZE'] and total_count > 0:
                        migration_opportunities.append({
                            'source': table_name,
                            'target': info['target'],
                            'database': 'crypto_prices',
                            'records': total_count,
                            'priority': info['priority'],
                            'recent': recent_count
                        })
                        
                except Exception as e:
                    print(f"  {table_name:25} | ERROR: {e}")
    
    except Exception as e:
        print(f"Error analyzing crypto_prices: {e}")
    
    # Check crypto_news database
    print("\n📰 CRYPTO_NEWS DATABASE ANALYSIS:")
    print("-" * 40)
    
    try:
        config = db_config.copy()
        config['database'] = 'crypto_news'
        
        with mysql.connector.connect(**config) as conn:
            cursor = conn.cursor()
            
            news_tables = {
                'crypto_news_data': {'target': 'KEEP', 'priority': 'PRIMARY'},
                'news_data': {'target': 'KEEP', 'priority': 'COMPREHENSIVE'},
                'social_media_posts': {'target': 'KEEP', 'priority': 'SOCIAL'},
                'crypto_sentiment_data': {'target': 'KEEP', 'priority': 'SENTIMENT'},
                'social_sentiment_data': {'target': 'KEEP', 'priority': 'SOCIAL_SENTIMENT'},
                'sentiment_data': {'target': 'crypto_sentiment_data', 'priority': 'LOW'},
                'technical_indicators': {'target': 'crypto_prices.technical_indicators', 'priority': 'MEDIUM'}
            }
            
            for table_name, info in news_tables.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    total_count = cursor.fetchone()[0]
                    
                    status = "DATA" if total_count > 0 else "EMPTY"
                    action = "KEEP" if info['target'] == 'KEEP' else f"MIGRATE to {info['target']}"
                    
                    print(f"  {table_name:25} | {total_count:>10,} | {status:>10} | {action}")
                    
                    # Add small tables to migration list
                    if info['target'] != 'KEEP' and total_count > 0 and total_count < 50000:
                        migration_opportunities.append({
                            'source': table_name,
                            'target': info['target'],
                            'database': 'crypto_news',
                            'records': total_count,
                            'priority': info['priority'],
                            'recent': 0
                        })
                        
                except Exception as e:
                    print(f"  {table_name:25} | ERROR: {e}")
    
    except Exception as e:
        print(f"Error analyzing crypto_news: {e}")
    
    return migration_opportunities


def execute_data_migrations(migration_opportunities):
    """Execute the data migrations"""
    
    print(f"\n🔄 EXECUTING DATA MIGRATIONS")
    print("=" * 40)
    
    if not migration_opportunities:
        print("No migrations needed - all data is already in optimal tables!")
        return True
    
    # Database connection
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    # Sort by priority
    priority_order = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    migration_opportunities.sort(key=lambda x: priority_order.get(x['priority'], 4))
    
    for migration in migration_opportunities:
        print(f"\n📋 MIGRATION: {migration['database']}.{migration['source']} -> {migration['target']}")
        print(f"   Records: {migration['records']:,} | Priority: {migration['priority']}")
        
        try:
            config = db_config.copy()
            config['database'] = migration['database']
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                # Get source table structure
                cursor.execute(f"SHOW COLUMNS FROM `{migration['source']}`")
                source_columns = [col[0] for col in cursor.fetchall()]
                
                # Get target table structure
                if '.' in migration['target']:
                    target_db, target_table = migration['target'].split('.')
                    cursor.execute(f"SHOW COLUMNS FROM `{target_db}`.`{target_table}`")
                else:
                    cursor.execute(f"SHOW COLUMNS FROM `{migration['target']}`")
                target_columns = [col[0] for col in cursor.fetchall()]
                
                # Find common columns
                common_columns = list(set(source_columns) & set(target_columns))
                
                if common_columns:
                    print(f"   ✅ Common columns: {', '.join(common_columns[:5])}{'...' if len(common_columns) > 5 else ''}")
                    
                    # Create INSERT statement for migration
                    columns_str = ', '.join(f'`{col}`' for col in common_columns)
                    
                    if '.' in migration['target']:
                        target_full = migration['target']
                    else:
                        target_full = f"`{migration['target']}`"
                    
                    # Use INSERT IGNORE to avoid duplicates
                    migration_sql = f"""
                        INSERT IGNORE INTO {target_full} ({columns_str})
                        SELECT {columns_str} FROM `{migration['source']}`
                    """
                    
                    print(f"   🔄 Executing migration...")
                    cursor.execute(migration_sql)
                    
                    migrated_count = cursor.rowcount
                    conn.commit()
                    
                    print(f"   ✅ Migrated {migrated_count:,} records successfully")
                    
                else:
                    print(f"   ⚠️  No common columns found - manual migration needed")
                    
        except Exception as e:
            print(f"   ❌ Migration failed: {e}")
    
    return True


def rename_old_tables():
    """Rename tables to _old suffix for cleanup"""
    
    print(f"\n🏷️  RENAMING OLD TABLES")
    print("=" * 30)
    
    # Database connection
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    # Tables to rename (only smaller/redundant ones)
    tables_to_rename = {
        'crypto_prices': [
            'price_data',  # Now using hourly_data
            'ohlc_data',   # Migrated to hourly_data  
        ],
        'crypto_news': [
            'sentiment_data',  # Small table, migrated to crypto_sentiment_data
        ]
    }
    
    for db_name, table_list in tables_to_rename.items():
        print(f"\n📊 DATABASE: {db_name}")
        print("-" * 25)
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                for table_name in table_list:
                    try:
                        # Check if table exists
                        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                        if cursor.fetchone():
                            
                            # Check if _old version already exists
                            cursor.execute(f"SHOW TABLES LIKE '{table_name}_old'")
                            if cursor.fetchone():
                                print(f"  ⚠️  {table_name}_old already exists, skipping")
                                continue
                            
                            # Rename table
                            cursor.execute(f"RENAME TABLE `{table_name}` TO `{table_name}_old`")
                            print(f"  ✅ Renamed {table_name} -> {table_name}_old")
                            
                        else:
                            print(f"  ℹ️  {table_name} doesn't exist, skipping")
                            
                    except Exception as e:
                        print(f"  ❌ Failed to rename {table_name}: {e}")
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error with database {db_name}: {e}")


def main():
    """Main migration and cleanup process"""
    
    print("🚀 CRYPTO DATA MIGRATION AND CLEANUP")
    print("=" * 60)
    
    # Step 1: Analyze migration opportunities
    migration_opportunities = analyze_data_migration_opportunities()
    
    # Step 2: Execute migrations
    if migration_opportunities:
        print(f"\n📋 MIGRATION PLAN:")
        print("-" * 20)
        for mig in migration_opportunities:
            print(f"  • {mig['database']}.{mig['source']} -> {mig['target']} ({mig['records']:,} records)")
        
        response = input(f"\nProceed with migrations? (y/n): ")
        if response.lower() == 'y':
            execute_data_migrations(migration_opportunities)
        else:
            print("⏸️  Migrations skipped")
    
    # Step 3: Rename old tables
    print(f"\n📋 TABLE CLEANUP PLAN:")
    print("-" * 25)
    print("  • price_data -> price_data_old")
    print("  • ohlc_data -> ohlc_data_old")
    print("  • sentiment_data -> sentiment_data_old")
    
    response = input(f"\nProceed with table renaming? (y/n): ")
    if response.lower() == 'y':
        rename_old_tables()
    else:
        print("⏸️  Table renaming skipped")
    
    print(f"\n✨ MIGRATION AND CLEANUP COMPLETE!")
    print("🎯 Database structure optimized with enhanced tables")
    print("📊 Old tables preserved with '_old' suffix")


if __name__ == "__main__":
    main()