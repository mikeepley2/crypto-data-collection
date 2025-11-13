import mysql.connector

config = {
    'host': '172.22.32.1',
    'port': 3306,
    'user': 'news_collector',
    'password': '99Rules!'
}

print("MIGRATING UNIQUE TECHNICAL INDICATORS")
print("=" * 50)

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

try:
    # Get unique symbols list
    cursor.execute("USE crypto_news")
    cursor.execute("SELECT DISTINCT symbol FROM technical_indicators")
    news_symbols = {row[0] for row in cursor.fetchall()}
    
    cursor.execute("USE crypto_prices")
    cursor.execute("SELECT DISTINCT symbol FROM technical_indicators") 
    prices_symbols = {row[0] for row in cursor.fetchall()}
    
    unique_symbols = news_symbols - prices_symbols
    
    print(f"Unique symbols to migrate: {len(unique_symbols)}")
    
    if len(unique_symbols) == 0:
        print("No migration needed")
    else:
        # Get common columns for mapping
        cursor.execute("USE crypto_news")
        cursor.execute("DESCRIBE technical_indicators")
        news_cols = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("USE crypto_prices")
        cursor.execute("DESCRIBE technical_indicators")
        prices_cols = [row[0] for row in cursor.fetchall()]
        
        # Common technical indicator columns
        common = []
        skip_cols = ['id', 'timestamp', 'datetime_utc', 'timestamp_iso', 'created_at', 'updated_at']
        
        for col in news_cols:
            if col in prices_cols and col not in skip_cols:
                common.append(col)
        
        print(f"Common columns: {len(common)}")
        print(f"Sample: {common[:5]}")
        
        # Prepare migration
        select_cols = ['symbol', 'datetime_utc'] + common
        insert_cols = ['symbol', 'timestamp_iso'] + common
        
        cursor.execute("USE crypto_news")
        
        # Get data for unique symbols only
        symbol_list = list(unique_symbols)
        placeholders = ', '.join(['%s'] * len(symbol_list))
        
        query = f"SELECT {', '.join(select_cols)} FROM technical_indicators WHERE symbol IN ({placeholders})"
        cursor.execute(query, symbol_list)
        
        migration_data = cursor.fetchall()
        print(f"Records to migrate: {len(migration_data):,}")
        
        if len(migration_data) > 0:
            # Switch to target database
            cursor.execute("USE crypto_prices")
            
            # Insert data
            insert_query = f"INSERT INTO technical_indicators ({', '.join(insert_cols)}) VALUES ({', '.join(['%s'] * len(insert_cols))})"
            
            cursor.executemany(insert_query, migration_data)
            conn.commit()
            
            print(f"Migration completed: {len(migration_data):,} records")
            
            # Verify
            cursor.execute(f"SELECT COUNT(*) FROM technical_indicators WHERE symbol IN ({placeholders})", symbol_list)
            verify_count = cursor.fetchone()[0]
            print(f"Verification: {verify_count:,} records found after migration")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

finally:
    cursor.close()
    conn.close()

print("Migration complete!")
