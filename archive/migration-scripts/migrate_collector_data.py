#!/usr/bin/env python3
"""
Data Migration Script for Collector Table Consolidation
Migrate unique data from duplicate tables before cleanup
"""
import mysql.connector
import sys
from contextlib import contextmanager
from datetime import datetime

# Database credentials
MYSQL_HOST = "172.22.32.1"
MYSQL_PORT = 3306
MYSQL_USER = "news_collector"
MYSQL_PASSWORD = "99Rules!"

@contextmanager
def mysql_connection(database=None):
    """Context manager for MySQL connections"""
    connection = None
    try:
        config = {
            'host': MYSQL_HOST,
            'port': MYSQL_PORT,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'autocommit': True,
            'charset': 'utf8mb4',
            'use_unicode': True
        }
        if database:
            config['database'] = database
            
        connection = mysql.connector.connect(**config)
        yield connection
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()

def check_table_schema(cursor, database, table):
    """Get table schema for comparison"""
    cursor.execute(f"DESCRIBE {database}.{table}")
    result = cursor.fetchall()
    cursor.fetchall()  # Clear any remaining results
    return [row[0] for row in result]  # Column names

def migrate_macro_data():
    """Migrate macro economic data from crypto_news to crypto_prices"""
    print("\n🔄 MIGRATING MACRO DATA")
    print("-" * 50)
    
    with mysql_connection() as conn:
        cursor = conn.cursor()
        
        # Check schemas
        source_schema = check_table_schema(cursor, 'crypto_news', 'macro_economic_data')
        target_schema = check_table_schema(cursor, 'crypto_prices', 'macro_indicators')
        
        print(f"📊 Source schema (crypto_news.macro_economic_data): {len(source_schema)} columns")
        print(f"📊 Target schema (crypto_prices.macro_indicators): {len(target_schema)} columns")
        
        # Count source records
        cursor.execute("SELECT COUNT(*) FROM crypto_news.macro_economic_data")
        source_count = cursor.fetchone()[0]
        cursor.fetchall()  # Clear buffer
        
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.macro_indicators")
        target_count_before = cursor.fetchone()[0]
        cursor.fetchall()  # Clear buffer
        
        print(f"📈 Source records: {source_count:,}")
        print(f"📈 Target records (before): {target_count_before:,}")
        
        if source_count == 0:
            print("✅ No data to migrate")
            return
        
        # Check for common columns for migration
        common_columns = set(source_schema) & set(target_schema)
        print(f"🔗 Common columns: {len(common_columns)}")
        
        if len(common_columns) < 3:  # Need at least some key columns
            print("⚠️  Schema mismatch - manual migration required")
            # Show sample data
            cursor.execute("SELECT * FROM crypto_news.macro_economic_data LIMIT 5")
            sample = cursor.fetchall()
            print("📋 Sample source data:")
            for row in sample:
                print(f"   {row}")
            return
        
        # Attempt migration of unique records
        # Find records that don't exist in target (by timestamp/date if available)
        if 'timestamp' in common_columns:
            print("🎯 Using timestamp for deduplication...")
            
            # Find unique timestamps from source not in target
            cursor.execute("""
                SELECT COUNT(*) 
                FROM crypto_news.macro_economic_data s
                LEFT JOIN crypto_prices.macro_indicators t ON s.timestamp = t.timestamp
                WHERE t.timestamp IS NULL
            """)
            
            unique_count = cursor.fetchone()[0]
            print(f"📊 Unique records to migrate: {unique_count:,}")
            
            if unique_count > 0:
                # Migrate unique records
                column_list = ', '.join(common_columns)
                insert_query = f"""
                    INSERT INTO crypto_prices.macro_indicators ({column_list})
                    SELECT {column_list}
                    FROM crypto_news.macro_economic_data s
                    LEFT JOIN crypto_prices.macro_indicators t ON s.timestamp = t.timestamp
                    WHERE t.timestamp IS NULL
                """
                
                cursor.execute(insert_query)
                print(f"✅ Migrated {unique_count:,} unique macro records")
            
        else:
            print("⚠️  No timestamp column found - checking for other deduplication keys...")
            
        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.macro_indicators")
        target_count_after = cursor.fetchone()[0]
        
        print(f"📈 Target records (after): {target_count_after:,}")
        print(f"📈 Records added: {target_count_after - target_count_before:,}")

def migrate_sentiment_data():
    """Migrate sentiment data from various tables"""
    print("\n🔄 MIGRATING SENTIMENT DATA")
    print("-" * 50)
    
    with mysql_connection() as conn:
        cursor = conn.cursor()
        
        # Check primary sentiment table
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.real_time_sentiment_signals")
        primary_count = cursor.fetchone()[0]
        print(f"📊 Primary sentiment table: {primary_count:,} records")
        
        # Check duplicates with data
        sentiment_sources = [
            ('crypto_prices', 'sentiment_aggregation'),
            ('crypto_news', 'crypto_sentiment_data'),
            ('crypto_news', 'social_sentiment_metrics')
        ]
        
        for db_name, table_name in sentiment_sources:
            cursor.execute(f"SELECT COUNT(*) FROM {db_name}.{table_name}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"📊 {db_name}.{table_name}: {count:,} records")
                
                # Check schema compatibility
                source_schema = check_table_schema(cursor, db_name, table_name)
                target_schema = check_table_schema(cursor, 'crypto_prices', 'real_time_sentiment_signals')
                
                common_cols = set(source_schema) & set(target_schema)
                print(f"   🔗 Common columns: {len(common_cols)}")
                
                if len(common_cols) >= 3:
                    print(f"   ✅ Schema compatible - can migrate")
                else:
                    print(f"   ⚠️  Schema incompatible - needs manual review")
                    
                    # Show sample data for manual review
                    cursor.execute(f"SELECT * FROM {db_name}.{table_name} LIMIT 3")
                    sample = cursor.fetchall()
                    print(f"   📋 Sample data:")
                    for row in sample:
                        print(f"      {row}")

def migrate_news_data():
    """Migrate news data ensuring no duplicates"""
    print("\n🔄 MIGRATING NEWS DATA")  
    print("-" * 50)
    
    with mysql_connection() as conn:
        cursor = conn.cursor()
        
        # Check primary news table
        cursor.execute("SELECT COUNT(*) FROM crypto_news.news_data")
        primary_count = cursor.fetchone()[0]
        print(f"📊 Primary news table: {primary_count:,} records")
        
        # Check crypto_prices.crypto_news
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.crypto_news")
        duplicate_count = cursor.fetchone()[0]
        
        if duplicate_count > 0:
            print(f"📊 Duplicate table (crypto_prices.crypto_news): {duplicate_count:,} records")
            
            # Check schemas
            source_schema = check_table_schema(cursor, 'crypto_prices', 'crypto_news')
            target_schema = check_table_schema(cursor, 'crypto_news', 'news_data')
            
            print(f"📋 Source columns: {source_schema}")
            print(f"📋 Target columns: {target_schema}")
            
            # Check for URL-based deduplication (common in news tables)
            if 'url' in source_schema and 'url' in target_schema:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM crypto_prices.crypto_news s
                    LEFT JOIN crypto_news.news_data t ON s.url = t.url
                    WHERE t.url IS NULL
                """)
                unique_count = cursor.fetchone()[0]
                print(f"📊 Unique URLs to migrate: {unique_count:,}")
                
            elif 'title' in source_schema and 'title' in target_schema:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM crypto_prices.crypto_news s
                    LEFT JOIN crypto_news.news_data t ON s.title = t.title
                    WHERE t.title IS NULL
                """)
                unique_count = cursor.fetchone()[0]
                print(f"📊 Unique titles to migrate: {unique_count:,}")

def migrate_social_data():
    """Migrate social platform stats"""
    print("\n🔄 MIGRATING SOCIAL DATA")
    print("-" * 50)
    
    with mysql_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM crypto_news.social_media_posts")
        primary_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crypto_news.social_platform_stats")
        stats_count = cursor.fetchone()[0]
        
        print(f"📊 Primary social table: {primary_count:,} records")
        print(f"📊 Social stats to migrate: {stats_count:,} records")
        
        if stats_count > 0:
            # These are likely different types of data - platform stats vs posts
            print("📋 These appear to be different data types - both should be preserved")

def main():
    """Main migration function"""
    print("🚀 STARTING DATA MIGRATION FOR COLLECTOR TABLE CONSOLIDATION")
    print("=" * 80)
    
    try:
        # Test connection first
        with mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        
        print("✅ Database connection established")
        
        # Run migrations
        migrate_macro_data()
        migrate_sentiment_data()  
        migrate_news_data()
        migrate_social_data()
        
        print(f"\n🎯 MIGRATION SUMMARY")
        print("=" * 50)
        print("✅ Data analysis completed")
        print("⚠️  Some tables require manual review due to schema differences")
        print("📋 Next step: Review migration results and proceed with cleanup")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()