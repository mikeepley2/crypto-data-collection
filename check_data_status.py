import mysql.connector

# MySQL connection config
db_config = {
    'host': '127.0.0.1',
    'user': 'news_collector', 
    'password': '99Rules!',
    'database': 'crypto_prices'
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Check recent records count
    cursor.execute("SELECT COUNT(*) as count FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)")
    recent_count = cursor.fetchone()['count']
    print(f"📊 Recent records (2h): {recent_count}")
    
    # Check sample BTC record to see populated columns
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        non_null_cols = [col for col, val in btc_record.items() if val is not None]
        total_cols = len(btc_record)
        population_rate = len(non_null_cols) / total_cols * 100
        print(f"🎯 BTC latest record: {len(non_null_cols)}/{total_cols} columns populated ({population_rate:.1f}%)")
        print(f"✅ Populated columns: {sorted(non_null_cols)[:15]}")
        
        # Show latest timestamp
        latest_time = btc_record.get('timestamp_iso')
        print(f"🕒 Latest BTC record: {latest_time}")
    else:
        print("❌ No BTC records found")
        
    # Check collection activity - recent price data
    cursor.execute("SELECT COUNT(*) as count FROM price_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
    recent_price_data = cursor.fetchone()['count']
    print(f"📈 Recent price data (1h): {recent_price_data} records")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")