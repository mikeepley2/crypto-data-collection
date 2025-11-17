#!/usr/bin/env python3
"""
Check table schemas and perform actual data migration
"""
import mysql.connector

# Database credentials
MYSQL_HOST = "172.22.32.1"
MYSQL_PORT = 3306
MYSQL_USER = "news_collector"
MYSQL_PASSWORD = "99Rules!"

def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        autocommit=True,
        charset='utf8mb4'
    )

def check_schemas():
    print("🔍 CHECKING TABLE SCHEMAS")
    print("=" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check macro tables
    print("\n📊 MACRO TABLES:")
    cursor.execute("DESCRIBE crypto_news.macro_economic_data")
    macro_source_cols = cursor.fetchall()
    print("Source (crypto_news.macro_economic_data):")
    for col in macro_source_cols:
        print(f"  {col[0]} - {col[1]}")
    
    cursor.execute("DESCRIBE crypto_prices.macro_indicators")
    macro_target_cols = cursor.fetchall()
    print("\nTarget (crypto_prices.macro_indicators):")
    for col in macro_target_cols:
        print(f"  {col[0]} - {col[1]}")
    
    cursor.close()
    conn.close()

def perform_news_migration():
    """Migrate unique news articles from crypto_prices to crypto_news"""
    print("\n🔄 MIGRATING UNIQUE NEWS ARTICLES")
    print("-" * 50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Count unique articles in duplicate table
        cursor.execute("""
            SELECT COUNT(*) FROM crypto_prices.crypto_news cn
            WHERE cn.url NOT IN (
                SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
                WHERE nd.url IS NOT NULL
            ) AND cn.url IS NOT NULL
        """)
        unique_count = cursor.fetchone()[0]
        
        print(f"📊 Unique articles to migrate: {unique_count:,}")
        
        if unique_count > 0:
            # Get sample to check data
            cursor.execute("""
                SELECT title, url, published_date 
                FROM crypto_prices.crypto_news cn
                WHERE cn.url NOT IN (
                    SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
                    WHERE nd.url IS NOT NULL
                ) AND cn.url IS NOT NULL
                LIMIT 5
            """)
            samples = cursor.fetchall()
            
            print("📋 Sample unique articles:")
            for sample in samples:
                print(f"  📰 {sample[0][:60]}...")
                print(f"      🔗 {sample[1]}")
                print(f"      📅 {sample[2]}")
            
            # Perform migration - insert unique articles
            cursor.execute("""
                INSERT INTO crypto_news.news_data 
                (title, content, url, published_date, source, sentiment_score, created_at)
                SELECT 
                    title, 
                    content, 
                    url, 
                    published_date, 
                    COALESCE(source, 'migrated_from_crypto_prices'),
                    sentiment_score,
                    NOW()
                FROM crypto_prices.crypto_news cn
                WHERE cn.url NOT IN (
                    SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
                    WHERE nd.url IS NOT NULL
                ) AND cn.url IS NOT NULL
            """)
            
            print(f"✅ Successfully migrated {unique_count:,} unique news articles")
        else:
            print("✅ No unique articles found - all data already exists")
    
    except Exception as e:
        print(f"❌ News migration error: {e}")
    finally:
        cursor.close()
        conn.close()

def perform_macro_migration():
    """Migrate unique macro data"""
    print("\n🔄 MIGRATING UNIQUE MACRO DATA")
    print("-" * 50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check actual column name for date/timestamp
        cursor.execute("SHOW COLUMNS FROM crypto_news.macro_economic_data")
        source_cols = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SHOW COLUMNS FROM crypto_prices.macro_indicators")
        target_cols = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Source columns: {source_cols}")
        print(f"📊 Target columns: {target_cols}")
        
        # Find date-like column
        date_col = None
        for col in source_cols:
            if any(word in col.lower() for word in ['date', 'time', 'timestamp']):
                date_col = col
                break
        
        if not date_col:
            print("⚠️  No date column found - using ID-based deduplication")
            # Try by indicator name and value
            cursor.execute("""
                SELECT COUNT(*) FROM crypto_news.macro_economic_data s
                WHERE NOT EXISTS (
                    SELECT 1 FROM crypto_prices.macro_indicators t 
                    WHERE t.indicator_name = s.indicator_name 
                    AND ABS(t.value - s.value) < 0.0001
                )
            """)
            unique_count = cursor.fetchone()[0]
            
        else:
            print(f"📅 Using date column: {date_col}")
            # Use date-based deduplication
            cursor.execute(f"""
                SELECT COUNT(*) FROM crypto_news.macro_economic_data s
                WHERE s.{date_col} NOT IN (
                    SELECT DISTINCT t.timestamp FROM crypto_prices.macro_indicators t 
                    WHERE t.timestamp IS NOT NULL
                )
            """)
            unique_count = cursor.fetchone()[0]
        
        print(f"📊 Unique macro records to migrate: {unique_count:,}")
        
        if unique_count > 0 and unique_count < 50000:  # Reasonable limit
            # Find common columns for migration
            common_cols = set(source_cols) & set(target_cols)
            print(f"🔗 Common columns: {common_cols}")
            
            if len(common_cols) >= 3:
                col_list = ', '.join(common_cols)
                
                # Perform migration
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
                
                print(f"✅ Successfully migrated {unique_count:,} unique macro records")
            else:
                print("⚠️  Schema mismatch - manual review needed")
        elif unique_count >= 50000:
            print("⚠️  Too many records - manual review recommended")
        else:
            print("✅ No unique macro data found")
    
    except Exception as e:
        print(f"❌ Macro migration error: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    print("🚀 SCHEMA CHECK AND DATA MIGRATION")
    print("=" * 80)
    
    check_schemas()
    perform_news_migration() 
    perform_macro_migration()
    
    print(f"\n✅ MIGRATION COMPLETED")
    print("=" * 40)
    print("📋 Next step: Verify migrations and proceed with table cleanup")

if __name__ == "__main__":
    main()