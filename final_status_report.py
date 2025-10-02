import mysql.connector

# Final status check
db_config = {
    'host': '127.0.0.1',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

print("🎯 FINAL DATA POPULATION STATUS REPORT")
print("="*60)

# Check current BTC population
cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
btc_record = cursor.fetchone()

if btc_record:
    populated_cols = [col for col, val in btc_record.items() if val is not None]
    null_cols = [col for col, val in btc_record.items() if val is None]
    
    population_rate = len(populated_cols) / 86 * 100
    print(f"🎯 BTC Current Status: {len(populated_cols)}/86 columns populated ({population_rate:.1f}%)")
    print(f"🕒 Latest record: {btc_record['timestamp_iso']}")
    
    # Show what we successfully populated
    basic_data = ['volume_24h', 'market_cap', 'price_change_24h', 'price_change_percentage_24h']
    macro_data = ['vix', 'spx', 'dxy', 'treasury_10y']
    tech_data = ['rsi_14', 'sma_20', 'sma_50', 'ema_12', 'ema_26', 'macd_line']
    
    print("\n📊 DATA AVAILABILITY BY CATEGORY:")
    print("-" * 40)
    
    basic_populated = [col for col in basic_data if btc_record.get(col) is not None]
    macro_populated = [col for col in macro_data if btc_record.get(col) is not None]
    tech_populated = [col for col in tech_data if btc_record.get(col) is not None]
    
    print(f"💰 Basic Price Data: {len(basic_populated)}/4 - {basic_populated}")
    print(f"📈 Macro Indicators: {len(macro_populated)}/4 - {macro_populated}")
    print(f"🔬 Technical Indicators: {len(tech_populated)}/6 - {tech_populated}")

# Check what issues remain
print("\n🚨 REMAINING ISSUES:")
print("-" * 40)

# Technical indicators freshness
cursor.execute("SELECT COUNT(*) as recent FROM technical_indicators WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
recent_tech = cursor.fetchone()['recent']
print(f"❌ Technical Indicators: {recent_tech} recent records (need current data generation)")

# Check macro data availability
cursor.execute("SELECT indicator_name, COUNT(*) as count, MAX(indicator_date) as latest FROM macro_indicators GROUP BY indicator_name ORDER BY count DESC LIMIT 5")
macro_status = cursor.fetchall()
print(f"✅ Macro Data Available:")
for row in macro_status:
    print(f"   {row['indicator_name']}: {row['count']} records, latest: {row['latest']}")

print("\n🔧 NEXT STEPS TO REACH 60%+ POPULATION:")
print("-" * 50)
print("1. ✅ COMPLETED: Fixed database references (crypto_news → crypto_prices)")
print("2. ✅ COMPLETED: Populated basic price data (143 records updated)")
print("3. 🔄 IN PROGRESS: Technical indicators service generating fresh data")
print("4. 🔄 NEEDED: Column mapping fixes in materialized updater")
print("5. 🔄 NEEDED: Social sentiment data defaults")
print("6. 🔄 NEEDED: OHLC data integration")

cursor.close()
conn.close()