#!/usr/bin/env python3
import mysql.connector

def test_data_improvements():
    """Test if our fixes improved data population"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    # Test price data integration - check if OHLC fields are populated
    print("=== TESTING DATA IMPROVEMENTS ===\n")
    
    # 1. Check if we have recent price data with OHLC
    cursor.execute("""
        SELECT symbol, timestamp, open, high, low, close, volume, market_cap_usd
        FROM price_data 
        WHERE symbol = 'BTC' 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        ORDER BY timestamp DESC 
        LIMIT 3
    """)
    
    recent_price = cursor.fetchall()
    print(f"📊 Recent BTC price data (last 2h): {len(recent_price)} records")
    for row in recent_price:
        print(f"  {row['timestamp']}: O:{row['open']} H:{row['high']} L:{row['low']} C:{row['close']} V:{row['volume']}")
    
    # 2. Check technical indicators data
    cursor.execute("""
        SELECT symbol, timestamp, rsi_14, sma_20, macd_line 
        FROM technical_indicators 
        WHERE symbol = 'BTC' 
        ORDER BY timestamp DESC 
        LIMIT 3
    """)
    
    tech_data = cursor.fetchall()
    print(f"\n🔧 BTC technical indicators: {len(tech_data)} recent records")
    for row in tech_data:
        print(f"  {row['timestamp']}: RSI:{row['rsi_14']} SMA20:{row['sma_20']} MACD:{row['macd_line']}")
    
    # 3. Check macro data availability
    cursor.execute("""
        SELECT indicator_name, COUNT(*) as records, MAX(indicator_date) as latest
        FROM macro_indicators 
        WHERE indicator_name IN ('VIX', 'SPX', 'DGS10', 'FEDFUNDS')
        GROUP BY indicator_name
    """)
    
    macro_data = cursor.fetchall()
    print(f"\n📈 Macro indicators available:")
    for row in macro_data:
        print(f"  {row['indicator_name']}: {row['records']} records, latest: {row['latest']}")
    
    # 4. Run our data gap analysis on materialized table
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        # Count populated fields by category
        price_fields = ['current_price', 'open_price', 'high_price', 'low_price', 'close_price', 'ohlc_volume']
        tech_fields = ['rsi_14', 'sma_20', 'sma_50', 'ema_12', 'ema_26', 'macd_line', 'vwap']
        macro_fields = ['vix', 'spx', 'dxy', 'tnx', 'fed_funds_rate']
        volume_fields = ['volume_24h', 'market_cap']
        
        def count_populated(fields):
            return len([f for f in fields if btc_record.get(f) is not None])
        
        price_pop = count_populated(price_fields)
        tech_pop = count_populated(tech_fields) 
        macro_pop = count_populated(macro_fields)
        volume_pop = count_populated(volume_fields)
        
        total_populated = len([col for col, val in btc_record.items() if val is not None])
        total_cols = len(btc_record)
        rate = (total_populated / total_cols) * 100
        
        print(f"\n🎯 BTC MATERIALIZED TABLE STATUS:")
        print(f"  Overall: {total_populated}/{total_cols} columns ({rate:.1f}%)")
        print(f"  Price/OHLC: {price_pop}/{len(price_fields)} populated")
        print(f"  Technical: {tech_pop}/{len(tech_fields)} populated") 
        print(f"  Macro: {macro_pop}/{len(macro_fields)} populated")
        print(f"  Volume/Market: {volume_pop}/{len(volume_fields)} populated")
        print(f"  Latest timestamp: {btc_record['timestamp_iso']}")
        
        # Show specific values to diagnose
        print(f"\n📋 Sample values:")
        print(f"  current_price: {btc_record.get('current_price')}")
        print(f"  open_price: {btc_record.get('open_price')}")
        print(f"  rsi_14: {btc_record.get('rsi_14')}")
        print(f"  vix: {btc_record.get('vix')}")
        
    conn.close()

if __name__ == "__main__":
    test_data_improvements()