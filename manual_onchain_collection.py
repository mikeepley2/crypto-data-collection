#!/usr/bin/env python3
"""Direct manual onchain data collection with real APIs"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('manual-onchain-collector')

class ManualOnchainCollector:
    def __init__(self):
        self.coingecko_api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        self.min_delay = 0.1  # Premium API delay
        
        # Get symbols from crypto_assets table
        self.symbols = self.get_symbols_from_database()
        
    def get_symbols_from_database(self) -> List[str]:
        """Get active symbols from crypto_assets table"""
        try:
            import mysql.connector
            import os
            
            db = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'crypto_user'),
                password=os.getenv('DB_PASS', 'CryptoData2024!'),
                database=os.getenv('DB_NAME', 'crypto_data'),
                charset='utf8mb4'
            )
            
            cursor = db.cursor()
            cursor.execute("""
                SELECT DISTINCT symbol FROM crypto_assets 
                WHERE is_active = 1 
                ORDER BY symbol
            """)
            
            symbols = [row[0] for row in cursor.fetchall()]
            cursor.close()
            db.close()
            
            return symbols if symbols else ['BTC', 'ETH']  # Fallback
            
        except Exception as e:
            logger.warning(f"Error getting symbols from database: {e}")
            return ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC']  # Fallback
    
    def get_coingecko_id_from_db(self, symbol: str) -> str:
        """Get CoinGecko ID from crypto_assets table"""
        try:
            import mysql.connector
            import os
            
            db = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'crypto_user'),
                password=os.getenv('DB_PASS', 'CryptoData2024!'),
                database=os.getenv('DB_NAME', 'crypto_data'),
                charset='utf8mb4'
            )
            
            cursor = db.cursor()
            cursor.execute("""
                SELECT coingecko_id FROM crypto_assets 
                WHERE symbol = %s AND coingecko_id IS NOT NULL
            """, (symbol,))
            
            result = cursor.fetchone()
            cursor.close()
            db.close()
            
            return result[0] if result else symbol.lower()
            
        except Exception as e:
            logger.warning(f"Error getting CoinGecko ID for {symbol}: {e}")
            return symbol.lower()
    
    def get_defilama_id_from_db(self, symbol: str) -> Optional[str]:
        """Get DeFiLlama protocol ID from crypto_assets table"""
        try:
            import mysql.connector
            import os
            
            db = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'crypto_user'),
                password=os.getenv('DB_PASS', 'CryptoData2024!'),
                database=os.getenv('DB_NAME', 'crypto_data'),
                charset='utf8mb4'
            )
            
            cursor = db.cursor()
            cursor.execute("""
                SELECT defilama_id FROM crypto_assets 
                WHERE symbol = %s AND defilama_id IS NOT NULL
            """, (symbol,))
            
            result = cursor.fetchone()
            cursor.close()
            db.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.warning(f"Error getting DeFiLlama ID for {symbol}: {e}")
            return None
    
    def get_staking_data_from_db(self, symbol: str) -> Optional[Dict]:
        """Get staking data from crypto_assets table"""
        try:
            import mysql.connector
            import os
            
            db = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'crypto_user'),
                password=os.getenv('DB_PASS', 'CryptoData2024!'),
                database=os.getenv('DB_NAME', 'crypto_data'),
                charset='utf8mb4'
            )
            
            cursor = db.cursor()
            cursor.execute("""
                SELECT staking_yield, staked_percentage 
                FROM crypto_assets 
                WHERE symbol = %s AND staking_yield IS NOT NULL
            """, (symbol,))
            
            result = cursor.fetchone()
            cursor.close()
            db.close()
            
            if result:
                yield_pct, staked_pct = result
                return {
                    'staking_yield': yield_pct,
                    'staked_percentage': staked_pct
                }
            return None
            
        except Exception as e:
            logger.warning(f"Error getting staking data for {symbol}: {e}")
            return None

    async def get_coingecko_data(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Get comprehensive data from CoinGecko Premium API"""
        try:
            await asyncio.sleep(self.min_delay)  # Rate limiting
            
            # Use database lookup for CoinGecko ID
            coin_id = self.get_coingecko_id_from_db(symbol)
            url = f"https://pro-api.coingecko.com/api/v3/coins/{coin_id}"
            
            headers = {'x-cg-pro-api-key': self.coingecko_api_key}
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'true', 
                'developer_data': 'true',
                'sparkline': 'false'
            }
            
            async with session.get(url, headers=headers, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_coingecko_data(data, symbol)
                else:
                    logger.warning(f"CoinGecko error for {symbol}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching CoinGecko data for {symbol}: {e}")
            return None
    
    async def get_defilama_data(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Get TVL data from DeFiLlama"""
        try:
            await asyncio.sleep(0.2)  # Conservative delay
            
            # Use database lookup for DeFiLlama protocol
            protocol = self.get_defilama_id_from_db(symbol)
            if not protocol:
                return None
            url = f"https://api.llama.fi/protocol/{protocol}"
            
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    current_tvl = data.get('tvl', [{}])[-1].get('totalLiquidityUSD', 0) if data.get('tvl') else 0
                    chain_tvls = data.get('chainTvls', {})
                    protocol_count = len(chain_tvls) if chain_tvls else 1
                    
                    return {
                        'total_value_locked': current_tvl,
                        'defi_protocols_count': protocol_count
                    }
                else:
                    logger.warning(f"DeFiLlama error for {symbol}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching DeFiLlama data for {symbol}: {e}")
            return None
    
    def parse_coingecko_data(self, data: Dict, symbol: str) -> Dict:
        """Parse CoinGecko response into onchain metrics"""
        try:
            market_data = data.get('market_data', {})
            developer_data = data.get('developer_data', {})
            community_data = data.get('community_data', {})
            
            parsed = {
                'symbol': symbol,
                'coin_id': data.get('id'),
                'timestamp_iso': datetime.now().isoformat(),
                'collected_at': datetime.now().isoformat(),
                
                # Supply metrics
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply'),
                
                # Market metrics
                'price_change_24h': market_data.get('price_change_24h'),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
                'market_cap_rank': data.get('market_cap_rank'),
                
                # Developer activity (real GitHub data)
                'github_commits_30d': developer_data.get('commit_count_4_weeks'),
                'developer_activity_score': developer_data.get('commit_count_4_weeks', 0) / 100.0 if developer_data.get('commit_count_4_weeks') else None,
                
                # Social metrics (real data)
                'social_volume_24h': (
                    (community_data.get('twitter_followers', 0) or 0) +
                    (community_data.get('reddit_subscribers', 0) or 0) + 
                    (community_data.get('telegram_channel_user_count', 0) or 0)
                ),
                'social_sentiment_score': market_data.get('sentiment_votes_up_percentage', 50) / 100.0 if market_data.get('sentiment_votes_up_percentage') else None,
                
                'data_source': 'coingecko',
                'data_quality_score': 0.85
            }
            
            # Get staking data from database if available
            staking_data = self.get_staking_data_from_db(symbol)
            if staking_data:
                parsed.update(staking_data)
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing CoinGecko data for {symbol}: {e}")
            return {}
    
    async def collect_comprehensive_data(self) -> List[Dict]:
        """Collect comprehensive onchain data for all symbols"""
        collected_data = []
        
        logger.info(f"🚀 Starting comprehensive onchain data collection for {len(self.symbols)} symbols...")
        
        async with aiohttp.ClientSession() as session:
            for symbol in self.symbols:
                logger.info(f"📊 Collecting data for {symbol}...")
                
                # Get CoinGecko data
                coingecko_data = await self.get_coingecko_data(session, symbol)
                defilama_data = await self.get_defilama_data(session, symbol)
                
                # Merge data
                if coingecko_data:
                    merged_data = coingecko_data.copy()
                    
                    # Add DeFiLlama data if available
                    if defilama_data:
                        merged_data.update(defilama_data)
                        merged_data['data_source'] += ',defilama'
                    
                    collected_data.append(merged_data)
                    logger.info(f"✅ Collected comprehensive data for {symbol}")
                    
                    # Show key metrics
                    supply = merged_data.get('circulating_supply', 0)
                    commits = merged_data.get('github_commits_30d', 0)  
                    social = merged_data.get('social_volume_24h', 0)
                    tvl = merged_data.get('total_value_locked', 0)
                    
                    supply_str = f"{supply:,.0f}" if supply else "0"
                    tvl_str = f"{tvl:,.0f}" if tvl else "0"
                    social_str = f"{social:,}" if social else "0"
                    logger.info(f"   Supply: {supply_str} | Commits: {commits} | Social: {social_str} | TVL: ${tvl_str}")
                else:
                    logger.warning(f"❌ No data collected for {symbol}")
                
        return collected_data
    
    def save_data_to_file(self, data: List[Dict], filename: str = None):
        """Save collected data to JSON file"""
        if not filename:
            filename = f"onchain_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"💾 Saved {len(data)} records to {filename}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

async def main():
    collector = ManualOnchainCollector()
    
    # Collect comprehensive data
    data = await collector.collect_comprehensive_data()
    
    # Save results
    collector.save_data_to_file(data)
    
    # Summary
    logger.info(f"🎯 Collection Summary:")
    logger.info(f"   Total symbols: {len(collector.symbols)}")
    logger.info(f"   Successful collections: {len(data)}")
    logger.info(f"   Data sources: CoinGecko Premium + DeFiLlama")
    logger.info(f"   Collection time: {datetime.now().isoformat()}")
    
    # Show sample data
    if data:
        sample = data[0]
        logger.info(f"   Sample metrics for {sample['symbol']}:")
        for key, value in sample.items():
            if key not in ['timestamp_iso', 'collected_at', 'coin_id']:
                logger.info(f"     {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())