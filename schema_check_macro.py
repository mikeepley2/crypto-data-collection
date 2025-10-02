import mysql.connector

connection = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_prices'
)
print("Connected to database")

cursor = connection.cursor()

# Check macro_indicators table schema
print("Checking macro_indicators table schema...")
cursor.execute("DESCRIBE macro_indicators")
columns = cursor.fetchall()
print("Columns:")
for col in columns:
    print(f"  {col[0]} ({col[1]})")

# Check sample data
print("\nSample data (first 5 rows):")
cursor.execute("SELECT * FROM macro_indicators ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(f"  {row}")

# Check total records
cursor.execute("SELECT COUNT(*) FROM macro_indicators")
total = cursor.fetchone()[0]
print(f"\nTotal macro_indicators records: {total:,}")

# Check ml_features_materialized macro fields
cursor.execute("DESCRIBE ml_features_materialized")
all_columns = [col[0] for col in cursor.fetchall()]

macro_keywords = ['vix', 'dxy', 'yield', 'treasury', 'bond', 'fed', 'macro', 'economic']
macro_fields = [col for col in all_columns if any(keyword in col.lower() for keyword in macro_keywords)]

print(f"\nFound {len(macro_fields)} potential macro fields in ml_features_materialized:")
for field in macro_fields:
    print(f"  {field}")

cursor.close()
connection.close()