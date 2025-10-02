import mysql.connector
import time

# Connect to database
conn = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector',
    password='99Rules!',
    database='crypto_prices'
)

cursor = conn.cursor()

# Get initial stats
cursor.execute('SELECT COUNT(*) FROM ml_features_materialized')
total = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM ml_features_materialized WHERE open_price IS NOT NULL')
initial_ohlc = cursor.fetchone()[0]

print(f'Initial OHLC: {initial_ohlc:,}/{total:,} ({initial_ohlc*100.0/total:.1f}%)')

# Run bulk update
start_time = time.time()
cursor.execute('''
UPDATE ml_features_materialized ml
JOIN (
    SELECT 
        symbol,
        DATE(timestamp_iso) as ohlc_date,
        open_price, high_price, low_price, close_price,
        volume as ohlc_volume, data_source as ohlc_source,
        ROW_NUMBER() OVER (PARTITION BY symbol, DATE(timestamp_iso) ORDER BY timestamp_iso DESC) as rn
    FROM ohlc_data 
) ohlc ON ml.symbol = ohlc.symbol AND ml.price_date = ohlc.ohlc_date
SET 
    ml.open_price = ohlc.open_price,
    ml.high_price = ohlc.high_price,
    ml.low_price = ohlc.low_price,
    ml.close_price = ohlc.close_price,
    ml.ohlc_volume = ohlc.ohlc_volume,
    ml.ohlc_source = ohlc.ohlc_source
WHERE ohlc.rn = 1 AND ml.open_price IS NULL AND ohlc.open_price IS NOT NULL
''')

rows_updated = cursor.rowcount
duration = time.time() - start_time

# Get final stats
cursor.execute('SELECT COUNT(*) FROM ml_features_materialized WHERE open_price IS NOT NULL')
final_ohlc = cursor.fetchone()[0]

conn.commit()
cursor.close()
conn.close()

print(f'Bulk update complete: {rows_updated:,} records updated in {duration:.1f}s')
print(f'Final OHLC: {final_ohlc:,}/{total:,} ({final_ohlc*100.0/total:.1f}%)')
print(f'Improvement: +{final_ohlc-initial_ohlc:,} records')