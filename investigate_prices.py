#!/usr/bin/env python3

import sys
sys.path.append('/app')

from shared.database_pool import execute_query

def investigate_price_data():
    print("=== INVESTIGATING NONE PRICE VALUES ===")
    print()
    
    # Check latest collection data
    print("Latest 10 records from recent collection:")
    result = execute_query("""
        SELECT symbol, current_price, price_change_24h, high_24h, low_24h, open_24h, timestamp_iso 
        FROM price_data_real 
        WHERE timestamp_iso >= '2025-10-01 19:00:00' 
        ORDER BY symbol 
        LIMIT 10
    """, fetch_results=True)
    
    for row in result:
        symbol, price, change, high, low, open_price, timestamp = row
        print(f"{symbol}: price={price}, change={change}, H={high}, L={low}, O={open_price}, time={timestamp}")
    
    print()
    print("Checking for any records with actual price values:")
    
    # Check if any records have actual values
    result2 = execute_query("""
        SELECT symbol, current_price, price_change_24h 
        FROM price_data_real 
        WHERE timestamp_iso >= '2025-10-01 19:00:00' 
        AND current_price IS NOT NULL 
        AND current_price > 0
        LIMIT 5
    """, fetch_results=True)
    
    if result2:
        for row in result2:
            symbol, price, change = row
            print(f"{symbol}: price=${price}, change={change}")
    else:
        print("No records found with actual price values!")
    
    print()
    print("Checking storage validation function behavior...")

if __name__ == "__main__":
    investigate_price_data()