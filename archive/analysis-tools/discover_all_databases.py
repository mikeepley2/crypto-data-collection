import mysql.connector

conn = mysql.connector.connect(host='172.22.32.1', port=3306, user='news_collector', password='99Rules!')
cur = conn.cursor()

print('�� DISCOVERING ALL DATABASES')
print('=' * 50)

# Get ALL databases on server
cur.execute('SHOW DATABASES')
all_databases = []
for (db_name,) in cur.fetchall():
    if db_name not in ['information_schema', 'performance_schema', 'mysql', 'sys']:
        all_databases.append(db_name)

print(f'Found {len(all_databases)} user databases:')
for i, db in enumerate(all_databases, 1):
    print(f'  {i:2d}. {db}')

print()
print('🔍 CHECKING FOR TECHNICAL_INDICATORS TABLES:')
print('=' * 50)

tech_indicators_found = []

for db in all_databases:
    try:
        cur.execute(f'USE `{db}`')
        cur.execute('SHOW TABLES')
        tables = [row[0] for row in cur.fetchall()]
        
        # Look for technical_indicators table (exact match)
        if 'technical_indicators' in tables:
            cur.execute('SELECT COUNT(*) FROM technical_indicators')
            count = cur.fetchone()[0]
            
            # Try to get date range and symbols
            date_range = 'Unknown'
            symbols = 'Unknown'
            
            # Try different timestamp column names
            for ts_col in ['timestamp_iso', 'datetime_utc', 'timestamp', 'date']:
                try:
                    cur.execute(f'DESCRIBE technical_indicators')
                    columns = [row[0] for row in cur.fetchall()]
                    
                    if ts_col in columns:
                        cur.execute(f'SELECT MIN({ts_col}), MAX({ts_col}), COUNT(DISTINCT symbol) FROM technical_indicators WHERE {ts_col} IS NOT NULL')
                        min_date, max_date, sym_count = cur.fetchone()
                        if min_date and max_date:
                            date_range = f'{min_date} to {max_date}'
                            symbols = sym_count
                        break
                except:
                    continue
            
            tech_indicators_found.append({
                'database': db,
                'rows': count,
                'date_range': date_range,
                'symbols': symbols
            })
            
            print(f'�� {db}.technical_indicators: {count:,} rows, {symbols} symbols')
            print(f'    Date range: {date_range}')
        
    except Exception as e:
        print(f'❌ Error checking {db}: {e}')

print()
print('📊 SUMMARY:')
print('=' * 30)

if len(tech_indicators_found) == 0:
    print('❌ No technical_indicators tables found')
elif len(tech_indicators_found) == 1:
    db_info = tech_indicators_found[0]
    print(f'✅ Single table: {db_info["database"]} ({db_info["rows"]:,} rows)')
else:
    print(f'🚨 {len(tech_indicators_found)} technical_indicators tables found!')
    
    # Sort by size
    tech_indicators_found.sort(key=lambda x: x['rows'], reverse=True)
    
    primary = tech_indicators_found[0]
    print(f'👑 LARGEST: {primary["database"]} ({primary["rows"]:,} rows)')
    
    duplicates = tech_indicators_found[1:]
    print(f'📤 NEED MIGRATION/CLEANUP:')
    
    for dup in duplicates:
        print(f'   {dup["database"]}: {dup["rows"]:,} rows, {dup["symbols"]} symbols')

cur.close()
conn.close()
