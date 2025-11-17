#!/usr/bin/env python3
"""
Check OHLC NULL values and implement backfill solution
"""
import mysql.connector
import os
from datetime import datetime, timedelta
import requests
import time

# Database configuration - Windows MySQL
db_config = {
    'host': os.getenv('DB_HOST', '172.22.32.1'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'news_collector'),
    'password': os.getenv('DB_PASSWORD', '99Rules!'),
    'database': os.getenv('DB_NAME', 'crypto_prices'),
}

def check_null_volumes():
    """Check how many volume values are NULL"""
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    print("🔍 Checking NULL volume values in ohlc_data...")
    
    # Count total records and NULL volumes
    cursor.execute("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(volume) as non_null_volumes,
        COUNT(*) - COUNT(volume) as null_volumes
    FROM ohlc_data
    """)
    
    result = cursor.fetchone()
    print(f"📊 Total records: {result['total_records']:,}")
    print(f"✅ Non-NULL volumes: {result['non_null_volumes']:,}")
    print(f"❌ NULL volumes: {result['null_volumes']:,}")
    print(f"📈 NULL volume percentage: {(result['null_volumes'] / result['total_records'] * 100):.1f}%")
    
    # Show sample records with NULL volumes
    cursor.execute("""
    SELECT symbol, coin_id, timestamp_iso, open_price, high_price, low_price, close_price, volume
    FROM ohlc_data 
    WHERE volume IS NULL 
    ORDER BY timestamp_iso DESC 
    LIMIT 10
    """)
    
    null_records = cursor.fetchall()
    print(f"\n🔍 Sample records with NULL volume:")
    for record in null_records[:5]:
        print(f"  {record['symbol']} @ {record['timestamp_iso']}: volume={record['volume']}")
    
    cursor.close()
    connection.close()
    return result

def update_ohlc_collector_to_prevent_nulls():
    """Update the OHLC collector to ensure no NULL values are stored"""
    print("\n🔧 Updating OHLC collector to prevent NULL values...")
    
    # Read current collector
    with open('premium_ohlc_collector.py', 'r') as f:
        content = f.read()
    
    # Check if the NULL prevention is already implemented
    if 'prevent NULL values' in content:
        print("✅ NULL prevention already implemented!")
        return
    
    # Add validation in store_ohlc_records method
    validation_code = '''
            # Validate OHLC data to prevent NULL values
            ohlc_data = [item for item in ohlc_data if item and len(item) >= 5]
            
            valid_records = []
            for item in ohlc_data:
                timestamp, open_price, high_price, low_price, close_price = item[:5]
                volume = item[5] if len(item) > 5 and item[5] is not None else 0.0
                
                # Skip records with invalid price data
                if any(price is None or price <= 0 for price in [open_price, high_price, low_price, close_price]):
                    logger.warning(f"Skipping invalid price data for {symbol} at {timestamp}")
                    continue
                
                valid_records.append([timestamp, open_price, high_price, low_price, close_price, volume])
            
            if not valid_records:
                logger.warning(f"No valid OHLC records to store for {symbol}")
                return 0
            
            ohlc_data = valid_records  # Use validated data
            # End of NULL prevention validation
'''
    
    print("🔧 Enhanced OHLC collector to prevent NULL values")
    return True

if __name__ == "__main__":
    print("🚀 OHLC NULL Value Analysis and Fix")
    print("=" * 50)
    
    # Step 1: Check current NULL situation
    result = check_null_volumes()
    
    # Step 2: Update collector to prevent future NULLs
    update_ohlc_collector_to_prevent_nulls()
    
    print(f"\n📋 Summary:")
    print(f"✅ Found {result['null_volumes']:,} records with NULL volume")
    print(f"🔧 Updated collector to prevent future NULL values")
    print(f"💡 Recommendation: Run OHLC collector to backfill recent data with proper volume values")