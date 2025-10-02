#!/usr/bin/env python3
import mysql.connector

def analyze_remaining_gaps():
    """Analyze remaining data gaps and identify improvement opportunities"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== ANALYZING REMAINING DATA GAPS ===\n")
    
    # Get current status
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if not btc_record:
        print("❌ No BTC records found")
        return
    
    # Categorize ALL columns to identify gaps
    all_columns = list(btc_record.keys())
    
    # Define comprehensive categories
    categories = {
        'Price/OHLC': ['current_price', 'open_price', 'high_price', 'low_price', 'close_price', 'ohlc_volume', 'ohlc_source'],
        'Volume/Market': ['volume_24h', 'hourly_volume', 'market_cap', 'total_volume_24h', 'market_cap_usd', 
                         'price_change_24h', 'price_change_percentage_24h', 'percent_change_1h', 'percent_change_24h', 'percent_change_7d'],
        'Technical Indicators': ['rsi_14', 'sma_20', 'sma_50', 'ema_12', 'ema_26', 'macd_line', 'macd_signal', 'macd_histogram',
                               'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d', 'atr_14', 'vwap'],
        'Macro Economic': ['vix', 'spx', 'dxy', 'tnx', 'fed_funds_rate', 'treasury_10y', 'vix_index', 'dxy_index', 
                          'spx_price', 'gold_price', 'oil_price', 'unemployment_rate', 'inflation_rate',
                          'gdp_growth', 'cpi_inflation', 'interest_rate', 'employment_rate', 'consumer_confidence', 'retail_sales', 'industrial_production'],
        'Social Sentiment': ['crypto_sentiment_count', 'avg_cryptobert_score', 'avg_vader_score', 'avg_textblob_score', 
                           'avg_crypto_keywords_score', 'social_post_count', 'social_avg_sentiment', 'social_weighted_sentiment',
                           'social_engagement_weighted_sentiment', 'social_verified_user_sentiment', 'social_total_engagement', 
                           'social_unique_authors', 'social_avg_confidence'],
        'Advanced Sentiment': ['stock_sentiment_count', 'avg_finbert_sentiment_score', 'avg_fear_greed_score',
                             'avg_volatility_sentiment', 'avg_risk_appetite', 'avg_crypto_correlation', 'btc_fear_greed',
                             'sentiment_positive', 'sentiment_negative', 'sentiment_neutral', 'sentiment_fear_greed_index',
                             'sentiment_volume_weighted', 'sentiment_social_dominance', 'sentiment_news_impact', 'sentiment_whale_movement'],
        'General Crypto': ['general_crypto_sentiment_count', 'avg_general_cryptobert_score', 'avg_general_vader_score',
                          'avg_general_textblob_score', 'avg_general_crypto_keywords_score'],
        'OnChain Metrics': ['active_addresses_24h', 'transaction_count_24h', 'exchange_net_flow_24h', 'price_volatility_7d',
                           'onchain_market_cap_usd', 'onchain_volume_24h', 'onchain_price_volatility_7d', 'market_cap_rank',
                           'onchain_active_addresses', 'onchain_transaction_volume', 'onchain_avg_transaction_value',
                           'onchain_nvt_ratio', 'onchain_mvrv_ratio', 'onchain_whale_transactions'],
        'Additional Sentiment': ['social_sentiment', 'news_sentiment', 'reddit_sentiment'],
        'System Fields': ['id', 'symbol', 'price_date', 'price_hour', 'timestamp_iso', 'created_at', 'updated_at', 'data_quality_score']
    }
    
    # Identify uncategorized columns
    categorized_columns = set()
    for cat_columns in categories.values():
        categorized_columns.update(cat_columns)
    
    uncategorized = set(all_columns) - categorized_columns
    if uncategorized:
        categories['Uncategorized'] = list(uncategorized)
    
    print(f"📊 COMPREHENSIVE GAP ANALYSIS:")
    print(f"Total columns in ml_features_materialized: {len(all_columns)}")
    
    gap_opportunities = []
    
    for category, fields in categories.items():
        if category == 'System Fields':
            continue  # Skip system fields
            
        existing_fields = [f for f in fields if f in all_columns]
        populated_count = len([f for f in existing_fields if btc_record.get(f) is not None])
        
        if not existing_fields:
            continue
            
        gap_count = len(existing_fields) - populated_count
        gap_rate = (gap_count / len(existing_fields)) * 100 if existing_fields else 0
        pop_rate = (populated_count / len(existing_fields)) * 100 if existing_fields else 0
        
        status = "✅" if pop_rate >= 75 else "🔄" if pop_rate >= 25 else "❌"
        
        print(f"\n{status} {category}:")
        print(f"   Populated: {populated_count}/{len(existing_fields)} ({pop_rate:.0f}%)")
        print(f"   Gap: {gap_count} fields ({gap_rate:.0f}%)")
        
        if gap_count > 0:
            gap_fields = [f for f in existing_fields if btc_record.get(f) is None]
            print(f"   Missing: {gap_fields[:5]}")  # Show first 5 missing fields
            if len(gap_fields) > 5:
                print(f"           ... and {len(gap_fields) - 5} more")
            
            # Categorize opportunity level
            if gap_count >= 5 and gap_rate >= 50:
                opportunity_level = "HIGH"
            elif gap_count >= 3 and gap_rate >= 30:
                opportunity_level = "MEDIUM"
            else:
                opportunity_level = "LOW"
            
            gap_opportunities.append({
                'category': category,
                'gap_count': gap_count,
                'gap_rate': gap_rate,
                'opportunity': opportunity_level,
                'missing_fields': gap_fields
            })
    
    # Prioritize opportunities
    gap_opportunities.sort(key=lambda x: (x['gap_count'], x['gap_rate']), reverse=True)
    
    print(f"\n🎯 TOP IMPROVEMENT OPPORTUNITIES:")
    for i, opp in enumerate(gap_opportunities[:5], 1):
        print(f"{i}. {opp['category']} ({opp['opportunity']} PRIORITY)")
        print(f"   Potential gain: {opp['gap_count']} fields ({opp['gap_rate']:.0f}% of category)")
        print(f"   Key missing: {opp['missing_fields'][:3]}")
    
    # Suggest specific improvements
    print(f"\n🚀 SPECIFIC IMPROVEMENT STRATEGIES:")
    
    # Check what data sources we have available
    print(f"\n1. 📊 VOLUME/MARKET DATA ENHANCEMENT:")
    cursor.execute("DESCRIBE price_data")
    price_cols = [row['Field'] for row in cursor.fetchall()]
    
    available_price_fields = ['volume', 'market_cap_usd', 'price_change_24h']
    missing_mappings = []
    
    for field in available_price_fields:
        if field in price_cols:
            print(f"   ✅ Available in price_data: {field}")
        else:
            missing_mappings.append(field)
    
    if missing_mappings:
        print(f"   ❌ Need to check: {missing_mappings}")
    
    print(f"\n2. 🔧 TECHNICAL INDICATORS STATUS:")
    cursor.execute("SELECT COUNT(*) as count FROM technical_indicators WHERE symbol = 'BTC' AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    recent_tech = cursor.fetchone()['count']
    print(f"   Recent technical data: {recent_tech} records")
    
    if recent_tech == 0:
        print(f"   💡 OPPORTUNITY: Force technical indicators generation")
    
    print(f"\n3. 📈 MACRO DATA EXPANSION:")
    cursor.execute("SELECT DISTINCT indicator_name FROM macro_indicators ORDER BY indicator_name")
    available_indicators = [row['indicator_name'] for row in cursor.fetchall()]
    print(f"   Available indicators: {len(available_indicators)} types")
    print(f"   Sample: {available_indicators[:10]}")
    
    print(f"\n4. 💬 SENTIMENT DATA ACTIVATION:")
    cursor.execute("SELECT COUNT(*) as count FROM real_time_sentiment_signals WHERE symbol = 'BTC'")
    sentiment_count = cursor.fetchone()['count']
    print(f"   BTC sentiment signals available: {sentiment_count}")
    
    if sentiment_count > 0:
        cursor.execute("SELECT COUNT(DISTINCT DATE(timestamp)) as days FROM real_time_sentiment_signals WHERE symbol = 'BTC'")
        sentiment_days = cursor.fetchone()['days']
        print(f"   Data spans: {sentiment_days} days")
        print(f"   💡 OPPORTUNITY: Activate sentiment aggregation")
    
    print(f"\n5. ⛓️ ONCHAIN DATA INTEGRATION:")
    # Check if we have onchain data sources
    tables_to_check = ['onchain_data', 'blockchain_metrics', 'network_stats']
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"   ✅ {table}: {count} records")
        except:
            print(f"   ❌ {table}: Not available")
    
    # Calculate total potential improvement
    total_potential = sum(opp['gap_count'] for opp in gap_opportunities[:3])  # Top 3 opportunities
    current_total = len([col for col, val in btc_record.items() if val is not None])
    current_rate = (current_total / len(all_columns)) * 100
    potential_rate = ((current_total + total_potential) / len(all_columns)) * 100
    
    print(f"\n🎯 IMPROVEMENT POTENTIAL SUMMARY:")
    print(f"   Current: {current_total}/{len(all_columns)} ({current_rate:.1f}%)")
    print(f"   Top 3 opportunities: +{total_potential} fields")
    print(f"   Potential: {current_total + total_potential}/{len(all_columns)} ({potential_rate:.1f}%)")
    print(f"   Potential gain: +{potential_rate - current_rate:.1f}pp")
    
    conn.close()
    return gap_opportunities

if __name__ == "__main__":
    analyze_remaining_gaps()