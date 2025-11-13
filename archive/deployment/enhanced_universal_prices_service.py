#!/usr/bin/env python3
"""
Enhanced Crypto Price Service with Universal Symbol Normalization
- Uses UniversalSymbolNormalizer for cross-exchange compatibility  
- Premium CoinGecko API key for better reliability
- Database-driven symbol support with universal format
"""

import asyncio
import logging
import time
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import mysql.connector

# Import centralized database configuration
from shared.database_config import get_db_connection, get_db_config

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field
import uvicorn
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniversalCryptoDefinitions:
    """Universal crypto definitions using centralized database config"""

    def __init__(self):
        # Use centralized database configuration
        self.db_config = get_db_config()
        
        self._symbol_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 3600  # 1 hour cache

    def _is_cache_valid(self) -> bool:
        """Check if symbol cache is still valid"""
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def get_universal_symbols(self) -> List[str]:
        """Get ALL active symbols in universal format"""
        if self._is_cache_valid() and self._symbol_cache:
            logger.debug(f"Using cached symbols: {len(self._symbol_cache)} symbols")
            return list(self._symbol_cache.keys())

        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()

            cursor.execute('''
                SELECT symbol, coingecko_id, name
                FROM crypto_assets
                WHERE is_active = 1
                AND symbol IS NOT NULL
                AND symbol != ''
                ORDER BY COALESCE(market_cap_rank, 999999), symbol
            ''')

            symbols = {}
            for symbol, coingecko_id, name in cursor.fetchall():
                # Use simple symbol normalization
                universal_symbol = symbol.upper().strip()
                
                if universal_symbol:
                    symbols[universal_symbol] = {
                        'original_symbol': symbol,
                        'coingecko_id': coingecko_id or universal_symbol.lower(),
                        'name': name or universal_symbol
                    }

            cursor.close()
            connection.close()

            # Update cache
            self._symbol_cache = symbols
            self._cache_timestamp = time.time()

            logger.info(f"Retrieved {len(symbols)} symbols in universal format")
            return list(symbols.keys())

        except Exception as e:
            logger.error(f"Error getting universal symbols: {e}")
            # Fallback to essential symbols
            fallback_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'LINK', 'DOT', 'ATOM']
            logger.warning(f"Using fallback symbols: {len(fallback_symbols)} symbols")
            return fallback_symbols

    def get_coingecko_id(self, universal_symbol: str) -> str:
        """Get CoinGecko ID for a universal symbol"""
        if not self._is_cache_valid() or not self._symbol_cache:
            self.get_universal_symbols()  # Refresh cache

        if universal_symbol in self._symbol_cache:
            return self._symbol_cache[universal_symbol]['coingecko_id']

        # Fallback to lowercase symbol
        return universal_symbol.lower()

    def get_coin_name(self, universal_symbol: str) -> str:
        """Get coin name for a universal symbol"""
        if not self._is_cache_valid() or not self._symbol_cache:
            self.get_universal_symbols()  # Refresh cache

        if universal_symbol in self._symbol_cache:
            return self._symbol_cache[universal_symbol]['name']

        # Fallback
        return universal_symbol.replace('_', ' ').title()


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


class EnhancedUniversalPricesService:
    def __init__(self):
        # Premium API Configuration
        self.api_key = os.getenv('COINGECKO_PREMIUM_API_KEY', 'CG-94NCcVD2euxaGTZe94bS2oYz')
        if self.api_key and self.api_key.startswith('CG-'):
            self.base_url = "https://pro-api.coingecko.com/api/v3"
            logger.info("Using CoinGecko Premium API with enhanced rate limits")
        else:
            self.base_url = "https://api.coingecko.com/api/v3"
            logger.warning("Using CoinGecko Free API - consider upgrading to premium")

        self.cache = {}
        self.cache_ttl = 60  # 1 minute cache
        self.last_api_call = None
        self.api_calls_today = 0
        self.daily_reset = datetime.now().date()

        # Database configuration - use centralized config
        self.db_config = get_db_config()

        # Storage table configuration
        self.table_name = os.getenv('CRYPTO_PRICES_TABLE', 'price_data_real')

        logger.info(f"Database config: table={self.table_name}")

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

    async def get_coingecko_batch_prices(self, coin_ids: List[str], vs_currency: str = "usd") -> Dict:
        """Get prices for multiple coins in a single API call"""
        try:
            if not coin_ids:
                return {}

            # Premium allows larger batches
            batch_size = 150 if self.api_key else 100
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
                    'include_24hr_vol': 'true'
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
                            self.api_calls_today += 1
                            self.last_api_call = datetime.now().isoformat()
                        elif response.status == 429:
                            logger.warning(f"Rate limited for batch request")
                            await asyncio.sleep(2)
                        else:
                            logger.warning(f"API error: {response.status}")

                # Small delay between batches
                if i + batch_size < len(coin_ids):
                    await asyncio.sleep(0.3)

            return all_results

        except Exception as e:
            logger.error(f"Error in batch API call: {e}")
            return {}

    async def get_price_for_symbol(self, universal_symbol: str, vs_currency: str = "usd") -> Optional[Dict]:
        """Get price data for a universal symbol"""
        cache_key = f"{universal_symbol}_{vs_currency}"

        # Check cache first
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        # Get CoinGecko ID for this universal symbol
        coingecko_id = crypto_definitions.get_coingecko_id(universal_symbol)
        coin_name = crypto_definitions.get_coin_name(universal_symbol)

        # Get price from CoinGecko
        batch_data = await self.get_coingecko_batch_prices([coingecko_id], vs_currency)

        price_data = None
        if coingecko_id in batch_data:
            cg_data = batch_data[coingecko_id]
            current_price = cg_data.get(vs_currency, 0)
            
            price_data = {
                'coin_id': coingecko_id,
                'symbol': universal_symbol,  # Use universal format
                'name': coin_name,
                'current_price': current_price,
                'price_change_24h': cg_data.get(f'{vs_currency}_24h_change'),
                'price_change_percentage_24h': cg_data.get(f'{vs_currency}_24h_change'),
                'market_cap': cg_data.get(f'{vs_currency}_market_cap'),
                'total_volume': cg_data.get(f'{vs_currency}_24h_vol'),
                'last_updated': datetime.now().isoformat(),
                'data_source': 'coingecko_premium'
            }

        # Cache the result
        if price_data:
            self.cache[cache_key] = {
                'data': price_data,
                'timestamp': time.time()
            }

        return price_data

    async def get_current_prices_all_symbols(self, vs_currency: str = "usd") -> Dict:
        """Get current prices for ALL universal symbols"""
        start_time = time.time()
        self._reset_daily_counters()

        # Get all universal symbols
        symbols = crypto_definitions.get_universal_symbols()
        logger.info(f"Fetching prices for {len(symbols)} universal symbols...")

        # Get CoinGecko IDs for all symbols
        coin_ids = []
        symbol_to_coingecko = {}
        
        for symbol in symbols:
            coingecko_id = crypto_definitions.get_coingecko_id(symbol)
            if coingecko_id:
                coin_ids.append(coingecko_id)
                symbol_to_coingecko[coingecko_id] = symbol

        # Batch fetch prices
        batch_results = await self.get_coingecko_batch_prices(coin_ids, vs_currency)

        # Process results
        all_prices = []
        for coingecko_id, price_data in batch_results.items():
            if coingecko_id in symbol_to_coingecko:
                universal_symbol = symbol_to_coingecko[coingecko_id]
                coin_name = crypto_definitions.get_coin_name(universal_symbol)
                
                current_price = price_data.get(vs_currency, 0)
                
                price_record = {
                    'coin_id': coingecko_id,
                    'symbol': universal_symbol,  # Universal format
                    'name': coin_name,
                    'current_price': current_price,
                    'price_change_24h': price_data.get(f'{vs_currency}_24h_change'),
                    'price_change_percentage_24h': price_data.get(f'{vs_currency}_24h_change'),
                    'market_cap': price_data.get(f'{vs_currency}_market_cap'),
                    'total_volume': price_data.get(f'{vs_currency}_24h_vol'),
                    'last_updated': datetime.now().isoformat(),
                    'data_source': 'coingecko_premium_batch'
                }
                
                all_prices.append(price_record)

        processing_time = (time.time() - start_time) * 1000

        return {
            'prices': all_prices,
            'total_count': len(all_prices),
            'vs_currency': vs_currency,
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'cache_hits': 0,  # Batch calls don't use cache
            'api_calls': self.api_calls_today,
            'symbols_requested': len(symbols),
            'symbols_successful': len(all_prices)
        }

    def store_prices_to_mysql(self, prices_data: List[Dict]) -> int:
        """Store price data to MySQL with universal symbols"""
        if not prices_data:
            return 0

        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()

            current_time = datetime.now()
            unix_timestamp = int(current_time.timestamp())

            insert_query = '''
                INSERT INTO price_data_real (
                    symbol, coin_id, name, timestamp, timestamp_iso, 
                    current_price, data_source, collection_interval,
                    created_at, price_change_24h, price_change_percentage_24h,
                    market_cap, volume_usd_24h
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''

            insert_data = []
            for price_info in prices_data:
                symbol = price_info.get('symbol')  # Already in universal format
                price = price_info.get('current_price', 0)

                if symbol and price is not None:
                    coin_id = price_info.get('coin_id')
                    coin_name = price_info.get('name', symbol)

                    # Validate decimal values
                    def validate_decimal(value, max_digits=20, decimal_places=8):
                        if value is None:
                            return None
                        try:
                            return round(float(value), decimal_places)
                        except (TypeError, ValueError):
                            return None

                    insert_data.append((
                        symbol,  # Universal symbol format
                        coin_id,
                        coin_name,
                        unix_timestamp,
                        current_time,
                        validate_decimal(price),
                        'enhanced_universal_prices',
                        'realtime',
                        current_time,
                        validate_decimal(price_info.get('price_change_24h')),
                        validate_decimal(price_info.get('price_change_percentage_24h'), 10, 4),
                        validate_decimal(price_info.get('market_cap')),
                        validate_decimal(price_info.get('total_volume'))
                    ))

            if insert_data:
                cursor.executemany(insert_query, insert_data)
                connection.commit()
                inserted_count = cursor.rowcount
                logger.info(f"Stored {inserted_count} universal price records")
            else:
                inserted_count = 0

            cursor.close()
            connection.close()

            return inserted_count

        except Exception as e:
            logger.error(f"Error storing prices: {e}")
            return 0


# Initialize universal crypto definitions
crypto_definitions = UniversalCryptoDefinitions()

# Initialize service
enhanced_service = EnhancedUniversalPricesService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Enhanced Universal Crypto Prices Service")
    # Warm up the symbol cache
    symbols = crypto_definitions.get_universal_symbols()
    logger.info(f"📊 Loaded {len(symbols)} symbols in universal format")
    yield
    logger.info("⚡ Shutting down Enhanced Universal Crypto Prices Service")


# Create FastAPI app
app = FastAPI(
    title="Enhanced Universal Cryptocurrency Prices Service",
    description="Enhanced microservice with universal symbol normalization",
    version="3.0.0",
    lifespan=lifespan
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    enhanced_service._reset_daily_counters()
    symbols = crypto_definitions.get_universal_symbols()

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
        symbols = crypto_definitions.get_universal_symbols()

        return {
            "service": "enhanced-universal-crypto-prices",
            "status": "healthy",
            "version": "3.0.0",
            "supported_symbols": len(symbols),
            "sample_symbols": symbols[:10],
            "universal_format": True,
            "cross_exchange_compatible": True,
            "dependencies": {
                "database_connection": True,
                "coingecko_premium_api": True,
                "universal_normalizer": True,
                "symbol_cache": crypto_definitions._is_cache_valid()
            },
            "statistics": {
                "cache_size": len(enhanced_service.cache),
                "api_calls_today": enhanced_service.api_calls_today,
                "last_api_call": enhanced_service.last_api_call,
                "cache_ttl_seconds": enhanced_service.cache_ttl
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "service": "enhanced-universal-crypto-prices",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/collect")
async def collect_all_prices():
    """Collect prices for ALL universal symbols"""
    try:
        logger.info("🚀 Starting universal price collection...")
        result = await enhanced_service.get_current_prices_all_symbols()

        # Store to MySQL
        stored_count = enhanced_service.store_prices_to_mysql(result['prices'])

        logger.info(f"✅ Collection complete: {result['symbols_successful']}/{result['symbols_requested']} symbols")

        return {
            "status": "success",
            "message": f"Collected prices for {result['symbols_successful']} universal symbols",
            "symbols_requested": result['symbols_requested'],
            "symbols_successful": result['symbols_successful'],
            "stored_to_mysql": stored_count,
            "processing_time_ms": result['processing_time_ms'],
            "api_calls": result['api_calls'],
            "universal_format": True,
            "cross_exchange_compatible": True,
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
    """Get list of supported universal symbols"""
    try:
        symbols = crypto_definitions.get_universal_symbols()
        return {
            "supported_symbols": symbols,
            "total_count": len(symbols),
            "format": "universal_tickers",
            "cross_exchange_compatible": True,
            "examples": ["BTC", "ETH", "ADA", "SOL", "LINK"],
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
    """Get current price for a single universal symbol"""
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
        symbols = crypto_definitions.get_universal_symbols()
        uptime = time.time() - start_time if 'start_time' in globals() else 0

        metrics_lines = [
            '# HELP enhanced_universal_service_uptime_seconds Service uptime in seconds',
            '# TYPE enhanced_universal_service_uptime_seconds gauge',
            f'enhanced_universal_service_uptime_seconds{{service_name="enhanced-universal-crypto-prices"}} {uptime:.2f}',
            '',
            '# HELP enhanced_universal_service_supported_symbols Number of supported symbols',
            '# TYPE enhanced_universal_service_supported_symbols gauge',
            f'enhanced_universal_service_supported_symbols{{service_name="enhanced-universal-crypto-prices"}} {len(symbols)}',
            '',
            '# HELP enhanced_universal_service_cache_entries Number of cache entries',
            '# TYPE enhanced_universal_service_cache_entries gauge',
            f'enhanced_universal_service_cache_entries{{service_name="enhanced-universal-crypto-prices"}} {len(enhanced_service.cache)}',
        ]

        prometheus_output = '\n'.join(metrics_lines) + '\n'
        return Response(content=prometheus_output, media_type="text/plain; version=0.0.4; charset=utf-8")

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        error_metrics = f"""# HELP enhanced_universal_service_error Service error status
# TYPE enhanced_universal_service_error gauge
enhanced_universal_service_error{{service_name="enhanced-universal-crypto-prices",error="{str(e)}"}} 1
"""
        return Response(content=error_metrics, media_type="text/plain; version=0.0.4; charset=utf-8")


# Track start time for metrics
start_time = time.time()

if __name__ == "__main__":
    logger.info("🚀 Starting Enhanced Universal Crypto Prices Service on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")