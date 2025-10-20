import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor(dictionary=True)

cursor.execute(
    "SELECT COUNT(*) as cnt, MIN(timestamp) as oldest, MAX(timestamp) as newest FROM technical_indicators"
)
r = cursor.fetchone()
print(f"Technical Indicators: {r['cnt']:,} records")
print(f"  Oldest: {r['oldest']}")
print(f"  Newest: {r['newest']}")

conn.close()
