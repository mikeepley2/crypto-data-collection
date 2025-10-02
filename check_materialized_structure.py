#!/usr/bin/env python3

import mysql.connector
from datetime import datetime

def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host='host.docker.internal',
            database='crypto_prices',
            user='news_collector',
            password='99Rules!'
        )
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def check_materialized_table_structure():
    """Check the exact structure and data of ml_features_materialized"""
    
    connection = connect_to_db()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    print("=== ML_FEATURES_MATERIALIZED TABLE ANALYSIS ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # 1. Get full table structure
    print("1. COMPLETE TABLE STRUCTURE:")
    try:
        cursor.execute("DESCRIBE ml_features_materialized")
        columns = cursor.fetchall()
        print(f"   Total columns: {len(columns)}")
        print("   Column details:")
        for i, col in enumerate(columns, 1):
            print(f"     {i:3d}. {col[0]:30} | {col[1]:20} | Null: {col[2]} | Key: {col[3]} | Default: {col[4]}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 2. Check recent data
    print("2. RECENT DATA ANALYSIS:")
    try:
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_count = cursor.fetchone()[0]
        print(f"   Total records: {total_count:,}")
        
        # Get the timestamp column name (it might not be 'timestamp')
        timestamp_cols = [col[0] for col in columns if 'time' in col[0].lower() or 'date' in col[0].lower()]
        print(f"   Timestamp-like columns: {timestamp_cols}")
        
        if timestamp_cols:
            ts_col = timestamp_cols[0]  # Use first timestamp column
            cursor.execute(f"SELECT MAX({ts_col}) FROM ml_features_materialized")
            latest_ts = cursor.fetchone()[0]
            print(f"   Latest timestamp ({ts_col}): {latest_ts}")
            
            cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE {ts_col} > DATE_SUB(NOW(), INTERVAL 1 HOUR)")
            recent_count = cursor.fetchone()[0]
            print(f"   Records in last hour: {recent_count}")
            
            # Get latest few records
            cursor.execute(f"SELECT symbol, {ts_col}, dxy, tnx FROM ml_features_materialized ORDER BY {ts_col} DESC LIMIT 5")
            recent_data = cursor.fetchall()
            print(f"   Latest 5 records:")
            for row in recent_data:
                print(f"     {row}")
        print()
        
    except Exception as e:
        print(f"   Error checking recent data: {e}")
    
    # 3. Check macro indicators table
    print("3. MACRO_INDICATORS TABLE:")
    try:
        cursor.execute("DESCRIBE macro_indicators")
        macro_cols = cursor.fetchall()
        print(f"   Columns: {[col[0] for col in macro_cols]}")
        
        cursor.execute("SELECT COUNT(*) FROM macro_indicators")
        macro_count = cursor.fetchone()[0]
        print(f"   Total records: {macro_count}")
        
        if macro_count > 0:
            cursor.execute("SELECT * FROM macro_indicators ORDER BY timestamp DESC LIMIT 3")
            recent_macro = cursor.fetchall()
            print(f"   Recent macro data:")
            for row in recent_macro:
                print(f"     {row}")
        print()
        
    except Exception as e:
        print(f"   Error checking macro_indicators: {e}")
    
    # 4. Check for any processing errors or logs
    print("4. LOOKING FOR ERROR PATTERNS:")
    try:
        # Check if there's a logs table or status table
        cursor.execute("SHOW TABLES LIKE '%log%'")
        log_tables = cursor.fetchall()
        print(f"   Log tables: {[t[0] for t in log_tables]}")
        
        cursor.execute("SHOW TABLES LIKE '%status%'")
        status_tables = cursor.fetchall()
        print(f"   Status tables: {[t[0] for t in status_tables]}")
        
        cursor.execute("SHOW TABLES LIKE '%monitoring%'")
        monitoring_tables = cursor.fetchall()
        print(f"   Monitoring tables: {[t[0] for t in monitoring_tables]}")
        
    except Exception as e:
        print(f"   Error checking for logs: {e}")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    check_materialized_table_structure()