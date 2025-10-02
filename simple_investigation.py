import mysql.connector

db_config = {
    'host': '127.0.0.1', 
    'user': 'news_collector', 
    'password': '99Rules!', 
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**db_config)
cursor = cursor = conn.cursor(dictionary=True)

print("🔍 INVESTIGATING DATA GAPS:")
print("="*50)

# Check what tables exist
cursor.execute("SHOW TABLES")
tables = [list(row.values())[0] for row in cursor.fetchall()]
print(f"📋 Tables available: {tables}")

# Check technical_indicators specifically
if 'technical_indicators' in tables:
    cursor.execute("SELECT COUNT(*) as total FROM technical_indicators")
    total = cursor.fetchone()['total']
    print(f"📈 Technical indicators total: {total}")
    
    cursor.execute("SELECT COUNT(*) as recent FROM technical_indicators WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    recent = cursor.fetchone()['recent']
    print(f"📈 Technical indicators (24h): {recent}")
    
    if recent > 0:
        cursor.execute("SELECT symbol, COUNT(*) as count FROM technical_indicators WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR) GROUP BY symbol LIMIT 5")
        recent_symbols = cursor.fetchall()
        print(f"📈 Recent tech symbols: {[(r['symbol'], r['count']) for r in recent_symbols]}")

# Check macro_indicators
if 'macro_indicators' in tables:
    cursor.execute("SELECT COUNT(*) as total FROM macro_indicators")
    macro_total = cursor.fetchone()['total']
    print(f"📊 Macro indicators total: {macro_total}")

# Check price_data columns
if 'price_data' in tables:
    cursor.execute("DESCRIBE price_data")
    price_columns = [row['Field'] for row in cursor.fetchall()]
    print(f"💰 Price data columns: {price_columns}")
    
    cursor.execute("SELECT COUNT(*) as count FROM price_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
    recent_price = cursor.fetchone()['count']
    print(f"💰 Recent price data (1h): {recent_price}")

# Check what columns are NULL in materialized table
cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
btc_record = cursor.fetchone()
if btc_record:
    null_cols = [col for col, val in btc_record.items() if val is None]
    populated_cols = [col for col, val in btc_record.items() if val is not None]
    print(f"🎯 BTC materialized: {len(populated_cols)}/86 populated, {len(null_cols)} NULL")
    print(f"✅ Populated: {populated_cols[:10]}...")
    print(f"❌ Missing: {null_cols[:20]}...")

conn.close()