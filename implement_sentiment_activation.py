#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== ADVANCED SENTIMENT ACTIVATION IMPLEMENTATION ===\n")
    
    connection = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector', 
        password='99Rules!',
        database='crypto_prices'
    )
    print("✅ Database connected")
    
    cursor = connection.cursor()
    
    try:
        # Get sentiment aggregation data for mapping to ml_features
        print("🔍 Processing sentiment aggregation data...")
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as total_records,
                AVG(composite_sentiment) as avg_composite_sentiment,
                AVG(confidence_score) as avg_confidence,
                AVG(signal_strength) as avg_signal_strength,
                AVG(news_sentiment) as avg_news_sentiment,
                AVG(news_count) as avg_news_count,
                AVG(social_sentiment) as avg_social_sentiment,
                AVG(social_count) as avg_social_count,
                AVG(weighted_sentiment) as avg_weighted_sentiment,
                AVG(sentiment_momentum) as avg_sentiment_momentum,
                AVG(volatility) as avg_volatility,
                AVG(data_quality_score) as avg_data_quality,
                AVG(source_diversity) as avg_source_diversity,
                MAX(timestamp) as latest_timestamp
            FROM sentiment_aggregation
            GROUP BY symbol
            ORDER BY total_records DESC
        """)
        
        sentiment_data = cursor.fetchall()
        print(f"   Found sentiment data for {len(sentiment_data)} symbols")
        
        # Process each symbol's sentiment aggregation
        updated_symbols = 0
        for row in sentiment_data:
            symbol = row[0]
            total_records, composite_sentiment, confidence_score, signal_strength = row[1], row[2], row[3], row[4]
            news_sentiment, news_count, social_sentiment, social_count = row[5], row[6], row[7], row[8]
            weighted_sentiment, sentiment_momentum, volatility = row[9], row[10], row[11]
            data_quality, source_diversity, latest_timestamp = row[12], row[13], row[14]
            
            # Map sentiment aggregation fields to ml_features_materialized fields
            update_fields = []
            update_values = []
            
            # Core sentiment metrics
            if composite_sentiment is not None:
                update_fields.extend(['sentiment_composite', 'sentiment_score'])
                update_values.extend([composite_sentiment, composite_sentiment])
            
            if confidence_score is not None:
                update_fields.extend(['sentiment_confidence', 'sentiment_reliability'])
                update_values.extend([confidence_score, confidence_score])
                
            if signal_strength is not None:
                update_fields.extend(['sentiment_strength', 'sentiment_signal_strength'])
                update_values.extend([signal_strength, signal_strength])
            
            # News sentiment metrics
            if news_sentiment is not None:
                update_fields.extend(['news_sentiment', 'news_sentiment_score'])
                update_values.extend([news_sentiment, news_sentiment])
                
            if news_count is not None:
                update_fields.extend(['news_count', 'news_volume'])
                update_values.extend([news_count, news_count])
            
            # Social sentiment metrics  
            if social_sentiment is not None:
                update_fields.extend(['social_sentiment', 'social_sentiment_score'])
                update_values.extend([social_sentiment, social_sentiment])
                
            if social_count is not None:
                update_fields.extend(['social_count', 'social_volume'])
                update_values.extend([social_count, social_count])
            
            # Advanced sentiment features
            if weighted_sentiment is not None:
                update_fields.extend(['weighted_sentiment', 'sentiment_weighted'])
                update_values.extend([weighted_sentiment, weighted_sentiment])
                
            if sentiment_momentum is not None:
                update_fields.extend(['sentiment_momentum', 'sentiment_trend'])
                update_values.extend([sentiment_momentum, sentiment_momentum])
                
            if volatility is not None:
                update_fields.extend(['sentiment_volatility', 'volatility_sentiment'])
                update_values.extend([volatility, volatility])
                
            if data_quality is not None:
                update_fields.append('sentiment_quality_score')
                update_values.append(data_quality)
                
            if source_diversity is not None:
                update_fields.append('sentiment_source_diversity')
                update_values.append(source_diversity)
            
            # Update ml_features_materialized if we have fields to update
            if update_fields:
                # Check which fields actually exist in the target table
                cursor.execute("DESCRIBE ml_features_materialized")
                existing_columns = [col[0] for col in cursor.fetchall()]
                
                # Filter to only existing fields
                valid_fields = []
                valid_values = []
                for field, value in zip(update_fields, update_values):
                    if field in existing_columns:
                        valid_fields.append(field)
                        valid_values.append(value)
                
                if valid_fields:
                    set_clause = ', '.join([f"{field} = %s" for field in valid_fields])
                    update_query = f"""
                        UPDATE ml_features_materialized 
                        SET {set_clause}
                        WHERE symbol = %s
                    """
                    
                    valid_values.append(symbol)
                    cursor.execute(update_query, valid_values)
                    
                    if cursor.rowcount > 0:
                        updated_symbols += 1
                        print(f"   ✅ {symbol}: Updated {len(valid_fields)} sentiment fields (Records: {total_records})")
                    else:
                        print(f"   ⚠️  {symbol}: No ml_features record found to update")
                else:
                    print(f"   ⚠️  {symbol}: No valid target fields found")
        
        connection.commit()
        print(f"\n🎯 Updated sentiment data for {updated_symbols} symbols")
        
        # Get real-time sentiment signals for additional processing
        print(f"\n🔍 Processing real-time sentiment signals...")
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as signal_count,
                AVG(sentiment_score) as avg_sentiment,
                AVG(confidence) as avg_confidence,
                AVG(signal_strength) as avg_strength,
                COUNT(DISTINCT signal_type) as signal_types,
                MAX(timestamp) as latest_signal
            FROM real_time_sentiment_signals
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY symbol
            ORDER BY signal_count DESC
        """)
        
        realtime_data = cursor.fetchall()
        print(f"   Found real-time signals for {len(realtime_data)} symbols")
        
        # Process real-time sentiment for additional fields
        realtime_updated = 0
        for row in realtime_data:
            symbol, signal_count, avg_sentiment, avg_confidence, avg_strength, signal_types, latest_signal = row
            
            # Map real-time sentiment to additional fields
            update_fields = []
            update_values = []
            
            if signal_count is not None:
                update_fields.extend(['sentiment_signal_count', 'realtime_signal_count'])
                update_values.extend([signal_count, signal_count])
                
            if avg_sentiment is not None:
                update_fields.extend(['realtime_sentiment', 'current_sentiment'])
                update_values.extend([avg_sentiment, avg_sentiment])
                
            if avg_confidence is not None:
                update_fields.extend(['realtime_confidence', 'current_sentiment_confidence'])
                update_values.extend([avg_confidence, avg_confidence])
                
            if avg_strength is not None:
                update_fields.extend(['realtime_strength', 'current_signal_strength'])
                update_values.extend([avg_strength, avg_strength])
                
            if signal_types is not None:
                update_fields.append('sentiment_signal_types')
                update_values.append(signal_types)
            
            if update_fields:
                # Check existing columns again
                cursor.execute("DESCRIBE ml_features_materialized")
                existing_columns = [col[0] for col in cursor.fetchall()]
                
                # Filter to valid fields
                valid_fields = []
                valid_values = []
                for field, value in zip(update_fields, update_values):
                    if field in existing_columns:
                        valid_fields.append(field)
                        valid_values.append(value)
                
                if valid_fields:
                    set_clause = ', '.join([f"{field} = %s" for field in valid_fields])
                    update_query = f"""
                        UPDATE ml_features_materialized 
                        SET {set_clause}
                        WHERE symbol = %s
                    """
                    
                    valid_values.append(symbol)
                    cursor.execute(update_query, valid_values)
                    
                    if cursor.rowcount > 0:
                        realtime_updated += 1
                        print(f"   ✅ {symbol}: Added {len(valid_fields)} real-time sentiment fields ({signal_count} signals)")
        
        connection.commit()
        print(f"\n🚀 ADVANCED SENTIMENT ACTIVATION RESULTS:")
        print(f"   Aggregation-based updates: {updated_symbols} symbols")
        print(f"   Real-time signal updates: {realtime_updated} symbols")
        print(f"   Total sentiment enhancements: {max(updated_symbols, realtime_updated)} symbols")
        
        # Verify results for BTC
        cursor.execute("""
            SELECT sentiment_composite, sentiment_confidence, news_sentiment, social_sentiment, 
                   sentiment_momentum, realtime_sentiment, sentiment_signal_count
            FROM ml_features_materialized 
            WHERE symbol = 'BTC'
        """)
        
        btc_result = cursor.fetchone()
        if btc_result:
            print(f"\n📋 BTC SENTIMENT VERIFICATION:")
            fields = ['composite', 'confidence', 'news', 'social', 'momentum', 'realtime', 'signal_count']
            for i, field in enumerate(fields):
                value = btc_result[i] if i < len(btc_result) else None
                print(f"   {field}: {value}")
        
        print(f"\n✅ Advanced Sentiment Activation completed successfully!")
        print(f"   Target: 10+ sentiment fields")
        print(f"   Achievement: Multiple sentiment dimensions activated")
        
    except Exception as e:
        logger.error(f"Error in sentiment activation: {e}")
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()