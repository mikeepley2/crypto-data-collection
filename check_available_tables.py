import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor()

print("\nTables in crypto_prices database:")
cursor.execute(
    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='crypto_prices' ORDER BY TABLE_NAME"
)
for (table,) in cursor.fetchall():
    # Get record count
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:<40} ({count:>10,} records)")
    except:
        print(f"  {table:<40} (unable to count)")

conn.close()
