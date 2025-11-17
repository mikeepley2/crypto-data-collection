#!/usr/bin/env python3
"""
Simple Data Migration Analysis
Check for unique data before cleanup - one table at a time
"""
import mysql.connector
import sys

# Database credentials
MYSQL_HOST = "172.22.32.1"
MYSQL_PORT = 3306
MYSQL_USER = "news_collector"
MYSQL_PASSWORD = "99Rules!"

def get_connection():
    """Get a fresh database connection"""
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        autocommit=True,
        charset='utf8mb4',
        use_unicode=True
    )

def analyze_macro_migration():
    """Analyze macro data migration needs"""
    print("🔍 MACRO DATA MIGRATION ANALYSIS")
    print("-" * 50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check source data
        cursor.execute("SELECT COUNT(*) FROM crypto_news.macro_economic_data")
        source_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.macro_indicators")
        target_count = cursor.fetchone()[0]
        
        print(f"📊 Source (crypto_news.macro_economic_data): {source_count:,} records")
        print(f"📊 Target (crypto_prices.macro_indicators): {target_count:,} records")
        
        if source_count == 0:
            print("✅ No data to migrate - safe to remove")
            return
        
        # Check date ranges
        cursor.execute("SELECT MIN(date), MAX(date) FROM crypto_news.macro_economic_data WHERE date IS NOT NULL")
        result = cursor.fetchone()
        if result[0]:
            print(f"📅 Source date range: {result[0]} to {result[1]}")
        
        cursor.execute("SELECT MIN(date), MAX(date) FROM crypto_prices.macro_indicators WHERE date IS NOT NULL") 
        result = cursor.fetchone()
        if result[0]:
            print(f"📅 Target date range: {result[0]} to {result[1]}")
        
        # Check for potential unique records
        cursor.execute("""
            SELECT COUNT(DISTINCT date) 
            FROM crypto_news.macro_economic_data 
            WHERE date IS NOT NULL
        """)
        source_unique_dates = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT date) 
            FROM crypto_prices.macro_indicators 
            WHERE date IS NOT NULL
        """)
        target_unique_dates = cursor.fetchone()[0]
        
        print(f"📊 Source unique dates: {source_unique_dates:,}")
        print(f"📊 Target unique dates: {target_unique_dates:,}")
        
        # Perform actual migration if needed
        if source_unique_dates > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT date FROM crypto_news.macro_economic_data 
                    WHERE date NOT IN (
                        SELECT DISTINCT date FROM crypto_prices.macro_indicators 
                        WHERE date IS NOT NULL
                    ) AND date IS NOT NULL
                ) as missing_dates
            """)
            missing_count = cursor.fetchone()[0]
            
            print(f"🎯 Records with dates missing from target: {missing_count:,}")
            
            if missing_count > 0:
                print("⚠️  Migration needed!")
                
                # Show sample of missing data
                cursor.execute("""
                    SELECT date, indicator_name, value 
                    FROM crypto_news.macro_economic_data 
                    WHERE date NOT IN (
                        SELECT DISTINCT date FROM crypto_prices.macro_indicators 
                        WHERE date IS NOT NULL
                    ) AND date IS NOT NULL
                    LIMIT 5
                """)
                
                samples = cursor.fetchall()
                print("📋 Sample missing records:")
                for sample in samples:
                    print(f"   {sample}")
                
                # Perform migration
                cursor.execute("""
                    INSERT INTO crypto_prices.macro_indicators 
                    (date, indicator_name, value, source, created_at)
                    SELECT date, indicator_name, value, source, NOW()
                    FROM crypto_news.macro_economic_data 
                    WHERE date NOT IN (
                        SELECT DISTINCT date FROM crypto_prices.macro_indicators 
                        WHERE date IS NOT NULL
                    ) AND date IS NOT NULL
                """)
                
                print(f"✅ Migrated {missing_count:,} unique macro records")
            else:
                print("✅ All data already exists in target table")
        
    except Exception as e:
        print(f"❌ Error analyzing macro data: {e}")
    finally:
        cursor.close()
        conn.close()

def analyze_sentiment_migration():
    """Analyze sentiment data migration needs"""
    print("\n🔍 SENTIMENT DATA MIGRATION ANALYSIS")
    print("-" * 50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check main duplicate: sentiment_aggregation
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.sentiment_aggregation")
        agg_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.real_time_sentiment_signals")
        primary_count = cursor.fetchone()[0]
        
        print(f"📊 Primary (real_time_sentiment_signals): {primary_count:,} records")
        print(f"📊 Duplicate (sentiment_aggregation): {agg_count:,} records")
        
        if agg_count > 0:
            # Check date ranges to see if there's unique data
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM crypto_prices.sentiment_aggregation")
            agg_range = cursor.fetchone()
            
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM crypto_prices.real_time_sentiment_signals")
            primary_range = cursor.fetchone()
            
            print(f"📅 Aggregation range: {agg_range[0]} to {agg_range[1]}")
            print(f"📅 Primary range: {primary_range[0]} to {primary_range[1]}")
            
            # Check for schema differences
            cursor.execute("SHOW COLUMNS FROM crypto_prices.sentiment_aggregation")
            agg_cols = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SHOW COLUMNS FROM crypto_prices.real_time_sentiment_signals")
            primary_cols = [row[0] for row in cursor.fetchall()]
            
            print(f"📊 Aggregation columns: {len(agg_cols)}")
            print(f"📊 Primary columns: {len(primary_cols)}")
            
            common_cols = set(agg_cols) & set(primary_cols)
            print(f"🔗 Common columns: {len(common_cols)} - {list(common_cols)[:5]}")
        
        # Check crypto_news.crypto_sentiment_data
        cursor.execute("SELECT COUNT(*) FROM crypto_news.crypto_sentiment_data")
        news_sentiment_count = cursor.fetchone()[0]
        
        print(f"📊 News sentiment data: {news_sentiment_count:,} records")
        
        if news_sentiment_count > 0:
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM crypto_news.crypto_sentiment_data")
            news_range = cursor.fetchone()
            print(f"📅 News sentiment range: {news_range[0]} to {news_range[1]}")
        
    except Exception as e:
        print(f"❌ Error analyzing sentiment data: {e}")
    finally:
        cursor.close()
        conn.close()

def analyze_news_migration():
    """Analyze news data migration needs"""
    print("\n🔍 NEWS DATA MIGRATION ANALYSIS")
    print("-" * 50)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check the big duplicate: crypto_prices.crypto_news
        cursor.execute("SELECT COUNT(*) FROM crypto_prices.crypto_news")
        duplicate_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crypto_news.news_data")
        primary_count = cursor.fetchone()[0]
        
        print(f"📊 Primary (crypto_news.news_data): {primary_count:,} records")
        print(f"📊 Duplicate (crypto_prices.crypto_news): {duplicate_count:,} records")
        
        if duplicate_count > 0:
            # Check for unique URLs/articles
            cursor.execute("SELECT COUNT(DISTINCT url) FROM crypto_prices.crypto_news WHERE url IS NOT NULL")
            duplicate_urls = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT url) FROM crypto_news.news_data WHERE url IS NOT NULL")
            primary_urls = cursor.fetchone()[0]
            
            print(f"📊 Primary unique URLs: {primary_urls:,}")
            print(f"📊 Duplicate unique URLs: {duplicate_urls:,}")
            
            # Check for URLs in duplicate not in primary
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT url FROM crypto_prices.crypto_news 
                    WHERE url IS NOT NULL 
                    AND url NOT IN (
                        SELECT DISTINCT url FROM crypto_news.news_data 
                        WHERE url IS NOT NULL
                    )
                ) as unique_urls
            """)
            missing_urls = cursor.fetchone()[0]
            
            print(f"🎯 URLs in duplicate but not in primary: {missing_urls:,}")
            
            if missing_urls > 0:
                print("⚠️  Migration needed!")
                
                # Show sample
                cursor.execute("""
                    SELECT title, url, published_date 
                    FROM crypto_prices.crypto_news 
                    WHERE url IS NOT NULL 
                    AND url NOT IN (
                        SELECT DISTINCT url FROM crypto_news.news_data 
                        WHERE url IS NOT NULL
                    )
                    LIMIT 3
                """)
                
                samples = cursor.fetchall()
                print("📋 Sample unique articles:")
                for sample in samples:
                    print(f"   {sample}")
            else:
                print("✅ All articles already exist in primary table")
    
    except Exception as e:
        print(f"❌ Error analyzing news data: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    print("🚀 DATA MIGRATION ANALYSIS FOR COLLECTOR CONSOLIDATION")
    print("=" * 80)
    
    try:
        # Test connection
        conn = get_connection()
        conn.close()
        print("✅ Database connection verified")
        
        # Analyze each migration
        analyze_macro_migration()
        analyze_sentiment_migration() 
        analyze_news_migration()
        
        print(f"\n🎯 ANALYSIS COMPLETE")
        print("=" * 50)
        print("📋 Review the analysis above to determine migration needs")
        print("📋 Tables with '⚠️  Migration needed!' require data preservation")
        print("📋 Tables showing '✅ safe to remove' can be archived directly")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()