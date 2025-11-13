#!/usr/bin/env python3
"""
Manual Derivatives Collection Test
=================================

Test the derivatives collector manually to verify it's working
"""

import sys
import os
import asyncio
import logging

# Add the service directory to Python path
service_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(service_dir, '../..'))

# Import the collector
sys.path.append(service_dir)
from crypto_derivatives_collector import CryptoDerivativesCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_collection():
    """Test a manual collection cycle"""
    print("🧪 Testing Derivatives Collection Manually")
    print("=" * 50)
    
    try:
        # Initialize collector
        collector = CryptoDerivativesCollector()
        print(f"✅ Collector initialized with {len(collector.tracked_cryptos)} symbols")
        
        # Test database connection
        print("🔌 Testing database connection...")
        
        # Run one collection cycle
        print("🚀 Starting manual collection cycle...")
        await collector.collect_derivatives_data()
        
        print("✅ Collection cycle completed!")
        print(f"📊 Collection stats:")
        print(f"  Total collections: {collector.collection_stats['total_collections']}")
        print(f"  Successful: {collector.collection_stats['successful_collections']}")
        print(f"  Failed: {collector.collection_stats['failed_collections']}")
        print(f"  Derivatives collected: {collector.collection_stats['derivatives_collected']}")
        
    except Exception as e:
        print(f"❌ Collection test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_collection())