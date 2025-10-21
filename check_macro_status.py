import mysql.connector
from datetime import datetime

config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Check macro indicators status
cursor.execute("""
SELECT 
    indicator_name,
    COUNT(*) as total_records,
    MAX(indicator_date) as latest_date,
    MIN(indicator_date) as oldest_date
FROM macro_indicators
GROUP BY indicator_name
ORDER BY indicator_name
""")

print("=" * 70)
print("MACRO INDICATORS CURRENT STATUS")
print("=" * 70)
results = cursor.fetchall()
for row in results:
    print(f"Indicator: {row[0]}")
    print(f"  Total Records: {row[1]:,}")
    print(f"  Date Range: {row[3]} to {row[2]}")
    print()

cursor.close()
conn.close()
