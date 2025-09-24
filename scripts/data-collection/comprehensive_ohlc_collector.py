#!/usr/bin/env python3
"""
COMPREHENSIVE OHLC COLLECTOR
Collect OHLC data for ALL symbols with CoinGecko mappings to improve coverage from 15.8% to 100%
"""

import requests
import mysql.connector
import logging
import time
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveOHLCCollector:
    """Collect OHLC data for ALL symbols with CoinGecko mappings"""
    
    def __init__(self):
        self.api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'x-cg-pro-api-key': self.api_key,
            'accept': 'application/json'
        })
        
        # Rate limiting - premium allows 500 calls/minute
        self.rate_limit_delay = 0.15  # 150ms between calls
        self.last_request_time = 0
        
        # Database connection
        self.db_config = {
            'host': 'localhost',
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices'
        }
    
    def rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting and error handling"""
        self.rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            return None
    
    def get_all_ml_symbols(self) -> List[Dict[str, str]]:
        """Get ALL ML symbols with CoinGecko mappings"""
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # First get all ML symbols
            cursor.execute("SELECT DISTINCT symbol FROM ml_features_materialized ORDER BY symbol")
            ml_symbols = [row[0] for row in cursor.fetchall()]
            
            # Then get CoinGecko mappings for these symbols
            symbols_with_mappings = []
            
            for symbol in ml_symbols:
                cursor.execute("""
                    SELECT DISTINCT coin_id 
                    FROM price_data 
                    WHERE symbol = %s
                    AND coin_id IS NOT NULL 
                    AND coin_id != ''
                    LIMIT 1
                """, (symbol,))
                
                result = cursor.fetchone()
                if result:
                    symbols_with_mappings.append({
                        'symbol': symbol,
                        'coin_id': result[0]
                    })
            
            conn.close()
            
            logger.info(f"📊 Found {len(symbols_with_mappings)} ML symbols with CoinGecko mappings for OHLC collection")
            return symbols_with_mappings
            
        except Exception as e:
            logger.error(f"❌ Error getting ML symbols: {e}")
            return []
    
    def get_existing_ohlc_symbols(self) -> set:
        """Get symbols that already have OHLC data"""
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT symbol FROM ohlc_data")
            existing_symbols = set(row[0] for row in cursor.fetchall())
            
            conn.close()
            logger.info(f"📈 Found {len(existing_symbols)} symbols already with OHLC data")
            return existing_symbols
            
        except Exception as e:
            logger.error(f"❌ Error getting existing OHLC symbols: {e}")
            return set()
    
    def collect_ohlc_for_symbol(self, coin_id: str, symbol: str, days: int = 365):
        """Collect OHLC data for a specific symbol"""
        
        try:
            # Get OHLC data for the last year (maximum for hourly granularity)
            endpoint = f"coins/{coin_id}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': days,
                  # hourly granularity
            }
            
            logger.info(f"📈 Collecting OHLC data for {symbol} ({coin_id})...")
            data = self.make_request(endpoint, params)
            
            if not data:
                logger.warning(f"⚠️  No OHLC data for {symbol}")
                return 0
            
            # Parse and store OHLC data
            return self.store_ohlc_data(symbol, coin_id, data)
            
        except Exception as e:
            logger.error(f"❌ Error collecting OHLC for {symbol}: {e}")
            return 0
    
    def store_ohlc_data(self, symbol: str, coin_id: str, ohlc_data: List) -> int:
        """Store OHLC data in database"""
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            insert_sql = """
                INSERT INTO ohlc_data 
                (symbol, coin_id, timestamp_unix, timestamp_iso, 
                 open_price, high_price, low_price, close_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    open_price = VALUES(open_price),
                    high_price = VALUES(high_price),
                    low_price = VALUES(low_price),
                    close_price = VALUES(close_price),
                    volume = VALUES(volume)
            """
            
            records_inserted = 0
            
            for ohlc in ohlc_data:
                # OHLC format: [timestamp, open, high, low, close]
                if len(ohlc) >= 5:
                    timestamp_unix = int(ohlc[0])
                    timestamp_iso = datetime.fromtimestamp(timestamp_unix / 1000, tz=timezone.utc)
                    
                    values = (
                        symbol,
                        coin_id,
                        timestamp_unix,
                        timestamp_iso,
                        float(ohlc[1]),  # open
                        float(ohlc[2]),  # high
                        float(ohlc[3]),  # low
                        float(ohlc[4]),  # close
                        float(ohlc[5]) if len(ohlc) > 5 else None  # volume (if available)
                    )
                    
                    cursor.execute(insert_sql, values)
                    records_inserted += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"   ✅ Stored {records_inserted} OHLC records for {symbol}")
            return records_inserted
            
        except Exception as e:
            logger.error(f"❌ Error storing OHLC data for {symbol}: {e}")
            return 0
    
    def run_comprehensive_collection(self, skip_existing=True):
        """Run comprehensive OHLC collection for all ML symbols"""
        
        try:
            logger.info("🚀 STARTING COMPREHENSIVE OHLC COLLECTION")
            logger.info("=" * 80)
            
            # Get all ML symbols with mappings
            all_symbols = self.get_all_ml_symbols()
            
            if not all_symbols:
                logger.warning("⚠️  No symbols found for OHLC collection")
                return
            
            # Get existing OHLC symbols to skip if requested
            existing_symbols = self.get_existing_ohlc_symbols() if skip_existing else set()
            
            # Filter symbols to collect
            symbols_to_collect = []
            for symbol_info in all_symbols:
                if not skip_existing or symbol_info['symbol'] not in existing_symbols:
                    symbols_to_collect.append(symbol_info)
            
            logger.info(f"📊 Collection Plan:")
            logger.info(f"   Total ML symbols with mappings: {len(all_symbols)}")
            logger.info(f"   Already have OHLC: {len(existing_symbols)}")
            logger.info(f"   Symbols to collect: {len(symbols_to_collect)}")
            
            if not symbols_to_collect:
                logger.info("✅ All symbols already have OHLC data!")
                return
            
            total_ohlc_records = 0
            successful_collections = 0
            failed_collections = 0
            
            # Collect OHLC for each symbol
            start_time = datetime.now()
            
            for i, symbol_info in enumerate(symbols_to_collect, 1):
                symbol = symbol_info['symbol']
                coin_id = symbol_info['coin_id']
                
                logger.info(f"[{i}/{len(symbols_to_collect)}] Processing {symbol}...")
                
                try:
                    records = self.collect_ohlc_for_symbol(coin_id, symbol)
                    
                    if records > 0:
                        total_ohlc_records += records
                        successful_collections += 1
                        logger.info(f"   ✅ SUCCESS: {records} records")
                    else:
                        failed_collections += 1
                        logger.warning(f"   ❌ FAILED: No data")
                    
                    # Progress update every 25 symbols
                    if i % 25 == 0:
                        elapsed = datetime.now() - start_time
                        success_rate = (successful_collections / i) * 100
                        avg_records = total_ohlc_records / successful_collections if successful_collections > 0 else 0
                        
                        logger.info(f"\n📊 PROGRESS UPDATE ({i}/{len(symbols_to_collect)}):")
                        logger.info(f"   ✅ Successful: {successful_collections}")
                        logger.info(f"   ❌ Failed: {failed_collections}")
                        logger.info(f"   📈 Success Rate: {success_rate:.1f}%")
                        logger.info(f"   📊 Total Records: {total_ohlc_records:,}")
                        logger.info(f"   ⚡ Avg Records/Symbol: {avg_records:.0f}")
                        logger.info(f"   ⏰ Elapsed: {elapsed}")
                        if i > 0:
                            eta = elapsed * (len(symbols_to_collect) / i) - elapsed
                            logger.info(f"   🎯 ETA: {eta}")
                        
                except KeyboardInterrupt:
                    logger.info(f"\n🛑 COLLECTION INTERRUPTED at {i}/{len(symbols_to_collect)}")
                    logger.info(f"✅ Successful: {successful_collections}, ❌ Failed: {failed_collections}")
                    logger.info(f"📊 Total Records: {total_ohlc_records:,}")
                    raise
                except Exception as e:
                    logger.error(f"❌ Unexpected error processing {symbol}: {e}")
                    failed_collections += 1
                    continue
            
            # Final summary
            elapsed_total = datetime.now() - start_time
            
            logger.info("\n" + "=" * 80)
            logger.info("🎉 COMPREHENSIVE OHLC COLLECTION COMPLETE!")
            logger.info("=" * 80)
            logger.info(f"📊 Results:")
            logger.info(f"   Total Processed: {len(symbols_to_collect)}")
            logger.info(f"   ✅ Successful: {successful_collections}")
            logger.info(f"   ❌ Failed: {failed_collections}")
            logger.info(f"   📈 Success Rate: {(successful_collections/len(symbols_to_collect))*100:.1f}%")
            logger.info(f"   📊 Total OHLC Records: {total_ohlc_records:,}")
            logger.info(f"   ⏰ Total Time: {elapsed_total}")
            if elapsed_total.total_seconds() > 0:
                logger.info(f"   ⚡ Speed: {total_ohlc_records/(elapsed_total.total_seconds()/60):.0f} records/minute")
            
            # Check final coverage
            final_existing = self.get_existing_ohlc_symbols()
            final_ml_symbols = len(self.get_all_ml_symbols())
            final_coverage = len(final_existing) / final_ml_symbols * 100
            
            logger.info(f"\n🎯 Final OHLC Coverage:")
            logger.info(f"   OHLC symbols: {len(final_existing)}")
            logger.info(f"   ML symbols: {final_ml_symbols}")
            logger.info(f"   Coverage: {final_coverage:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Collection failed: {e}")
            raise

if __name__ == "__main__":
    collector = ComprehensiveOHLCCollector()
    collector.run_comprehensive_collection(skip_existing=True)
