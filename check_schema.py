import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1', user='news_collector', password='99Rules!', database='crypto_prices')
cursor = conn.cursor(dictionary=True)

print("MATERIALIZED TABLE SCHEMA:")
print("="*50)

cursor.execute("DESCRIBE ml_features_materialized")
columns = cursor.fetchall()

for col in columns:
    field = col['Field']
    data_type = col['Type']
    nullable = col['Null']
    print(f"{field:30} {data_type:20} {nullable}")

print(f"\nTotal columns: {len(columns)}")

# Find columns with 'vix', 'treasury', 'macro' in name
macro_cols = [col['Field'] for col in columns if any(term in col['Field'].lower() for term in ['vix', 'treasury', 'macro', 'spx', 'dxy'])]
print(f"Macro-related columns: {macro_cols}")

conn.close()