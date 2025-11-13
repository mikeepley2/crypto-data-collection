#!/usr/bin/env python3
import mysql.connector
import os

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "172.22.32.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "cryptoai"),
    "password": os.getenv("DB_PASSWORD", "CryptoAI2024!"),
    "database": os.getenv("DB_NAME", "cryptoaidb"),
    "charset": "utf8mb4",
    "autocommit": True
}

try:
    print("🔧 Fixing ATL percentage column to handle large values...")
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    # Modify column to handle larger values
    cursor.execute("""
        ALTER TABLE crypto_onchain_data 
        MODIFY COLUMN atl_change_percentage DECIMAL(15,4) NULL
    """)
    
    print("✅ Successfully modified atl_change_percentage column")
    cursor.close()
    connection.close()

except Exception as e:
    print(f"❌ Error: {e}")
