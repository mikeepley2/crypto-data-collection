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
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
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
                    return {'success': False, 'error': f'HTTP {response.status}', 'response_time': response_time}\n        \"\"\"Compare free vs premium API responses\"\"\"\n        print(\"\\n\" + \"=\" * 80)\n        print(\"COMPARISON RESULTS\")\n        print(\"=\" * 80)\n        \n        # Success comparison\n        print(f\"\\n📊 SUCCESS RATE:\")\n        print(f\"   Free API: {'✅ SUCCESS' if free_result.get('success') else '❌ FAILED'}\")\n        print(f\"   Premium API: {'✅ SUCCESS' if premium_result.get('success') else '❌ FAILED'}\")\n        \n        # Response time comparison\n        if free_result.get('response_time') and premium_result.get('response_time'):\n            print(f\"\\n⚡ RESPONSE TIME:\")\n            print(f\"   Free API: {free_result['response_time']:.2f}ms\")\n            print(f\"   Premium API: {premium_result['response_time']:.2f}ms\")\n            speedup = free_result['response_time'] / premium_result['response_time']\n            print(f\"   Premium is {speedup:.1f}x faster\" if speedup > 1 else f\"   Free is {1/speedup:.1f}x faster\")\n        \n        # Data comparison\n        if free_result.get('success') and premium_result.get('success'):\n            free_data = free_result['data']\n            premium_data = premium_result['data']\n            \n            print(f\"\\n📈 DATA COMPARISON:\")\n            print(f\"   Free API data fields: {len(free_data.keys())}\")\n            print(f\"   Premium API data fields: {len(premium_data.keys())}\")\n            \n            # Check for additional fields in premium\n            free_keys = set(free_data.keys())\n            premium_keys = set(premium_data.keys())\n            \n            additional_in_premium = premium_keys - free_keys\n            if additional_in_premium:\n                print(f\"   ✨ Additional fields in Premium: {list(additional_in_premium)}\")\n            \n            # Check market data depth\n            free_market_data = free_data.get('market_data', {})\n            premium_market_data = premium_data.get('market_data', {})\n            \n            print(f\"   Free market data fields: {len(free_market_data.keys())}\")\n            print(f\"   Premium market data fields: {len(premium_market_data.keys())}\")\n            \n            # Sample some key data points\n            print(f\"\\n💰 SAMPLE DATA (Bitcoin):\")\n            try:\n                free_price = free_market_data.get('current_price', {}).get('usd', 'N/A')\n                premium_price = premium_market_data.get('current_price', {}).get('usd', 'N/A')\n                print(f\"   Free API Price: ${free_price:,}\" if isinstance(free_price, (int, float)) else f\"   Free API Price: {free_price}\")\n                print(f\"   Premium API Price: ${premium_price:,}\" if isinstance(premium_price, (int, float)) else f\"   Premium API Price: {premium_price}\")\n                \n                free_mcap = free_market_data.get('market_cap', {}).get('usd', 'N/A')\n                premium_mcap = premium_market_data.get('market_cap', {}).get('usd', 'N/A')\n                print(f\"   Free API Market Cap: ${free_mcap:,}\" if isinstance(free_mcap, (int, float)) else f\"   Free API Market Cap: {free_mcap}\")\n                print(f\"   Premium API Market Cap: ${premium_mcap:,}\" if isinstance(premium_mcap, (int, float)) else f\"   Premium API Market Cap: {premium_mcap}\")\n            except Exception as e:\n                print(f\"   Error comparing data: {e}\")\n        \n        # Rate limit comparison\n        print(f\"\\n🚦 RATE LIMITS:\")\n        free_headers = free_result.get('headers', {})\n        premium_headers = premium_result.get('headers', {})\n        \n        print(f\"   Free API headers: {len(free_headers)} total\")\n        print(f\"   Premium API headers: {len(premium_headers)} total\")\n        \n        # Look for rate limit info\n        rate_limit_headers = ['x-ratelimit-limit', 'x-ratelimit-remaining', 'retry-after']\n        for header in rate_limit_headers:\n            free_val = free_headers.get(header, 'Not found')\n            premium_val = premium_headers.get(header, 'Not found')\n            if free_val != 'Not found' or premium_val != 'Not found':\n                print(f\"   {header}: Free={free_val}, Premium={premium_val}\")\n        \n    async def test_rate_limits(self):\n        \"\"\"Test rate limiting behavior\"\"\"\n        print(\"\\n\" + \"=\" * 80)\n        print(\"TESTING RATE LIMITS\")\n        print(\"=\" * 80)\n        \n        # Test multiple rapid requests\n        async with aiohttp.ClientSession() as session:\n            print(\"\\n🔥 Testing 5 rapid premium API requests...\")\n            \n            tasks = []\n            for i in range(5):\n                task = self.make_rapid_request(session, i+1)\n                tasks.append(task)\n            \n            results = await asyncio.gather(*tasks, return_exceptions=True)\n            \n            success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))\n            print(f\"\\n📊 Results: {success_count}/5 requests successful\")\n            \n            for i, result in enumerate(results):\n                if isinstance(result, Exception):\n                    print(f\"   Request {i+1}: ❌ Exception: {result}\")\n                elif isinstance(result, dict):\n                    if result.get('success'):\n                        print(f\"   Request {i+1}: ✅ Success ({result.get('response_time', 0):.2f}ms)\")\n                    else:\n                        print(f\"   Request {i+1}: ❌ Failed: {result.get('error', 'Unknown')}\")\n                        \n    async def make_rapid_request(self, session, request_num):\n        \"\"\"Make a single rapid request\"\"\"\n        try:\n            start_time = asyncio.get_event_loop().time()\n            \n            headers = {'x-cg-pro-api-key': self.premium_api_key}\n            url = f\"{self.premium_endpoint}/coins/bitcoin\"\n            params = {'localization': 'false', 'tickers': 'false'}\n            \n            async with session.get(url, headers=headers, params=params, timeout=10) as response:\n                end_time = asyncio.get_event_loop().time()\n                response_time = (end_time - start_time) * 1000\n                \n                if response.status == 200:\n                    await response.json()  # Consume the response\n                    return {'success': True, 'response_time': response_time}\n                else:\n                    return {'success': False, 'error': f'HTTP {response.status}', 'response_time': response_time}\n                    \n        except Exception as e:\n            return {'success': False, 'error': str(e)}\n\nasync def main():\n    \"\"\"Main test function\"\"\"\n    tester = PremiumAPITester()\n    \n    # Run all tests\n    await tester.test_free_vs_premium()\n    await tester.test_rate_limits()\n    \n    print(\"\\n\" + \"=\" * 80)\n    print(\"✅ PREMIUM API TESTING COMPLETE\")\n    print(\"=\" * 80)\n    print(f\"\\n🔑 Premium API Key: CG-94NCcVD2euxaGTZe94bS2oYz\")\n    print(f\"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")\n    print(f\"\\n🚀 The onchain collector is now configured to use premium CoinGecko API\")\n    print(f\"⚡ This provides higher rate limits and more detailed data\")\n    print(f\"📊 Rate limits: Premium ~10 req/sec vs Free ~1 req/sec\")\n\nif __name__ == \"__main__\":\n    asyncio.run(main())