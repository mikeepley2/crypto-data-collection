#!/usr/bin/env python3
"""
Historical OHLC Backfill Script
Populate missing OHLC columns in existing price_data_real records
"""

import asyncio
import logging
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, timedelta
import aiohttp
import time
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OHLCBackfillService:
    """Backfill missing OHLC columns in price_data_real table"""
    
    def __init__(self):
        self.api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        
        # Database configuration
        self.db_config = {
            'host': 'crypto-mysql-service.crypto-data-collection.svc.cluster.local',
            'user': 'crypto_user',
            'password': 'crypto_password_2024',
            'database': 'crypto_prices',
            'pool_name': 'backfill_pool',
            'pool_size': 5
        }
        
        # Rate limiting
        self.rate_limit_delay = 0.2  # 200ms between calls
        self.last_request_time = 0
        
    def get_connection_pool(self):
        """Create MySQL connection pool"""
        return pooling.MySQLConnectionPool(**self.db_config)
    
    def rate_limit(self):
        """Enforce rate limiting for API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    async def get_missing_ohlc_records(self) -> List[Dict]:
        """Get records with missing OHLC data"""
        pool = self.get_connection_pool()
        
        with pool.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Find records where OHLC columns are NULL
            cursor.execute("""
                SELECT DISTINCT symbol, coin_id, name, 
                       COUNT(*) as missing_count,
                       MIN(timestamp) as earliest,
                       MAX(timestamp) as latest
                FROM price_data_real 
                WHERE (high_24h IS NULL OR low_24h IS NULL 
                       OR open_24h IS NULL OR volume_usd_24h IS NULL)
                AND timestamp > %s
                GROUP BY symbol, coin_id, name
                ORDER BY missing_count DESC
                LIMIT 100
            """, (datetime.now() - timedelta(days=7),))
            
            records = cursor.fetchall()
            cursor.close()
            
        return records
    
    async def get_coingecko_ohlc_data(self, session: aiohttp.ClientSession, 
                                     coin_id: str) -> Optional[Dict]:
        """Get OHLC data from CoinGecko for a specific coin"""
        self.rate_limit()
        
        url = f"{self.base_url}/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_vol': 'true',
            'include_24hr_high': 'true',
            'include_24hr_low': 'true'
        }
        
        headers = {
            'x-cg-pro-api-key': self.api_key,
            'accept': 'application/json'
        }
        
        try:
            async with session.get(url, params=params, headers=headers, 
                                 timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        return data[coin_id]
                else:
                    logger.warning(f"API error for {coin_id}: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching OHLC for {coin_id}: {e}")
            
        return None
    
    async def update_ohlc_for_symbol(self, symbol: str, coin_id: str, 
                                   ohlc_data: Dict) -> int:
        """Update OHLC columns for all records of a symbol"""
        pool = self.get_connection_pool()
        
        # Extract OHLC values
        high_24h = ohlc_data.get('usd_24h_high')
        low_24h = ohlc_data.get('usd_24h_low') 
        volume_24h = ohlc_data.get('usd_24h_vol')
        
        # Estimate open from current price (best we can do without historical data)
        current_price = ohlc_data.get('usd', 0)
        open_24h = current_price  # Approximation
        
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update records for this symbol from last 7 days
            update_query = """
                UPDATE price_data_real 
                SET high_24h = %s, 
                    low_24h = %s, 
                    open_24h = %s, 
                    volume_usd_24h = %s
                WHERE symbol = %s 
                AND timestamp > %s
                AND (high_24h IS NULL OR low_24h IS NULL 
                     OR open_24h IS NULL OR volume_usd_24h IS NULL)
            """
            
            cursor.execute(update_query, (
                high_24h, low_24h, open_24h, volume_24h, symbol,
                datetime.now() - timedelta(days=7)
            ))
            
            updated_count = cursor.rowcount
            conn.commit()
            cursor.close()
            
        return updated_count
    
    async def run_backfill(self):
        """Main backfill process"""
        logger.info("Starting OHLC backfill process...")
        
        # Get missing records
        missing_records = await self.get_missing_ohlc_records()
        logger.info(f"Found {len(missing_records)} symbols with missing OHLC data")
        
        total_updated = 0
        successful_symbols = 0
        
        async with aiohttp.ClientSession() as session:
            for record in missing_records:
                symbol = record['symbol']
                coin_id = record['coin_id']
                missing_count = record['missing_count']
                
                if not coin_id:
                    logger.warning(f"Skipping {symbol}: no coin_id")
                    continue
                
                logger.info(f"Processing {symbol} ({coin_id}): {missing_count} missing records")
                
                # Get OHLC data from CoinGecko
                ohlc_data = await self.get_coingecko_ohlc_data(session, coin_id)
                
                if ohlc_data:
                    # Update database records
                    updated = await self.update_ohlc_for_symbol(symbol, coin_id, ohlc_data)
                    total_updated += updated
                    successful_symbols += 1
                    
                    logger.info(f"✅ Updated {updated} records for {symbol}")
                else:
                    logger.error(f"❌ Failed to get OHLC data for {symbol}")
                
                # Rate limiting between symbols
                await asyncio.sleep(0.5)
        
        logger.info(f"""
=== OHLC BACKFILL COMPLETED ===
Symbols processed: {successful_symbols}/{len(missing_records)}
Total records updated: {total_updated}
        """)

if __name__ == "__main__":
    service = OHLCBackfillService()
    asyncio.run(service.run_backfill())