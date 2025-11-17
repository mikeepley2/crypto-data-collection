#!/usr/bin/env python3
"""
Simple verification script for the Enhanced Onchain Collector
Tests basic functionality without requiring pytest
"""

import sys
import os
import asyncio
from datetime import date, timedelta

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the collector
import importlib.util
collector_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'onchain-collection', 'enhanced_onchain_collector.py')
spec = importlib.util.spec_from_file_location("enhanced_onchain_collector", collector_path)
onchain_module = importlib.util.module_from_spec(spec)

def test_basic_functionality():
    """Test basic collector functionality"""
    print("🧪 Testing Enhanced Onchain Collector...")
    print("=" * 50)
    
    try:
        # Load the module
        spec.loader.exec_module(onchain_module)
        EnhancedOnchainCollector = onchain_module.EnhancedOnchainCollector
        
        print("✅ Successfully imported EnhancedOnchainCollector")
        
        # Test collector initialization
        collector = EnhancedOnchainCollector()
        print("✅ Successfully initialized collector")
        
        # Test configuration
        assert collector.db_config is not None
        assert 'host' in collector.db_config
        assert 'user' in collector.db_config
        assert 'database' in collector.db_config
        print("✅ Database configuration is valid")
        
        # Test API endpoints
        assert 'messari' in collector.api_endpoints
        assert 'coingecko' in collector.api_endpoints
        print("✅ API endpoints configured")
        
        # Test rate limiting setup
        assert collector.min_delay == 1.0
        assert isinstance(collector.last_api_call, dict)
        print("✅ Rate limiting configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during basic functionality test: {e}")
        return False

def test_symbol_retrieval():
    """Test symbol retrieval functionality"""
    print("\n🔍 Testing symbol retrieval...")
    print("-" * 30)
    
    try:
        collector = onchain_module.EnhancedOnchainCollector()
        
        # Test getting symbols (should fallback to hardcoded list if DB unavailable)
        symbols = collector.get_symbols()
        
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert all(isinstance(symbol, str) for symbol in symbols)
        
        print(f"✅ Retrieved {len(symbols)} symbols: {symbols[:5]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error during symbol retrieval test: {e}")
        return False

def test_data_parsing():
    """Test data parsing functionality"""
    print("\n📊 Testing data parsing...")
    print("-" * 30)
    
    try:
        collector = onchain_module.EnhancedOnchainCollector()
        
        # Test CoinGecko data parsing
        sample_coingecko_data = {
            'id': 'bitcoin',
            'symbol': 'btc',
            'market_data': {
                'circulating_supply': 19500000.0,
                'total_supply': 21000000.0,
                'market_cap': {'usd': 850000000000.0}
            },
            'developer_data': {
                'commit_count_4_weeks': 50
            },
            'community_data': {
                'twitter_followers': 5000000
            }
        }
        
        parsed = collector.parse_coingecko_data(sample_coingecko_data, 'BTC')
        
        assert parsed['symbol'] == 'BTC'
        assert parsed['coin_id'] == 'bitcoin'
        assert 'circulating_supply' in parsed
        assert 'github_commits_30d' in parsed
        assert 'data_source' in parsed
        
        print("✅ CoinGecko data parsing works correctly")
        print(f"   Parsed fields: {list(parsed.keys())[:5]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error during data parsing test: {e}")
        return False

async def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n⏱️  Testing rate limiting...")
    print("-" * 30)
    
    try:
        collector = onchain_module.EnhancedOnchainCollector()
        
        endpoint = 'test_endpoint'
        
        # Test rate limiting
        await collector.rate_limit(endpoint)
        
        # Should track the last call time
        assert endpoint in collector.last_api_call
        
        print("✅ Rate limiting works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error during rate limiting test: {e}")
        return False

def test_missing_dates():
    """Test missing dates calculation"""
    print("\n📅 Testing missing dates calculation...")
    print("-" * 30)
    
    try:
        collector = onchain_module.EnhancedOnchainCollector()
        
        # Mock the database connection to avoid actual DB calls
        from unittest.mock import Mock, patch
        
        with patch.object(collector, 'get_db_connection') as mock_conn:
            mock_cursor = Mock()
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                (date(2023, 1, 1),),
                (date(2023, 1, 3),)
            ]
            
            start_date = date(2023, 1, 1)
            end_date = date(2023, 1, 5)
            
            missing_dates = collector.get_missing_onchain_dates('BTC', start_date, end_date)
            
            assert isinstance(missing_dates, list)
            print(f"✅ Missing dates calculation works: {len(missing_dates)} missing dates")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during missing dates test: {e}")
        return False

async def main():
    """Run all verification tests"""
    print("🚀 Starting Enhanced Onchain Collector Verification")
    print("="*60)
    
    test_results = []
    
    # Run basic tests
    test_results.append(test_basic_functionality())
    test_results.append(test_symbol_retrieval())
    test_results.append(test_data_parsing())
    test_results.append(await test_rate_limiting())
    test_results.append(test_missing_dates())
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Onchain collector is ready for deployment.")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)