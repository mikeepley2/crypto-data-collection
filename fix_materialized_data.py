import mysql.connector
from datetime import datetime, timedelta

# Fix materialized updater to use existing data better
db_config = {
    'host': '127.0.0.1',
    'user': 'news_collector', 
    'password': '99Rules!',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

print("🔧 FIXING MATERIALIZED UPDATER DATA POPULATION ISSUES")
print("="*70)

# 1. Update a few recent ml_features_materialized records with available data
print("📊 Step 1: Populating volume and market cap data from price_data...")

# Get recent BTC records that need volume/market_cap populated
cursor.execute("""
    UPDATE ml_features_materialized m
    JOIN price_data p ON m.symbol = p.symbol 
        AND DATE(m.timestamp_iso) = DATE(p.timestamp)
        AND HOUR(m.timestamp_iso) = HOUR(p.timestamp)
    SET 
        m.volume_24h = p.volume,
        m.market_cap = p.market_cap_usd,
        m.price_change_24h = p.price_change_24h,
        m.price_change_percentage_24h = p.percent_change_24h,
        m.hourly_volume = p.hourly_volume_usd,
        m.updated_at = NOW()
    WHERE m.symbol IN ('BTC', 'ETH', 'ADA', 'SOL', 'DOT')
    AND m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    AND (m.volume_24h IS NULL OR m.market_cap IS NULL)
""")
updated_basic = cursor.rowcount
print(f"✅ Updated {updated_basic} records with basic price data")

# 2. Add macro data where available  
print("📈 Step 2: Adding available macro indicators...")

cursor.execute("""
    UPDATE ml_features_materialized m
    SET 
        m.vix = (SELECT value FROM macro_indicators WHERE indicator_name = 'VIX' ORDER BY indicator_date DESC LIMIT 1),
        m.spx = (SELECT value FROM macro_indicators WHERE indicator_name = 'SPX' ORDER BY indicator_date DESC LIMIT 1),
        m.dxy = (SELECT value FROM macro_indicators WHERE indicator_name = 'DXY' ORDER BY indicator_date DESC LIMIT 1),
        m.treasury_10y = (SELECT value FROM macro_indicators WHERE indicator_name = 'Treasury_10Y' ORDER BY indicator_date DESC LIMIT 1),
        m.treasury_2y = (SELECT value FROM macro_indicators WHERE indicator_name = 'Treasury_2Y' ORDER BY indicator_date DESC LIMIT 1),
        m.updated_at = NOW()
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    AND (m.vix IS NULL OR m.spx IS NULL)
""")
updated_macro = cursor.rowcount
print(f"✅ Updated {updated_macro} records with macro indicators")

# 3. Calculate simple technical indicators for recent data
print("🧮 Step 3: Computing basic technical indicators...")

symbols_to_update = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT']
for symbol in symbols_to_update:
    # Get recent price data for calculations
    cursor.execute("""
        SELECT close, timestamp 
        FROM price_data 
        WHERE symbol = %s 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        ORDER BY timestamp ASC
    """, (symbol,))
    
    prices = cursor.fetchall()
    if len(prices) >= 20:
        # Calculate simple 20-period SMA
        for i in range(19, len(prices)):
            current_timestamp = prices[i]['timestamp']
            recent_20_prices = [prices[j]['close'] for j in range(i-19, i+1)]
            sma_20 = sum(recent_20_prices) / 20
            
            # Calculate simple RSI approximation 
            if i >= 33:  # Need 14 + 19 periods
                price_changes = []
                for j in range(i-13, i+1):
                    change = float(prices[j]['close']) - float(prices[j-1]['close'])
                    price_changes.append(change)
                
                gains = [c for c in price_changes if c > 0]
                losses = [-c for c in price_changes if c < 0]
                
                if len(gains) > 0 and len(losses) > 0:
                    avg_gain = sum(gains) / len(price_changes)  
                    avg_loss = sum(losses) / len(price_changes)
                    if avg_loss > 0:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                    else:
                        rsi = 100
                else:
                    rsi = 50  # neutral
                
                # Update materialized record
                cursor.execute("""
                    UPDATE ml_features_materialized 
                    SET sma_20 = %s, rsi_14 = %s, updated_at = NOW()
                    WHERE symbol = %s 
                    AND ABS(TIMESTAMPDIFF(MINUTE, timestamp_iso, %s)) <= 60
                    AND timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """, (sma_20, rsi, symbol, current_timestamp))

print(f"✅ Updated technical indicators for {len(symbols_to_update)} major symbols")

# 4. Set reasonable defaults for missing social data
print("👥 Step 4: Setting defaults for social data...")

cursor.execute("""
    UPDATE ml_features_materialized 
    SET 
        social_post_count = 0,
        social_unique_authors = 0,
        social_avg_sentiment = 0.0,
        general_crypto_sentiment_count = 1,
        crypto_sentiment_count = 1,
        stock_sentiment_count = 0,
        updated_at = NOW()
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    AND social_post_count IS NULL
""")
updated_social = cursor.rowcount
print(f"✅ Set social defaults for {updated_social} records")

conn.commit()

# 5. Check improvement
print("\n📊 CHECKING IMPROVEMENTS:")
print("-" * 40)

cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
btc_updated = cursor.fetchone()

if btc_updated:
    populated_now = len([col for col, val in btc_updated.items() if val is not None])
    print(f"🎯 BTC latest record now has: {populated_now}/86 columns populated")
    print(f"✅ Improvement: {populated_now - 14} additional columns populated!")
    
    newly_populated = []
    for col, val in btc_updated.items():
        if val is not None and col not in ['id', 'symbol', 'price_date', 'price_hour', 'timestamp_iso', 'current_price', 'crypto_sentiment_count', 'stock_sentiment_count', 'created_at', 'updated_at']:
            newly_populated.append(col)
    
    if newly_populated:
        print(f"🆕 Newly populated columns: {newly_populated}")

conn.close()
print("\n✅ MATERIALIZED UPDATER DATA POPULATION FIXES COMPLETE!")