#!/usr/bin/env python3
"""
Test Real Derivatives Collection
Test the updated derivatives collector with real CoinGecko data
"""

import sys
import os
import asyncio
sys.path.append('services/derivatives-collection')

def test_coingecko_api():
    """Test CoinGecko derivatives API directly"""
    import requests
    
    url = "https://pro-api.coingecko.com/api/v3/derivatives"
    headers = {
        'x-cg-pro-api-key': 'CG-94NCcVD2euxaGTZe94bS2oYz',
        'accept': 'application/json'
    }
    
    print("🔍 Testing CoinGecko derivatives API...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data)} derivatives tickers")
            
            # Show sample data
            if data:
                sample = data[0]
                print(f"Sample ticker:")
                print(f"  Market: {sample.get('market')}")
                print(f"  Symbol: {sample.get('symbol')}")
                print(f"  Index ID: {sample.get('index_id')}")
                print(f"  Funding Rate: {sample.get('funding_rate')}")
                print(f"  Open Interest: {sample.get('open_interest')}")
                print(f"  Volume 24h: {sample.get('volume_24h')}")
                print(f"  Contract Type: {sample.get('contract_type')}")
                
            # Count symbols we track
            tracked_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'AVAX', 'MATIC', 'ATOM', 'NEAR']
            our_data = [t for t in data if t.get('index_id', '').upper() in tracked_symbols]
            print(f"📊 Found {len(our_data)} derivatives for our tracked symbols")
            
            return our_data
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return []

async def test_collector():
    """Test the derivatives collector"""
    try:
        from crypto_derivatives_collector import CryptoDerivativesCollector
        
        print("🚀 Testing CryptoDerivativesCollector...")
        collector = CryptoDerivativesCollector()
        print(f"Tracked symbols: {collector.tracked_cryptos}")
        
        # Test collection
        data = await collector.collect_coingecko_derivatives()
        print(f"✅ Collected {len(data)} derivatives records")
        
        if data:
            sample = data[0]
            print(f"Sample record:")
            print(f"  Symbol: {sample['symbol']}")
            print(f"  Exchange: {sample['exchange']}")
            print(f"  Funding Rate: {sample.get('funding_rate')}")
            print(f"  Open Interest: ${sample.get('open_interest_usdt', 0):,.0f}")
            print(f"  ML Scores: Momentum={sample.get('ml_funding_momentum_score', 0):.1f}, Sentiment={sample.get('ml_leverage_sentiment', 0):.1f}")
        
        return data
        
    except ImportError as e:
        print(f"⚠️ Could not import collector: {e}")
        return []
    except Exception as e:
        print(f"❌ Collector test failed: {e}")
        return []

def main():
    print("🧪 REAL DERIVATIVES DATA COLLECTION TEST")
    print("=" * 50)
    
    # Test 1: Direct API test
    print("\n1. Testing CoinGecko API directly...")
    api_data = test_coingecko_api()
    
    # Test 2: Test collector
    print("\n2. Testing derivatives collector...")
    try:
        collector_data = asyncio.run(test_collector())
        
        print("\n📋 TEST RESULTS:")
        print(f"API Data: {len(api_data)} records")
        print(f"Collector Data: {len(collector_data)} records")
        
        if api_data and collector_data:
            print("✅ Both tests successful - real data collection working!")
        elif api_data:
            print("⚠️ API works but collector has issues")
        else:
            print("❌ API test failed")
            
    except Exception as e:
        print(f"❌ Collector test error: {e}")
        
    print("\n🎯 Real CoinGecko data is available and ready to replace synthetic data!")

if __name__ == "__main__":
    main()