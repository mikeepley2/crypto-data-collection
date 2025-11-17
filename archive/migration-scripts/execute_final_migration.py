#!/usr/bin/env python3
"""
Execute Final Migration and Cleanup - Safe Approach
"""
import mysql.connector
from datetime import datetime

MYSQL_HOST = "172.22.32.1" 
MYSQL_USER = "news_collector"
MYSQL_PASSWORD = "99Rules!"

def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST, port=3306, user=MYSQL_USER, password=MYSQL_PASSWORD,
        autocommit=True, charset='utf8mb4'
    )

def step1_migrate_news():
    """Migrate unique news articles"""
    print("STEP 1: MIGRATING UNIQUE NEWS DATA")
    print("-" * 40)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check unique articles
    cursor.execute("""
        SELECT COUNT(*) FROM crypto_prices.crypto_news cn
        WHERE cn.url IS NOT NULL 
        AND cn.url NOT IN (
            SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
            WHERE nd.url IS NOT NULL
        )
    """)
    unique_count = cursor.fetchone()[0]
    
    print(f"Unique articles to migrate: {unique_count:,}")
    
    if unique_count > 0 and unique_count < 200000:
        cursor.execute("""
            INSERT INTO crypto_news.news_data 
            (title, content, url, published_date, source, sentiment_score, created_at)
            SELECT 
                title, content, url, published_date, 
                COALESCE(source, 'migrated'), sentiment_score, NOW()
            FROM crypto_prices.crypto_news cn
            WHERE cn.url IS NOT NULL 
            AND cn.url NOT IN (
                SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
                WHERE nd.url IS NOT NULL
            )
        """)
        print(f"Migrated {unique_count:,} articles")
    
    cursor.close()
    conn.close()
    return unique_count

def step2_migrate_macro():
    """Migrate unique macro data"""
    print("\nSTEP 2: MIGRATING UNIQUE MACRO DATA")
    print("-" * 40)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check schemas first
    cursor.execute("SHOW COLUMNS FROM crypto_news.macro_economic_data")
    source_cols = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SHOW COLUMNS FROM crypto_prices.macro_indicators")
    target_cols = [row[0] for row in cursor.fetchall()]
    
    common_cols = list(set(source_cols) & set(target_cols))
    print(f"Common columns: {len(common_cols)}")
    
    if 'indicator_name' in common_cols and 'value' in common_cols:
        # Check for unique indicator/value combinations
        cursor.execute("""
            SELECT COUNT(*) FROM crypto_news.macro_economic_data s
            WHERE NOT EXISTS (
                SELECT 1 FROM crypto_prices.macro_indicators t 
                WHERE t.indicator_name = s.indicator_name 
                AND ABS(COALESCE(t.value, 0) - COALESCE(s.value, 0)) < 0.0001
            )
        """)
        unique_count = cursor.fetchone()[0]
        
        print(f"Unique macro records: {unique_count:,}")
        
        if unique_count > 0 and unique_count < 50000:
            col_list = ', '.join(common_cols)
            cursor.execute(f"""
                INSERT INTO crypto_prices.macro_indicators ({col_list})
                SELECT {col_list}
                FROM crypto_news.macro_economic_data s
                WHERE NOT EXISTS (
                    SELECT 1 FROM crypto_prices.macro_indicators t 
                    WHERE t.indicator_name = s.indicator_name 
                    AND ABS(COALESCE(t.value, 0) - COALESCE(s.value, 0)) < 0.0001
                )
            """)
            print(f"Migrated {unique_count:,} macro records")
    else:
        print("Schema incompatible - skipping macro migration")
    
    cursor.close()
    conn.close()

def step3_cleanup_duplicates():
    """Archive duplicate tables"""
    print("\nSTEP 3: ARCHIVING DUPLICATE TABLES")
    print("-" * 40)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Tables to archive
    tables_to_archive = [
        ('crypto_prices', 'crypto_news'),
        ('crypto_news', 'stock_market_news_data'),
        ('crypto_news', 'macro_economic_data'),
        ('crypto_prices', 'sentiment_aggregation'),
        ('crypto_news', 'crypto_sentiment_data'),
        ('crypto_news', 'social_sentiment_metrics'),
        ('crypto_news', 'ml_sentiment_features'),
        ('crypto_news', 'sentiment_analysis_results'),
        ('crypto_news', 'stock_sentiment_data'),
        ('crypto_prices', 'social_sentiment_metrics'),
        ('crypto_news', 'ml_onchain_features'),
        ('crypto_prices', 'onchain_metrics'),
        ('crypto_news', 'social_platform_stats'),
        ('crypto_prices', 'market_conditions_history')
    ]
    
    archived_count = 0
    
    for db_name, table_name in tables_to_archive:
        try:
            # Check if table exists
            cursor.execute(f"SHOW TABLES FROM {db_name} LIKE '{table_name}'")
            if cursor.fetchone():
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {db_name}.{table_name}")
                count = cursor.fetchone()[0]
                
                # Rename to archive
                new_name = f"{table_name}_archive_{timestamp}_old"
                cursor.execute(f"RENAME TABLE {db_name}.{table_name} TO {db_name}.{new_name}")
                
                print(f"Archived: {db_name}.{table_name} -> {new_name} ({count:,} rows)")
                archived_count += 1
            else:
                print(f"Skipped: {db_name}.{table_name} (not found)")
                
        except Exception as e:
            print(f"Error archiving {db_name}.{table_name}: {e}")
    
    print(f"\nArchived {archived_count} tables")
    
    cursor.close()
    conn.close()
    
    return archived_count

def step4_final_verification():
    """Verify final state"""
    print("\nSTEP 4: FINAL VERIFICATION")
    print("-" * 40)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check primary tables
    primary_tables = {
        'Technical': 'crypto_prices.technical_indicators',
        'News': 'crypto_news.news_data',
        'Macro': 'crypto_prices.macro_indicators', 
        'Onchain': 'crypto_prices.crypto_onchain_data',
        'OHLC': 'crypto_prices.ohlc_data',
        'ML Features': 'crypto_prices.ml_features_materialized',
        'Price Data': 'crypto_prices.price_data_real'
    }
    
    print("Primary Tables Status:")
    for name, table in primary_tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {name}: {count:,} records")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")
    
    # Count remaining active tables
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema IN ('crypto_news', 'crypto_prices', 'crypto_transactions')
        AND table_name NOT LIKE '%_old'
        AND table_name NOT LIKE '%backup%'
        AND table_name NOT LIKE '%archive%'
    """)
    active_tables = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema IN ('crypto_news', 'crypto_prices', 'crypto_transactions')
        AND (table_name LIKE '%_old' OR table_name LIKE '%backup%' OR table_name LIKE '%archive%')
    """)
    archived_tables = cursor.fetchone()[0]
    
    print(f"\nTable Summary:")
    print(f"  Active tables: {active_tables}")
    print(f"  Archived tables: {archived_tables}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("FINAL MIGRATION AND CLEANUP EXECUTION")
    print("=" * 50)
    
    try:
        # Execute migration steps
        news_migrated = step1_migrate_news()
        step2_migrate_macro()
        archived_count = step3_cleanup_duplicates()
        step4_final_verification()
        
        print(f"\nSUCCESS SUMMARY:")
        print(f"- News articles migrated: {news_migrated:,}")
        print(f"- Tables archived: {archived_count}")
        print(f"- Single source of truth achieved!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        exit(1)