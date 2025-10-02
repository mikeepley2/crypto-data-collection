import mysql.connector

connection = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_prices'
)
print("Connected to database")

cursor = connection.cursor()

# Check macro_indicators data
cursor.execute("""
    SELECT 
        indicator_type,
        COUNT(*) as record_count,
        MIN(date) as first_date,
        MAX(date) as last_date,
        AVG(value) as avg_value
    FROM macro_indicators
    GROUP BY indicator_type
    ORDER BY record_count DESC
    LIMIT 15
""")

indicators = cursor.fetchall()
print(f"\nTop 15 macro indicators:")
for indicator_type, count, first_date, last_date, avg_val in indicators:
    print(f"  {indicator_type}: {count:,} records, avg={avg_val:.4f}")

# Check ml_features_materialized macro fields
cursor.execute("DESCRIBE ml_features_materialized")
all_columns = [col[0] for col in cursor.fetchall()]

macro_keywords = ['vix', 'dxy', 'yield', 'treasury', 'bond', 'fed']
macro_fields = [col for col in all_columns if any(keyword in col.lower() for keyword in macro_keywords)]

print(f"\nFound {len(macro_fields)} potential macro fields:")
for field in macro_fields:
    print(f"  {field}")

# Check population
if macro_fields:
    field_checks = [f"SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as {field}_count" for field in macro_fields[:5]]
    
    query = f"""
        SELECT COUNT(*) as total, {', '.join(field_checks)}
        FROM ml_features_materialized
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    
    total = result[0]
    print(f"\nMacro field population (out of {total} symbols):")
    for i, field in enumerate(macro_fields[:5]):
        count = result[i + 1]
        print(f"  {field}: {count} ({count/total*100:.1f}%)")

cursor.close()
connection.close()