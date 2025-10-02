#!/usr/bin/env python3

import mysql.connector
import os
from datetime import datetime, timedelta

def main():
    print("=== CHECKING VOLUME/MARKET DATA AVAILABILITY ===\n")
    
    # Database connection
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'crypto_user'),
            password=os.getenv('DB_PASSWORD', 'cryptoP@ss123!'),
            database=os.getenv('DB_NAME', 'crypto_prices')
        )
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    cursor = connection.cursor()
    
    try:
        # Check recent price_data for any non-null volume/market data
        print("🔍 Checking recent price_data for volume/market availability...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN volume IS NOT NULL AND volume != 0 THEN 1 ELSE 0 END) as volume_count,
                SUM(CASE WHEN market_cap_usd IS NOT NULL AND market_cap_usd != 0 THEN 1 ELSE 0 END) as market_cap_count,
                SUM(CASE WHEN price_change_24h IS NOT NULL THEN 1 ELSE 0 END) as price_change_count,
                SUM(CASE WHEN percent_change_24h IS NOT NULL THEN 1 ELSE 0 END) as percent_change_count
            FROM price_data 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 6 HOUR)
        """)
        
        result = cursor.fetchone()
        total, volume_count, market_cap_count, price_change_count, percent_change_count = result
        
        print(f"📊 Last 6 hours data summary:")
        print(f"   Total records: {total}")
        print(f"   Records with volume: {volume_count} ({volume_count/total*100:.1f}%)")
        print(f"   Records with market_cap: {market_cap_count} ({market_cap_count/total*100:.1f}%)")
        print(f"   Records with price_change_24h: {price_change_count} ({price_change_count/total*100:.1f}%)")
        print(f"   Records with percent_change_24h: {percent_change_count} ({percent_change_count/total*100:.1f}%)")
        
        # Sample some actual values
        print(f"\n🔍 Sample recent records...")
        cursor.execute("""
            SELECT symbol, timestamp, price, volume, market_cap_usd, price_change_24h, percent_change_24h
            FROM price_data 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            AND (volume IS NOT NULL OR market_cap_usd IS NOT NULL OR price_change_24h IS NOT NULL)
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        if rows:
            print("📋 Recent records with data:")
            for row in rows:
                symbol, timestamp, price, volume, market_cap, price_change, percent_change = row
                print(f"   {symbol} @ {timestamp}: Price=${price}, Vol={volume}, MCap={market_cap}, Change24h={price_change}, %Change={percent_change}")
        else:
            print("❌ No recent records found with volume/market data")
        
        # Check if data collection is working at all
        print(f"\n🔍 Checking overall data freshness...")
        cursor.execute("""
            SELECT MAX(timestamp) as latest_timestamp, 
                   COUNT(DISTINCT symbol) as symbol_count,
                   COUNT(*) as total_records
            FROM price_data 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        
        result = cursor.fetchone()
        latest_timestamp, symbol_count, total_records = result
        
        print(f"📊 Data freshness check:")
        print(f"   Latest timestamp: {latest_timestamp}")
        print(f"   Unique symbols (last hour): {symbol_count}")
        print(f"   Total records (last hour): {total_records}")
        
        if latest_timestamp:
            time_diff = datetime.now() - latest_timestamp
            print(f"   Data age: {time_diff}")
        
    except Exception as e:
        print(f"❌ Query error: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()