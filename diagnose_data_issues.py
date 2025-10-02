#!/usr/bin/env python3
import mysql.connector

config = {
    'host': 'host.docker.internal',
    'user': 'news_collector', 
    'password': '99Rules!',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print("=== DIAGNOSING DATA POPULATION ISSUES ===")

# Check price_data table structure and sample
print("\n1. PRICE_DATA TABLE ANALYSIS:")
cursor.execute('DESCRIBE price_data')
price_columns = [col[0] for col in cursor.fetchall()]
print(f"Columns available: {price_columns}")

cursor.execute('SELECT * FROM price_data WHERE symbol = "BTC" ORDER BY timestamp DESC LIMIT 1')
sample = cursor.fetchone()
if sample:
    print(f"\nSample BTC record ({len(sample)} fields):")
    for i, (col, val) in enumerate(zip(price_columns, sample)):
        if val is not None and val != 0 and val != '':
            print(f"  {col}: {val}")

# Check technical_indicators table
print("\n2. TECHNICAL_INDICATORS TABLE ANALYSIS:")
try:
    cursor.execute('DESCRIBE technical_indicators')
    tech_columns = [col[0] for col in cursor.fetchall()]
    print(f"Technical indicators columns: {len(tech_columns)} total")
    print(f"Key columns: {[col for col in tech_columns if col in ['symbol', 'timestamp', 'rsi_14', 'sma_20', 'macd_line']]}")
    
    cursor.execute('SELECT COUNT(*) FROM technical_indicators WHERE DATE(timestamp) >= DATE_SUB(NOW(), INTERVAL 1 DAY)')
    tech_count = cursor.fetchone()[0]
    print(f"Recent technical records (24h): {tech_count}")
    
    if tech_count > 0:
        cursor.execute('SELECT symbol, timestamp, rsi_14, sma_20, macd_line FROM technical_indicators WHERE symbol = "BTC" ORDER BY timestamp DESC LIMIT 1')
        tech_sample = cursor.fetchone()
        if tech_sample:
            print(f"Sample BTC technical data: symbol={tech_sample[0]}, timestamp={tech_sample[1]}, rsi_14={tech_sample[2]}, sma_20={tech_sample[3]}, macd_line={tech_sample[4]}")
            
except Exception as e:
    print(f"Technical indicators table issue: {e}")

# Check macro_indicators table
print("\n3. MACRO_INDICATORS TABLE ANALYSIS:")
try:
    cursor.execute('SHOW TABLES LIKE "macro_%"')
    macro_tables = cursor.fetchall()
    print(f"Macro-related tables: {macro_tables}")
    
    # Try different possible table names
    for table_candidate in ['macro_indicators', 'macro_economic_data', 'economic_indicators']:
        try:
            cursor.execute(f'DESCRIBE {table_candidate}')
            macro_columns = [col[0] for col in cursor.fetchall()]
            print(f"{table_candidate} columns: {macro_columns[:5]}")
            
            cursor.execute(f'SELECT COUNT(*) FROM {table_candidate}')
            count = cursor.fetchone()[0]
            print(f"{table_candidate} total records: {count}")
            break
        except:
            continue
            
except Exception as e:
    print(f"Macro indicators issue: {e}")

# Check OHLC data
print("\n4. OHLC_DATA TABLE ANALYSIS:")
try:
    cursor.execute('DESCRIBE ohlc_data')
    ohlc_columns = [col[0] for col in cursor.fetchall()]
    print(f"OHLC columns: {ohlc_columns}")
    
    cursor.execute('SELECT COUNT(*) FROM ohlc_data WHERE DATE(timestamp) >= DATE_SUB(NOW(), INTERVAL 1 DAY)')
    ohlc_count = cursor.fetchone()[0]
    print(f"Recent OHLC records (24h): {ohlc_count}")
    
    if ohlc_count > 0:
        cursor.execute('SELECT symbol, timestamp, open_price, high_price, low_price, close_price FROM ohlc_data WHERE symbol = "BTC" ORDER BY timestamp DESC LIMIT 1')
        ohlc_sample = cursor.fetchone()
        if ohlc_sample:
            print(f"Sample BTC OHLC: {ohlc_sample}")
            
except Exception as e:
    print(f"OHLC table issue: {e}")

# Check what columns actually exist vs what should be populated
print("\n5. MATERIALIZED TABLE CURRENT STATE:")
cursor.execute('SELECT symbol, current_price, volume_24h, market_cap, rsi_14, vwap FROM ml_features_materialized ORDER BY created_at DESC LIMIT 1')
current_sample = cursor.fetchone()
if current_sample:
    print(f"Current materialized sample: symbol={current_sample[0]}, price={current_sample[1]}, volume={current_sample[2]}, market_cap={current_sample[3]}, rsi={current_sample[4]}, vwap={current_sample[5]}")

conn.close()
print("\n=== DIAGNOSIS COMPLETE ===")