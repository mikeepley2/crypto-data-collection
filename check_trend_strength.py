#!/usr/bin/env python3
import mysql.connector

def check_missing_columns():
    """Check what technical indicator columns are missing"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor()

    # Get table structure
    cursor.execute("DESCRIBE technical_indicators")
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(existing_columns)} columns in technical_indicators table:")
    
    # Check for trend_strength specifically
    if 'trend_strength' in existing_columns:
        print("✅ trend_strength column exists")
    else:
        print("❌ trend_strength column missing")
        # Add it
        cursor.execute("ALTER TABLE technical_indicators ADD COLUMN trend_strength DECIMAL(10,4) DEFAULT NULL")
        print("✅ Added trend_strength column")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    check_missing_columns()