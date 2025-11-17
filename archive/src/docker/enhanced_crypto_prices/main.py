#!/usr/bin/env python3
"""
Enhanced Crypto Price Service with Database-Driven Symbol Support
Supports ALL Coinbase-compatible symbols from crypto_assets table
"""

import asyncio
import logging
import time
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager       
from pathlib import Path
import mysql.connector

# Import shared database pool
sys.path.append('/app/shared')
from shared.database_pool import get_connection_context, execute_query

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field
import uvicorn
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseCryptoDefinitions:
    """Database-driven crypto definitions"""     

    def __init__(self):
        # Database config removed - using shared connection pool
        pass
        self._symbol_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 3600  # 1 hour cache   

        # Fallback definitions for essential symbols (expanded for comprehensive coverage)
        self.fallback_coingecko_ids = {
            # Major cryptocurrencies by market cap
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'ADA': 'cardano', 'SOL': 'solana',
            'DOT': 'polkadot', 'LINK': 'chainlink', 'DOGE': 'dogecoin', 'XRP': 'ripple',
            'UNI': 'uniswap', 'AAVE': 'aave', 'ALGO': 'algorand', 'APT': 'aptos',
            'ARB': 'arbitrum', 'ATOM': 'cosmos', 'AVAX': 'avalanche-2', 'BNB': 'binancecoin',
            'COMP': 'compound-governance-token', 'CRV': 'curve-dao-token', 'FIL': 'filecoin',
            'ICP': 'internet-computer', 'LTC': 'litecoin', 'MATIC': 'polygon',
            'NEAR': 'near', 'OP': 'optimism', 'SHIB': 'shiba-inu', 'SUSHI': 'sushi',
            'YFI': 'yearn-finance', 'ZEC': 'zcash', 'BCH': 'bitcoin-cash', 'TRX': 'tron',
            'MKR': 'maker', 'BAL': 'balancer', 'SNX': 'synthetix', 'DASH': 'dash',
            'EOS': 'eos', 'XLM': 'stellar', 'XTZ': 'tezos', 'VET': 'vechain', 'XMR': 'monero',
            
            # Additional major tokens for comprehensive coverage
            'USDC': 'usd-coin', 'LDO': 'lido-dao', 'QNT': 'quant-network',
            'HBAR': 'hedera-hashgraph', 'GRT': 'the-graph', 'SAND': 'the-sandbox',
            'MANA': 'decentraland', 'FLOW': 'flow', 'CHZ': 'chiliz', 'EGLD': 'elrond-erd-2',
            'THETA': 'theta-token', 'FTM': 'fantom', 'AXS': 'axie-infinity', 'ENJ': 'enjincoin',
            'ROSE': 'oasis-network', 'KSM': 'kusama', 'ONE': 'harmony', 'CELO': 'celo',
            
            # DeFi ecosystem tokens
            'REN': 'republic-protocol', 'BADGER': 'badger-dao', 'ALPHA': 'alpha-finance',
            'RUNE': 'thorchain', 'KAVA': 'kava', 'SRM': 'serum', 'RAY': 'raydium',
            'PERP': 'perpetual-protocol', 'DPI': 'defipulse-index', 'OHM': 'olympus',
            
            # Gaming/NFT tokens
            'GALA': 'gala', 'IMX': 'immutable-x', 'LRC': 'loopring', 'ENS': 'ethereum-name-service',
            'APE': 'apecoin', 'GMT': 'stepn', 'BLUR': 'blur',
            
            # AI/ML tokens
            'FET': 'fetch-ai', 'OCEAN': 'ocean-protocol', 'AGIX': 'singularitynet',
            'RLC': 'iexec-rlc', 'NMR': 'numeraire',
            
            # Infrastructure tokens
            'BAT': 'basic-attention-token', 'ZRX': '0x', 'REP': 'augur', 'BNT': 'bancor',
            'KNC': 'kyber-network-crystal', 'ANT': 'aragon', 'STORJ': 'storj',
            'CVC': 'civic', 'DNT': 'district0x', 'MTL': 'metal', 'AMP': 'amp-token',
            'BAND': 'band-protocol', 'ORN': 'orion-protocol', 'CTSI': 'cartesi',
            'SKALE': 'skale', 'CELR': 'celer-network',
            
            # Legacy but important
            'ZEN': 'horizen', 'IOST': 'iost', 'ZIL': 'zilliqa', 'ICX': 'icon',
            'QTUM': 'qtum', 'ONT': 'ontology', 'IOTA': 'iota', 'NANO': 'nano',
            'DCR': 'decred', 'XEM': 'nem', 'WAVES': 'waves', 'LSK': 'lisk',
            'DGB': 'digibyte', 'SIA': 'siacoin', 'GAS': 'gas', 'NEO': 'neo',
            'MONA': 'monacoin', 'BTG': 'bitcoin-gold', 'ETC': 'ethereum-classic'
        }

    def _is_cache_valid(self) -> bool:
        """Check if symbol cache is still valid"""
        return (time.time() - self._cache_timestamp) < self._cache_ttl
                            
    def get_coinbase_symbols(self) -> List[str]: 
        """Get ALL Coinbase-supported symbols from database"""
        if self._is_cache_valid() and self._symbol_cache:
            logger.debug(f"Using cached symbols: {len(self._symbol_cache)} symbols")
            return list(self._symbol_cache.keys())
                                                
        try:
            with get_connection_context() as db:
                cursor = db.cursor()

                cursor.execute('''
                    SELECT symbol, coingecko_id, name
                    FROM crypto_assets
                    WHERE coinbase_supported = 1     
                    AND symbol NOT LIKE '%-%'  -- Skip USD pairs
                    AND symbol IS NOT NULL
                    AND symbol != ''
                    ORDER BY symbol
                ''')

                symbols = {}
                for symbol, coingecko_id, name in cursor.fetchall():
                    symbols[symbol] = {
                        'coingecko_id': coingecko_id or self.fallback_coingecko_ids.get(symbol, symbol.lower()),
                        'name': name or symbol       
                    }

                cursor.close()

            # Update cache
            self._symbol_cache = symbols
            self._cache_timestamp = time.time()  

            logger.info(f"Retrieved {len(symbols)} Coinbase-supported symbols from database")
            return list(symbols.keys())

        except Exception as e:
            logger.error(f"Error getting Coinbase symbols from database: {e}")
            # Fallback to essential symbols      
            fallback_symbols = list(self.fallback_coingecko_ids.keys())
            logger.warning(f"Using fallback symbols: {len(fallback_symbols)} symbols")
            return fallback_symbols

    def get_coingecko_id(self, symbol: str) -> str:
        """Get CoinGecko ID for a symbol"""      
        if not self._is_cache_valid() or not self._symbol_cache:
            self.get_coinbase_symbols()  # Refresh cache
                                          
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]['coingecko_id']
                                     
        # Fallback
        return self.fallback_coingecko_ids.get(symbol, symbol.lower())
                            
    def get_coin_name(self, symbol: str) -> str: 
        """Get coin name for a symbol"""
        if not self._is_cache_valid() or not self._symbol_cache:
            self.get_coinbase_symbols()  # Refresh cache
                                          
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]['name']
                                             
        # Fallback
        return symbol.replace('_', ' ').title()  

    def get_all_coingecko_ids(self) -> List[str]:
        """Get all CoinGecko IDs"""
        symbols = self.get_coinbase_symbols()    
        return [self.get_coingecko_id(symbol) for symbol in symbols]
                              
# Initialize database-driven crypto definitions  
crypto_definitions = DatabaseCryptoDefinitions() 

# Response Models
class PriceResponse(BaseModel):
    coin_id: str
    symbol: str
    name: str
    current_price: float
    price_change_24h: Optional[float] = None     
    price_change_percentage_24h: Optional[float] = None
    market_cap: Optional[float] = None
    last_updated: str

class MultiPriceResponse(BaseModel):
    prices: List[PriceResponse]
    total_count: int
    vs_currency: str
    timestamp: str
    processing_time_ms: float
    cache_hits: int
    api_calls: int

class HealthResponse(BaseModel):
    status: str
    cache_entries: int
    last_api_call: Optional[str]
    api_calls_today: int
    supported_symbols: int
    timestamp: str

class EnhancedCryptoPricesService:
    def __init__(self):
        # API Configuration with premium key support
        self.api_key = os.getenv('COINGECKO_API_KEY', '')
        if self.api_key:
            # Use premium endpoints for higher rate limits
            self.base_url = "https://pro-api.coingecko.com/api/v3"
            logger.info("Using CoinGecko Premium API with enhanced rate limits")
        else:
            self.base_url = "https://api.coingecko.com/api/v3"
            logger.warning("Using CoinGecko Free API - consider upgrading to premium for better reliability")
            
        self.coinbase_base_url = "https://api.coinbase.com/v2"
        self.cache = {}
        self.cache_ttl = 60  # 1 minute cache    
        self.last_api_call = None
        self.api_calls_today = 0
        self.daily_reset = datetime.now().date() 

        # MySQL storage removed - using shared connection pool
        # Table and column configuration from environment
        self.table_name = os.getenv('CRYPTO_PRICES_TABLE', 'price_data')
        self.high_column = os.getenv('HIGH_COLUMN', 'high_24h')
        self.low_column = os.getenv('LOW_COLUMN', 'low_24h')
        self.open_column = os.getenv('OPEN_COLUMN', 'open_24h')
        self.volume_column = os.getenv('VOLUME_COLUMN', 'volume_usd_24h')
        
        logger.info(f"Database config: table={self.table_name}, high={self.high_column}, low={self.low_column}, open={self.open_column}, volume={self.volume_column}")

    def _is_cache_valid(self, key: str) -> bool: 
        """Check if cache entry is still valid"""
        if key not in self.cache:
            return False

        entry_time = self.cache[key].get('timestamp', 0)
        return (time.time() - entry_time) < self.cache_ttl
                                        
    def _reset_daily_counters(self):
        """Reset daily API call counter if needed"""
        today = datetime.now().date()
        if today != self.daily_reset:
            self.api_calls_today = 0
            self.daily_reset = today

    async def get_current_price_coinbase(self, symbol: str) -> Optional[float]:
        """Get current price from Coinbase API"""
        try:
            url = f"{self.coinbase_base_url}/exchange-rates?currency={symbol}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:   
                        data = await response.json()
                        price = float(data['data']['rates']['USD'])
                        return price
                    elif response.status == 404: 
                        # Symbol not supported by Coinbase
                        return None
                    else:
                        logger.warning(f"Coinbase API error for {symbol}: {response.status}")
                        return None
        except Exception as e:
            logger.debug(f"Coinbase API failed for {symbol}: {e}")
            return None

    async def get_coingecko_batch_prices(self, coin_ids: List[str], vs_currency: str = "usd") -> Dict:
        """Get prices for multiple coins in a single API call - more efficient"""
        try:
            if not coin_ids:
                return {}
                
            # CoinGecko allows up to 250 coin IDs per request
            batch_size = 100  # Conservative batch size to avoid rate limits
            all_results = {}
            
            for i in range(0, len(coin_ids), batch_size):
                batch_ids = coin_ids[i:i + batch_size]
                ids_string = ','.join(batch_ids)
                
                url = f"{self.base_url}/simple/price"
                params = {
                    'ids': ids_string,
                    'vs_currencies': vs_currency,
                    'include_24hr_change': 'true',
                    'include_market_cap': 'true',
                    'include_24hr_vol': 'true',
                    'include_24hr_high': 'true',
                    'include_24hr_low': 'true'
                }
                
                # Add premium API key headers if available
                headers = {}
                if self.api_key:
                    headers['x-cg-pro-api-key'] = self.api_key

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers, timeout=30) as response:
                        if response.status == 200:
                            batch_data = await response.json()
                            all_results.update(batch_data)
                            logger.debug(f"Batch API success for {len(batch_ids)} coins")
                        elif response.status == 429:
                            logger.warning(f"CoinGecko rate limited for batch request")
                            await asyncio.sleep(2)  # Back off for rate limiting
                        elif response.status == 401:
                            logger.warning(f"CoinGecko authentication error for batch: {await response.text()}")
                        else:
                            logger.warning(f"CoinGecko batch API error: {response.status}")
                
                # Small delay between batches to respect rate limits
                if i + batch_size < len(coin_ids):
                    await asyncio.sleep(0.5)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error in batch CoinGecko API call: {e}")
            return {}

    async def get_coingecko_price(self, coin_id: str, vs_currency: str = "usd") -> Optional[Dict]:
        """Get comprehensive price data including OHLC from CoinGecko API - LEGACY single call"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': vs_currency,
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_high': 'true',
                'include_24hr_low': 'true'
            }
            
            # Add premium API key headers if available
            headers = {}
            if self.api_key:
                headers['x-cg-pro-api-key'] = self.api_key

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=15) as response:
                    if response.status == 200:   
                        data = await response.json()
                        if coin_id in data:      
                            self.api_calls_today += 1
                            self.last_api_call = datetime.now().isoformat()
                            return data[coin_id] 
                    elif response.status == 429: 
                        logger.warning(f"CoinGecko rate limited for {coin_id}")
                        await asyncio.sleep(2)  # Wait before retry
                        return None
                    else:
                        logger.warning(f"CoinGecko API error for {coin_id}: {response.status}")
                        return None
        except Exception as e:
            logger.debug(f"CoinGecko API failed for {coin_id}: {e}")
            return None

    async def get_price_for_symbol(self, symbol: str, vs_currency: str = "usd") -> Optional[Dict]:
        """Get price data for a specific symbol using multiple sources"""
        cache_key = f"{symbol}_{vs_currency}"    

        # Check cache first
        if self._is_cache_valid(cache_key):      
            return self.cache[cache_key]['data'] 

        # Get CoinGecko ID for this symbol       
        coingecko_id = crypto_definitions.get_coingecko_id(symbol)
        coin_name = crypto_definitions.get_coin_name(symbol)
                                      
        price_data = None

        # Try CoinGecko first
        if coingecko_id:
            cg_data = await self.get_coingecko_price(coingecko_id, vs_currency)
            if cg_data:
                current_price = cg_data.get(vs_currency, 0)
                price_data = {
                    'coin_id': coingecko_id,
                    'symbol': symbol,
                    'name': coin_name,
                    'current_price': current_price,
                    'price_change_24h': cg_data.get(
                        f'{vs_currency}_24h_change'),
                    'price_change_percentage_24h': cg_data.get(
                        f'{vs_currency}_24h_change'),
                    'market_cap': cg_data.get(f'{vs_currency}_market_cap'),
                    'total_volume': cg_data.get(f'{vs_currency}_24h_vol'),
                    'high_24h': cg_data.get(
                        f'{vs_currency}_24h_high', current_price),
                    'low_24h': cg_data.get(
                        f'{vs_currency}_24h_low', current_price),
                    'open_24h': current_price,  # Estimate open
                    'last_updated': datetime.now().isoformat(),
                    'data_source': 'coingecko'
                }

        # Fallback to Coinbase if CoinGecko fails
        if not price_data:
            coinbase_price = await self.get_current_price_coinbase(symbol)
            if coinbase_price:
                price_data = {
                    'coin_id': coingecko_id or symbol.lower(),
                    'symbol': symbol,
                    'name': coin_name,
                    'current_price': coinbase_price,
                    'price_change_24h': None,    
                    'price_change_percentage_24h': None,
                    'market_cap': None,
                    'last_updated': datetime.now().isoformat(),
                    'data_source': 'coinbase'    
                }

        # Cache the result
        if price_data:
            self.cache[cache_key] = {
                'data': price_data,
                'timestamp': time.time()
            }

        return price_data

    async def get_current_prices_all_symbols(self, vs_currency: str = "usd") -> Dict:
        """Get current prices for ALL Coinbase-supported symbols"""
        start_time = time.time()
        self._reset_daily_counters()

        # Get all symbols from database
        symbols = crypto_definitions.get_coinbase_symbols()
        logger.info(f"Fetching prices for {len(symbols)} symbols...")
                             
        # Process symbols in batches to avoid overwhelming APIs
        batch_size = 25
        all_prices = []
        cache_hits = 0
        api_calls = 0

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]    
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size}: {batch[:5]}...")
                     
            # Process batch concurrently but with rate limiting
            batch_tasks = []
            for symbol in batch:
                batch_tasks.append(self.get_price_for_symbol(symbol, vs_currency))
                
            # Execute batch with small delay between batches
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.warning(f"Error in batch processing: {result}")
                    continue

                if result:
                    all_prices.append(result)    
                    if result.get('data_source') == 'cache':
                        cache_hits += 1
                    else:
                        api_calls += 1

            # Rate limiting between batches      
            if i + batch_size < len(symbols):    
                await asyncio.sleep(1)  # 1 second between batches
                
        processing_time = (time.time() - start_time) * 1000
                                       
        logger.info(f"Collected prices for {len(all_prices)}/{len(symbols)} symbols")
             
        return {
            'prices': all_prices,
            'total_count': len(all_prices),      
            'vs_currency': vs_currency,
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'cache_hits': cache_hits,
            'api_calls': api_calls,
            'symbols_requested': len(symbols),   
            'symbols_successful': len(all_prices)
        }

    def _validate_decimal_value(self, value, max_digits=20, decimal_places=8):
        """Validate and round decimal values to fit MySQL decimal(20,8) format"""
        if value is None:
            return None
        
        try:
            # Convert to float if it's not already
            float_value = float(value)
            
            # Check for infinity and NaN values (fixed logic)
            import math
            if math.isnan(float_value) or math.isinf(float_value):
                logger.warning(f"Invalid decimal value {value} (inf/nan), setting to None")
                return None
            
            # Round to the specified decimal places
            rounded_value = round(float_value, decimal_places)
            
            # Check if the rounded value fits in the decimal format
            # decimal(20,8) can handle up to 12 integer digits + 8 decimal places
            max_value = 10**(max_digits - decimal_places) - 1
            min_value = -max_value
            
            if min_value <= rounded_value <= max_value:
                logger.debug(f"Validated decimal value {value} -> {rounded_value}")
                return rounded_value
            else:
                # Value too large, cap it at the maximum
                capped_value = max_value if rounded_value > 0 else min_value
                logger.warning(f"Value {value} exceeds decimal({max_digits},{decimal_places}) range, capping at {capped_value}")
                return capped_value
                
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not convert value {value} to decimal: {e}")
            return None
                                        
    def store_prices_to_mysql(self, prices_data: List[Dict]) -> int:
        """Store price data to MySQL price_data_real table"""
        if not prices_data:
            return 0

        try:
            with get_connection_context() as db:
                cursor = db.cursor()

                current_time = datetime.now()
                unix_timestamp = int(current_time.timestamp())
                
                # Insert into price_data_real table with simplified query for debugging
                insert_query = '''
                INSERT INTO price_data_real (
                    symbol, coin_id, name, timestamp, timestamp_iso, 
                    current_price, data_source, collection_interval,
                    created_at, price_change_24h, price_change_percentage_24h,
                    market_cap, volume_usd_24h, high_24h, low_24h, open_24h
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''

                insert_data = []
                for price_info in prices_data:
                    price = price_info.get('current_price', 0)
                    symbol = price_info.get('symbol')
                    
                    # Debug logging for price validation
                    logger.debug(f"Processing {symbol}: raw_price={price}, type={type(price)}")
                    
                    if symbol and price is not None:  # Allow 0 prices, just not None
                        # Get coin_id from our definitions
                        coin_id = crypto_definitions.get_coingecko_id(symbol)
                        coin_name = crypto_definitions.get_coin_name(symbol)
                        
                        # Handle large market cap values
                        market_cap = price_info.get('market_cap')
                        if market_cap and market_cap > 999999999999999999:
                            market_cap = 999999999999999999  # Cap for DECIMAL(25,2)
                        
                        # Validate decimal values to prevent truncation errors
                        price_change_24h = self._validate_decimal_value(
                            price_info.get('price_change_24h'))
                        price_change_percentage_24h = self._validate_decimal_value(
                            price_info.get('price_change_percentage_24h'), 10, 4)  # decimal(10,4)
                        current_price_validated = self._validate_decimal_value(
                            price, 20, 8)
                        high_24h_validated = self._validate_decimal_value(
                            price_info.get('high_24h', price), 20, 8)
                        low_24h_validated = self._validate_decimal_value(
                            price_info.get('low_24h', price), 20, 8)
                        open_24h_validated = self._validate_decimal_value(
                            price_info.get('open_24h', price), 20, 8)
                        
                        # Debug the validated price
                        logger.info(f"{symbol}: validated_price={current_price_validated}, market_cap={market_cap}")
                        
                        insert_data.append((
                            symbol,
                            coin_id,
                            coin_name,
                            unix_timestamp,
                            current_time,
                            current_price_validated,
                            'enhanced_crypto_prices',
                            'realtime',
                            current_time,
                            price_change_24h,
                            price_change_percentage_24h,
                            market_cap,
                            price_info.get('total_volume', 0),
                            high_24h_validated,
                            low_24h_validated,
                            open_24h_validated
                        ))
                    else:
                        logger.warning(f"Skipping {symbol}: price={price} (type={type(price)})")

                if insert_data:
                    try:
                        logger.info(f"Attempting to insert {len(insert_data)} records")
                        # Log first record for debugging
                        if insert_data:
                            first_record = insert_data[0]
                            logger.info(f"Sample record: symbol={first_record[0]}, price={first_record[5]}, type={type(first_record[5])}")
                        
                        cursor.executemany(insert_query, insert_data)
                        db.commit()
                        inserted_count = cursor.rowcount
                        logger.info(f"Successfully stored {inserted_count} records to price_data_real")
                    except Exception as e:
                        logger.error(f"Error executing insert query: {e}")
                        logger.error(f"Query: {insert_query}")
                        if insert_data:
                            logger.error(f"Sample data: {insert_data[0]}")
                        raise e
                else:
                    inserted_count = 0

                cursor.close()

                return inserted_count

        except Exception as e:
            logger.error(f"Error storing prices to MySQL: {e}")
            return 0

# Initialize service
enhanced_service = EnhancedCryptoPricesService() 

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""        
    logger.info("🚀 Starting Enhanced Crypto Prices Service")
    # Warm up the symbol cache
    symbols = crypto_definitions.get_coinbase_symbols()
    logger.info(f"📊 Loaded {len(symbols)} Coinbase-supported symbols")
    yield
    logger.info("⚡ Shutting down Enhanced Crypto Prices Service")

# Create FastAPI app
app = FastAPI(
    title="Enhanced Cryptocurrency Prices Service",
    description="Enhanced microservice supporting ALL Coinbase-compatible symbols",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    enhanced_service._reset_daily_counters()     
    symbols = crypto_definitions.get_coinbase_symbols()
                                           
    return HealthResponse(
        status="healthy",
        cache_entries=len(enhanced_service.cache),
        last_api_call=enhanced_service.last_api_call,
        api_calls_today=enhanced_service.api_calls_today,
        supported_symbols=len(symbols),
        timestamp=datetime.now().isoformat()     
    )

@app.get("/status")
async def get_status():
    """Get service status and statistics"""      
    try:
        enhanced_service._reset_daily_counters() 
        symbols = crypto_definitions.get_coinbase_symbols()
                                       
        return {
            "service": "enhanced-crypto-prices", 
            "status": "healthy",
            "version": "2.0.0",
            "supported_symbols": len(symbols),   
            "sample_symbols": symbols[:10],      
            "dependencies": {
                "database_connection": True,     
                "coingecko_api": True,
                "coinbase_api": True,
                "symbol_cache": crypto_definitions._is_cache_valid()
            },
            "statistics": {
                "cache_size": len(enhanced_service.cache),
                "api_calls_today": enhanced_service.api_calls_today,
                "last_api_call": enhanced_service.last_api_call,
                "cache_ttl_seconds": enhanced_service.cache_ttl
            },
            "database_config": {
                "table": enhanced_service.table_name,
                "high_column": enhanced_service.high_column,
                "low_column": enhanced_service.low_column,
                "open_column": enhanced_service.open_column,
                "volume_column": enhanced_service.volume_column
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "service": "enhanced-crypto-prices", 
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/collect")
async def collect_all_prices():
    """Collect prices for ALL Coinbase-supported symbols"""
    try:
        logger.info("🚀 Starting comprehensive price collection...")
        result = await enhanced_service.get_current_prices_all_symbols()
                          
        # Store to MySQL
        stored_count = enhanced_service.store_prices_to_mysql(result['prices'])
                   
        logger.info(f"✅ Collection complete: {result['symbols_successful']}/{result['symbols_requested']} symbols")
                
        return {
            "status": "success",
            "message": f"Collected prices for {result['symbols_successful']} symbols",
            "symbols_requested": result['symbols_requested'],
            "symbols_successful": result['symbols_successful'],
            "stored_to_mysql": stored_count,     
            "processing_time_ms": result['processing_time_ms'],
            "cache_hits": result['cache_hits'],  
            "api_calls": result['api_calls'],    
            "coverage_percentage": (result['symbols_successful'] / result['symbols_requested']) * 100 if result['symbols_requested'] > 0 else 0,   
            "timestamp": result['timestamp']     
        }

    except Exception as e:
        logger.error(f"Error in collect endpoint: {e}")
        return {
            "status": "error",
            "message": f"Collection failed: {str(e)}",
            "symbols_collected": 0,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/symbols")
async def get_supported_symbols():
    """Get list of supported symbols"""
    try:
        symbols = crypto_definitions.get_coinbase_symbols()
        return {
            "supported_symbols": symbols,        
            "total_count": len(symbols),
            "source": "database",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/price/{symbol}")
async def get_single_price(symbol: str, vs_currency: str = "usd"):
    """Get current price for a single symbol"""  
    try:
        symbol = symbol.upper()
        price_data = await enhanced_service.get_price_for_symbol(symbol, vs_currency)
             
        if not price_data:
            raise HTTPException(status_code=404, detail=f"Price data not found for {symbol}")

        return PriceResponse(**price_data)       

    except Exception as e:
        logger.error(f"Error getting single price for {symbol}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error fetching price: {str(e)}")
            
@app.get("/metrics")
async def get_metrics():
    """Get service metrics in Prometheus format"""
    try:
        enhanced_service._reset_daily_counters() 
        symbols = crypto_definitions.get_coinbase_symbols()
        uptime = time.time() - start_time if 'start_time' in globals() else 0
                     
        metrics_lines = [
            '# HELP enhanced_crypto_service_uptime_seconds Service uptime in seconds',
            '# TYPE enhanced_crypto_service_uptime_seconds gauge',
            f'enhanced_crypto_service_uptime_seconds{{service_name="enhanced-crypto-prices"}} {uptime:.2f}',
            '',
            '# HELP enhanced_crypto_service_supported_symbols Number of supported symbols',
            '# TYPE enhanced_crypto_service_supported_symbols gauge',
            f'enhanced_crypto_service_supported_symbols{{service_name="enhanced-crypto-prices"}} {len(symbols)}',
            '',
            '# HELP enhanced_crypto_service_cache_entries Number of cache entries',
            '# TYPE enhanced_crypto_service_cache_entries gauge',
            f'enhanced_crypto_service_cache_entries{{service_name="enhanced-crypto-prices"}} {len(enhanced_service.cache)}',
            '',
            '# HELP enhanced_crypto_service_api_calls_total Total API calls today',
            '# TYPE enhanced_crypto_service_api_calls_total counter',
            f'enhanced_crypto_service_api_calls_total{{service_name="enhanced-crypto-prices"}} {enhanced_service.api_calls_today}',
        ]

        prometheus_output = '\n'.join(metrics_lines) + '\n'
        return Response(content=prometheus_output, media_type="text/plain; version=0.0.4; charset=utf-8")
                          
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        error_metrics = f"""# HELP enhanced_crypto_service_error Service error status             
# TYPE enhanced_crypto_service_error gauge       
enhanced_crypto_service_error{{service_name="enhanced-crypto-prices",error="{str(e)}"}} 1         
"""
        return Response(content=error_metrics, media_type="text/plain; version=0.0.4; charset=utf-8")
                              
# Track start time for metrics
start_time = time.time()

if __name__ == "__main__":
    logger.info("🚀 Starting Enhanced Crypto Prices Service on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")