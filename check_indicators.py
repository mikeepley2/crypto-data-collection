#!/usr/bin/env python3
"""
Check what macro indicators exist and find TNX
"""
import mysql.connector

def check_macro_indicators():
    try:
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        print("🔍 AVAILABLE MACRO INDICATORS")
        print("=" * 50)
        
        # Show distinct indicator names
        cursor.execute("SELECT DISTINCT indicator_name FROM macro_indicators ORDER BY indicator_name")
        indicators = cursor.fetchall()
        print("Available indicators:")
        for indicator in indicators:
            print(f"  {indicator[0]}")
        
        # Check if TNX or similar exists
        cursor.execute("SELECT DISTINCT indicator_name FROM macro_indicators WHERE indicator_name LIKE '%tnx%' OR indicator_name LIKE '%TNX%'")
        tnx_like = cursor.fetchall()
        print(f"\nTNX-like indicators: {[t[0] for t in tnx_like]}")
        
        # Check latest data for each indicator
        cursor.execute("""
            SELECT indicator_name, MAX(indicator_date) as latest_date, COUNT(*) as count
            FROM macro_indicators 
            GROUP BY indicator_name 
            ORDER BY latest_date DESC
        """)
        results = cursor.fetchall()
        print(f"\nIndicator summary:")
        for name, latest, count in results:
            print(f"  {name}: {count} records, latest: {latest}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking indicators: {e}")

if __name__ == "__main__":
    check_macro_indicators()