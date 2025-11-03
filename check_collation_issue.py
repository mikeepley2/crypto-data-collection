import mysql.connector

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print("=== COLLATION MISMATCH ANALYSIS ===")
print()

# Check collation of both tables
print("1. PRICE DATA TABLE COLLATION")
print("-" * 50)
try:
    cursor.execute(
        """
    SELECT COLUMN_NAME, COLLATION_NAME, CHARACTER_SET_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'price_data_real' 
    AND COLUMN_NAME = 'symbol'
    """
    )
    price_collation = cursor.fetchone()
    print(f"price_data_real.symbol: {price_collation[1]} ({price_collation[2]})")

except Exception as e:
    print(f"Error checking price collation: {e}")

print()

print("2. ONCHAIN DATA TABLE COLLATION")
print("-" * 50)
try:
    cursor.execute(
        """
    SELECT COLUMN_NAME, COLLATION_NAME, CHARACTER_SET_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'crypto_onchain_data' 
    AND COLUMN_NAME = 'coin_symbol'
    """
    )
    onchain_collation = cursor.fetchone()
    print(
        f"crypto_onchain_data.coin_symbol: {onchain_collation[1]} ({onchain_collation[2]})"
    )

except Exception as e:
    print(f"Error checking onchain collation: {e}")

print()

print("3. SAMPLE DATA COMPARISON")
print("-" * 50)
try:
    cursor.execute(
        """
    SELECT DISTINCT symbol FROM price_data_real 
    WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR) 
    ORDER BY symbol LIMIT 5
    """
    )
    price_symbols = cursor.fetchall()
    print("Price data symbols:")
    for (symbol,) in price_symbols:
        print(f'  "{symbol}"')

    print()

    cursor.execute(
        """
    SELECT DISTINCT coin_symbol FROM crypto_onchain_data 
    WHERE collection_date >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    ORDER BY coin_symbol LIMIT 5
    """
    )
    onchain_symbols = cursor.fetchall()
    print("Onchain data symbols:")
    for (symbol,) in onchain_symbols:
        print(f'  "{symbol}"')

except Exception as e:
    print(f"Error checking sample data: {e}")

cursor.close()
conn.close()




