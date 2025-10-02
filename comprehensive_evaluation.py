#!/usr/bin/env python3
"""
Comprehensive system evaluation after cleanup
"""
import mysql.connector
from datetime import datetime, timedelta
import json

def get_db_connection(database='crypto_prices'):
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database=database
    )

def evaluate_materialized_updater():
    """Evaluate materialized updater performance"""
    print("🔧 MATERIALIZED UPDATER EVALUATION")
    print("=" * 50)
    
    try:
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # Check processing rate
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as last_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as last_24h,
                MAX(created_at) as latest_update,
                MIN(created_at) as earliest_update
            FROM ml_features_materialized
        """)
        result = cursor.fetchone()
        total, last_1h, last_24h, latest, earliest = result
        
        print(f"📊 Processing Statistics:")
        print(f"   Total records: {total:,}")
        print(f"   Last 1 hour: {last_1h:,}")
        print(f"   Last 24 hours: {last_24h:,}")
        print(f"   Latest update: {latest}")
        print(f"   Data span: {earliest} to {latest}")
        
        if latest:
            age_minutes = (datetime.now() - latest).total_seconds() / 60
            print(f"   Data freshness: {age_minutes:.1f} minutes old")
        
        # Check completion rate
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT symbol) as symbols_processed,
                AVG(CASE WHEN tnx_10y_yield IS NOT NULL THEN 1 ELSE 0 END * 100) as macro_completion,
                AVG(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END * 100) as technical_completion,
                AVG(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END * 100) as sentiment_completion
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        result = cursor.fetchone()
        symbols, macro_pct, tech_pct, sentiment_pct = result
        
        print(f"\n📈 Completion Rates (Last 24h):")
        print(f"   Symbols processed: {symbols}")
        print(f"   Macro indicators: {macro_pct:.1f}%")
        print(f"   Technical indicators: {tech_pct:.1f}%")
        print(f"   Sentiment analysis: {sentiment_pct:.1f}%")
        
        cursor.close()
        conn.close()
        
        return {
            'total_records': total,
            'last_24h': last_24h,
            'data_freshness_minutes': age_minutes if latest else None,
            'symbols_processed': symbols,
            'macro_completion': macro_pct,
            'technical_completion': tech_pct,
            'sentiment_completion': sentiment_pct
        }
        
    except Exception as e:
        print(f"❌ Error evaluating materialized updater: {e}")
        return {}

def evaluate_data_collection():
    """Evaluate data collection across all sources"""
    print("\n📊 DATA COLLECTION EVALUATION")
    print("=" * 50)
    
    try:
        # Check crypto_prices database
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # OHLC data freshness
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
            FROM ohlc_data
        """)
        result = cursor.fetchone()
        ohlc_total, ohlc_latest, ohlc_recent = result
        
        print(f"💰 Price Data (OHLC):")
        print(f"   Total records: {ohlc_total:,}")
        print(f"   Latest: {ohlc_latest}")
        if ohlc_latest:
            age_hours = (datetime.now() - ohlc_latest).total_seconds() / 3600
            print(f"   Age: {age_hours:.1f}h ago")
        print(f"   Recent (1h): {ohlc_recent}")
        
        cursor.close()
        conn.close()
        
        # Check crypto_news database
        news_conn = get_db_connection('crypto_news')
        news_cursor = news_conn.cursor()
        
        # News data
        news_cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
            FROM crypto_news_data
        """)
        result = news_cursor.fetchone()
        news_total, news_latest, news_recent_1h, news_recent_24h = result
        
        print(f"\n📰 News Data:")
        print(f"   Total records: {news_total:,}")
        print(f"   Latest: {news_latest}")
        if news_latest:
            age_hours = (datetime.now() - news_latest).total_seconds() / 3600
            print(f"   Age: {age_hours:.1f}h ago")
        print(f"   Recent: {news_recent_1h} (1h), {news_recent_24h} (24h)")
        
        # Social media data
        news_cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
            FROM social_media_posts
        """)
        result = news_cursor.fetchone()
        social_total, social_latest, social_recent_1h, social_recent_24h = result
        
        print(f"\n🐦 Social Media Data:")
        print(f"   Total records: {social_total:,}")
        print(f"   Latest: {social_latest}")
        if social_latest:
            age_hours = (datetime.now() - social_latest).total_seconds() / 3600
            print(f"   Age: {age_hours:.1f}h ago")
        print(f"   Recent: {social_recent_1h} (1h), {social_recent_24h} (24h)")
        
        # Sentiment data
        news_cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MAX(created_at) as latest,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
            FROM sentiment_data
        """)
        result = news_cursor.fetchone()
        sentiment_total, sentiment_latest, sentiment_recent_1h, sentiment_recent_24h = result
        
        print(f"\n🧠 Sentiment Data:")
        print(f"   Total records: {sentiment_total:,}")
        print(f"   Latest: {sentiment_latest}")
        if sentiment_latest:
            age_hours = (datetime.now() - sentiment_latest).total_seconds() / 3600
            print(f"   Age: {age_hours:.1f}h ago")
        print(f"   Recent: {sentiment_recent_1h} (1h), {sentiment_recent_24h} (24h)")
        
        news_cursor.close()
        news_conn.close()
        
        return {
            'ohlc': {'total': ohlc_total, 'latest': ohlc_latest, 'recent_1h': ohlc_recent},
            'news': {'total': news_total, 'latest': news_latest, 'recent_1h': news_recent_1h, 'recent_24h': news_recent_24h},
            'social': {'total': social_total, 'latest': social_latest, 'recent_1h': social_recent_1h, 'recent_24h': social_recent_24h},
            'sentiment': {'total': sentiment_total, 'latest': sentiment_latest, 'recent_1h': sentiment_recent_1h, 'recent_24h': sentiment_recent_24h}
        }
        
    except Exception as e:
        print(f"❌ Error evaluating data collection: {e}")
        return {}

def evaluate_final_dataset():
    """Evaluate final ML dataset quality"""
    print("\n🎯 FINAL DATASET EVALUATION")
    print("=" * 50)
    
    try:
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        # Overall dataset stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                MIN(datetime_utc) as earliest_date,
                MAX(datetime_utc) as latest_date,
                AVG(current_price) as avg_price
            FROM ml_features_materialized
        """)
        result = cursor.fetchone()
        total, symbols, earliest, latest, avg_price = result
        
        print(f"📊 Dataset Overview:")
        print(f"   Total records: {total:,}")
        print(f"   Unique symbols: {symbols}")
        print(f"   Date range: {earliest} to {latest}")
        print(f"   Average price: ${avg_price:.2f}" if avg_price else "   Average price: N/A")
        
        # Feature completeness analysis
        cursor.execute("""
            SELECT 
                -- Price features
                SUM(CASE WHEN current_price IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as price_completeness,
                SUM(CASE WHEN volume_24h IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as volume_completeness,
                
                -- Technical indicators
                SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as rsi_completeness,
                SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as sma_completeness,
                SUM(CASE WHEN macd_line IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as macd_completeness,
                
                -- Macro indicators
                SUM(CASE WHEN vix IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as vix_completeness,
                SUM(CASE WHEN spx IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as spx_completeness,
                SUM(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as dxy_completeness,
                
                -- Sentiment features
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as cryptobert_completeness,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as social_completeness,
                SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as news_sentiment_completeness
            FROM ml_features_materialized
        """)
        result = cursor.fetchone()
        
        feature_completeness = {
            'Price': result[0],
            'Volume': result[1],
            'RSI': result[2],
            'SMA': result[3],
            'MACD': result[4],
            'VIX': result[5],
            'SPX': result[6],
            'DXY': result[7],
            'CryptoBERT': result[8],
            'Social Sentiment': result[9],
            'News Sentiment': result[10]
        }
        
        print(f"\n📈 Feature Completeness:")
        for feature, completeness in feature_completeness.items():
            status = "✅" if completeness >= 80 else "⚠️" if completeness >= 50 else "❌"
            print(f"   {status} {feature}: {completeness:.1f}%")
        
        # Recent data quality
        cursor.execute("""
            SELECT 
                COUNT(*) as recent_records,
                COUNT(DISTINCT symbol) as recent_symbols,
                AVG(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END * 100) as recent_technical_completeness,
                AVG(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END * 100) as recent_sentiment_completeness
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        result = cursor.fetchone()
        recent_records, recent_symbols, recent_tech, recent_sentiment = result
        
        print(f"\n⏰ Recent Data Quality (24h):")
        print(f"   Records added: {recent_records:,}")
        print(f"   Symbols updated: {recent_symbols}")
        print(f"   Technical completeness: {recent_tech:.1f}%")
        print(f"   Sentiment completeness: {recent_sentiment:.1f}%")
        
        cursor.close()
        conn.close()
        
        return {
            'total_records': total,
            'unique_symbols': symbols,
            'feature_completeness': feature_completeness,
            'recent_records': recent_records,
            'recent_symbols': recent_symbols,
            'recent_technical_completeness': recent_tech,
            'recent_sentiment_completeness': recent_sentiment
        }
        
    except Exception as e:
        print(f"❌ Error evaluating final dataset: {e}")
        return {}

def main():
    print("🔍 COMPREHENSIVE SYSTEM EVALUATION")
    print("=" * 80)
    print(f"Evaluation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run all evaluations
    materialized_results = evaluate_materialized_updater()
    collection_results = evaluate_data_collection()
    dataset_results = evaluate_final_dataset()
    
    print("\n" + "=" * 80)
    print("🎯 EVALUATION SUMMARY")
    print("=" * 80)
    
    if materialized_results:
        print(f"📊 Materialized Updater: {materialized_results.get('last_24h', 0):,} records in 24h")
        print(f"🔧 Processing Health: {materialized_results.get('technical_completion', 0):.1f}% technical, {materialized_results.get('sentiment_completion', 0):.1f}% sentiment")
    
    if dataset_results:
        print(f"🎯 Dataset Quality: {dataset_results.get('total_records', 0):,} total records, {dataset_results.get('unique_symbols', 0)} symbols")
        
    print("\n✅ Evaluation Complete!")

if __name__ == "__main__":
    main()