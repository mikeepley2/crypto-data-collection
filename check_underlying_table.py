import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='news_collector',
    password='99Rules!',
    database='crypto_prices'
)
cursor = conn.cursor()

cursor.execute('DESCRIBE crypto_onchain_data')
cols = cursor.fetchall()

print("CRYPTO_ONCHAIN_DATA (underlying table for onchain_metrics view):")
print("=" * 80)

for i, col in enumerate(cols[:10], 1):
    name = col[0]
    dtype = col[1]
    nullable = col[2]
    print(f"{i:2}. {name:<25} {dtype:<20} {nullable}")

conn.close()

print("\nRecommendation: Insert directly into crypto_onchain_data table instead of view")
