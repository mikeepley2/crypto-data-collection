#!/usr/bin/env python3
"""
Add missing columns to all tables for placeholder tracking
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

def add_missing_columns():
    """Add missing columns for placeholder tracking"""
    
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    # Check and add data_source column to technical_indicators
    try:
        cursor.execute("SHOW COLUMNS FROM technical_indicators LIKE 'data_source'")
        if not cursor.fetchone():
            print("Adding data_source column to technical_indicators...")
            cursor.execute("""
                ALTER TABLE technical_indicators 
                ADD COLUMN data_source VARCHAR(100) DEFAULT NULL
                COMMENT 'Source of the technical indicator data'
            """)
            print("✅ Added data_source to technical_indicators")
        else:
            print("data_source column already exists in technical_indicators")
    except Exception as e:
        print(f"❌ Error adding data_source to technical_indicators: {e}")
    
    # Check and add data_source column to crypto_onchain_data
    try:
        cursor.execute("SHOW COLUMNS FROM crypto_onchain_data LIKE 'data_source'")
        if not cursor.fetchone():
            print("Adding data_source column to crypto_onchain_data...")
            cursor.execute("""
                ALTER TABLE crypto_onchain_data 
                ADD COLUMN data_source VARCHAR(100) DEFAULT NULL
                COMMENT 'Source of the onchain data'
            """)
            print("✅ Added data_source to crypto_onchain_data")
        else:
            print("data_source column already exists in crypto_onchain_data")
    except Exception as e:
        print(f"❌ Error adding data_source to crypto_onchain_data: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Missing columns addition completed!")

if __name__ == "__main__":
    add_missing_columns()