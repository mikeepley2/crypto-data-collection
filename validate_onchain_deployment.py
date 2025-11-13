#!/usr/bin/env python3
"""
Direct deployment validation for onchain collector.
This script runs the collector logic directly to validate functionality.
"""

import asyncio
import aiohttp
import mysql.connector.aio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OnchainCollectorValidator:
    """Validates onchain collector functionality without K8s"""
    
    def __init__(self):
        self.symbols = ["BTC", "ETH", "ADA", "DOT", "SOL", "MATIC", "AVAX", "LINK", "UNI", "AAVE"]
        self.coingecko_api_base = "https://api.coingecko.com/api/v3"
        self.session = None
        self.db_connection = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'CryptoDataCollection/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.db_connection:
            await self.db_connection.close()
            
    async def validate_api_connectivity(self) -> bool:
        """Test API connectivity"""
        try:
            logger.info("Testing CoinGecko API connectivity...")
            url = f"{self.coingecko_api_base}/ping"
            async with self.session.get(url) as response:
                if response.status == 200:
                    logger.info("✓ CoinGecko API is accessible")
                    return True
                else:
                    logger.error(f"✗ CoinGecko API returned status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"✗ CoinGecko API connectivity failed: {e}")
            return False
            
    async def fetch_onchain_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch onchain data for a symbol"""
        try:
            # Get coin ID from symbol
            coin_id = symbol.lower()
            if symbol == "BTC":
                coin_id = "bitcoin"
            elif symbol == "ETH":
                coin_id = "ethereum"
            elif symbol == "ADA":
                coin_id = "cardano"
            elif symbol == "DOT":
                coin_id = "polkadot"
            elif symbol == "SOL":
                coin_id = "solana"
            elif symbol == "MATIC":
                coin_id = "matic-network"
            elif symbol == "AVAX":
                coin_id = "avalanche-2"
            elif symbol == "LINK":
                coin_id = "chainlink"
            elif symbol == "UNI":
                coin_id = "uniswap"
            elif symbol == "AAVE":
                coin_id = "aave"
                
            # Fetch onchain metrics
            url = f"{self.coingecko_api_base}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true',
                'developer_data': 'true',
                'sparkline': 'false'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract onchain metrics
                    onchain_data = {
                        'symbol': symbol,
                        'name': data.get('name'),
                        'market_cap_rank': data.get('market_cap_rank'),
                        'current_price': data.get('market_data', {}).get('current_price', {}).get('usd'),
                        'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd'),
                        'total_volume': data.get('market_data', {}).get('total_volume', {}).get('usd'),
                        'circulating_supply': data.get('market_data', {}).get('circulating_supply'),
                        'total_supply': data.get('market_data', {}).get('total_supply'),
                        'max_supply': data.get('market_data', {}).get('max_supply'),
                        'ath': data.get('market_data', {}).get('ath', {}).get('usd'),
                        'atl': data.get('market_data', {}).get('atl', {}).get('usd'),
                        'price_change_24h': data.get('market_data', {}).get('price_change_24h'),
                        'price_change_percentage_24h': data.get('market_data', {}).get('price_change_percentage_24h'),
                        'price_change_percentage_7d': data.get('market_data', {}).get('price_change_percentage_7d'),
                        'price_change_percentage_30d': data.get('market_data', {}).get('price_change_percentage_30d'),
                        'community_score': data.get('community_data', {}).get('community_score'),
                        'developer_score': data.get('developer_data', {}).get('developer_score'),
                        'last_updated': data.get('last_updated'),
                        'collection_timestamp': datetime.utcnow().isoformat()
                    }
                    
                    logger.info(f"✓ Fetched onchain data for {symbol}")
                    return onchain_data
                else:
                    logger.error(f"✗ Failed to fetch data for {symbol}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"✗ Error fetching onchain data for {symbol}: {e}")
            return None
            
    async def test_data_collection(self) -> List[Dict[str, Any]]:
        """Test data collection for all symbols"""
        logger.info("Testing onchain data collection...")
        results = []
        
        for symbol in self.symbols:
            data = await self.fetch_onchain_data(symbol)
            if data:
                results.append(data)
            
            # Rate limiting
            await asyncio.sleep(1)
            
        logger.info(f"✓ Successfully collected data for {len(results)}/{len(self.symbols)} symbols")
        return results
        
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity (optional)"""
        try:
            # Try to connect using environment variables or defaults
            db_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'user': os.getenv('MYSQL_USER', 'crypto_user'),
                'password': os.getenv('MYSQL_PASSWORD', 'crypto_password'),
                'database': os.getenv('MYSQL_DATABASE', 'crypto_data'),
                'port': int(os.getenv('MYSQL_PORT', 3306))
            }
            
            logger.info("Testing database connectivity...")
            self.db_connection = await mysql.connector.aio.connect(**db_config)
            
            # Test query
            cursor = await self.db_connection.cursor()
            await cursor.execute("SELECT VERSION()")
            version = await cursor.fetchone()
            await cursor.close()
            
            logger.info(f"✓ Database connected successfully (MySQL {version[0]})")
            return True
            
        except Exception as e:
            logger.warning(f"⚠ Database connectivity test failed: {e}")
            logger.warning("This is expected if database is not configured")
            return False
            
    async def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        report = {
            'validation_timestamp': datetime.utcnow().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Test API connectivity
        api_ok = await self.validate_api_connectivity()
        report['tests']['api_connectivity'] = {
            'status': 'PASS' if api_ok else 'FAIL',
            'details': 'CoinGecko API connectivity test'
        }
        
        # Test data collection
        if api_ok:
            collected_data = await self.test_data_collection()
            data_collection_ok = len(collected_data) >= len(self.symbols) * 0.8  # 80% success rate
            report['tests']['data_collection'] = {
                'status': 'PASS' if data_collection_ok else 'FAIL',
                'details': f'Collected {len(collected_data)}/{len(self.symbols)} symbols',
                'sample_data': collected_data[0] if collected_data else None
            }
        else:
            report['tests']['data_collection'] = {
                'status': 'SKIP',
                'details': 'Skipped due to API connectivity failure'
            }
            data_collection_ok = False
            
        # Test database connectivity
        db_ok = await self.test_database_connectivity()
        report['tests']['database_connectivity'] = {
            'status': 'PASS' if db_ok else 'WARN',
            'details': 'Database connectivity test (optional)'
        }
        
        # Overall status
        if api_ok and data_collection_ok:
            report['overall_status'] = 'PASS'
        elif api_ok:
            report['overall_status'] = 'PARTIAL'
        else:
            report['overall_status'] = 'FAIL'
            
        return report

async def main():
    """Main validation function"""
    print("=" * 60)
    print("ONCHAIN COLLECTOR VALIDATION")
    print("=" * 60)
    
    async with OnchainCollectorValidator() as validator:
        report = await validator.generate_validation_report()
        
        # Print results
        print(f"\nValidation completed at: {report['validation_timestamp']}")
        print(f"Overall Status: {report['overall_status']}")
        print("\nTest Results:")
        print("-" * 40)
        
        for test_name, test_result in report['tests'].items():
            status_symbol = {
                'PASS': '✓',
                'FAIL': '✗',
                'WARN': '⚠',
                'SKIP': '-'
            }.get(test_result['status'], '?')
            
            print(f"{status_symbol} {test_name}: {test_result['status']}")
            print(f"   {test_result['details']}")
            
        # Show sample data if available
        if 'data_collection' in report['tests'] and report['tests']['data_collection'].get('sample_data'):
            print("\nSample Collected Data:")
            print("-" * 40)
            sample = report['tests']['data_collection']['sample_data']
            print(f"Symbol: {sample['symbol']}")
            print(f"Name: {sample['name']}")
            print(f"Price: ${sample['current_price']:,.2f}" if sample['current_price'] else "N/A")
            print(f"Market Cap: ${sample['market_cap']:,.0f}" if sample['market_cap'] else "N/A")
            print(f"24h Change: {sample['price_change_percentage_24h']:.2f}%" if sample['price_change_percentage_24h'] else "N/A")
            
        print("\n" + "=" * 60)
        print("VALIDATION COMPLETE")
        print("=" * 60)
        
        # Return exit code
        return 0 if report['overall_status'] in ['PASS', 'PARTIAL'] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)