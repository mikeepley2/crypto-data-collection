#!/usr/bin/env python3
"""
Check macro_indicators table structure
"""
import mysql.connector

def check_macro_table_structure():
    try:
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        print("🔍 MACRO INDICATORS TABLE STRUCTURE")
        print("=" * 50)
        
        # Show table structure
        cursor.execute("DESCRIBE macro_indicators")
        columns = cursor.fetchall()
        print("Table columns:")
        for col in columns:
            print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]}")
        
        # Show sample data
        cursor.execute("SELECT * FROM macro_indicators LIMIT 3")
        results = cursor.fetchall()
        print(f"\nSample data ({len(results)} rows):")
        for row in results:
            print(f"  {row}")
        
        # Check total count
        cursor.execute("SELECT COUNT(*) FROM macro_indicators")
        count = cursor.fetchone()[0]
        print(f"\nTotal records: {count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking macro table: {e}")

if __name__ == "__main__":
    check_macro_table_structure()