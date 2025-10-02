import mysql.connector
from collections import defaultdict

# MySQL connection config  
db_config = {
    'host': '127.0.0.1',
    'user': 'news_collector',
    'password': '99Rules!', 
    'database': 'crypto_prices'
}

def check_table_data(cursor, table_name, symbol='BTC', hours=24):
    """Check what data exists in a specific table"""
    try:
        # Check if table exists
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not cursor.fetchone():
            return f"❌ Table {table_name} does not exist"
            
        # Check recent data count
        if table_name == 'price_data':
            cursor.execute(f"""
                SELECT COUNT(*) as count, MIN(timestamp) as min_time, MAX(timestamp) as max_time
                FROM {table_name} 
                WHERE symbol = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """, (symbol, hours))
        else:
            # Try common timestamp column names
            timestamp_cols = ['timestamp', 'timestamp_iso', 'created_at', 'date', 'indicator_date']
            timestamp_col = None
            
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [row[0] for row in cursor.fetchall()]
            
            for col in timestamp_cols:
                if col in columns:
                    timestamp_col = col
                    break
                    
            if timestamp_col:
                if 'symbol' in columns:
                    cursor.execute(f"""
                        SELECT COUNT(*) as count, MIN({timestamp_col}) as min_time, MAX({timestamp_col}) as max_time
                        FROM {table_name} 
                        WHERE symbol = %s AND {timestamp_col} >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                    """, (symbol, hours))
                else:
                    cursor.execute(f"""
                        SELECT COUNT(*) as count, MIN({timestamp_col}) as min_time, MAX({timestamp_col}) as max_time
                        FROM {table_name} 
                        WHERE {timestamp_col} >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                    """, (hours,))
            else:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                
        result = cursor.fetchone()
        return f"✅ {table_name}: {result['count']} records, {result.get('min_time', 'N/A')} to {result.get('max_time', 'N/A')}"
        
    except Exception as e:
        return f"❌ {table_name}: Error - {e}"

def analyze_materialized_updater_logic():
    """Analyze what the current materialized updater is actually doing"""
    try:
        with open('materialized_updater_fixed.py', 'r') as f:
            content = f.read()
            
        # Find what tables it's querying
        import re
        table_queries = re.findall(r'FROM\s+(\w+)', content, re.IGNORECASE)
        unique_tables = list(set(table_queries))
        
        print(f"📋 Materialized updater queries these tables: {unique_tables}")
        
        # Find what columns it's selecting
        select_patterns = re.findall(r'SELECT\s+(.+?)\s+FROM', content, re.DOTALL | re.IGNORECASE)
        
        return unique_tables
        
    except Exception as e:
        print(f"❌ Error analyzing materialized updater: {e}")
        return []

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    print("🔍 INVESTIGATING DATA AVAILABILITY vs MATERIALIZED UPDATER POPULATION")
    print("="*70)
    
    # Check what tables the materialized updater should be using
    tables_to_check = analyze_materialized_updater_logic()
    
    # Core data tables to investigate
    key_tables = [
        'price_data',
        'technical_indicators', 
        'macro_indicators',
        'social_sentiment_data',
        'ohlc_data',
        'onchain_data',
        'sentiment_analysis',
        'ml_features_materialized'
    ]
    
    print("\n📊 CHECKING DATA AVAILABILITY BY TABLE:")
    print("-" * 50)
    
    for table in key_tables:
        result = check_table_data(cursor, table, 'BTC', 24)
        print(result)
        
    print("\n🔍 DETAILED COLUMN ANALYSIS:")
    print("-" * 50)
    
    # Check what columns exist in key tables
    for table in ['price_data', 'technical_indicators', 'macro_indicators']:
        try:
            cursor.execute(f"DESCRIBE {table}")
            columns = [row[0] for row in cursor.fetchall()]
            print(f"📋 {table} columns: {columns[:10]}{'...' if len(columns) > 10 else ''}")
        except Exception as e:
            print(f"❌ {table}: {e}")
    
    print("\n🎯 SAMPLE DATA CHECK:")
    print("-" * 50)
    
    # Check sample technical indicators data
    try:
        cursor.execute("""
            SELECT COUNT(*) as count, symbol, 
                   COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as rsi_count,
                   COUNT(CASE WHEN sma_20 IS NOT NULL THEN 1 END) as sma_count,
                   MAX(timestamp) as latest_time
            FROM technical_indicators 
            WHERE symbol IN ('BTC', 'ETH', 'ADA') 
            AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY symbol
        """)
        tech_results = cursor.fetchall()
        for row in tech_results:
            print(f"📈 Technical indicators - {row['symbol']}: {row['count']} records, RSI: {row['rsi_count']}, SMA: {row['sma_count']}, Latest: {row['latest_time']}")
    except Exception as e:
        print(f"❌ Technical indicators check failed: {e}")
        
    # Check sample macro data
    try:
        cursor.execute("""
            SELECT COUNT(*) as count, indicator_name, AVG(value) as avg_value, MAX(indicator_date) as latest_date
            FROM macro_indicators 
            WHERE indicator_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY indicator_name
            ORDER BY count DESC
            LIMIT 5
        """)
        macro_results = cursor.fetchall()
        print(f"📊 Top macro indicators (7 days):")
        for row in macro_results:
            print(f"   • {row['indicator_name']}: {row['count']} records, avg: {row['avg_value']:.2f}, latest: {row['latest_date']}")
    except Exception as e:
        print(f"❌ Macro indicators check failed: {e}")
    
    print("\n⚠️  MATERIALIZED UPDATER POPULATION GAPS:")
    print("-" * 50)
    
    # Check what the materialized table is missing vs what's available
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        null_columns = [col for col, val in btc_record.items() if val is None]
        print(f"🚫 BTC record has {len(null_columns)} NULL columns out of {len(btc_record)} total")
        print(f"🚫 Missing columns: {null_columns[:20]}{'...' if len(null_columns) > 20 else ''}")
        
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Investigation failed: {e}")