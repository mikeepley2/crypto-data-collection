import mysql.connector

config = {
    'host': '172.22.32.1',
    'port': 3306,
    'user': 'news_collector',
    'password': '99Rules!'
}

print("SCANNING DATABASES FOR DUPLICATE TABLES")
print("=" * 50)

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Get databases
cursor.execute("SHOW DATABASES")
databases = []
for (db_name,) in cursor.fetchall():
    if db_name not in ['information_schema', 'performance_schema', 'mysql', 'sys']:
        databases.append(db_name)

print(f"Databases found: {databases}")
print()

# Look for technical_indicators specifically
print("TECHNICAL_INDICATORS TABLES:")
tech_instances = []

for db in databases:
    try:
        cursor.execute(f"USE `{db}`")
        cursor.execute("SHOW TABLES LIKE '%technical_indicators%'")
        
        for (table_name,) in cursor.fetchall():
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            tech_instances.append((db, table_name, row_count))
            print(f"  {db}.{table_name}: {row_count:,} rows")
    
    except Exception as e:
        print(f"  Error in {db}: {e}")

print(f"\nTotal technical_indicators instances: {len(tech_instances)}")

if len(tech_instances) > 1:
    tech_instances.sort(key=lambda x: x[2], reverse=True)
    print("\nRECOMMENDATION:")
    print(f"  KEEP: {tech_instances[0][0]}.{tech_instances[0][1]} ({tech_instances[0][2]:,} rows)")
    print("  REMOVE:")
    for db, table, rows in tech_instances[1:]:
        print(f"    - {db}.{table} ({rows:,} rows)")

cursor.close()
conn.close()
