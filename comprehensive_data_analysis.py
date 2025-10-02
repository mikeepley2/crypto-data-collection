#!/usr/bin/env python3
import mysql.connector
from collections import defaultdict

def analyze_data_gaps():
    """Comprehensive analysis of data gaps in our ML features"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== COMPREHENSIVE DATA GAP ANALYSIS ===\n")

    # 1. Check ml_features_materialized population by column type
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if not btc_record:
        print("❌ No BTC records found in ml_features_materialized")
        return

    print(f"📊 Latest BTC record timestamp: {btc_record['timestamp_iso']}")
    
    # Categorize columns by type
    categories = {
        'price_data': ['current_price', 'price', 'open', 'high', 'low', 'close', 'open_price', 'high_price', 'low_price', 'close_price'],
        'volume': ['volume_24h', 'hourly_volume', 'volume_qty_24h', 'volume_24h_usd', 'total_volume_24h', 'ohlc_volume'],
        'technical_indicators': ['rsi_14', 'sma_20', 'sma_50', 'ema_12', 'ema_26', 'macd_line', 'macd_signal', 'macd_histogram', 
                               'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d', 'atr_14', 'vwap'],
        'macro_economic': ['vix', 'spx', 'dxy', 'tnx', 'fed_funds_rate', 'treasury_10y', 'vix_index', 'dxy_index', 
                          'spx_price', 'gold_price', 'oil_price', 'unemployment_rate', 'inflation_rate', 
                          'gdp_growth', 'cpi_inflation', 'interest_rate', 'employment_rate', 'consumer_confidence', 'retail_sales', 'industrial_production'],
        'social_sentiment': ['crypto_sentiment_count', 'avg_cryptobert_score', 'avg_vader_score', 'avg_textblob_score', 
                           'avg_crypto_keywords_score', 'general_crypto_sentiment_count', 'avg_general_cryptobert_score',
                           'avg_general_vader_score', 'avg_general_textblob_score', 'avg_general_crypto_keywords_score',
                           'social_post_count', 'social_avg_sentiment', 'social_weighted_sentiment', 'social_engagement_weighted_sentiment',
                           'social_verified_user_sentiment', 'social_total_engagement', 'social_unique_authors', 'social_avg_confidence',
                           'social_sentiment', 'news_sentiment', 'reddit_sentiment'],
        'market_data': ['market_cap', 'market_cap_usd', 'price_change_24h', 'price_change_percentage_24h', 
                       'percent_change_1h', 'percent_change_24h', 'percent_change_7d', 'market_cap_rank'],
        'onchain_data': ['active_addresses_24h', 'transaction_count_24h', 'exchange_net_flow_24h', 'price_volatility_7d',
                        'onchain_market_cap_usd', 'onchain_volume_24h', 'onchain_price_volatility_7d',
                        'onchain_active_addresses', 'onchain_transaction_volume', 'onchain_avg_transaction_value',
                        'onchain_nvt_ratio', 'onchain_mvrv_ratio', 'onchain_whale_transactions'],
        'sentiment_advanced': ['stock_sentiment_count', 'avg_finbert_sentiment_score', 'avg_fear_greed_score',
                             'avg_volatility_sentiment', 'avg_risk_appetite', 'avg_crypto_correlation', 
                             'btc_fear_greed', 'sentiment_positive', 'sentiment_negative', 'sentiment_neutral',
                             'sentiment_fear_greed_index', 'sentiment_volume_weighted', 'sentiment_social_dominance',
                             'sentiment_news_impact', 'sentiment_whale_movement']
    }
    
    # Analyze each category
    for category, columns in categories.items():
        populated = 0
        total = 0
        missing_cols = []
        
        for col in columns:
            if col in btc_record:
                total += 1
                if btc_record[col] is not None:
                    populated += 1
                else:
                    missing_cols.append(col)
        
        if total > 0:
            rate = (populated / total) * 100
            print(f"📈 {category.upper()}: {populated}/{total} ({rate:.1f}%)")
            if missing_cols:
                print(f"   Missing: {', '.join(missing_cols[:5])}")
                if len(missing_cols) > 5:
                    print(f"   ... and {len(missing_cols) - 5} more")
        else:
            print(f"❌ {category.upper()}: No columns found in table")
    
    print("\n=== SOURCE DATA AVAILABILITY ===\n")
    
    # 2. Check source data tables for recent data
    tables_to_check = [
        ('price_data', 'symbol', 'timestamp'),
        ('technical_indicators', 'symbol', 'timestamp'), 
        ('macro_indicators', 'indicator_name', 'date'),
        ('social_sentiment_data', 'symbol', 'created_at'),
        ('ohlc_data', 'symbol', 'timestamp')
    ]
    
    for table, symbol_col, time_col in tables_to_check:
        try:
            if table == 'macro_indicators':
                cursor.execute(f"SELECT COUNT(*) as count, MAX({time_col}) as latest FROM {table}")
            else:
                cursor.execute(f"SELECT COUNT(*) as count, MAX({time_col}) as latest FROM {table} WHERE {symbol_col} = 'BTC'")
            result = cursor.fetchone()
            print(f"📊 {table}: {result['count']} records, latest: {result['latest']}")
            
            # Check for recent data (last 24 hours)
            if table == 'macro_indicators':
                cursor.execute(f"SELECT COUNT(*) as recent FROM {table} WHERE {time_col} >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            else:
                cursor.execute(f"SELECT COUNT(*) as recent FROM {table} WHERE {symbol_col} = 'BTC' AND {time_col} >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            recent = cursor.fetchone()['recent']
            print(f"   Recent (24h): {recent} records")
            
        except Exception as e:
            print(f"❌ {table}: Error - {e}")
    
    print("\n=== MATERIALIZED UPDATER ANALYSIS ===\n")
    
    # 3. Check what the materialized updater is actually doing
    cursor.execute("SELECT COUNT(*) as total_records FROM ml_features_materialized")
    total = cursor.fetchone()['total_records']
    print(f"📊 Total ml_features_materialized records: {total}")
    
    cursor.execute("SELECT COUNT(DISTINCT symbol) as symbols FROM ml_features_materialized")
    symbols = cursor.fetchone()['symbols']
    print(f"📊 Distinct symbols: {symbols}")
    
    cursor.execute("SELECT COUNT(*) as recent FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    recent_updates = cursor.fetchone()['recent']
    print(f"📊 Records updated in last 24h: {recent_updates}")
    
    # 4. Check for processing patterns
    cursor.execute("""
        SELECT symbol, COUNT(*) as records, 
               MAX(updated_at) as last_update,
               COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_technical,
               COUNT(CASE WHEN vix IS NOT NULL THEN 1 END) as has_macro,
               COUNT(CASE WHEN social_post_count > 0 THEN 1 END) as has_social
        FROM ml_features_materialized 
        GROUP BY symbol 
        ORDER BY records DESC 
        LIMIT 10
    """)
    
    print(f"\n📈 TOP 10 SYMBOLS BY RECORD COUNT:")
    print(f"{'Symbol':<8} {'Records':<8} {'Technical':<10} {'Macro':<8} {'Social':<8} {'Last Update'}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        tech_pct = (row['has_technical'] / row['records'] * 100) if row['records'] > 0 else 0
        macro_pct = (row['has_macro'] / row['records'] * 100) if row['records'] > 0 else 0
        social_pct = (row['has_social'] / row['records'] * 100) if row['records'] > 0 else 0
        
        print(f"{row['symbol']:<8} {row['records']:<8} {tech_pct:<9.1f}% {macro_pct:<7.1f}% {social_pct:<7.1f}% {row['last_update']}")

    conn.close()

if __name__ == "__main__":
    analyze_data_gaps()