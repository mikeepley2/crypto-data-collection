#!/usr/bin/env python3
import mysql.connector

def implement_social_sentiment_fixed():
    """Fixed social sentiment integration using available sentiment tables"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== IMPLEMENTING SOCIAL SENTIMENT INTEGRATION (FIXED) ===\n")
    
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
    print(f"📊 Processing {len(price_records)} recent BTC records")
    
    for price_record in price_records:
        timestamp_iso = price_record['timestamp']
        print(f"\n🔄 Processing {timestamp_iso}")
        
        # Initialize social data with defaults
        social_data = {
            'social_post_count': 0,
            'social_avg_sentiment': None,
            'social_avg_confidence': None,
            'social_unique_authors': 0,
            'social_weighted_sentiment': None,
            'social_engagement_weighted_sentiment': None,
            'social_verified_user_sentiment': None,
            'social_total_engagement': 0
        }
        
        # Try to get real-time sentiment signals
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as signal_count,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(confidence) as avg_confidence,
                    AVG(signal_strength) as avg_strength
                FROM real_time_sentiment_signals
                WHERE symbol = %s
                AND DATE(timestamp) = %s
            """, ('BTC', timestamp_iso.date()))
            
            sentiment_result = cursor.fetchone()
            if sentiment_result and sentiment_result['signal_count'] > 0:
                social_data.update({
                    'social_post_count': sentiment_result['signal_count'],
                    'social_avg_sentiment': sentiment_result['avg_sentiment'],
                    'social_avg_confidence': sentiment_result['avg_confidence'],
                    'social_weighted_sentiment': sentiment_result['avg_strength']
                })
                print(f"  ✅ Real-time signals: {sentiment_result['signal_count']} signals, avg sentiment: {sentiment_result['avg_sentiment']:.3f}")
            else:
                print(f"  📊 No real-time sentiment signals for {timestamp_iso.date()}")
        except Exception as e:
            print(f"  ⚠️  Real-time sentiment lookup failed: {e}")
        
        # Try to get aggregated sentiment data
        try:
            cursor.execute("""
                SELECT 
                    composite_sentiment,
                    confidence_score,
                    signal_strength,
                    news_count
                FROM sentiment_aggregation
                WHERE symbol = %s
                AND DATE(timestamp) = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, ('BTC', timestamp_iso.date()))
            
            agg_result = cursor.fetchone()
            if agg_result:
                # Update with aggregated data if we don't have real-time data
                if social_data['social_post_count'] == 0:
                    social_data.update({
                        'social_avg_sentiment': agg_result['composite_sentiment'],
                        'social_avg_confidence': agg_result['confidence_score'],
                        'social_weighted_sentiment': agg_result['signal_strength'],
                        'social_post_count': agg_result['news_count'] or 0
                    })
                    print(f"  ✅ Aggregated sentiment: {agg_result['composite_sentiment']:.3f}, news count: {agg_result['news_count']}")
        except Exception as e:
            print(f"  ⚠️  Aggregated sentiment lookup failed: {e}")
        
        # Update the materialized record
        update_cursor = conn.cursor()
        
        # Check if record exists first
        update_cursor.execute("""
            SELECT id FROM ml_features_materialized 
            WHERE symbol = %s AND price_date = %s AND price_hour = %s
        """, ('BTC', timestamp_iso.date(), timestamp_iso.hour))
        
        existing = update_cursor.fetchone()
        if existing:
            # Build update query for social fields
            set_clauses = []
            values = []
            
            for field, value in social_data.items():
                set_clauses.append(f"{field} = %s")
                values.append(value)
                
            update_sql = f"""
                UPDATE ml_features_materialized 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = %s AND price_date = %s AND price_hour = %s
            """
            values.extend(['BTC', timestamp_iso.date(), timestamp_iso.hour])
            
            update_cursor.execute(update_sql, values)
            affected = update_cursor.rowcount
            print(f"  ✅ Updated materialized record ({affected} affected)")
        else:
            print(f"  ⚠️  No materialized record found for {timestamp_iso.date()} hour {timestamp_iso.hour}")
        
        conn.commit()
    
    # Check our improvement
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        # Count social sentiment fields that are now populated
        social_fields = ['social_post_count', 'social_avg_sentiment', 'social_avg_confidence', 'social_unique_authors', 
                        'social_weighted_sentiment', 'social_engagement_weighted_sentiment', 'social_total_engagement']
        
        social_populated = len([f for f in social_fields if btc_record.get(f) is not None])
        
        total_populated = len([col for col, val in btc_record.items() if val is not None])
        total_cols = len(btc_record)
        rate = (total_populated / total_cols) * 100
        
        print(f"\n🎯 SOCIAL SENTIMENT INTEGRATION RESULTS:")
        print(f"   Social fields populated: {social_populated}/{len(social_fields)}")
        print(f"   Overall population: {total_populated}/{total_cols} ({rate:.1f}%)")
        print(f"   Social post count: {btc_record.get('social_post_count')}")
        print(f"   Social avg sentiment: {btc_record.get('social_avg_sentiment')}")
        print(f"   Social confidence: {btc_record.get('social_avg_confidence')}")
    
    conn.close()

if __name__ == "__main__":
    implement_social_sentiment_fixed()