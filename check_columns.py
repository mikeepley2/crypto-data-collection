#!/usr/bin/env python3
import pymysql

# Connect to database
conn = pymysql.connect(
    host='host.docker.internal',
    user='news_collector',
    password='99Rules!',
    database='crypto_prices',
    port=3306,
    charset='utf8mb4'
)

cursor = conn.cursor()

print("🔍 MATERIALIZED TABLE SCHEMA:")
cursor.execute('SHOW COLUMNS FROM ml_features_materialized')
columns = cursor.fetchall()

print(f"📊 Total columns: {len(columns)}")
print("\n📋 First 30 columns:")
for i, (col_name, col_type, null, key, default, extra) in enumerate(columns[:30], 1):
    print(f"{i:2d}. {col_name} ({col_type})")

# Check data population for key columns
print("\n📈 DATA POPULATION ANALYSIS:")
cursor.execute('SELECT COUNT(*) FROM ml_features_materialized')
total_records = cursor.fetchone()[0]

# Check some key columns that likely exist
key_columns = ['current_price', 'volume_24h', 'price_change_percentage_24h', 'rsi_14', 'open', 'high', 'low', 'close']
for col in key_columns:
    try:
        cursor.execute(f'SELECT COUNT(CASE WHEN {col} IS NOT NULL THEN 1 END) FROM ml_features_materialized')
        populated = cursor.fetchone()[0]
        percentage = 100 * populated / total_records if total_records > 0 else 0
        print(f"📊 {col}: {populated:,}/{total_records:,} ({percentage:.1f}%)")
    except Exception as e:
        print(f"❌ {col}: Column not found")

cursor.close()
conn.close()