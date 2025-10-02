import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1', user='news_collector', password='99Rules!', database='crypto_prices')
cursor = conn.cursor(dictionary=True)

print("🔍 TECHNICAL INDICATORS DATA AVAILABILITY:")
print("="*60)

# Check technical_indicators table data
cursor.execute("SELECT COUNT(*) as total FROM technical_indicators")
total = cursor.fetchone()['total'] 
print(f"📈 Total technical indicators records: {total}")

# Check recent data
cursor.execute("SELECT COUNT(*) as recent, MAX(timestamp) as latest FROM technical_indicators WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
recent_data = cursor.fetchone()
print(f"📈 Recent (7d) records: {recent_data['recent']}, Latest: {recent_data['latest']}")

# Check what symbols have recent technical data  
cursor.execute("SELECT symbol, COUNT(*) as count, MAX(timestamp) as latest FROM technical_indicators WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY symbol ORDER BY count DESC LIMIT 10")
symbol_counts = cursor.fetchall()
print("📈 Recent technical data by symbol:")
for row in symbol_counts:
    print(f"   {row['symbol']}: {row['count']} records, latest: {row['latest']}")

# Check what columns exist in technical_indicators
cursor.execute("DESCRIBE technical_indicators")  
tech_columns = [row['Field'] for row in cursor.fetchall()]
print(f"📋 Technical indicators columns: {tech_columns}")

# Check if BTC has any technical data
cursor.execute("SELECT COUNT(*) as btc_count, MAX(timestamp) as btc_latest FROM technical_indicators WHERE symbol='BTC'")
btc_tech = cursor.fetchone()
print(f"🔸 BTC technical data: {btc_tech['btc_count']} records, latest: {btc_tech['btc_latest']}")

# Check sample BTC technical data
cursor.execute("SELECT * FROM technical_indicators WHERE symbol='BTC' ORDER BY timestamp DESC LIMIT 1")
btc_sample = cursor.fetchone()
if btc_sample:
    print("🔸 Latest BTC technical data sample:")
    for col, val in btc_sample.items():
        if val is not None:
            print(f"   {col}: {val}")

conn.close()