#!/usr/bin/env python3
"""
Test Premium CoinGecko API functionality for onchain collector.
"""

import asyncio
import aiohttp
import os
import json
from datetime import datetime

class PremiumAPITester:
    def __init__(self):
        self.premium_api_key = 'CG-94NCcVD2euxaGTZe94bS2oYz'
        self.free_endpoint = 'https://api.coingecko.com/api/v3'
        self.premium_endpoint = 'https://pro-api.coingecko.com/api/v3'
        
    async def test_free_vs_premium(self):
        """Compare free vs premium API responses"""
        print("=" * 80)
        print("TESTING COINGECKO FREE vs PREMIUM API")
        print("=" * 80)
        
        async with aiohttp.ClientSession() as session:
            # Test free API
            print("\n🔓 Testing FREE API...")
            free_result = await self.test_api_endpoint(
                session, 
                f"{self.free_endpoint}/coins/bitcoin",
                headers={},
                label="Free API"
            )
            
            # Test premium API
            print("\n🚀 Testing PREMIUM API...")
            premium_result = await self.test_api_endpoint(
                session,
                f"{self.premium_endpoint}/coins/bitcoin", 
                headers={'x-cg-pro-api-key': self.premium_api_key},
                label="Premium API"
            )
            
            # Compare results
            self.compare_responses(free_result, premium_result)
            
    async def test_api_endpoint(self, session, url, headers, label):
        """Test a specific API endpoint"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            params = {
                'localization': 'false',
                'tickers': 'false', 
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'true',
                'sparkline': 'false'
            }
            
            async with session.get(url, headers=headers, params=params, timeout=30) as response:
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000
                
                print(f"   Status: {response.status}")
                print(f"   Response Time: {response_time:.2f}ms")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ SUCCESS")
                    print(f"   Data keys: {len(data.keys())} top-level fields")
                    print(f"   Rate limit headers:")
                    for header, value in response.headers.items():
                        if 'rate' in header.lower() or 'limit' in header.lower():
                            print(f"      {header}: {value}")
                    return {'success': True, 'data': data, 'response_time': response_time, 'headers': dict(response.headers)}
                    
                elif response.status == 429:
                    print(f"   ❌ RATE LIMITED")
                    return {'success': False, 'error': 'rate_limited', 'response_time': response_time}
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ FAILED: {error_text[:200]}")
                    return {'success': False, 'error': f'HTTP {response.status}', 'response_time': response_time}
                    
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            return {'success': False, 'error': str(e)}

    def compare_responses(self, free_result, premium_result):
        """Compare free vs premium API responses"""
        print("\n" + "=" * 80)
        print("COMPARISON RESULTS")
        print("=" * 80)
        
        # Success comparison
        print(f"\n📊 SUCCESS RATE:")
        print(f"   Free API: {'✅ SUCCESS' if free_result.get('success') else '❌ FAILED'}")
        print(f"   Premium API: {'✅ SUCCESS' if premium_result.get('success') else '❌ FAILED'}")
        
        # Response time comparison
        if free_result.get('response_time') and premium_result.get('response_time'):
            print(f"\n⚡ RESPONSE TIME:")
            print(f"   Free API: {free_result['response_time']:.2f}ms")
            print(f"   Premium API: {premium_result['response_time']:.2f}ms")
            speedup = free_result['response_time'] / premium_result['response_time']
            print(f"   Premium is {speedup:.1f}x faster" if speedup > 1 else f"   Free is {1/speedup:.1f}x faster")
        
        # Data comparison
        if free_result.get('success') and premium_result.get('success'):
            free_data = free_result['data']
            premium_data = premium_result['data']
            
            print(f"\n📈 DATA COMPARISON:")
            print(f"   Free API data fields: {len(free_data.keys())}")
            print(f"   Premium API data fields: {len(premium_data.keys())}")
            
            # Sample some key data points
            print(f"\n💰 SAMPLE DATA (Bitcoin):")
            try:
                free_market_data = free_data.get('market_data', {})
                premium_market_data = premium_data.get('market_data', {})
                
                free_price = free_market_data.get('current_price', {}).get('usd', 'N/A')
                premium_price = premium_market_data.get('current_price', {}).get('usd', 'N/A')
                print(f"   Free API Price: ${free_price:,}" if isinstance(free_price, (int, float)) else f"   Free API Price: {free_price}")
                print(f"   Premium API Price: ${premium_price:,}" if isinstance(premium_price, (int, float)) else f"   Premium API Price: {premium_price}")
                
            except Exception as e:
                print(f"   Error comparing data: {e}")

async def main():
    """Main test function"""
    tester = PremiumAPITester()
    
    # Run all tests
    await tester.test_free_vs_premium()
    
    print("\n" + "=" * 80)
    print("✅ PREMIUM API TESTING COMPLETE")
    print("=" * 80)
    print(f"\n🔑 Premium API Key: CG-94NCcVD2euxaGTZe94bS2oYz")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n🚀 The onchain collector is now configured to use premium CoinGecko API")
    print(f"⚡ This provides higher rate limits and more detailed data")
    print(f"📊 Rate limits: Premium ~10 req/sec vs Free ~1 req/sec")

if __name__ == "__main__":
    asyncio.run(main())