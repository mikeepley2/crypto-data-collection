#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta

def main():
    print("=== ADVANCED SENTIMENT ACTIVATION ANALYSIS ===\n")
    
    try:
        connection = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector', 
            password='99Rules!',
            database='crypto_prices'
        )
        print("✅ Database connected")
        
        cursor = connection.cursor()
        
        # Check available sentiment tables
        print("🔍 Checking available sentiment tables...")
        cursor.execute("SHOW TABLES LIKE '%sentiment%'")
        sentiment_tables = [table[0] for table in cursor.fetchall()]
        
        print(f"   Found sentiment tables: {sentiment_tables}")
        
        # Analyze real_time_sentiment_signals if it exists
        if 'real_time_sentiment_signals' in sentiment_tables:
            print(f"\n📊 REAL_TIME_SENTIMENT_SIGNALS ANALYSIS:")
            
            # Check schema
            cursor.execute("DESCRIBE real_time_sentiment_signals")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"   Columns: {columns}")
            
            # Check data volume and timeframe
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_signals,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MIN(timestamp) as earliest_timestamp,
                    MAX(timestamp) as latest_timestamp,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(confidence_score) as avg_confidence
                FROM real_time_sentiment_signals
            """)
            
            result = cursor.fetchone()
            if result:
                total, unique_symbols, earliest, latest, avg_sentiment, avg_confidence = result
                print(f"   Total signals: {total:,}")
                print(f"   Unique symbols: {unique_symbols}")
                print(f"   Timeframe: {earliest} to {latest}")
                print(f"   Avg sentiment: {avg_sentiment:.3f}" if avg_sentiment else "   Avg sentiment: None")
                print(f"   Avg confidence: {avg_confidence:.3f}" if avg_confidence else "   Avg confidence: None")
            
            # Check BTC specific data
            cursor.execute("""
                SELECT 
                    COUNT(*) as btc_signals,
                    MIN(timestamp) as btc_earliest,
                    MAX(timestamp) as btc_latest,
                    AVG(sentiment_score) as btc_avg_sentiment
                FROM real_time_sentiment_signals 
                WHERE symbol = 'BTC'
            """)
            
            btc_result = cursor.fetchone()
            if btc_result:
                btc_count, btc_earliest, btc_latest, btc_sentiment = btc_result
                print(f"   BTC signals: {btc_count:,}")
                if btc_count > 0:
                    print(f"   BTC timeframe: {btc_earliest} to {btc_latest}")
                    print(f"   BTC avg sentiment: {btc_sentiment:.3f}" if btc_sentiment else "   BTC avg sentiment: None")
        
        # Analyze sentiment_aggregation if it exists
        if 'sentiment_aggregation' in sentiment_tables:
            print(f"\n📊 SENTIMENT_AGGREGATION ANALYSIS:")
            
            # Check schema
            cursor.execute("DESCRIBE sentiment_aggregation")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"   Columns: {columns}")
            
            # Check data volume
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MIN(aggregation_date) as earliest_date,
                    MAX(aggregation_date) as latest_date
                FROM sentiment_aggregation
            """)
            
            result = cursor.fetchone()
            if result:
                total, unique_symbols, earliest, latest = result
                print(f"   Total records: {total:,}")
                print(f"   Unique symbols: {unique_symbols}")
                print(f"   Date range: {earliest} to {latest}")
        
        # Check current sentiment field population in ml_features_materialized
        print(f"\n🔍 Current sentiment field population in ml_features_materialized...")
        
        cursor.execute("DESCRIBE ml_features_materialized")
        all_columns = [col[0] for col in cursor.fetchall()]
        
        # Identify sentiment-related fields
        sentiment_keywords = ['sentiment', 'social', 'news', 'reddit', 'twitter', 'fear', 'greed', 'buzz']
        sentiment_fields = [col for col in all_columns if any(keyword in col.lower() for keyword in sentiment_keywords)]
        
        print(f"   Found {len(sentiment_fields)} potential sentiment fields:")
        for field in sentiment_fields:
            print(f"      {field}")
        
        # Check population of sentiment fields
        if sentiment_fields:
            field_checks = []
            for field in sentiment_fields[:10]:  # Check first 10 to avoid query complexity
                field_checks.append(f"SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as {field}_count")
            
            query = f"""
                SELECT 
                    COUNT(*) as total_symbols,
                    {', '.join(field_checks)}
                FROM ml_features_materialized
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                total_symbols = result[0]
                print(f"\n📊 SENTIMENT FIELD POPULATION (out of {total_symbols} symbols):")
                
                populated_fields = 0
                for i, field in enumerate(sentiment_fields[:10]):
                    count = result[i + 1]
                    percentage = count / total_symbols * 100 if total_symbols > 0 else 0
                    status = "✅" if count > 0 else "❌"
                    print(f"   {status} {field}: {count} ({percentage:.1f}%)")
                    if count > 0:
                        populated_fields += 1
                
                print(f"\n🎯 SENTIMENT CATEGORY STATUS:")
                print(f"   Fields populated: {populated_fields}/{len(sentiment_fields[:10])}")
                print(f"   Category completion: {populated_fields/len(sentiment_fields[:10])*100:.1f}%")
        
        # Sample BTC sentiment values
        if sentiment_fields:
            cursor.execute(f"""
                SELECT {', '.join(sentiment_fields[:5])} 
                FROM ml_features_materialized 
                WHERE symbol = 'BTC'
            """)
            
            btc_result = cursor.fetchone()
            if btc_result:
                print(f"\n📋 BTC SAMPLE SENTIMENT VALUES:")
                for i, field in enumerate(sentiment_fields[:5]):
                    value = btc_result[i] if i < len(btc_result) else None
                    print(f"   {field}: {value}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()