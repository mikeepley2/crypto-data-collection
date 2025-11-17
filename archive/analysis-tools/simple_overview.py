#!/usr/bin/env python3
"""
Simple Data Overview
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.database_config import get_db_connection
from datetime import datetime, timedelta

def simple_overview():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    print("📊 DATABASE OVERVIEW")
    print("=" * 50)
    
    # Show all tables
    cursor.execute("SHOW TABLES")
    all_tables = [row[0] for row in cursor.fetchall()]
    print(f"Total tables: {len(all_tables)}")
    print("Tables:", ", ".join(all_tables[:10]) + ("..." if len(all_tables) > 10 else ""))
    print()
    
    # Key data tables
    key_tables = ['crypto_news', 'crypto_onchain_data', 'ohlc_data']
    
    for table in key_tables:
        if table in all_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count:,} records")
        else:
            print(f"{table}: Not found")
    
    print()
    
    # Recent data check
    print("📅 RECENT DATA (last 24 hours)")
    print("-" * 30)
    
    yesterday = datetime.now() - timedelta(days=1)
    
    # Check crypto_news
    try:
        cursor.execute("SELECT COUNT(*) FROM crypto_news WHERE created_at >= %s", (yesterday,))
        recent_news = cursor.fetchone()[0]
        print(f"Recent news: {recent_news}")
    except Exception as e:
        print(f"News check error: {e}")
    
    # Check crypto_onchain_data 
    try:
        cursor.execute("SELECT COUNT(*) FROM crypto_onchain_data WHERE created_at >= %s", (yesterday,))
        recent_onchain = cursor.fetchone()[0]
        print(f"Recent onchain: {recent_onchain}")
    except Exception as e:
        print(f"Onchain check error: {e}")
    
    # Check ohlc_data
    try:
        cursor.execute("SELECT COUNT(*) FROM ohlc_data WHERE created_at >= %s", (yesterday,))
        recent_ohlc = cursor.fetchone()[0]
        print(f"Recent OHLC: {recent_ohlc}")
    except Exception as e:
        print(f"OHLC check error: {e}")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    simple_overview()