#!/usr/bin/env python3
"""
LLM Integration Testing Suite
============================

Comprehensive testing of the LLM integration with your crypto data collection system.
Tests the bridge to aitest Ollama services and validates enhanced data processing.
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional

class LLMIntegrationTester:
    """Test suite for LLM integration"""
    
    def __init__(self):
        # Service endpoints (will use port forwarding)
        self.llm_client_url = "http://localhost:8040"
        self.enhanced_sentiment_url = "http://localhost:8038"
        self.narrative_analyzer_url = "http://localhost:8039"
        
        # Test data
        self.test_news_text = """
        Bitcoin Surges to New All-Time High as Major Institution Announces $1B Purchase
        
        Bitcoin reached a new record high of $68,000 today following news that a major 
        financial institution has allocated $1 billion to cryptocurrency investments. 
        The move signals growing institutional adoption and has sparked optimism across 
        the crypto market. Ethereum and other altcoins are also seeing significant gains 
        as investors react to the positive regulatory developments.
        """
        
        self.test_sentiment_texts = [
            "Bitcoin is looking extremely bullish with massive institutional adoption!",
            "Market crash incoming - all technical indicators are showing bearish signals",
            "Uncertain times ahead as regulatory clarity remains elusive",
            "Revolutionary DeFi protocol launches with innovative yield farming mechanisms"
        ]
        
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
    
    def print_header(self):
        """Print test header"""
        print("🧠 LLM Integration Testing Suite")
        print("=" * 50)
        print(f"Started at: {datetime.now().isoformat()}")
        print()
    
    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result"""
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def record_test(self, name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
        else:
            self.results["failed_tests"] += 1
        
        self.results["test_results"].append({
            "name": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_service_health(self, service_name: str, url: str) -> bool:
        """Test service health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.print_test(f"{service_name} Health Check", "PASS", 
                                      f"Status: {data.get('status', 'unknown')}")
                        self.record_test(f"{service_name} Health", True, str(data))
                        return True
                    else:
                        self.print_test(f"{service_name} Health Check", "FAIL", 
                                      f"HTTP {response.status}")
                        self.record_test(f"{service_name} Health", False, f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.print_test(f"{service_name} Health Check", "FAIL", str(e))
            self.record_test(f"{service_name} Health", False, str(e))
            return False
    
    async def test_llm_client_models(self) -> bool:
        """Test LLM client models endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.llm_client_url}/models", 
                                     timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('configured', {})
                        self.print_test("LLM Models Available", "PASS", 
                                      f"Models: {', '.join(models.keys()) if models else 'None'}")
                        self.record_test("LLM Models", True, str(data))
                        return True
                    else:
                        self.print_test("LLM Models Available", "FAIL", f"HTTP {response.status}")
                        self.record_test("LLM Models", False, f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.print_test("LLM Models Available", "FAIL", str(e))
            self.record_test("LLM Models", False, str(e))
            return False
    
    async def test_sentiment_enhancement(self) -> bool:
        """Test sentiment enhancement endpoint"""
        try:
            test_data = {
                "text": self.test_sentiment_texts[0],
                "original_score": 0.8
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.llm_client_url}/enhance-sentiment",
                                      json=test_data,
                                      timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('result')
                        if result:
                            self.print_test("Sentiment Enhancement", "PASS",
                                          f"Enhanced emotion: {result.get('enhanced_emotion', 'unknown')}")
                            self.record_test("Sentiment Enhancement", True, str(result))
                            return True
                        else:
                            self.print_test("Sentiment Enhancement", "FAIL", "No result data")
                            self.record_test("Sentiment Enhancement", False, "No result data")
                            return False
                    else:
                        self.print_test("Sentiment Enhancement", "FAIL", f"HTTP {response.status}")
                        self.record_test("Sentiment Enhancement", False, f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.print_test("Sentiment Enhancement", "FAIL", str(e))
            self.record_test("Sentiment Enhancement", False, str(e))
            return False
    
    async def test_narrative_analysis(self) -> bool:
        """Test narrative analysis endpoint"""
        try:
            test_data = {
                "text": self.test_news_text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.llm_client_url}/analyze-narrative",
                                      json=test_data,
                                      timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('result')
                        if result:
                            self.print_test("Narrative Analysis", "PASS",
                                          f"Primary theme: {result.get('primary_theme', 'unknown')}")
                            self.record_test("Narrative Analysis", True, str(result))
                            return True
                        else:
                            self.print_test("Narrative Analysis", "FAIL", "No result data")
                            self.record_test("Narrative Analysis", False, "No result data")
                            return False
                    else:
                        self.print_test("Narrative Analysis", "FAIL", f"HTTP {response.status}")
                        self.record_test("Narrative Analysis", False, f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.print_test("Narrative Analysis", "FAIL", str(e))
            self.record_test("Narrative Analysis", False, str(e))
            return False
    
    async def test_technical_patterns(self) -> bool:
        """Test technical pattern analysis endpoint"""
        try:
            test_data = {
                "symbol": "BTC",
                "timeframe": "1h"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.llm_client_url}/technical-patterns",
                                      json=test_data,
                                      timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('result')
                        if result:
                            self.print_test("Technical Pattern Analysis", "PASS",
                                          f"Pattern detected: {result.get('pattern_name', 'unknown')}")
                            self.record_test("Technical Pattern Analysis", True, str(result))
                            return True
                        else:
                            self.print_test("Technical Pattern Analysis", "WARN", 
                                          "No patterns detected (may be normal)")
                            self.record_test("Technical Pattern Analysis", True, "No patterns detected")
                            return True
                    else:
                        self.print_test("Technical Pattern Analysis", "FAIL", f"HTTP {response.status}")
                        self.record_test("Technical Pattern Analysis", False, f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.print_test("Technical Pattern Analysis", "FAIL", str(e))
            self.record_test("Technical Pattern Analysis", False, str(e))
            return False
    
    async def test_performance(self) -> bool:
        """Test performance of LLM integration"""
        try:
            start_time = time.time()
            
            # Run multiple sentiment enhancement requests
            tasks = []
            for text in self.test_sentiment_texts[:2]:  # Test with 2 texts
                test_data = {"text": text, "original_score": 0.5}
                tasks.append(self.make_request(f"{self.llm_client_url}/enhance-sentiment", test_data))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            
            if successful_requests > 0:
                avg_time = total_time / successful_requests
                self.print_test("Performance Test", "PASS",
                              f"{successful_requests}/{len(tasks)} requests successful, avg time: {avg_time:.2f}s")
                self.record_test("Performance Test", True, f"Avg response time: {avg_time:.2f}s")
                return True
            else:
                self.print_test("Performance Test", "FAIL", "No successful requests")
                self.record_test("Performance Test", False, "No successful requests")
                return False
                
        except Exception as e:
            self.print_test("Performance Test", "FAIL", str(e))
            self.record_test("Performance Test", False, str(e))
            return False
    
    async def make_request(self, url: str, data: dict):
        """Make HTTP request with timeout"""
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"HTTP {response.status}")
    
    async def run_all_tests(self):
        """Run all tests"""
        self.print_header()
        
        print("🔍 Testing Service Health...")
        await self.test_service_health("LLM Integration Client", self.llm_client_url)
        
        print("🧠 Testing LLM Integration Features...")
        await self.test_llm_client_models()
        await self.test_sentiment_enhancement()
        await self.test_narrative_analysis()
        await self.test_technical_patterns()
        
        print("⚡ Testing Performance...")
        await self.test_performance()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed_tests']} ✅")
        print(f"Failed: {self.results['failed_tests']} ❌")
        print(f"Success Rate: {(self.results['passed_tests'] / self.results['total_tests'] * 100):.1f}%")
        
        if self.results['failed_tests'] > 0:
            print("\n❌ Failed Tests:")
            for test in self.results['test_results']:
                if not test['passed']:
                    print(f"   • {test['name']}: {test['details']}")
        
        print(f"\n🕒 Completed at: {datetime.now().isoformat()}")
        
        if self.results['failed_tests'] == 0:
            print("\n🎉 All tests passed! LLM integration is working correctly.")
        else:
            print(f"\n⚠️ {self.results['failed_tests']} tests failed. Check aitest Ollama service connectivity.")
        
        # Save results to file
        with open('llm_integration_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Test results saved to: llm_integration_test_results.json")

async def main():
    """Main test runner"""
    print("🚀 Starting LLM Integration Test Suite...")
    print("\n⚠️ Prerequisites:")
    print("   1. Kubernetes cluster with services deployed")
    print("   2. Port forwarding set up:")
    print("      kubectl port-forward -n crypto-collectors svc/llm-integration-client 8040:8040")
    print("   3. aitest Ollama services running and accessible")
    
    input("\nPress Enter when ready to start testing...")
    
    tester = LLMIntegrationTester()
    await tester.run_all_tests()
    
    # Exit with proper code
    sys.exit(0 if tester.results['failed_tests'] == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())