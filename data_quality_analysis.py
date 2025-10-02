# Data Quality Analysis Script
import mysql.connector
from datetime import datetime, timedelta

def analyze_data_quality():
    print("🔍 CRYPTO DATA QUALITY & COMPLETENESS ANALYSIS")
    print("=" * 60)
    
    # Connect to crypto_news database
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector', 
        password='99Rules!',
        database='crypto_news'
    )
    cursor = conn.cursor()
    
    # 1. News Data Analysis
    print("\n📰 NEWS DATA ANALYSIS:")
    cursor.execute("SELECT COUNT(*) FROM crypto_news_data")
    total_news = cursor.fetchone()[0]
    print(f"Total news records: {total_news:,}")
    
    cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM crypto_news_data")
    date_range = cursor.fetchone()
    print(f"Date range: {date_range[0]} to {date_range[1]}")
    
    # Check for data gaps in recent days
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM crypto_news_data 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
        GROUP BY DATE(created_at) 
        ORDER BY date DESC
    """)
    recent_news = cursor.fetchall()
    print(f"Recent news activity (last 30 days): {len(recent_news)} days with data")
    
    if recent_news:
        print("Recent daily counts:")
        for date, count in recent_news[:5]:
            print(f"  {date}: {count} articles")
    else:
        print("⚠️  NO RECENT NEWS DATA - Significant gap detected!")
    
    # 2. Check table structure
    print("\n🗃️  DATABASE STRUCTURE:")
    cursor.execute("DESCRIBE crypto_news_data")
    columns = cursor.fetchall()
    print("crypto_news_data columns:")
    for col in columns:
        print(f"  {col[0]}: {col[1]}")
    
    # 3. Data sources analysis
    cursor.execute("SELECT COUNT(DISTINCT source) FROM crypto_news_data WHERE source IS NOT NULL")
    sources = cursor.fetchone()[0]
    print(f"\nData sources: {sources} unique sources")
    
    cursor.execute("SELECT source, COUNT(*) as count FROM crypto_news_data GROUP BY source ORDER BY count DESC LIMIT 10")
    top_sources = cursor.fetchall()
    print("Top news sources:")
    for source, count in top_sources:
        print(f"  {source}: {count:,} articles")
    
    # 4. Content quality checks
    cursor.execute("SELECT COUNT(*) FROM crypto_news_data WHERE title IS NULL OR title = ''")
    empty_titles = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM crypto_news_data WHERE content IS NULL OR content = ''")
    empty_content = cursor.fetchone()[0]
    
    print(f"\nContent quality:")
    print(f"  Empty titles: {empty_titles}")
    print(f"  Empty content: {empty_content}")
    print(f"  Quality score: {((total_news - empty_titles - empty_content) / total_news * 100):.1f}%")
    
    # 5. Sentiment data analysis
    print("\n💭 SENTIMENT DATA ANALYSIS:")
    
    tables = ['social_sentiment_data', 'stock_sentiment_data', 'crypto_sentiment_data']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        cursor.execute(f"SELECT MAX(created_at) FROM {table}")
        latest = cursor.fetchone()[0]
        
        # Check for recent data
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        recent_count = cursor.fetchone()[0]
        
        print(f"{table}:")
        print(f"  Total records: {count:,}")
        print(f"  Latest: {latest}")
        print(f"  Last 7 days: {recent_count} records")
        
        if recent_count == 0:
            print(f"  ⚠️  NO RECENT DATA - Collection gap!")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Data quality analysis complete!")

if __name__ == "__main__":
    analyze_data_quality()