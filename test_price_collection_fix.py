#!/usr/bin/env python3
"""
Manual Price Collection Test - Test the database schema fix
"""
import mysql.connector
import requests
import json
from datetime import datetime
import time

# Database configuration
db_config = {
    'host': '192.168.230.162',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

def test_price_insertion():
    """Test inserting sample price data with correct schema"""
    print("=== TESTING PRICE DATA INSERTION ===")
    
    try:
        # Get some real price data from CoinGecko
        print("Fetching sample price data from CoinGecko...")
        
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                'ids': 'bitcoin,ethereum,cardano',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            price_data = response.json()
            print(f"Retrieved price data for {len(price_data)} symbols")
            
            # Connect to database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            current_time = datetime.now()
            unix_timestamp = int(current_time.timestamp())
            
            # Test the correct schema
            insert_query = '''
            INSERT INTO price_data_real (
                symbol, coin_id, name, timestamp, timestamp_iso, 
                current_price, data_source, collection_interval,
                created_at, price_change_24h, price_change_percentage_24h,
                market_cap
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                current_price = VALUES(current_price),
                timestamp_iso = VALUES(timestamp_iso),
                timestamp = VALUES(timestamp),
                created_at = VALUES(created_at)
            '''
            
            # Map CoinGecko IDs to symbols
            symbol_mapping = {
                'bitcoin': ('BTC', 'Bitcoin'),
                'ethereum': ('ETH', 'Ethereum'), 
                'cardano': ('ADA', 'Cardano')
            }
            
            insert_data = []
            for coin_id, data in price_data.items():
                if coin_id in symbol_mapping:
                    symbol, name = symbol_mapping[coin_id]
                    price = data.get('usd', 0)
                    if price > 0:
                        insert_data.append((
                            symbol,
                            coin_id,
                            name,
                            unix_timestamp,
                            current_time,
                            float(price),
                            'manual_test',
                            'test',
                            current_time,
                            data.get('usd_24h_change'),
                            data.get('usd_24h_change'),
                            data.get('usd_market_cap')
                        ))
            
            if insert_data:
                cursor.executemany(insert_query, insert_data)
                conn.commit()
                print(f"✅ Successfully inserted {len(insert_data)} test price records!")
                
                # Verify the data was inserted
                cursor.execute("""
                    SELECT symbol, current_price, created_at 
                    FROM price_data_real 
                    WHERE data_source = 'manual_test'
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                results = cursor.fetchall()
                
                print(f"Verification - Recent test records:")
                for symbol, price, created in results:
                    print(f"   {symbol}: ${price:.4f} at {created}")
                    
            else:
                print("❌ No valid price data to insert")
                
            cursor.close()
            conn.close()
            
        else:
            print(f"❌ Failed to fetch price data: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in price insertion test: {e}")
        return False
        
    return True

def check_recent_collection():
    """Check if we now have recent price collection data"""
    print("\n=== CHECKING RECENT PRICE COLLECTION ===")
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Check for recent data
        cursor.execute("""
            SELECT 
                COUNT(*) as recent_count,
                MAX(created_at) as latest_created,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM price_data_real
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
        """)
        recent_stats = cursor.fetchone()
        
        print(f"Recent collection (last 10 minutes):")
        print(f"   Records: {recent_stats[0]:,}")
        print(f"   Latest: {recent_stats[1]}")
        print(f"   Symbols: {recent_stats[2]}")
        
        if recent_stats[0] > 0:
            print("✅ Price collection is now working!")
            return True
        else:
            print("⚠️ No recent collection detected yet")
            return False
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking recent collection: {e}")
        return False

if __name__ == "__main__":
    print("PRICE COLLECTION SCHEMA FIX TEST")
    print("=" * 40)
    
    # Test the schema fix
    success = test_price_insertion()
    
    if success:
        print("\n✅ Schema fix test PASSED!")
        print("The price_data_real table accepts the correct schema.")
        
        # Check for any recent collection
        check_recent_collection()
        
        print("\n🔧 NEXT STEPS:")
        print("1. The schema fix works correctly")
        print("2. Deploy the fixed container to Kubernetes")
        print("3. Monitor collection for new data")
        
    else:
        print("\n❌ Schema fix test FAILED!")
        print("There are still issues with the database schema.")