import mysql.connector

conn = mysql.connector.connect(host='172.22.32.1', port=3306, user='news_collector', password='99Rules!')
cur = conn.cursor()

print('🔍 SEARCHING FOR ALL TECHNICAL_INDICATORS TABLES')
print('=' * 60)

# Get all databases
cur.execute('SHOW DATABASES')
all_databases = [db[0] for db in cur.fetchall() if db[0] not in ['information_schema', 'performance_schema', 'mysql', 'sys']]

print(f'Scanning {len(all_databases)} databases: {all_databases}')
print()

tech_tables_found = []

for db in all_databases:
    try:
        cur.execute(f'USE `{db}`')
        cur.execute('SHOW TABLES LIKE "technical_indicators%"')
        tables = cur.fetchall()
        
        if tables:
            print(f'🔴 {db}: Found technical_indicators tables:')
            for (table_name,) in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM `{table_name}`')
                    count = cur.fetchone()[0]
                    tech_tables_found.append((db, table_name, count))
                    
                    if table_name.endswith('_old'):
                        print(f'  ✅ {table_name}: {count:,} rows (archived)')
                    elif db == 'crypto_prices' and table_name == 'technical_indicators':
                        print(f'  👑 {table_name}: {count:,} rows (PRIMARY)')
                    else:
                        print(f'  🚨 {table_name}: {count:,} rows (DUPLICATE - SHOULD BE REMOVED)')
                except Exception as e:
                    print(f'  ❌ {table_name}: Error reading - {e}')
        else:
            print(f'✅ {db}: No technical_indicators tables')
            
    except Exception as e:
        print(f'❌ Error accessing {db}: {e}')
    print()

print('📋 SUMMARY:')
print('=' * 30)

primary_count = 0
duplicate_count = 0
archived_count = 0

duplicates_to_remove = []

for db, table, count in tech_tables_found:
    if db == 'crypto_prices' and table == 'technical_indicators':
        primary_count += 1
        print(f'👑 PRIMARY: {db}.{table} ({count:,} rows)')
    elif table.endswith('_old'):
        archived_count += 1
    else:
        duplicate_count += 1
        duplicates_to_remove.append((db, table, count))
        print(f'🚨 DUPLICATE: {db}.{table} ({count:,} rows)')

print(f'\nCounts: {primary_count} primary, {duplicate_count} duplicates, {archived_count} archived')

if duplicates_to_remove:
    print('\n🗑️ CLEANUP COMMANDS:')
    for db, table, count in duplicates_to_remove:
        print(f'DROP TABLE `{db}`.`{table}`;  -- {count:,} rows')
else:
    print('\n✅ No duplicates found!')

cur.close()
conn.close()
