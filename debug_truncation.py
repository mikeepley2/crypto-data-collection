#!/usr/bin/env python3

import sys
sys.path.append('/app')

from shared.database_pool import execute_query
import requests
import logging

# Test CoinGecko API data to see what values we're getting
def test_real_coingecko_data():
    """Test actual CoinGecko API responses to find truncation culprits"""
    
    # Test some volatile crypto symbols that might have extreme values
    test_symbols = ['bitcoin', 'ethereum', 'pepe', 'shiba-inu', 'dogecoin', 'bonk']
    
    for symbol in test_symbols:
        try:
            # Get CoinGecko data like the real service does
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': symbol,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if symbol in data:
                    coin_data = data[symbol]
                    price_change = coin_data.get('usd_24h_change')
                    
                    print(f"\n{symbol}:")
                    print(f"  Price: {coin_data.get('usd')}")
                    print(f"  24h Change: {price_change}")
                    print(f"  24h Change Type: {type(price_change)}")
                    
                    # Test if this value would cause truncation
                    if price_change is not None:
                        try:
                            result = execute_query('SELECT %s as test_val', [price_change], fetch_results=True)
                            print(f"  MySQL Test: OK - {result[0][0]}")
                        except Exception as e:
                            print(f"  MySQL Test: ERROR - {e}")
                            print(f"  Problematic value: {price_change}")
                            print(f"  Value length: {len(str(price_change))}")
                            print(f"  Value repr: {repr(price_change)}")
                            
                            # Test rounded version
                            rounded_value = round(float(price_change), 8)
                            print(f"  Rounded to 8 places: {rounded_value}")
                            try:
                                result = execute_query('SELECT %s as test_val', [rounded_value], fetch_results=True)
                                print(f"  Rounded MySQL Test: OK - {result[0][0]}")
                            except Exception as re:
                                print(f"  Rounded MySQL Test: ERROR - {re}")
            else:
                print(f"Failed to get data for {symbol}: {response.status_code}")
                
        except Exception as e:
            print(f"Error testing {symbol}: {e}")

if __name__ == "__main__":
    test_real_coingecko_data()