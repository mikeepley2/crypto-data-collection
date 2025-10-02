import mysql.connector
import os

connection = mysql.connector.connect(
    host='host.docker.internal',
    port=3306,
    user='news_collector',
    password='99Rules!',
    database='crypto_prices'
)

cursor = connection.cursor()

# Check price_data table schema first
cursor.execute("DESCRIBE price_data")
columns = cursor.fetchall()
print("Price_data columns:")
for col in columns:
    print(f"  {col[0]} ({col[1]})")

# Check recent volume/market data availability
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN volume IS NOT NULL AND volume != 0 THEN 1 ELSE 0 END) as has_volume,
        SUM(CASE WHEN market_cap_usd IS NOT NULL AND market_cap_usd != 0 THEN 1 ELSE 0 END) as has_market_cap
    FROM price_data 
    WHERE timestamp > DATE_SUB(NOW(), INTERVAL 2 HOUR)
''')

result = cursor.fetchone()
print(f'\nRecent data: Total={result[0]}, Volume={result[1]}, MarketCap={result[2]}')

# Sample data with actual available columns
cursor.execute('''
    SELECT symbol, timestamp, current_price, volume, market_cap_usd 
    FROM price_data 
    WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
    AND (volume IS NOT NULL OR market_cap_usd IS NOT NULL)
    LIMIT 5
''')

rows = cursor.fetchall()
print('\nSample records:')
for row in rows:
    print(f'  {row[0]}: Price={row[2]}, Vol={row[3]}, MCap={row[4]}')

# Check what data sources we actually have
cursor.execute('''
    SELECT DISTINCT symbol, 
           MAX(CASE WHEN volume IS NOT NULL AND volume != 0 THEN volume ELSE NULL END) as max_volume,
           MAX(CASE WHEN market_cap_usd IS NOT NULL AND market_cap_usd != 0 THEN market_cap_usd ELSE NULL END) as max_market_cap,
           COUNT(*) as record_count
    FROM price_data 
    WHERE timestamp > DATE_SUB(NOW(), INTERVAL 6 HOUR)
    GROUP BY symbol
    HAVING max_volume IS NOT NULL OR max_market_cap IS NOT NULL
    ORDER BY record_count DESC
    LIMIT 10
''')

rows = cursor.fetchall()
print('\nSymbols with volume/market data (last 6h):')
for row in rows:
    print(f'  {row[0]}: Vol={row[1]}, MCap={row[2]}, Records={row[3]}')

cursor.close()
connection.close()

cursor.close()
connection.close()