#!/usr/bin/env python3
"""
Production Ultra-Fast Onchain Data Collector
Complete 2-year historical backfill using CoinGecko's efficient range endpoints
"""

import asyncio
import aiohttp
import mysql.connector
from mysql.connector import pooling
import logging
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import os
import sys
import time
from dataclasses import dataclass

# Import centralized database configuration
sys.path.append('.')
from shared.database_config import get_db_connection, test_db_connection, get_db_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ultra_fast_backfill.log')
    ]
)
logger = logging.getLogger('production-ultra-fast-collector')

@dataclass
class CollectionStats:
    total_symbols: int = 0
    processed_symbols: int = 0
    total_records: int = 0
    successful_symbols: List[str] = None
    failed_symbols: List[str] = None
    start_time: float = None
    
    def __post_init__(self):
        if self.successful_symbols is None:
            self.successful_symbols = []
        if self.failed_symbols is None:
            self.failed_symbols = []
        if self.start_time is None:
            self.start_time = time.time()

class ProductionUltraFastCollector:
    def __init__(self):
        # Get centralized database configuration
        self.db_config = get_db_config()
        
        # Test database connectivity on startup
        if not test_db_connection():
            raise ConnectionError("Database connection failed during initialization")
        
        # Connection pool for efficiency
        self.connection_pool = None
        self.init_connection_pool()
        
        # CoinGecko API configuration
        self.coingecko_api_key = 'CG-94NCcVD2euxaGTZe94bS2oYz'
        
        # Symbol ID mapping for CoinGecko
        self.symbol_mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'ADA': 'cardano',
            'ALGO': 'algorand',
            'ARB': 'arbitrum',
            'ATOM': 'cosmos',
            'AVAX': 'avalanche-2',
            'BCH': 'bitcoin-cash',
            'BNB': 'binancecoin',
            'CRO': 'crypto-com-chain',
            'DOGE': 'dogecoin',
            'DOT': 'polkadot',
            'FIL': 'filecoin',
            'ICP': 'internet-computer',
            'LINK': 'chainlink',
            'LTC': 'litecoin',
            'MATIC': 'matic-network',
            'NEAR': 'near',
            'OP': 'optimism',
            'SOL': 'solana',
            'UNI': 'uniswap',
            'XLM': 'stellar',
            'XRP': 'ripple'
        }

    def init_connection_pool(self):
        """Initialize database connection pool"""
        try:
            # Create a clean config without pool-specific parameters for connection pool
            pool_config = {k: v for k, v in self.db_config.items() 
                          if k not in ['pool_name', 'pool_size', 'pool_reset_session']}
            
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="ultra_fast_pool",
                pool_size=10,
                **pool_config
            )
            logger.info("✅ Database connection pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        return self.connection_pool.get_connection()

    async def get_all_coinbase_symbols(self) -> List[str]:
        """Get all Coinbase-supported symbols from database"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM crypto_assets 
                WHERE coinbase_supported = 1 
                AND symbol IS NOT NULL
                ORDER BY symbol
            """)
            
            symbols = [row[0] for row in cursor.fetchall()]
            logger.info(f"📋 Retrieved {len(symbols)} Coinbase symbols from database")
            
            # Add fallback symbols if database query fails
            if not symbols:
                symbols = list(self.symbol_mapping.keys())
                logger.warning(f"⚠️ Using fallback symbols: {len(symbols)} symbols")
            
            return symbols
            
        except Exception as e:
            logger.error(f"❌ Error getting symbols from database: {e}")
            # Return mapped symbols as fallback
            return list(self.symbol_mapping.keys())
        finally:
            if 'connection' in locals():
                connection.close()

    def get_coingecko_id(self, symbol: str) -> Optional[str]:
        """Get CoinGecko ID for symbol"""
        if symbol in self.symbol_mapping:
            return self.symbol_mapping[symbol]
        
        # Try lowercase as fallback
        return symbol.lower()

    async def get_bulk_market_data(self, session: aiohttp.ClientSession, symbol: str, start_date: date, end_date: date) -> List[Dict]:
        """Get bulk historical market data from CoinGecko range endpoint"""
        try:
            # Get CoinGecko ID
            coingecko_id = self.get_coingecko_id(symbol)
            if not coingecko_id:
                logger.warning(f"⚠️ No CoinGecko ID mapping for {symbol}")
                return []
            
            # Convert dates to Unix timestamps
            start_timestamp = int(start_date.strftime('%s'))
            end_timestamp = int(end_date.strftime('%s'))
            
            # CoinGecko Pro API endpoint
            url = f"https://pro-api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': start_timestamp,
                'to': end_timestamp,
                'x_cg_pro_api_key': self.coingecko_api_key
            }
            
            logger.info(f"🔍 Fetching {symbol} ({coingecko_id}) data: {start_date} → {end_date}")
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract data arrays
                    prices = data.get('prices', [])
                    market_caps = data.get('market_caps', [])
                    volumes = data.get('total_volumes', [])
                    
                    logger.info(f"📊 {symbol} raw data: {len(prices)} price points")
                    
                    if not prices:
                        logger.warning(f"⚠️ No price data for {symbol}")
                        return []
                    
                    # Convert to daily records
                    daily_records = []
                    processed_dates = set()
                    
                    for i, price_point in enumerate(prices):
                        if len(price_point) >= 2:
                            timestamp_ms, price = price_point[0], price_point[1]
                            record_date = date.fromtimestamp(timestamp_ms / 1000)
                            
                            # One record per day (skip duplicates)
                            if record_date not in processed_dates:
                                market_cap = market_caps[i][1] if i < len(market_caps) and len(market_caps[i]) >= 2 else None
                                volume = volumes[i][1] if i < len(volumes) and len(volumes[i]) >= 2 else None
                                
                                daily_records.append({
                                    'symbol': symbol,
                                    'timestamp_iso': record_date.strftime('%Y-%m-%d') + 'T00:00:00Z',
                                    'price': float(price) if price else None,
                                    'market_cap': float(market_cap) if market_cap else None,
                                    'volume_24h': float(volume) if volume else None,
                                    'data_sources': 'coingecko-pro-bulk-api'
                                })
                                processed_dates.add(record_date)
                    
                    logger.info(f"✅ {symbol}: Processed {len(daily_records)} daily records")
                    return daily_records
                    
                elif response.status == 404:
                    logger.warning(f"❌ {symbol} ({coingecko_id}) not found on CoinGecko")
                    return []
                elif response.status == 429:
                    logger.warning(f"⚠️ Rate limit hit for {symbol}, retrying after delay...")
                    await asyncio.sleep(5)
                    return []
                else:
                    logger.error(f"❌ API error for {symbol}: {response.status}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout error for {symbol}")
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol} data: {e}")
            return []

    def store_bulk_data(self, symbol: str, records: List[Dict]) -> int:
        """Store bulk records in database with transaction safety"""
        if not records:
            return 0
            
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Use INSERT IGNORE to avoid duplicates
            insert_query = """
                INSERT IGNORE INTO onchain_data (
                    symbol, timestamp_iso, price, market_cap, volume_24h, 
                    data_sources, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            
            # Prepare bulk data
            bulk_data = []
            for record in records:
                bulk_data.append((
                    record['symbol'],
                    record['timestamp_iso'],
                    record['price'],
                    record['market_cap'],
                    record['volume_24h'],
                    record['data_sources']
                ))
            
            # Execute bulk insert
            cursor.executemany(insert_query, bulk_data)
            connection.commit()
            
            stored_count = cursor.rowcount
            logger.info(f"💾 {symbol}: Stored {stored_count} records")
            
            return stored_count
            
        except Exception as e:
            logger.error(f"❌ Error storing {symbol} data: {e}")
            if 'connection' in locals():
                connection.rollback()
            return 0
        finally:
            if 'connection' in locals():
                connection.close()

    async def process_symbol(self, session: aiohttp.ClientSession, symbol: str, start_date: date, end_date: date) -> Dict:
        """Process a single symbol with bulk data collection"""
        result = {
            'symbol': symbol,
            'success': False,
            'records_stored': 0,
            'error': None
        }
        
        try:
            # Get bulk market data
            bulk_data = await self.get_bulk_market_data(session, symbol, start_date, end_date)
            
            if bulk_data:
                # Store data
                stored_count = self.store_bulk_data(symbol, bulk_data)
                result['records_stored'] = stored_count
                result['success'] = stored_count > 0
                
                if stored_count > 0:
                    logger.info(f"🎉 {symbol}: Successfully processed {stored_count} records")
                else:
                    logger.warning(f"⚠️ {symbol}: No records stored")
            else:
                result['error'] = 'No data retrieved from API'
                logger.warning(f"⚠️ {symbol}: No data retrieved")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ {symbol}: Processing failed - {e}")
            
        return result

    async def run_comprehensive_backfill(self, batch_size: int = 10) -> CollectionStats:
        """Run comprehensive 2-year backfill for all Coinbase symbols"""
        
        # Date range: 2023-01-01 to 2024-12-31 (2 years)
        start_date = date(2023, 1, 1)
        end_date = date(2024, 12, 31)
        
        stats = CollectionStats()
        
        # Get all Coinbase symbols
        symbols = await self.get_all_coinbase_symbols()
        stats.total_symbols = len(symbols)
        
        logger.info(f"🚀 PRODUCTION ULTRA-FAST BACKFILL STARTING")
        logger.info(f"📅 Date range: {start_date} → {end_date} (2 years)")
        logger.info(f"🎯 Processing {len(symbols)} Coinbase symbols")
        logger.info(f"⚡ Batch size: {batch_size} concurrent symbols")
        
        # Process symbols in batches
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(symbols) + batch_size - 1) // batch_size
                
                logger.info(f"📦 Processing batch {batch_num}/{total_batches}: {batch_symbols}")
                
                # Process batch concurrently
                batch_tasks = [
                    self.process_symbol(session, symbol, start_date, end_date)
                    for symbol in batch_symbols
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"❌ Batch processing exception: {result}")
                        stats.failed_symbols.append("unknown")
                    else:
                        stats.processed_symbols += 1
                        
                        if result['success']:
                            stats.successful_symbols.append(result['symbol'])
                            stats.total_records += result['records_stored']
                        else:
                            stats.failed_symbols.append(result['symbol'])
                            logger.warning(f"⚠️ Failed: {result['symbol']} - {result.get('error', 'Unknown error')}")
                
                # Progress update
                elapsed = time.time() - stats.start_time
                logger.info(f"📊 Progress: {stats.processed_symbols}/{stats.total_symbols} symbols | {stats.total_records:,} records | {elapsed:.1f}s elapsed")
                
                # Rate limiting between batches
                if i + batch_size < len(symbols):
                    await asyncio.sleep(1)
        
        # Final statistics
        elapsed_total = time.time() - stats.start_time
        success_rate = (len(stats.successful_symbols) / stats.total_symbols) * 100 if stats.total_symbols > 0 else 0
        
        logger.info(f"🏁 COMPREHENSIVE BACKFILL COMPLETED!")
        logger.info(f"⏱️ Total time: {elapsed_total:.1f} seconds ({elapsed_total/60:.1f} minutes)")
        logger.info(f"📈 Success rate: {success_rate:.1f}% ({len(stats.successful_symbols)}/{stats.total_symbols})")
        logger.info(f"💾 Total records stored: {stats.total_records:,}")
        logger.info(f"✅ Successful symbols: {len(stats.successful_symbols)}")
        logger.info(f"❌ Failed symbols: {len(stats.failed_symbols)}")
        
        if stats.failed_symbols:
            logger.info(f"❌ Failed symbols list: {stats.failed_symbols}")
        
        return stats

    def generate_summary_report(self, stats: CollectionStats) -> str:
        """Generate comprehensive summary report"""
        elapsed_total = time.time() - stats.start_time
        success_rate = (len(stats.successful_symbols) / stats.total_symbols) * 100 if stats.total_symbols > 0 else 0
        
        report = f"""
        ╔═══════════════════════════════════════════════════════════════╗
        ║                 ULTRA-FAST BACKFILL SUMMARY REPORT           ║
        ╚═══════════════════════════════════════════════════════════════╝
        
        📅 DATE RANGE: 2023-01-01 → 2024-12-31 (2 years)
        ⏱️ TOTAL TIME: {elapsed_total:.1f} seconds ({elapsed_total/60:.1f} minutes)
        
        📊 SYMBOL PROCESSING:
           • Total symbols: {stats.total_symbols}
           • Successful: {len(stats.successful_symbols)} ({success_rate:.1f}%)
           • Failed: {len(stats.failed_symbols)}
           
        💾 DATA COLLECTION:
           • Total records: {stats.total_records:,}
           • Average per symbol: {stats.total_records/len(stats.successful_symbols):.0f} records
           • Rate: {stats.total_records/elapsed_total:.0f} records/second
           
        🚀 EFFICIENCY METRICS:
           • Symbols/second: {stats.total_symbols/elapsed_total:.2f}
           • Records/minute: {(stats.total_records*60)/elapsed_total:.0f}
           
        ✅ SUCCESSFUL SYMBOLS ({len(stats.successful_symbols)}):
        {', '.join(sorted(stats.successful_symbols))}
        
        ❌ FAILED SYMBOLS ({len(stats.failed_symbols)}):
        {', '.join(sorted(stats.failed_symbols)) if stats.failed_symbols else 'None'}
        """
        
        return report

async def main():
    """Main execution function"""
    try:
        logger.info("🚀 Production Ultra-Fast Collector Starting...")
        
        # Initialize collector
        collector = ProductionUltraFastCollector()
        
        # Run comprehensive backfill
        stats = await collector.run_comprehensive_backfill(batch_size=10)
        
        # Generate and display report
        report = collector.generate_summary_report(stats)
        print(report)
        
        # Save report to file
        with open('ultra_fast_backfill_report.txt', 'w') as f:
            f.write(report)
        
        logger.info("📄 Report saved to: ultra_fast_backfill_report.txt")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main execution: {e}")
        raise

if __name__ == "__main__":
    try:
        # Run the ultra-fast backfill
        result = asyncio.run(main())
        print(f"\n🎉 Backfill completed successfully!")
        print(f"📊 Final stats: {result.total_records:,} records stored")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Backfill interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
