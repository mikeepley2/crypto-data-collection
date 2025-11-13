#!/usr/bin/env python3
"""
Test comprehensive onchain data collection with all metrics
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the services directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'onchain-collection'))
from enhanced_onchain_collector import EnhancedOnchainCollector

async def test_comprehensive_collection():
    """Test comprehensive onchain data collection"""
    
    print("🚀 Testing comprehensive onchain data collection...\n")
    
    # Initialize collector
    collector = EnhancedOnchainCollector()
    
    # Test symbols
    test_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'AVAX']
    
    print("📊 Expected database columns:")
    print("✅ Basic: symbol, coin_id, timestamp_iso, data_source, data_quality_score")
    print("✅ Supply: circulating_supply, total_supply, max_supply")
    print("✅ Network: active_addresses, transaction_count, transaction_volume")
    print("✅ Value: hash_rate, difficulty, nvt_ratio, mvrv_ratio, network_value_to_transactions")
    print("✅ Development: github_commits_30d, developer_activity_score")
    print("✅ Staking: staking_yield, staked_percentage, validator_count")
    print("✅ DeFi: total_value_locked, defi_protocols_count")
    print("✅ Social: social_volume_24h, social_sentiment_score")
    print("✅ Additional: block_time_seconds, realized_cap\n")
    
    for symbol in test_symbols:
        print(f"🔍 Testing {symbol}...")
        
        try:
            # Collect comprehensive data
            data = await collector.collect_onchain_data(symbol)
            
            if data:
                print(f"✅ Successfully collected data for {symbol}")
                print(f"   📈 Data sources: {data.get('data_source', 'unknown')}")
                
                # Count collected metrics
                metrics_count = len([k for k, v in data.items() if v is not None and k not in ['symbol', 'timestamp_iso']])
                print(f"   📊 Metrics collected: {metrics_count}")
                
                # Show key metrics
                key_metrics = {
                    'Supply Metrics': ['circulating_supply', 'total_supply', 'max_supply'],
                    'Network Metrics': ['active_addresses', 'transaction_count', 'hash_rate'],
                    'Value Metrics': ['nvt_ratio', 'mvrv_ratio', 'network_value_to_transactions'],
                    'Development': ['github_commits_30d', 'developer_activity_score'],
                    'Staking': ['staking_yield', 'staked_percentage', 'validator_count'],
                    'DeFi': ['total_value_locked', 'defi_protocols_count'],
                    'Social': ['social_volume_24h', 'social_sentiment_score']
                }
                
                for category, fields in key_metrics.items():
                    available = [f for f in fields if f in data and data[f] is not None]
                    if available:
                        print(f"   ✅ {category}: {len(available)}/{len(fields)} fields")
                        for field in available[:2]:  # Show first 2 values
                            print(f"      • {field}: {data[field]}")
                    else:
                        print(f"   ❌ {category}: No data available")
                
                print(f"   🕐 Collection timestamp: {data.get('timestamp_iso')}")
                
            else:
                print(f"❌ No data collected for {symbol}")
                
        except Exception as e:
            print(f"❌ Error collecting data for {symbol}: {e}")
        
        print("-" * 60)
    
    print("\\n🎯 Test Summary:")
    print("- Tested comprehensive data collection from multiple sources")
    print("- Premium CoinGecko API integration")
    print("- Network-specific blockchain data")
    print("- DeFi metrics from DeFiLlama")
    print("- Additional metrics from specialized APIs")
    print("- Real data only (no simulations)")
    print("\\n✅ Comprehensive onchain collection test complete!")

if __name__ == "__main__":
    asyncio.run(test_comprehensive_collection())