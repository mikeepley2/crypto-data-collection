#!/usr/bin/env python3
"""
Add data completeness columns to all collector tables
"""

import pymysql
import os

# Database configuration
db_config = {
    'host': os.getenv("DB_HOST", "172.22.32.1"),
    'user': os.getenv("DB_USER", "news_collector"),
    'password': os.getenv("DB_PASSWORD", "99Rules!"),
    'database': os.getenv("DB_NAME", "crypto_prices"),
    'charset': 'utf8mb4'
}

def add_completeness_columns():
    """Add data_completeness_percentage column to all tables"""
    
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    tables_to_update = [
        'macro_indicators',
        'technical_indicators', 
        'crypto_onchain_data',
        'onchain_data'
    ]
    
    for table in tables_to_update:
        try:
            print(f"Checking table: {table}")
            
            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                print(f"  Table {table} does not exist, skipping...")
                continue
            
            # Check if column already exists
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'data_completeness_percentage'")
            if cursor.fetchone():
                print(f"  Column data_completeness_percentage already exists in {table}")
                continue
            
            # Add the column
            alter_sql = f"""
                ALTER TABLE {table} 
                ADD COLUMN data_completeness_percentage DECIMAL(5,2) DEFAULT 0.0
                COMMENT 'Percentage of expected data fields that are populated (0-100)'
            """
            
            print(f"  Adding data_completeness_percentage column to {table}...")
            cursor.execute(alter_sql)
            print(f"  ✅ Added column to {table}")
            
        except Exception as e:
            print(f"  ❌ Error updating {table}: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Database schema updates completed!")

if __name__ == "__main__":
    add_completeness_columns()