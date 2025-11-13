#!/usr/bin/env python3
"""
CoinGecko Derivatives API Data Inspection
=========================================

Check what data fields are available in the CoinGecko derivatives API
to improve column population.
"""

import requests
import json
import time
from pprint import pprint

def inspect_coingecko_derivatives():
    """Inspect CoinGecko derivatives API response structure"""
    
    # CoinGecko API configuration
    headers = {
        'x-cg-pro-api-key': 'CG-94NCcVD2euxaGTZe94bS2oYz',
        'accept': 'application/json'
    }
    
    print("COINGECKO DERIVATIVES API DATA INSPECTION")
    print("=" * 60)
    
    try:
        # Fetch a small sample of derivatives data
        url = "https://pro-api.coingecko.com/api/v3/derivatives"
        params = {'per_page': 5}
        
        print("Fetching sample derivatives data...")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully fetched {len(data)} derivatives records")
            
            if data:
                print("\n📋 SAMPLE DERIVATIVE RECORD STRUCTURE:")
                print("-" * 40)
                sample_record = data[0]
                
                print("Available fields in CoinGecko derivatives:")
                for key, value in sample_record.items():
                    print(f"  {key}: {type(value).__name__} = {value}")
                
                print("\n🔍 DETAILED ANALYSIS:")
                print("-" * 40)
                
                # Check for useful fields we might be missing
                useful_fields = [
                    'funding_rate', 'open_interest', 'volume_24h', 'basis',
                    'spread', 'index', 'last', 'price_percentage_change_24h',
                    'contract_type', 'expired_at', 'number_of_contracts'
                ]
                
                for field in useful_fields:
                    if field in sample_record:
                        value = sample_record[field]
                        print(f"  ✅ {field}: {value}")
                    else:
                        print(f"  ❌ {field}: Not available")
                
                print("\n📊 FULL SAMPLE RECORD:")
                print("-" * 40)
                pprint(sample_record, width=80, depth=3)
                
                # Check multiple records for pattern consistency
                print(f"\n🔄 CHECKING {len(data)} RECORDS FOR CONSISTENCY:")
                print("-" * 40)
                
                field_availability = {}
                for record in data:
                    for key, value in record.items():
                        if key not in field_availability:
                            field_availability[key] = {'total': 0, 'non_null': 0}
                        field_availability[key]['total'] += 1
                        if value is not None and value != "":
                            field_availability[key]['non_null'] += 1
                
                for field, stats in field_availability.items():
                    availability = stats['non_null'] / stats['total'] * 100
                    print(f"  {field:<25}: {availability:5.1f}% available ({stats['non_null']}/{stats['total']})")
            
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_coingecko_derivatives()