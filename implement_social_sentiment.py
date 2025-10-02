#!/usr/bin/env python3
import mysql.connector

def implement_social_sentiment():
    """Implement social sentiment integration for materialized updater"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== IMPLEMENTING SOCIAL SENTIMENT INTEGRATION ===\n")
    
    # First, let's explore available social sentiment tables
    cursor.execute("SHOW TABLES LIKE '%sentiment%'")
    sentiment_tables = cursor.fetchall()
    
    print("📊 Available sentiment tables:")
    for table in sentiment_tables:
        table_name = list(table.values())[0]
        print(f"   {table_name}")
        
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"     Records: {count}")
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                columns = list(sample.keys())[:10]  # First 10 columns
                print(f"     Columns: {columns}")
        except Exception as e:
            print(f"     Error accessing table: {e}")
    
    # Now let's update our materialized table with social sentiment data
    print(f"\n🔄 INTEGRATING SOCIAL SENTIMENT DATA...")
    
    # Get recent BTC price records to update
    cursor.execute("""
        SELECT symbol, timestamp, close 
        FROM price_data 
        WHERE symbol = 'BTC' 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    price_records = cursor.fetchall()
    print(f"📊 Processing {len(price_records)} recent BTC records for social sentiment")
    
    for price_record in price_records:
        timestamp_iso = price_record['timestamp']
        print(f"\n🔄 Processing {timestamp_iso}")
        
        # Try to find social sentiment data for this symbol and timeframe
        social_data = {}
        
        # Set default values for social sentiment fields
        social_defaults = {
            'social_post_count': 0,
            'social_avg_sentiment': None,
            'social_avg_confidence': None,
            'social_unique_authors': 0,
            'social_weighted_sentiment': None,
            'social_engagement_weighted_sentiment': None,
            'social_verified_user_sentiment': None,
            'social_total_engagement': 0,
            'crypto_sentiment_count': 0,
            'avg_cryptobert_score': None,
            'avg_vader_score': None,
            'avg_textblob_score': None,
            'avg_crypto_keywords_score': None
        }
        
        social_data.update(social_defaults)
        
        # Try to get actual social sentiment data if available
        # Check if we have crypto_news database with sentiment data
        try:
            cursor.execute("USE crypto_news")
            
            # Look for social sentiment data
            cursor.execute("""
                SELECT COUNT(*) as post_count,
                       AVG(CASE WHEN sentiment_score BETWEEN -1 AND 1 THEN sentiment_score END) as avg_sentiment,
                       COUNT(DISTINCT author_id) as unique_authors,
                       SUM(engagement_count) as total_engagement
                FROM social_sentiment_data
                WHERE asset = %s
                AND DATE(timestamp) = %s
            """, ('BTC', timestamp_iso.date()))
            
            social_result = cursor.fetchone()
            if social_result and social_result['post_count'] > 0:
                social_data.update({
                    'social_post_count': social_result['post_count'],
                    'social_avg_sentiment': social_result['avg_sentiment'], 
                    'social_unique_authors': social_result['unique_authors'] or 0,
                    'social_total_engagement': social_result['total_engagement'] or 0
                })
                print(f"  ✅ Found social data: {social_result['post_count']} posts")
            else:
                print(f"  📊 Using default social values (no data found)")
                
            # Switch back to crypto_prices database
            cursor.execute("USE crypto_prices")
            
        except Exception as e:
            print(f"  ⚠️  Social sentiment lookup failed: {e}")
            # Use defaults
            
        # Update the materialized record
        update_cursor = conn.cursor()
        
        # Build update query for social fields
        set_clauses = []
        values = []
        
        for field, value in social_data.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)
            
        if set_clauses:
            update_sql = f"""
                UPDATE ml_features_materialized 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = %s 
                AND price_date = %s 
                AND price_hour = %s
            """
            values.extend(['BTC', timestamp_iso.date(), timestamp_iso.hour])
            
            update_cursor.execute(update_sql, values)
            affected = update_cursor.rowcount
            
            if affected > 0:
                print(f"  ✅ Updated {affected} materialized record(s)")
            else:
                print(f"  ⚠️  No materialized record found to update")
        
        conn.commit()
    
    # Check our improvement
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        # Count social sentiment fields that are now populated
        social_fields = ['social_post_count', 'social_avg_sentiment', 'social_unique_authors', 'social_total_engagement',
                        'crypto_sentiment_count', 'avg_cryptobert_score', 'avg_vader_score']
        
        social_populated = len([f for f in social_fields if btc_record.get(f) is not None])
        
        total_populated = len([col for col, val in btc_record.items() if val is not None])
        total_cols = len(btc_record)
        rate = (total_populated / total_cols) * 100
        
        print(f"\n🎯 SOCIAL SENTIMENT INTEGRATION RESULTS:")
        print(f"   Social fields populated: {social_populated}/{len(social_fields)}")
        print(f"   Overall population: {total_populated}/{total_cols} ({rate:.1f}%)")
        print(f"   Social post count: {btc_record.get('social_post_count')}")
        print(f"   Social avg sentiment: {btc_record.get('social_avg_sentiment')}")
    
    conn.close()

if __name__ == "__main__":
    implement_social_sentiment()