#!/usr/bin/env python3

import mysql.connector
import sys
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

def investigate_macro_columns():
    """Investigate the macro indicator column issues"""
    
    connection = connect_to_db()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    print("=== MACRO INDICATOR COLUMN INVESTIGATION ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # 1. Check what tables exist
    print("1. AVAILABLE TABLES:")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")
    print()
    
    # 2. Check ml_features_materialized schema
    print("2. ML_FEATURES_MATERIALIZED SCHEMA:")
    try:
        cursor.execute("DESCRIBE ml_features_materialized")
        columns = cursor.fetchall()
        print(f"   Total columns: {len(columns)}")
        
        # Look for tnx and dxy columns
        tnx_found = False
        dxy_found = False
        macro_columns = []
        
        for col in columns:
            col_name = col[0].lower()
            if 'tnx' in col_name:
                tnx_found = True
                macro_columns.append(col[0])
            if 'dxy' in col_name:
                dxy_found = True
                macro_columns.append(col[0])
            if 'macro' in col_name or 'economic' in col_name:
                macro_columns.append(col[0])
        
        print(f"   TNX column found: {tnx_found}")
        print(f"   DXY column found: {dxy_found}")
        print(f"   Macro-related columns: {macro_columns}")
        
    except Exception as e:
        print(f"   Error checking ml_features_materialized: {e}")
    print()
    
    # 3. Check macro_economic_data table
    print("3. MACRO_ECONOMIC_DATA TABLE:")
    try:
        cursor.execute("DESCRIBE macro_economic_data")
        columns = cursor.fetchall()
        print(f"   Columns: {[col[0] for col in columns]}")
        
        # Check recent data
        cursor.execute("SELECT * FROM macro_economic_data ORDER BY timestamp DESC LIMIT 3")
        recent_data = cursor.fetchall()
        print(f"   Recent records: {len(recent_data)}")
        if recent_data:
            for row in recent_data:
                print(f"     {row}")
                
    except Exception as e:
        print(f"   Error checking macro_economic_data: {e}")
    print()
    
    # 4. Check materialized updater logs for specific errors
    print("4. RECENT MATERIALIZED UPDATER STATUS:")
    try:
        cursor.execute("""
            SELECT timestamp, status, message 
            FROM ml_features_materialized 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        recent_status = cursor.fetchall()
        print(f"   Recent processing status:")
        for row in recent_status:
            print(f"     {row[0]} | {row[1]} | {row[2][:100] if row[2] else 'No message'}")
            
    except Exception as e:
        print(f"   Error checking recent status: {e}")
    print()
    
    # 5. Check what exact columns are being referenced in errors
    print("5. CHECKING FOR COLUMN REFERENCE PATTERNS:")
    try:
        # Look for any error messages mentioning column names
        cursor.execute("""
            SELECT DISTINCT message 
            FROM ml_features_materialized 
            WHERE message LIKE '%tnx%' OR message LIKE '%dxy%' OR message LIKE '%column%'
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        error_messages = cursor.fetchall()
        
        if error_messages:
            print("   Error messages mentioning columns:")
            for msg in error_messages:
                print(f"     {msg[0]}")
        else:
            print("   No error messages found with column references")
            
    except Exception as e:
        print(f"   Error checking error messages: {e}")
    
    # 6. Check price_data table status
    print("6. PRICE_DATA TABLE STATUS:")
    try:
        cursor.execute("SELECT COUNT(*) FROM price_data WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)")
        recent_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(timestamp) FROM price_data")
        latest_timestamp = cursor.fetchone()[0]
        
        print(f"   Records in last hour: {recent_count}")
        print(f"   Latest timestamp: {latest_timestamp}")
        
    except Exception as e:
        print(f"   Error checking price_data: {e}")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    investigate_macro_columns()