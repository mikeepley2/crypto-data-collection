import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='news_collector',
    password='99Rules!',
    database='crypto_prices'
)
cursor = conn.cursor()

# Check if it's a view or table
cursor.execute("""
    SELECT TABLE_TYPE, VIEW_DEFINITION 
    FROM INFORMATION_SCHEMA.TABLES 
    LEFT JOIN INFORMATION_SCHEMA.VIEWS 
    ON INFORMATION_SCHEMA.TABLES.TABLE_NAME = INFORMATION_SCHEMA.VIEWS.TABLE_NAME 
    AND INFORMATION_SCHEMA.TABLES.TABLE_SCHEMA = INFORMATION_SCHEMA.VIEWS.TABLE_SCHEMA
    WHERE INFORMATION_SCHEMA.TABLES.TABLE_SCHEMA='crypto_prices' 
    AND INFORMATION_SCHEMA.TABLES.TABLE_NAME='onchain_metrics'
""")

result = cursor.fetchone()
if result:
    table_type = result[0]
    view_def = result[1]
    print(f"onchain_metrics is a: {table_type}")
    if table_type == "VIEW" and view_def:
        print(f"\nView Definition:")
        print(view_def[:500])
else:
    print("onchain_metrics not found")

conn.close()
