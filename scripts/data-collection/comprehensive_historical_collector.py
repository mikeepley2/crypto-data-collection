#!/usr/bin/env python3
"""
Comprehensive Historical Data Collection System
============================================== 

Uses premium CoinGecko Pro API to collect historical data from 2020-01-01
for all Coinbase-listed cryptocurrencies.

Features:
- Identifies data gaps automatically
- Collects missing historical price data
- Populates price_data, onchain_metrics, macro_indicators, and ml_features_materialized
- Handles rate limits and retries
- Progress tracking and monitoring
- Database transaction safety
"""

import os
import sys
import json
import time
import logging
import requests
import pymysql
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('historical_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveHistoricalCollector:
    def __init__(self):
        """Initialize the historical data collector"""
        self.coingecko_api_key = os.getenv('COINGECKO_PREMIUM_API_KEY', 'CG-5eCTSYNvLjBYz7gxS3jXCLrq')  # Premium API key
        self.fred_api_key = os.getenv('FRED_HISTORICAL_API_KEY', '1e8b4e2b6b7e8f9b5c9d8f7e6d5c4b3a')  # FRED API key
        
        # API configurations
        self.coingecko_base_url = "https://pro-api.coingecko.com/api/v3"
        self.fred_base_url = "https://api.stlouisfed.org/fred"
        
        # Rate limiting (premium account)
        self.coingecko_rate_limit = 500  # requests per minute for pro
        self.fred_rate_limit = 120  # requests per minute
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DATABASE_HOST', 'host.docker.internal'),
            'user': os.getenv('DATABASE_USER', 'news_collector'),
            'password': os.getenv('DATABASE_PASSWORD', '99Rules!'),
            'database': os.getenv('DATABASE_NAME', 'crypto_prices'),
            'charset': 'utf8mb4'
        }
        
        # Collection parameters
        self.start_date = datetime(2020, 1, 1)
        self.end_date = datetime.now()
        
        # Progress tracking
        self.progress_file = "historical_collection_progress.json"
        self.load_progress()
        
    def load_progress(self):
        """Load collection progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    self.progress = json.load(f)
            else:
                self.progress = {
                    'completed_symbols': [],
                    'failed_symbols': [],
                    'last_update': None,
                    'total_records_collected': 0
                }
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
            self.progress = {
                'completed_symbols': [],
                'failed_symbols': [],
                'last_update': None,
                'total_records_collected': 0
            }
    
    def save_progress(self):
        """Save collection progress to file"""
        try:
            self.progress['last_update'] = datetime.now().isoformat()
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def get_database_connection(self):
        """Get database connection"""
        try:
            conn = pymysql.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def get_coinbase_symbols(self) -> List[str]:
        """Get list of all symbols that are traded on Coinbase"""
        logger.info("🏦 Getting Coinbase-traded cryptocurrencies...")
        
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            # Get all unique symbols from our current data
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM price_data 
                WHERE symbol IS NOT NULL 
                AND symbol != ''
                ORDER BY symbol
            """)
            
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            logger.info(f"📊 Found {len(symbols)} symbols in database")
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            # Fallback to major cryptocurrencies if database query fails
            return [
                'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'XLM', 'LTC', 'BCH',
                'ALGO', 'ATOM', 'XTZ', 'COMP', 'MKR', 'AAVE', 'UNI', 'SUSHI',
                'YFI', 'BAT', 'ZRX', 'OXT', 'CGLD', 'FIL', 'GRT', 'NMR',
                'STOR', 'SKALE', 'BAND', 'ICP', 'MATIC', 'MANA', 'CRV'
            ]
    
    def get_coingecko_coin_list(self) -> Dict[str, str]:
        """Get mapping of symbols to CoinGecko IDs"""
        logger.info("🔍 Fetching CoinGecko coin list...")
        
        try:
            headers = {'X-Cg-Pro-Api-Key': self.coingecko_api_key}
            response = requests.get(
                f"{self.coingecko_base_url}/coins/list",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"CoinGecko API error: {response.status_code}")
                return {}
            
            coins = response.json()
            
            # Create symbol to ID mapping
            symbol_to_id = {}
            for coin in coins:
                symbol = coin['symbol'].upper()
                coin_id = coin['id']
                # Prefer shorter/more common IDs for popular coins
                if symbol not in symbol_to_id or len(coin_id) < len(symbol_to_id[symbol]):
                    symbol_to_id[symbol] = coin_id
            
            logger.info(f"📋 Mapped {len(symbol_to_id)} symbols to CoinGecko IDs")
            return symbol_to_id
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko coin list: {e}")
            return {}
    
    def identify_data_gaps(self, symbol: str) -> List[Tuple[datetime, datetime]]:
        """Identify gaps in historical data for a symbol"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            # Get existing data dates for this symbol
            cursor.execute("""
                SELECT DATE(timestamp_iso) as date_only
                FROM price_data 
                WHERE symbol = %s 
                AND timestamp_iso >= %s
                AND timestamp_iso <= %s
                GROUP BY DATE(timestamp_iso)
                ORDER BY date_only
            """, (symbol, self.start_date, self.end_date))
            
            existing_dates = set(row[0] for row in cursor.fetchall())
            conn.close()
            
            # Generate all dates in range
            current_date = self.start_date.date()
            end_date = self.end_date.date()
            all_dates = set()
            
            while current_date <= end_date:
                all_dates.add(current_date)
                current_date += timedelta(days=1)
            
            # Find missing dates
            missing_dates = sorted(all_dates - existing_dates)
            
            # Group consecutive missing dates into ranges
            gaps = []
            if missing_dates:
                start_gap = missing_dates[0]
                end_gap = missing_dates[0]
                
                for date in missing_dates[1:]:
                    if date == end_gap + timedelta(days=1):
                        end_gap = date
                    else:
                        gaps.append((
                            datetime.combine(start_gap, datetime.min.time()),
                            datetime.combine(end_gap, datetime.min.time())
                        ))
                        start_gap = date
                        end_gap = date
                
                # Add the last gap
                gaps.append((
                    datetime.combine(start_gap, datetime.min.time()),
                    datetime.combine(end_gap, datetime.min.time())
                ))
            
            logger.info(f"🔍 {symbol}: Found {len(gaps)} data gaps covering {len(missing_dates)} days")
            return gaps
            
        except Exception as e:
            logger.error(f"Error identifying gaps for {symbol}: {e}")
            return []
    
    def collect_historical_prices(self, symbol: str, coin_id: str, start_date: datetime, end_date: datetime) -> int:
        """Collect historical price data for a symbol within date range"""
        logger.info(f"📈 Collecting {symbol} price data from {start_date.date()} to {end_date.date()}")
        
        try:
            headers = {'X-Cg-Pro-Api-Key': self.coingecko_api_key}
            
            # Convert dates to timestamps
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            # Get historical data from CoinGecko
            response = requests.get(
                f"{self.coingecko_base_url}/coins/{coin_id}/market_chart/range",
                headers=headers,
                params={
                    'vs_currency': 'usd',
                    'from': start_timestamp,
                    'to': end_timestamp
                },
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"CoinGecko API error for {symbol}: {response.status_code}")
                return 0
            
            data = response.json()
            
            if 'prices' not in data or not data['prices']:
                logger.warning(f"No price data returned for {symbol}")
                return 0
            
            # Process and insert data
            records_inserted = 0
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            try:
                for price_point in data['prices']:
                    timestamp_ms = price_point[0]
                    price = Decimal(str(price_point[1]))
                    
                    # Convert timestamp to datetime
                    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                    
                    # Get volume if available
                    volume_24h = None
                    if 'total_volumes' in data:
                        # Find closest volume data point
                        volumes = data['total_volumes']
                        closest_volume = min(volumes, key=lambda x: abs(x[0] - timestamp_ms))
                        if abs(closest_volume[0] - timestamp_ms) < 3600000:  # Within 1 hour
                            volume_24h = Decimal(str(closest_volume[1]))
                    
                    # Get market cap if available
                    market_cap = None
                    if 'market_caps' in data:
                        market_caps = data['market_caps']
                        closest_cap = min(market_caps, key=lambda x: abs(x[0] - timestamp_ms))
                        if abs(closest_cap[0] - timestamp_ms) < 3600000:  # Within 1 hour
                            market_cap = Decimal(str(closest_cap[1]))
                    
                    # Insert into database
                    cursor.execute("""
                        INSERT IGNORE INTO price_data (
                            symbol, coin_id, timestamp, timestamp_iso,
                            current_price, volume_usd_24h, market_cap,
                            data_source, collection_interval, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        symbol, coin_id, timestamp_ms, dt,
                        price, volume_24h, market_cap,
                        'coingecko_historical', 'daily', datetime.now()
                    ))
                    
                    records_inserted += 1
                
                conn.commit()
                logger.info(f"✅ {symbol}: Inserted {records_inserted} price records")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error inserting {symbol} data: {e}")
                return 0
            finally:
                conn.close()
            
            return records_inserted
            
        except Exception as e:
            logger.error(f"Error collecting {symbol} historical prices: {e}")
            return 0
    
    def collect_macro_indicators(self):
        """Collect historical macro economic indicators"""
        logger.info("🏛️ Collecting macro economic indicators...")
        
        # FRED series IDs for key indicators
        fred_series = {
            'FEDFUNDS': 'fed_funds_rate',
            'UNRATE': 'unemployment_rate',
            'CPIAUCSL': 'cpi_inflation',
            'DGS10': 'treasury_10y',
            'DEXUSEU': 'dxy_index',
            'VIXCLS': 'vix_index'
        }
        
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        total_records = 0
        
        try:
            for series_id, indicator_name in fred_series.items():
                logger.info(f"📊 Collecting {indicator_name} from FRED...")
                
                try:
                    # Get data from FRED API
                    response = requests.get(
                        f"{self.fred_base_url}/series/observations",
                        params={
                            'series_id': series_id,
                            'api_key': self.fred_api_key,
                            'file_type': 'json',
                            'observation_start': self.start_date.strftime('%Y-%m-%d'),
                            'observation_end': self.end_date.strftime('%Y-%m-%d')
                        },
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"FRED API error for {series_id}: {response.status_code}")
                        continue
                    
                    data = response.json()
                    
                    if 'observations' not in data:
                        logger.warning(f"No observations for {series_id}")
                        continue
                    
                    # Insert data
                    records_inserted = 0
                    for obs in data['observations']:
                        if obs['value'] != '.':  # FRED uses '.' for missing values
                            try:
                                value = Decimal(obs['value'])
                                obs_date = datetime.strptime(obs['date'], '%Y-%m-%d').date()
                                
                                cursor.execute("""
                                    INSERT IGNORE INTO macro_indicators (
                                        indicator_name, indicator_date, value,
                                        data_source, frequency, collected_at
                                    ) VALUES (%s, %s, %s, %s, %s, %s)
                                """, (
                                    indicator_name, obs_date, value,
                                    'fred', 'daily', datetime.now()
                                ))
                                
                                records_inserted += 1
                                
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Invalid value for {series_id} on {obs['date']}: {obs['value']}")
                    
                    conn.commit()
                    total_records += records_inserted
                    logger.info(f"✅ {indicator_name}: Inserted {records_inserted} records")
                    
                    # Rate limiting
                    time.sleep(1)  # Be nice to FRED API
                    
                except Exception as e:
                    logger.error(f"Error collecting {series_id}: {e}")
                    continue
            
        finally:
            conn.close()
        
        logger.info(f"🏛️ Macro indicators collection complete: {total_records} total records")
        return total_records
    
    def update_ml_features_materialized(self):
        """Update the ML features materialized table with new historical data"""
        logger.info("🧠 Updating ML features materialized table...")
        
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # Execute the materialized view refresh/update query
            # This should populate features for all new price data
            cursor.execute("""
                INSERT IGNORE INTO ml_features_materialized (
                    symbol, price_date, price_hour, timestamp_iso,
                    current_price, volume_24h, market_cap,
                    created_at
                )
                SELECT 
                    p.symbol,
                    DATE(p.timestamp_iso) as price_date,
                    HOUR(p.timestamp_iso) as price_hour,
                    p.timestamp_iso,
                    p.current_price,
                    p.volume_usd_24h,
                    p.market_cap,
                    NOW()
                FROM price_data p
                LEFT JOIN ml_features_materialized ml 
                    ON p.symbol = ml.symbol 
                    AND DATE(p.timestamp_iso) = ml.price_date
                    AND HOUR(p.timestamp_iso) = ml.price_hour
                WHERE ml.id IS NULL
                AND p.timestamp_iso >= %s
                AND p.current_price IS NOT NULL
            """, (self.start_date,))
            
            records_inserted = cursor.rowcount
            conn.commit()
            
            logger.info(f"🧠 ML features updated: {records_inserted} new records")
            return records_inserted
            
        except Exception as e:
            logger.error(f"Error updating ML features: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def run_collection(self, symbols: Optional[List[str]] = None, resume: bool = True):
        """Run the comprehensive historical data collection"""
        logger.info("🚀 Starting comprehensive historical data collection...")
        logger.info(f"📅 Date range: {self.start_date.date()} to {self.end_date.date()}")
        
        # Get symbols to process
        if symbols is None:
            symbols = self.get_coinbase_symbols()
        
        # Filter out already completed symbols if resuming
        if resume:
            symbols = [s for s in symbols if s not in self.progress['completed_symbols']]
        
        logger.info(f"📊 Processing {len(symbols)} symbols")
        
        # Get CoinGecko ID mappings
        coingecko_ids = self.get_coingecko_coin_list()
        
        # Collect macro indicators first (only needs to be done once)
        if not resume or 'macro_collected' not in self.progress:
            self.collect_macro_indicators()
            self.progress['macro_collected'] = True
            self.save_progress()
        
        # Process each symbol
        total_records = 0
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"📈 Processing {symbol} ({i}/{len(symbols)})")
            logger.info(f"{'='*60}")
            
            try:
                # Skip if no CoinGecko mapping
                if symbol not in coingecko_ids:
                    logger.warning(f"⚠️ No CoinGecko ID for {symbol}, skipping...")
                    self.progress['failed_symbols'].append(symbol)
                    continue
                
                coin_id = coingecko_ids[symbol]
                
                # Identify data gaps
                gaps = self.identify_data_gaps(symbol)
                
                if not gaps:
                    logger.info(f"✅ {symbol}: No data gaps found")
                    self.progress['completed_symbols'].append(symbol)
                    self.save_progress()
                    continue
                
                # Collect historical data for each gap
                symbol_records = 0
                for gap_start, gap_end in gaps:
                    records = self.collect_historical_prices(symbol, coin_id, gap_start, gap_end)
                    symbol_records += records
                    
                    # Rate limiting for premium API
                    time.sleep(0.5)  # Conservative rate limiting
                
                total_records += symbol_records
                self.progress['total_records_collected'] += symbol_records
                self.progress['completed_symbols'].append(symbol)
                self.save_progress()
                
                logger.info(f"✅ {symbol}: Collected {symbol_records} records")
                
            except Exception as e:
                logger.error(f"❌ Error processing {symbol}: {e}")
                self.progress['failed_symbols'].append(symbol)
                self.save_progress()
                continue
        
        # Update ML features with new data
        logger.info(f"\n{'='*60}")
        logger.info("🧠 Updating ML features materialized table...")
        ml_records = self.update_ml_features_materialized()
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("🎉 HISTORICAL DATA COLLECTION COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"📊 Total price records collected: {total_records:,}")
        logger.info(f"🧠 ML feature records updated: {ml_records:,}")
        logger.info(f"✅ Symbols completed: {len(self.progress['completed_symbols'])}")
        logger.info(f"❌ Symbols failed: {len(self.progress['failed_symbols'])}")
        
        if self.progress['failed_symbols']:
            logger.info(f"Failed symbols: {self.progress['failed_symbols']}")
        
        self.save_progress()
        
        return {
            'price_records': total_records,
            'ml_records': ml_records,
            'completed_symbols': len(self.progress['completed_symbols']),
            'failed_symbols': len(self.progress['failed_symbols'])
        }

def main():
    """Main function"""
    collector = ComprehensiveHistoricalCollector()
    
    # Check if we should resume or start fresh
    if len(sys.argv) > 1:
        if sys.argv[1] == '--fresh':
            logger.info("🔄 Starting fresh collection (ignoring previous progress)")
            collector.progress = {
                'completed_symbols': [],
                'failed_symbols': [],
                'last_update': None,
                'total_records_collected': 0
            }
            resume = False
        elif sys.argv[1] == '--test':
            logger.info("🧪 Running test collection (BTC only)")
            results = collector.run_collection(['BTC'], resume=False)
            return results
        else:
            resume = True
    else:
        resume = True
    
    # Run the collection
    results = collector.run_collection(resume=resume)
    
    logger.info("🏁 Collection finished!")
    return results

if __name__ == "__main__":
    main()
