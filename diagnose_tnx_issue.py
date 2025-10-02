#!/usr/bin/env python3
"""
Diagnose the TNX macro indicator issue in materialized updater
"""
import mysql.connector
from datetime import datetime

def diagnose_tnx_issue():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        print("🔍 DIAGNOSING TNX MACRO INDICATOR ISSUE")
        print("=" * 60)
        
        # Check if TNX exists in macro_indicators
        cursor.execute("SELECT COUNT(*) FROM macro_indicators WHERE symbol = 'tnx'")
        tnx_count = cursor.fetchone()[0]
        print(f"TNX records in macro_indicators: {tnx_count}")
        
        if tnx_count > 0:
            cursor.execute("""
                SELECT symbol, price, timestamp, created_at 
                FROM macro_indicators 
                WHERE symbol = 'tnx' 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            results = cursor.fetchall()
            print("\nRecent TNX data:")
            for row in results:
                print(f"  {row}")
        
        # Check materialized updater configuration
        cursor.execute("SHOW TABLES LIKE '%macro%'")
        macro_tables = cursor.fetchall()
        print(f"\nMacro-related tables: {[t[0] for t in macro_tables]}")
        
        # Check what macro symbols are expected
        cursor.execute("SELECT DISTINCT symbol FROM macro_indicators ORDER BY symbol")
        symbols = cursor.fetchall()
        print(f"\nAll macro symbols: {[s[0] for s in symbols]}")
        
        # Check latest processed records in materialized table
        cursor.execute("""
            SELECT symbol, created_at, tnx_10y_yield
            FROM ml_features_materialized 
            WHERE symbol = 'AAVE'
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        results = cursor.fetchall()
        print(f"\nRecent AAVE materialized records:")
        for row in results:
            print(f"  Symbol: {row[0]}, Created: {row[1]}, TNX: {row[2]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error diagnosing TNX issue: {e}")

if __name__ == "__main__":
    diagnose_tnx_issue()