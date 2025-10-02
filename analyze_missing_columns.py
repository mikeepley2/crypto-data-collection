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

print("=== IDENTIFYING MISSING COLUMN POPULATION ===")

# Get recent record to analyze what's missing
cursor.execute('''
    SELECT * FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    ORDER BY created_at DESC 
    LIMIT 1
''')
record = cursor.fetchone()

# Get column names
cursor.execute('DESCRIBE ml_features_materialized')
columns_info = cursor.fetchall()
column_names = [col[0] for col in columns_info]

if record:
    print(f"Analyzing record for symbol with {len(record)} fields...")
    
    # Identify empty columns
    empty_columns = []
    populated_columns = []
    
    for i, (col_name, value) in enumerate(zip(column_names, record)):
        if value is None or value == '' or (isinstance(value, (int, float)) and value == 0):
            empty_columns.append((col_name, columns_info[i][1]))  # name, type
        else:
            populated_columns.append(col_name)
    
    print(f"\nEmpty/Zero columns ({len(empty_columns)}):")
    
    # Categorize missing columns by likely data source
    social_missing = []
    macro_missing = []
    onchain_missing = []
    sentiment_missing = []
    ohlc_missing = []
    other_missing = []
    
    for col_name, col_type in empty_columns:
        if any(x in col_name.lower() for x in ['social', 'reddit']):
            social_missing.append((col_name, col_type))
        elif any(x in col_name.lower() for x in ['vix', 'spx', 'dxy', 'treasury', 'fed', 'unemployment', 'inflation', 'gold', 'oil']):
            macro_missing.append((col_name, col_type))
        elif any(x in col_name.lower() for x in ['addresses', 'transaction', 'exchange', 'onchain', 'flow']):
            onchain_missing.append((col_name, col_type))
        elif any(x in col_name.lower() for x in ['sentiment', 'fear', 'greed']):
            sentiment_missing.append((col_name, col_type))
        elif any(x in col_name.lower() for x in ['open', 'high', 'low', 'close', 'ohlc']):
            ohlc_missing.append((col_name, col_type))
        else:
            other_missing.append((col_name, col_type))
    
    if social_missing:
        print(f"\n📱 Social Data Missing ({len(social_missing)} columns):")
        for col, dtype in social_missing:
            print(f"  - {col} ({dtype})")
    
    if macro_missing:
        print(f"\n📊 Macro Economic Missing ({len(macro_missing)} columns):")
        for col, dtype in macro_missing:
            print(f"  - {col} ({dtype})")
    
    if onchain_missing:
        print(f"\n⛓️ On-Chain Data Missing ({len(onchain_missing)} columns):")
        for col, dtype in onchain_missing:
            print(f"  - {col} ({dtype})")
    
    if sentiment_missing:
        print(f"\n😊 Sentiment Data Missing ({len(sentiment_missing)} columns):")
        for col, dtype in sentiment_missing:
            print(f"  - {col} ({dtype})")
    
    if ohlc_missing:
        print(f"\n📈 OHLC Data Missing ({len(ohlc_missing)} columns):")
        for col, dtype in ohlc_missing:
            print(f"  - {col} ({dtype})")
    
    if other_missing:
        print(f"\n❓ Other Missing ({len(other_missing)} columns):")
        for col, dtype in other_missing:
            print(f"  - {col} ({dtype})")

# Check if data exists in source tables for missing columns
print("\n=== CHECKING SOURCE DATA AVAILABILITY ===")

# Check social sentiment data
try:
    cursor.execute("SELECT COUNT(*) FROM crypto_news.social_sentiment_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    social_count = cursor.fetchone()[0]
    print(f"Social sentiment records (24h): {social_count}")
except Exception as e:
    print(f"Social sentiment table issue: {e}")

# Check stock sentiment data (we saw this error earlier)
try:
    cursor.execute("SELECT COUNT(*) FROM crypto_news.stock_sentiment_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    stock_count = cursor.fetchone()[0]
    print(f"Stock sentiment records (24h): {stock_count}")
except Exception as e:
    print(f"Stock sentiment table issue: {e}")

# Check macro data
try:
    cursor.execute("SELECT COUNT(*) FROM macro_indicators WHERE date >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    macro_count = cursor.fetchone()[0]
    print(f"Macro indicators records (7d): {macro_count}")
except Exception as e:
    print(f"Macro indicators table issue: {e}")

# Check onchain data
try:
    cursor.execute("SELECT COUNT(*) FROM onchain_data WHERE date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    onchain_count = cursor.fetchone()[0]
    print(f"Onchain data records (24h): {onchain_count}")
except Exception as e:
    print(f"Onchain data table issue: {e}")

# Check OHLC data
try:
    cursor.execute("SELECT COUNT(*) FROM ohlc_data WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    ohlc_count = cursor.fetchone()[0]
    print(f"OHLC data records (24h): {ohlc_count}")
except Exception as e:
    print(f"OHLC data table issue: {e}")

conn.close()
print("\n=== ANALYSIS COMPLETE ===")