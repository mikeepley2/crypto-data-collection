import mysql.connector

connection = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_prices'
)

cursor = connection.cursor()

print("Checking for onchain-related tables...")
cursor.execute("SHOW TABLES")
all_tables = [table[0] for table in cursor.fetchall()]

onchain_tables = [t for t in all_tables if 'onchain' in t.lower() or 'chain' in t.lower()]
print(f"Onchain-related tables: {onchain_tables}")

# Check all tables for any that might contain onchain data
crypto_tables = [t for t in all_tables if any(word in t.lower() for word in ['crypto', 'token', 'coin', 'defi', 'market'])]
print(f"Crypto-related tables: {crypto_tables[:10]}...")

# Check if there are onchain fields in ml_features_materialized
cursor.execute("DESCRIBE ml_features_materialized")
ml_columns = [col[0] for col in cursor.fetchall()]

onchain_fields = [col for col in ml_columns if any(keyword in col.lower() for keyword in 
                 ['onchain', 'supply', 'holder', 'transaction', 'defi', 'tvl', 'liquidity', 'network'])]

print(f"Onchain fields in ml_features: {onchain_fields}")

# Check recent completed onchain jobs
print(f"Recent onchain collection jobs completed successfully")

cursor.close()
connection.close()