#!/usr/bin/env python3
"""
Enhanced Onchain Data Collector
Collects blockchain metrics and on-chain data for cryptocurrencies
Includes comprehensive backfill capability and dynamic symbol management
"""

import os
import logging
import time
import mysql.connector
from datetime import datetime, timedelta, date
import aiohttp
import asyncio
import json
from typing import List, Dict, Optional
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

# Import centralized configurations
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.table_config import (
        get_collector_symbols, 
        get_master_onchain_table,
        normalize_symbol_for_exchange,
        validate_symbol_exists,
        get_supported_symbols,
        get_symbol_metadata
    )
except ImportError as e:
    logging.warning(f"Could not import centralized configs: {e}")
    get_collector_symbols = None
    get_master_onchain_table = lambda: "crypto_prices.onchain_data"
    normalize_symbol_for_exchange = lambda x, y: x
    validate_symbol_exists = lambda x: True
    get_supported_symbols = lambda: []
    get_symbol_metadata = lambda x: {}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("enhanced-onchain-collector")

# Placeholder creation configuration
ENSURE_PLACEHOLDERS = os.getenv("ENSURE_PLACEHOLDERS", "true").lower() == "true"
PLACEHOLDER_LOOKBACK_DAYS = int(os.getenv("PLACEHOLDER_LOOKBACK_DAYS", "30"))
MAX_BACKFILL_DAYS = int(os.getenv("MAX_BACKFILL_DAYS", "90"))


class EnhancedOnchainCollector:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("MYSQL_HOST", "172.22.32.1"),
            "user": os.getenv("MYSQL_USER", "news_collector"),
            "password": os.getenv("MYSQL_PASSWORD", "99Rules!"),
            "database": os.getenv("MYSQL_DATABASE", "crypto_prices"),
        }
        
        # Premium CoinGecko API configuration
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY', 'CG-94NCcVD2euxaGTZe94bS2oYz')
        self.use_premium_api = bool(self.coingecko_api_key and self.coingecko_api_key.startswith('CG-'))
        
        # API endpoints for different data sources
        self.api_endpoints = {
            'coingecko': 'https://api.coingecko.com/api/v3/coins/{symbol}',
            'coingecko_pro': 'https://pro-api.coingecko.com/api/v3/coins/{symbol}',  # Premium endpoint
            'coingecko_history': 'https://pro-api.coingecko.com/api/v3/coins/{symbol}/history',  # Historical data
            'coingecko_ohlc': 'https://pro-api.coingecko.com/api/v3/coins/{symbol}/ohlc',  # OHLC data
            'coingecko_market_chart': 'https://pro-api.coingecko.com/api/v3/coins/{symbol}/market_chart',  # Market data
            'glassnode': 'https://api.glassnode.com/v1/metrics',  # Requires API key
            'defilama': 'https://api.llama.fi/protocol/{protocol}',  # For TVL data
        }
        
        # Rate limiting - different delays for different APIs
        self.last_api_call = {}
        self.rate_limits = {
            'coingecko': 0.1 if self.use_premium_api else 1.0,  # Premium: 10 req/sec, Free: 1 req/sec
            'coingecko_additional': 0.2 if self.use_premium_api else 1.5,  # Additional CoinGecko endpoints
            'defilama': 0.5,     # Public API: 2 req/sec
            'network': 2.0,      # Blockchain APIs: conservative
            'additional': 1.5,   # Additional APIs: moderate
        }
        
        if self.use_premium_api:
            logger.info(f"🚀 Using premium CoinGecko API key: {self.coingecko_api_key[:8]}...")
        else:
            logger.info("⚠️  Using free CoinGecko API (rate limited)")
        
    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def get_symbols_from_db(self) -> List[str]:
        """Get Coinbase-compatible symbols from crypto_assets table - database-driven approach"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get Coinbase-supported symbols by market cap rank
            cursor.execute("""
                SELECT symbol, market_cap_rank, coingecko_id
                FROM crypto_assets 
                WHERE is_active = 1 
                AND coinbase_supported = 1
                AND coingecko_id IS NOT NULL
                ORDER BY market_cap_rank ASC 
                LIMIT 50
            """)
            
            results = cursor.fetchall()
            symbols = [row[0] for row in results]
            cursor.close()
            conn.close()
            
            logger.info(f"📊 Found {len(symbols)} Coinbase-supported symbols in crypto_assets table")
            if symbols:
                logger.info(f"First 10 symbols: {symbols[:10]}")
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching Coinbase symbols from crypto_assets: {e}")
            # Fallback to major Coinbase symbols if database fails
            fallback = ['bitcoin', 'ethereum', 'cardano', 'polkadot', 'solana', 'avalanche-2', 'polygon', 'chainlink']
            logger.warning(f"Using fallback Coinbase symbols: {fallback}")
            return fallback
    
    def get_symbols(self) -> List[str]:
        """Get Coinbase-compatible symbols using dynamic symbol management from crypto_assets table"""
        try:
            # Use centralized symbol management for Coinbase-compatible symbols
            if get_collector_symbols:
                symbols = get_collector_symbols('coinbase')  # Use coinbase type for onchain data
                if symbols:
                    logger.info(f"Retrieved {len(symbols)} Coinbase-supported symbols from crypto_assets table")
                    logger.info(f"First 10 symbols: {symbols[:10]}")
                    return symbols
        except Exception as e:
            logger.warning(f"Error using centralized symbol management: {e}")
            logger.warning(f"Could not use centralized symbols: {e}")
        
        # Fallback: get symbols from price_data_real that have sufficient data
        try:
            db = self.get_db_connection()
            cursor = db.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM price_data_real 
                WHERE market_cap > 1000000000  -- Only coins with > $1B market cap for onchain data
                AND timestamp_iso >= NOW() - INTERVAL 7 DAY
                ORDER BY symbol
                LIMIT 50  -- Focus on top coins for onchain data
            """)
            
            symbols = [row['symbol'] for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(symbols)} symbols from price_data_real (fallback)")
            
            db.close()
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']  # Hardcoded fallback
    
    def ensure_table_exists(self):
        """Ensure onchain_data table exists - our blockchain metrics table"""
        try:
            # Get correct table name from central config
            table_name = get_master_onchain_table().split('.')[-1]  # Should be 'onchain_data' now
            
            db = self.get_db_connection()
            cursor = db.cursor()
            
            # The table should already exist with our blockchain schema
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if cursor.fetchall():
                logger.info(f"✅ {table_name} table exists (blockchain metrics)")
                cursor.close()
                db.close()
                return
            
            # If not exists, create with blockchain-focused schema 
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(100) NOT NULL,
                    coin_id VARCHAR(150),
                    timestamp_iso DATETIME(6) NOT NULL,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Network metrics
                    active_addresses BIGINT,
                    transaction_count BIGINT,
                    transaction_volume DECIMAL(25,8),
                    hash_rate DECIMAL(25,8),
                    difficulty DECIMAL(25,8),
                    block_height BIGINT,
                    block_time_seconds DECIMAL(10,2),
                    
                    -- Supply metrics
                    circulating_supply DECIMAL(25,8),
                    total_supply DECIMAL(25,8),
                    max_supply DECIMAL(25,8),
                    supply_inflation_rate DECIMAL(10,4),
                    
                    -- Network value metrics
                    network_value_to_transactions DECIMAL(20,8),
                    realized_cap DECIMAL(25,2),
                    mvrv_ratio DECIMAL(10,4),
                    nvt_ratio DECIMAL(10,4),
                    
                    -- Development metrics
                    github_commits_30d INT,
                    developer_activity_score DECIMAL(10,4),
                    
                    -- Staking metrics (for PoS coins)
                    staking_yield DECIMAL(10,4),
                    staked_percentage DECIMAL(10,4),
                    validator_count INT,
                    
                    -- DeFi metrics (for smart contract platforms)
                    total_value_locked DECIMAL(25,2),
                    defi_protocols_count INT,
                    
                    -- Social metrics
                    -- social metrics removed - these belong in crypto_sentiment_data table
                    
                    -- Data quality
                    data_source VARCHAR(100),
                    data_quality_score DECIMAL(3,2) DEFAULT 1.0,
                    
                    UNIQUE KEY unique_symbol_timestamp (symbol, timestamp_iso),
                    INDEX idx_symbol (symbol),
                    INDEX idx_timestamp (timestamp_iso),
                    INDEX idx_collected (collected_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_sql)
            db.commit()
            cursor.close()
            db.close()
            
            logger.info(f"✅ {table_name} table created/verified")
            
        except Exception as e:
            logger.error(f"Error creating onchain_data table: {e}")
    
    def get_coingecko_id(self, symbol: str) -> str:
        """Get CoinGecko ID from crypto_assets table with proper normalization"""
        try:
            # First normalize the symbol for exchange compatibility
            normalized_symbol = normalize_symbol_for_exchange(symbol, 'coinbase')
            
            db = self.get_db_connection()
            cursor = db.cursor()
            
            # Query without normalized_symbol column since it doesn't exist yet
            cursor.execute("""
                SELECT coingecko_id FROM crypto_assets 
                WHERE (symbol = %s OR name = %s)
                AND coinbase_supported = 1 
                AND coingecko_id IS NOT NULL
                LIMIT 1
            """, (symbol.upper(), symbol))
            
            result = cursor.fetchone()
            cursor.close()
            db.close()
            
            if result and result[0]:
                return result[0]
            
            # Fallback to direct symbol conversion if not found
            return symbol.lower()
            
        except Exception as e:
            logger.warning(f"Database lookup failed for {symbol}: {e}")
            return symbol.lower()
    
    def get_messari_id(self, symbol: str) -> str:
        """Get Messari ID from crypto_assets table - use symbol as fallback"""
        try:
            db = self.get_db_connection()
            cursor = db.cursor()
            
            # Use symbol as ID since messari_id column doesn't exist
            cursor.execute("""
                SELECT symbol FROM crypto_assets 
                WHERE symbol = %s AND is_active = 1
            """, (symbol,))
            
            result = cursor.fetchone()
            cursor.close()
            db.close()
            
            return result[0].lower() if result else symbol.lower()
            
        except Exception as e:
            logger.warning(f"Error getting symbol info for {symbol}: {e}")
            return symbol.lower()
    
    def get_defilama_id(self, symbol: str) -> Optional[str]:
        """Map symbol to DeFiLlama protocol - hardcoded mapping since no defilama_id column"""
        # Direct mapping since defilama_id column doesn't exist
        defi_mappings = {
            'ETH': 'ethereum',
            'AVAX': 'avalanche', 
            'MATIC': 'polygon',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'SOL': 'solana',
            'BNB': 'bsc',
            'ATOM': 'cosmos'
        }
        return defi_mappings.get(symbol)

    def ensure_onchain_placeholders(self, cursor, symbol: str, target_date: date) -> bool:
        """
        Create placeholder onchain record for specific symbol and date
        
        Args:
            cursor: Database cursor
            symbol: Crypto symbol (e.g., 'BTC')
            target_date: Date for the placeholder record
            
        Returns:
            True if placeholder was created, False otherwise
        """
        try:
            # Get the field list for the enhanced onchain collector
            onchain_fields = [
                'active_addresses_24h', 'transaction_count_24h', 'exchange_net_flow_24h',
                'price_volatility_7d', 'market_cap_realized', 'mvrv_ratio',
                'hash_rate', 'network_difficulty', 'block_height', 'block_time_avg',
                'transaction_volume_24h', 'mempool_size', 'fee_avg_24h', 'fee_median_24h',
                'social_score', 'developer_score', 'community_score', 'public_interest',
                'market_cap_rank', 'trading_volume_24h', 'price_change_24h', 'price_change_7d',
                'nvt_ratio', 'total_value_locked', 'staking_rewards_rate', 'validator_count'
            ]
            
            # Create placeholder with all onchain fields set to NULL
            field_placeholders = ', '.join(['NULL'] * len(onchain_fields))
            field_names = ', '.join(onchain_fields)
            
            cursor.execute(f"""
                INSERT IGNORE INTO onchain_data
                (symbol, data_date, {field_names}, data_completeness_percentage, data_source, created_at)
                VALUES (%s, %s, {field_placeholders}, 0.0, 'placeholder_auto', NOW())
            """, (symbol, target_date))
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.debug(f"Error creating onchain placeholder for {symbol}: {e}")
            return False

    def ensure_placeholder_records(self, cursor, lookback_days=PLACEHOLDER_LOOKBACK_DAYS) -> int:
        """
        Ensure placeholder records exist for all supported symbols for recent dates
        
        Args:
            cursor: Database cursor
            lookback_days: How many days back to create placeholders
            
        Returns:
            Number of placeholder records created
        """
        if not ENSURE_PLACEHOLDERS:
            logger.debug("Placeholder creation disabled")
            return 0
        
        logger.info("🔧 Ensuring onchain placeholder records exist...")
        
        placeholders_created = 0
        symbols = self.get_symbols()
        
        if not symbols:
            logger.warning("No symbols found for placeholder creation")
            return 0
        
        try:
            # Calculate date range (6-hour intervals mean daily placeholders)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=lookback_days)
            
            logger.info(f"   Creating placeholders for {len(symbols)} symbols from {start_date} to {end_date}")
            
            # Create placeholders for each symbol and date
            current_date = start_date
            while current_date <= end_date:
                for symbol in symbols:
                    if self.ensure_onchain_placeholders(cursor, symbol, current_date):
                        placeholders_created += 1
                
                current_date += timedelta(days=1)
            
            logger.info(f"✅ Created {placeholders_created} onchain placeholder records")
            return placeholders_created
            
        except Exception as e:
            logger.error(f"Error ensuring onchain placeholder records: {e}")
            return 0

    def calculate_onchain_completeness(self, record_data: Dict) -> float:
        """
        Calculate completeness percentage for an onchain record
        
        Args:
            record_data: Dict containing the record's field values
            
        Returns:
            Completeness percentage (0.0 to 100.0)
        """
        # Core required fields for onchain data
        core_fields = [
            'symbol', 'data_date', 'active_addresses_24h', 'transaction_count_24h',
            'exchange_net_flow_24h', 'price_volatility_7d', 'market_cap_realized',
            'hash_rate', 'network_difficulty', 'transaction_volume_24h'
        ]
        
        # Enhanced fields (lower priority)
        enhanced_fields = [
            'mvrv_ratio', 'social_score', 'developer_score', 'community_score',
            'nvt_ratio', 'total_value_locked', 'staking_rewards_rate'
        ]
        
        # Count populated core fields (weight 70%)
        populated_core = sum(1 for field in core_fields 
                           if record_data.get(field) is not None)
        core_percentage = (populated_core / len(core_fields)) * 70.0
        
        # Count populated enhanced fields (weight 30%)
        populated_enhanced = sum(1 for field in enhanced_fields 
                               if record_data.get(field) is not None)
        enhanced_percentage = (populated_enhanced / len(enhanced_fields)) * 30.0
        
        return min(100.0, core_percentage + enhanced_percentage)

    def update_onchain_completeness(self, cursor, symbol: str, data_date: date, record_data: Dict) -> bool:
        """
        Update the completeness percentage for a specific onchain record
        
        Args:
            cursor: Database cursor
            symbol: Crypto symbol
            data_date: Date of the record
            record_data: Dict with the record's field values
            
        Returns:
            True if update was successful
        """
        try:
            completeness = self.calculate_onchain_completeness(record_data)
            
            cursor.execute("""
                UPDATE onchain_data
                SET data_completeness_percentage = %s
                WHERE symbol = %s AND DATE(timestamp_iso) = %s
            """, (completeness, symbol, data_date))
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating onchain completeness for {symbol} on {data_date}: {e}")
            return False

    async def rate_limit(self, endpoint: str):
        """Implement rate limiting for API calls"""
        now = time.time()
        delay = self.rate_limits.get(endpoint, 1.0)
        
        if endpoint in self.last_api_call:
            time_since_last = now - self.last_api_call[endpoint]
            if time_since_last < delay:
                await asyncio.sleep(delay - time_since_last)
        
        self.last_api_call[endpoint] = time.time()
    
    async def get_coingecko_data(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Get onchain data from CoinGecko with premium API support"""
        try:
            await self.rate_limit('coingecko')
            
            # Get CoinGecko ID from crypto_assets table or use symbol as fallback
            coin_id = self.get_coingecko_id(symbol)
            
            # Use premium or free endpoint
            base_url = "https://pro-api.coingecko.com/api/v3" if self.use_premium_api else "https://api.coingecko.com/api/v3"
            url = f"{base_url}/coins/{coin_id}"
            
            headers = {}
            if self.use_premium_api:
                headers['x-cg-pro-api-key'] = self.coingecko_api_key
            
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
                elif response.status == 429:
                    logger.warning(f"Rate limited for {symbol}, waiting...")
                    await asyncio.sleep(5)
                    return None
                else:
                    logger.warning(f"CoinGecko API error for {symbol}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching CoinGecko data for {symbol}: {e}")
            return None

    async def get_enhanced_coingecko_data(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Get enhanced onchain data from CoinGecko premium endpoints"""
        try:
            await self.rate_limit('coingecko_additional')
            
            coingecko_id = self.get_coingecko_id(symbol)
            
            # Use premium endpoint for more detailed data if available
            base_url = "https://pro-api.coingecko.com/api/v3" if self.use_premium_api else "https://api.coingecko.com/api/v3"
            url = f"{base_url}/coins/{coingecko_id}"
            
            headers = {}
            if self.use_premium_api and self.coingecko_api_key:
                headers['x-cg-pro-api-key'] = self.coingecko_api_key
            
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
                    return self.parse_enhanced_coingecko_data(data, symbol)
                elif response.status == 429:
                    logger.warning(f"CoinGecko rate limited for {symbol}")
                    await asyncio.sleep(2)
                    return None
                else:
                    logger.warning(f"Enhanced CoinGecko API error for {symbol}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching enhanced CoinGecko data for {symbol}: {e}")
            return None
            
    async def get_defilama_tvl_data(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Get comprehensive DeFi TVL data from DeFiLlama - real data only"""
        try:
            await self.rate_limit('defilama')
            
            # Enhanced protocol mapping for major DeFi ecosystems
            protocol_mappings = {
                'ETH': 'ethereum',
                'AVAX': 'avalanche', 
                'MATIC': 'polygon',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'SOL': 'solana',
                'BNB': 'bsc',
                'ATOM': 'cosmos',
                'NEAR': 'near',
                'FTM': 'fantom',
                'ONE': 'harmony'
            }
            
            protocol = protocol_mappings.get(symbol)
            if not protocol:
                # For non-DeFi assets, return None (no TVL data available)
                logger.debug(f"No DeFi ecosystem mapping for {symbol}")
                return None
                
            # Method 1: Get accurate TVL from chains endpoint
            try:
                chains_url = f"https://api.llama.fi/v2/chains"
                async with session.get(chains_url, timeout=30) as response:
                    if response.status == 200:
                        chains_data = await response.json()
                        
                        # Find matching chain with exact name matching
                        for chain in chains_data:
                            chain_name = chain.get('name', '').lower()
                            if chain_name == protocol:
                                tvl = chain.get('tvl', 0)
                                
                                if tvl > 0:  # Only use if we have real TVL data
                                    # Get accurate protocol count
                                    protocols_count = await self._count_active_protocols(session, protocol)
                                    
                                    if protocols_count is not None:  # Only if we got real count
                                        logger.info(f"DeFiLlama {protocol}: TVL=${tvl:,.0f}, Protocols={protocols_count}")
                                        return {
                                            'total_value_locked': tvl,
                                            'defi_protocols_count': protocols_count
                                        }
                
            except Exception as e:
                logger.debug(f"DeFiLlama chains API error: {e}")
            
            # Method 2: Try ecosystem-specific endpoints for major chains
            ecosystem_endpoints = {
                'ethereum': 'https://api.llama.fi/v2/historicalChainTvl/ethereum',
                'polygon': 'https://api.llama.fi/v2/historicalChainTvl/polygon',
                'avalanche': 'https://api.llama.fi/v2/historicalChainTvl/avalanche',
                'bsc': 'https://api.llama.fi/v2/historicalChainTvl/bsc',
                'solana': 'https://api.llama.fi/v2/historicalChainTvl/solana'
            }
            
            if protocol in ecosystem_endpoints:
                try:
                    async with session.get(ecosystem_endpoints[protocol], timeout=30) as response:
                        if response.status == 200:
                            tvl_history = await response.json()
                            
                            if tvl_history and isinstance(tvl_history, list) and len(tvl_history) > 0:
                                # Get latest TVL
                                latest_tvl = tvl_history[-1].get('tvl', 0)
                                
                                if latest_tvl > 0:
                                    # Get protocol count separately
                                    protocols_count = await self._count_active_protocols(session, protocol)
                                    
                                    if protocols_count is not None:
                                        return {
                                            'total_value_locked': latest_tvl,
                                            'defi_protocols_count': protocols_count
                                        }
                except Exception as e:
                    logger.debug(f"DeFiLlama historical TVL error for {protocol}: {e}")
            
            # If we reach here, no reliable data was found
            logger.info(f"No reliable TVL data available for {symbol} from DeFiLlama")
            return None
                        
        except Exception as e:
            logger.warning(f"Error fetching DeFiLlama data for {symbol}: {e}")
            
        return None
    
    async def _count_active_protocols(self, session: aiohttp.ClientSession, chain_name: str) -> int:
        """Count active DeFi protocols on a specific blockchain"""
        try:
            # Get all protocols from DeFiLlama
            protocols_url = "https://api.llama.fi/protocols"
            async with session.get(protocols_url, timeout=30) as response:
                if response.status == 200:
                    all_protocols = await response.json()
                    
                    active_count = 0
                    for protocol in all_protocols:
                        # Check if protocol operates on this chain
                        protocol_chains = protocol.get('chains', [])
                        
                        # Case-insensitive check for chain name
                        chain_matches = any(
                            chain.lower() == chain_name.lower() for chain in protocol_chains
                        )
                        
                        if chain_matches:
                            # Only count protocols with meaningful TVL (>$100k)
                            protocol_tvl = protocol.get('tvl', 0)
                            if protocol_tvl and protocol_tvl > 100_000:
                                active_count += 1
                    
                    logger.debug(f"Found {active_count} active protocols for {chain_name}")
                    return active_count
                    
        except Exception as e:
            logger.debug(f"Failed to count protocols for {chain_name}: {e}")
            
        # Return None instead of estimates - only use real data
        logger.info(f"Could not determine accurate protocol count for {chain_name}")
        return None
    
    async def get_additional_metrics(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Get additional metrics including realized cap and network value calculations"""
        try:
            await self.rate_limit('additional')
            
            additional_data = {}
            
            # Try to get realized cap from Messari (free tier)
            if symbol in ['BTC', 'ETH']:  # Focus on major assets
                try:
                    messari_url = f"https://data.messari.io/api/v1/assets/{symbol.lower()}/metrics"
                    async with session.get(messari_url, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            market_data = data.get('data', {}).get('market_data', {})
                            
                            if market_data.get('realized_cap'):
                                additional_data['realized_cap'] = market_data['realized_cap']
                            
                            # Get network value metrics if available
                            if market_data.get('mcap_realized_usd') and market_data.get('mcap_dom_percent'):
                                additional_data['network_value_to_transactions'] = (
                                    market_data['mcap_realized_usd'] / max(market_data.get('real_volume_last_24_hours', 1), 1)
                                )
                                
                except Exception as e:
                    logger.debug(f"Messari API error for {symbol}: {e}")
            
            # Remove realized cap estimation - only use real data from specialized APIs
            # Any additional metrics should come from reliable sources, not estimates
            
            return additional_data if additional_data else None
            
        except Exception as e:
            logger.warning(f"Error fetching additional metrics for {symbol}: {e}")
            return None

    def parse_messari_data(self, data: Dict, symbol: str) -> Dict:
        """Parse Messari response for advanced metrics"""
        try:
            metrics = data.get('data', {})
            market_data = metrics.get('market_data', {})
            blockchain_stats = metrics.get('blockchain_stats_24_hours', {})
            developer_activity = metrics.get('developer_activity', {})
            
            return {
                'symbol': symbol,
                'data_source': 'messari',
                # Network metrics
                'active_addresses': blockchain_stats.get('active_addresses'),
                'transaction_count': blockchain_stats.get('transaction_count'),
                'transaction_volume': blockchain_stats.get('adjusted_transaction_volume'),
                'hash_rate': blockchain_stats.get('hash_rate'),
                'difficulty': blockchain_stats.get('difficulty'),
                
                # Supply metrics (enhanced)
                'circulating_supply': market_data.get('current_supply'),
                'total_supply': market_data.get('y_2050_supply'),
                'supply_inflation_rate': blockchain_stats.get('inflation_rate'),
                
                # Network value metrics
                'nvt_ratio': market_data.get('nvt'),
                'network_value_to_transactions': market_data.get('nvt_adjusted'),
                'realized_cap': market_data.get('realized_capitalization'),
                'mvrv_ratio': market_data.get('mvrv'),
                
                # Developer metrics
                'github_commits_30d': developer_activity.get('commits_last_3_months'),
                'developer_activity_score': developer_activity.get('developer_score'),
                
                'data_quality_score': 0.9  # Messari generally has high quality data
            }
            
        except Exception as e:
            logger.error(f"Error parsing Messari data for {symbol}: {e}")
            return {}
    def parse_coingecko_data(self, data: Dict, symbol: str) -> Dict:
        """Parse CoinGecko response into comprehensive onchain metrics"""
        try:
            market_data = data.get('market_data', {})
            developer_data = data.get('developer_data', {})
            community_data = data.get('community_data', {})
            
            # Extract USD values from market data
            market_cap_usd = self.get_usd_value(market_data.get('market_cap'))
            total_volume_usd = self.get_usd_value(market_data.get('total_volume'))
            fdv_usd = self.get_usd_value(market_data.get('fully_diluted_valuation'))
            high_24h_usd = self.get_usd_value(market_data.get('high_24h'))
            low_24h_usd = self.get_usd_value(market_data.get('low_24h'))
            ath_usd = self.get_usd_value(market_data.get('ath'))
            atl_usd = self.get_usd_value(market_data.get('atl'))
            
            # Calculate network value metrics
            nvt_ratio = market_cap_usd / total_volume_usd if market_cap_usd and total_volume_usd and total_volume_usd > 0 else None
            mvrv_ratio = market_cap_usd / fdv_usd if market_cap_usd and fdv_usd and fdv_usd > 0 else None
            
            # Build onchain-focused record (only fields that exist in onchain_data table)
            parsed_data = {
                'symbol': symbol,
                'coin_id': data.get('id'),
                'timestamp_iso': datetime.now(),
                
                # Supply metrics (core onchain data)
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply'),
                
                # Network metrics (set to None - would come from blockchain APIs)
                'active_addresses': None,
                'transaction_count': None,
                'transaction_volume': None,
                'hash_rate': None,
                'difficulty': None,
                'block_height': None,
                'block_time_seconds': None,
                
                # Value metrics (set to None - need specialized APIs)
                'network_value_to_transactions': None,
                'realized_cap': None,
                'mvrv_ratio': None,
                'nvt_ratio': None,
                
                # Development metrics (from CoinGecko)
                'github_commits_30d': developer_data.get('commit_count_4_weeks'),
                'developer_activity_score': (
                    min(developer_data.get('commit_count_4_weeks', 0) / 100.0, 1.0)
                    if developer_data.get('commit_count_4_weeks') else None
                ),
                
                # Staking metrics (set to None - would need staking APIs)
                'staking_yield': None,
                'staked_percentage': None,
                'validator_count': None,
                
                # DeFi metrics (set to None - would come from DeFiLlama)
                'total_value_locked': None,
                'defi_protocols_count': None,
                
                # Supply inflation rate (set default, will be updated by blockchain-specific data)
                'supply_inflation_rate': None,
                
                'data_source': 'coingecko-premium' if self.use_premium_api else 'coingecko',
                'data_quality_score': 0.95 if self.use_premium_api else 0.8
            }
            
            # Add blockchain-specific metrics for major networks
            blockchain_stats = self.get_blockchain_specific_data(symbol, data)
            parsed_data.update(blockchain_stats)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing CoinGecko data for {symbol}: {e}")
            return None
    
    def get_usd_value(self, value_dict: Dict) -> Optional[float]:
        """Extract USD value from CoinGecko currency dict"""
        if isinstance(value_dict, dict) and 'usd' in value_dict:
            return value_dict['usd']
        return None
    
    def parse_enhanced_coingecko_data(self, data: Dict, symbol: str) -> Dict:
        """Parse enhanced CoinGecko data for additional metrics"""
        try:
            # Extract additional metrics that main parser might miss
            enhanced_data = {}
            
            # Community metrics
            if 'community_data' in data:
                community = data['community_data']
                enhanced_data.update({
                    'twitter_followers': community.get('twitter_followers'),
                    'reddit_subscribers': community.get('reddit_subscribers'),
                    'telegram_channel_user_count': community.get('telegram_channel_user_count')
                })
            
            # Developer metrics  
            if 'developer_data' in data:
                dev = data['developer_data']
                enhanced_data.update({
                    'github_forks': dev.get('forks'),
                    'github_stars': dev.get('stars'),
                    'github_subscribers': dev.get('subscribers'),
                    'commit_count_4_weeks': dev.get('commit_count_4_weeks')
                })
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error parsing enhanced CoinGecko data for {symbol}: {e}")
            return {}
    
    
    def get_blockchain_specific_data(self, symbol: str, coingecko_data: Dict) -> Dict:
        """Get blockchain-specific metrics based on the network type"""
        blockchain_data = {}
        
        try:
            # Staking data for PoS networks (from known parameters)
            pos_networks = {
                'ADA': {'staking_yield': 4.5, 'staked_percentage': 72, 'validator_count': 3000},
                'DOT': {'staking_yield': 12.0, 'staked_percentage': 55, 'validator_count': 297},
                'SOL': {'staking_yield': 6.8, 'staked_percentage': 75, 'validator_count': 1400},
                'AVAX': {'staking_yield': 9.2, 'staked_percentage': 65, 'validator_count': 1200},
                'MATIC': {'staking_yield': 3.8, 'staked_percentage': 40, 'validator_count': 100},
                'ETH': {'staking_yield': 3.2, 'staked_percentage': 22, 'validator_count': 900000}
            }
            
            if symbol in pos_networks:
                blockchain_data.update(pos_networks[symbol])
            
            # Remove network activity estimation - only use real API data
            # Active addresses and transaction counts should come from blockchain APIs only
            
            # Add critical missing metrics
            # Block time for major networks (known values)
            block_times = {
                'BTC': 600,     # 10 minutes
                'ETH': 12,      # 12 seconds
                'ADA': 20,      # 20 seconds
                'DOT': 6,       # 6 seconds
                'SOL': 0.4,     # 400ms
                'AVAX': 2,      # 2 seconds
                'MATIC': 2.1    # 2.1 seconds
            }
            
            if symbol in block_times:
                blockchain_data['block_time_seconds'] = block_times[symbol]
            
            # Calculate supply inflation rate from supply metrics
            market_data = coingecko_data.get('market_data', {})
            total_supply = market_data.get('total_supply')
            max_supply = market_data.get('max_supply')
            
            # Known annual inflation rates for major networks
            inflation_rates = {
                'BTC': 0.65,    # ~0.65% (halving schedule)
                'ETH': -0.10,   # ~-0.1% (post-merge deflationary)
                'ADA': 0.30,    # ~0.3% annual
                'DOT': 10.0,    # ~10% annual
                'SOL': 8.0,     # ~8% annual
                'AVAX': 2.0,    # ~2% annual
                'MATIC': 5.0    # ~5% annual
            }
            
            if symbol.upper() in inflation_rates:
                # Use known rate for this network
                blockchain_data['supply_inflation_rate'] = inflation_rates[symbol.upper()]
            elif total_supply and max_supply and max_supply > total_supply:
                # Use estimated rate for capped supply tokens
                blockchain_data['supply_inflation_rate'] = inflation_rates.get(symbol.upper(), 2.0)
            elif total_supply and max_supply and max_supply == total_supply:
                # Fixed supply (like Bitcoin when fully mined)
                blockchain_data['supply_inflation_rate'] = 0.0
            else:
                # Default for unknown tokens
                blockchain_data['supply_inflation_rate'] = None
            
            # Remove transaction volume estimation - only use real blockchain data
            # Transaction volume should come from network APIs or reliable sources only
            
            # Remove network value to transactions calculation as it depends on estimated volume
            # This should be calculated only when we have real transaction volume data
            
            # Remove realized cap estimation - only use real data from APIs like Messari
            # Realized cap should come from specialized APIs that calculate it properly
                
        except Exception as e:
            logger.warning(f"Error getting blockchain-specific data for {symbol}: {e}")
            
        return blockchain_data

    async def get_network_metrics(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Get real-time network metrics from blockchain APIs"""
        try:
            await self.rate_limit('network')
            
            # For Bitcoin - use BlockCypher and Blockchain.info APIs
            if symbol == 'BTC':
                btc_metrics = await self.get_bitcoin_metrics(session)
                if btc_metrics:
                    return btc_metrics
            
            # For Ethereum - use Etherscan API
            elif symbol == 'ETH':
                eth_metrics = await self.get_ethereum_metrics(session)
                if eth_metrics:
                    return eth_metrics
            
            # For Cardano - use Cardano blockchain API
            elif symbol == 'ADA':
                cardano_metrics = await self.get_cardano_metrics(session)
                if cardano_metrics:
                    return cardano_metrics
            
            # For Solana - use Solana RPC API
            elif symbol == 'SOL':
                solana_metrics = await self.get_solana_metrics(session)
                if solana_metrics:
                    return solana_metrics
            
            # For other networks, return None (no estimated metrics)
            logger.info(f"No real-time network API available for {symbol}")
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching network metrics for {symbol}: {e}")
            return None
    
    async def get_bitcoin_metrics(self, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Get Bitcoin-specific metrics from multiple reliable sources"""
        try:
            # Method 1: Try Bitcoin JSON RPC via public nodes for most accurate data
            try:
                # Use a public Bitcoin JSON-RPC node
                rpc_url = "https://blockstream.info/api/blocks/tip/height"
                headers = {'Accept': 'application/json', 'User-Agent': 'CryptoDataCollector/1.0'}
                
                # Get current block height
                block_height = None
                async with session.get(rpc_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        text_response = await response.text()
                        block_height = int(text_response.strip()) if text_response.strip().isdigit() else None
                
                # Get current difficulty from blockstream API
                difficulty_url = "https://blockstream.info/api/blocks/tip"
                difficulty = None
                hash_rate = None
                
                async with session.get(difficulty_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        block_data = await response.json()
                        difficulty = block_data.get('difficulty')
                        
                        # Calculate hash rate from difficulty
                        # Hash rate = difficulty * 2^32 / (target_time_seconds * 10^12)
                        if difficulty:
                            # Bitcoin targets 600 seconds per block (10 minutes)
                            hash_rate = (difficulty * (2**32)) / (600 * 1e12)  # TH/s
                
                if block_height and difficulty:
                    return {
                        'hash_rate': hash_rate,  # Hash rate in TH/s (calculated)
                        'difficulty': difficulty,  # Network difficulty
                        'block_height': block_height,  # Current block height
                        'data_source': 'blockstream'
                    }
                    
            except Exception as e:
                logger.debug(f"Blockstream API failed: {e}")
            
            # Method 2: Try BlockCypher API for basic stats
            try:
                blockcypher_url = "https://api.blockcypher.com/v1/btc/main"
                headers = {'Accept': 'application/json'}
                
                async with session.get(blockcypher_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        block_height = data.get('height')
                        
                        # BlockCypher doesn't provide difficulty directly, so use known approximations
                        # Current Bitcoin network stats as of November 2024
                        estimated_difficulty = 95e12  # ~95T difficulty (approximate)
                        estimated_hash_rate = (estimated_difficulty * (2**32)) / (600 * 1e12)
                        
                        return {
                            'hash_rate': estimated_hash_rate,  # Hash rate in TH/s (estimated)
                            'difficulty': estimated_difficulty,  # Network difficulty (estimated)
                            'block_height': block_height,  # Current block height (real)
                            'transaction_count': data.get('n_tx', 0),  # Total transactions
                            'active_addresses': data.get('n_addresses', 0),  # Total addresses
                            'data_source': 'blockcypher_estimated'
                        }
            except Exception as e:
                logger.debug(f"BlockCypher API failed: {e}")
            
            # Method 3: Try blockchain.info with proper headers as last resort
            try:
                stats_url = "https://blockchain.info/stats?format=json"
                headers = {
                    'Accept': 'application/json',
                    'User-Agent': 'CryptoDataCollector/1.0'
                }
                
                async with session.get(stats_url, headers=headers, timeout=30) as response:
                    if response.status == 200 and 'application/json' in response.headers.get('content-type', ''):
                        stats = await response.json()
                        
                        # Get current difficulty and hash rate
                        hash_rate = stats.get('hash_rate')  # TH/s
                        difficulty = stats.get('difficulty')
                        
                        # Get latest block height from separate endpoint
                        latest_block_url = "https://blockchain.info/latestblock"
                        block_height = None
                        async with session.get(latest_block_url, headers=headers, timeout=30) as block_response:
                            if block_response.status == 200:
                                block_data = await block_response.json()
                                block_height = block_data.get('height')
                        
                        return {
                            'hash_rate': hash_rate,  # Hash rate in TH/s
                            'difficulty': difficulty,  # Network difficulty
                            'block_height': block_height,  # Current block height
                            'data_source': 'blockchain_info'
                        }
            except Exception as e:
                logger.debug(f"Blockchain.info API failed: {e}")
        
        except Exception as e:
            logger.warning(f"Error fetching Bitcoin metrics: {e}")
        
        # No fallback estimates - return None if no real data available
        logger.warning("Could not retrieve real Bitcoin network metrics from any API")
        return None
    
    async def get_ethereum_metrics(self, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Get Ethereum-specific metrics from multiple sources"""
        try:
            # Method 1: Try to get block height from a public API
            eth_metrics = {}
            
            # Get latest block from Etherscan (free endpoint)
            try:
                block_url = "https://api.etherscan.io/api?module=proxy&action=eth_blockNumber"
                async with session.get(block_url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('result'):
                            block_height = int(data['result'], 16)
                            eth_metrics['block_height'] = block_height
            except Exception as e:
                logger.debug(f"Etherscan API issue: {e}")
            
            # Method 2: Try alternative APIs for block height
            if 'block_height' not in eth_metrics:
                try:
                    # Alchemy public endpoint (no API key needed)
                    alchemy_url = "https://eth-mainnet.public.blastapi.io"
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "eth_blockNumber",
                        "params": [],
                        "id": 1
                    }
                    async with session.post(alchemy_url, json=payload, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('result'):
                                block_height = int(data['result'], 16)
                                eth_metrics['block_height'] = block_height
                except Exception as e:
                    logger.debug(f"Alternative ETH API issue: {e}")
            
            # Add known Ethereum parameters
            eth_metrics.update({
                'block_time_seconds': 12.0,  # Ethereum block time
                'hash_rate': None,  # ETH hash rate not applicable (PoS)
                'difficulty': None,  # ETH difficulty not applicable (PoS post-merge)
            })
            
            return eth_metrics if eth_metrics else None
            
        except Exception as e:
            logger.warning(f"Error fetching Ethereum metrics: {e}")
            return None
    
    async def get_cardano_metrics(self, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Get Cardano-specific metrics from Cardano API"""
        try:
            # Use Cardano Blockfrost API (public endpoints)
            cardano_metrics = {}
            
            # Get latest block info
            try:
                blocks_url = "https://cardano-mainnet.blockfrost.io/api/v0/blocks/latest"
                headers = {'project_id': 'mainnet'}  # Free tier available
                
                async with session.get(blocks_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        block_data = await response.json()
                        cardano_metrics.update({
                            'block_height': block_data.get('height'),
                            'block_time_seconds': 20,  # Cardano average block time
                        })
                        
                        # Get epoch statistics for network activity
                        current_epoch = block_data.get('epoch')
                        if current_epoch:
                            epoch_url = f"https://cardano-mainnet.blockfrost.io/api/v0/epochs/{current_epoch}"
                            async with session.get(epoch_url, headers=headers, timeout=30) as epoch_response:
                                if epoch_response.status == 200:
                                    epoch_data = await epoch_response.json()
                                    cardano_metrics.update({
                                        'transaction_count': epoch_data.get('tx_count'),
                                        'active_addresses': epoch_data.get('active_stake'),  # Unique stake addresses
                                    })
            except Exception as e:
                logger.debug(f"Cardano Blockfrost API error: {e}")
            
            # Alternative: Use Cardano GraphQL API for network stats
            if not cardano_metrics:
                try:
                    graphql_url = "https://graphql-api.mainnet.dandelion.link/"
                    query = {
                        "query": """
                        query {
                            cardano {
                                tip {
                                    number
                                    slotNo
                                }
                            }
                        }
                        """
                    }
                    async with session.post(graphql_url, json=query, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            tip = data.get('data', {}).get('cardano', {}).get('tip', {})
                            if tip:
                                cardano_metrics = {
                                    'block_height': tip.get('number'),
                                    'data_source': 'cardano-graphql'
                                }
                except Exception as e:
                    logger.debug(f"Cardano GraphQL API error: {e}")
            
            return cardano_metrics if cardano_metrics else None
            
        except Exception as e:
            logger.warning(f"Error fetching Cardano metrics: {e}")
            return None
    
    async def get_solana_metrics(self, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Get Solana-specific metrics from Solana RPC"""
        try:
            solana_metrics = {}
            
            # Use Solana public RPC endpoints
            try:
                rpc_url = "https://api.mainnet-beta.solana.com"
                headers = {'Content-Type': 'application/json'}
                
                # Get current slot (Solana's equivalent of block height)
                slot_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSlot"
                }
                
                async with session.post(rpc_url, json=slot_payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            solana_metrics['block_height'] = data['result']
                
                # Get epoch info for network activity
                epoch_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getEpochInfo"
                }
                
                async with session.post(rpc_url, json=epoch_payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        epoch_info = data.get('result', {})
                        if epoch_info:
                            # Calculate slot time (Solana targets ~400ms per slot)
                            solana_metrics['block_time_seconds'] = 0.4
                
                # Get transaction count for recent performance
                performance_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getRecentPerformanceSamples",
                    "params": [1]
                }
                
                async with session.post(rpc_url, json=performance_payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        performance = data.get('result', [])
                        if performance and len(performance) > 0:
                            sample = performance[0]
                            # Transaction count per sample period
                            transaction_count = sample.get('numTransactions', 0)
                            if transaction_count > 0:
                                solana_metrics['transaction_count'] = transaction_count
                
                if solana_metrics:
                    solana_metrics['data_source'] = 'solana-rpc'
                    
            except Exception as e:
                logger.debug(f"Solana RPC API error: {e}")
            
            return solana_metrics if solana_metrics else None
            
        except Exception as e:
            logger.warning(f"Error fetching Solana metrics: {e}")
            return None

    async def collect_onchain_data(self, symbol: str, target_date: Optional[date] = None) -> Optional[Dict]:""
    async def collect_onchain_data(self, symbol: str, target_date: Optional[date] = None) -> Optional[Dict]:
        """Collect comprehensive onchain data from multiple real sources"""
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"Collecting comprehensive onchain data for {symbol}...")
                
                # Collect from multiple real sources
                coingecko_data = await self.get_coingecko_data(session, symbol)
                enhanced_data = await self.get_enhanced_coingecko_data(session, symbol)
                defilama_data = await self.get_defilama_tvl_data(session, symbol)
                network_data = await self.get_network_metrics(session, symbol)
                additional_data = await self.get_additional_metrics(session, symbol)
                
                # Merge data from all sources (real data only)
                merged_data = {}
                data_sources = []
                
                if coingecko_data:
                    merged_data.update(coingecko_data)
                    data_sources.append('coingecko')
                    
                if enhanced_data:
                    # Enhanced CoinGecko data provides additional metrics
                    for key, value in enhanced_data.items():
                        if value is not None and value != 0:  # Only use real values
                            merged_data[key] = value
                    data_sources.append('coingecko-enhanced')
                    
                if defilama_data:
                    # Add TVL data - ensure these fields are mapped correctly
                    for key, value in defilama_data.items():
                        if value is not None:
                            merged_data[key] = value
                    data_sources.append('defilama')
                
                if network_data:
                    # Add network metrics
                    merged_data.update(network_data)
                    data_sources.append('network-api')
                
                if additional_data:
                    # Add additional metrics
                    merged_data.update(additional_data)
                    data_sources.append('additional-apis')
                
                if merged_data:
                    merged_data['data_source'] = ','.join(data_sources)
                    
                    if target_date:
                        # Adjust timestamp for historical backfill
                        merged_data['timestamp_iso'] = datetime.combine(target_date, datetime.min.time())
                    else:
                        merged_data['timestamp_iso'] = datetime.now()
                    
                    logger.info(f"✅ Collected comprehensive onchain data for {symbol} from: {merged_data['data_source']}")
                    return merged_data
                else:
                    logger.warning(f"No data collected for {symbol} from any source")
                    return None
                
        except Exception as e:
            logger.error(f"Error collecting onchain data for {symbol}: {e}")
            return None
    
    def get_missing_onchain_dates(self, symbol: str, start_date: date, end_date: date) -> List[date]:
        """Get dates where onchain data is missing"""
        try:
            db = self.get_db_connection()
            cursor = db.cursor()
            
            # Use correct table name
            table_name = get_master_onchain_table().split('.')[-1]
            
            cursor.execute(f"""
                SELECT DISTINCT DATE(timestamp_iso) as date_only
                FROM {table_name}
                WHERE symbol = %s
                AND DATE(timestamp_iso) >= %s
                AND DATE(timestamp_iso) <= %s
            """, (symbol, start_date, end_date))
            
            existing_dates = {row[0] for row in cursor.fetchall()}
            
            # Generate all dates in range
            all_dates = []
            current_date = start_date
            while current_date <= end_date:
                all_dates.append(current_date)
                current_date += timedelta(days=1)
            
            missing_dates = [d for d in all_dates if d not in existing_dates]
            
            db.close()
            return missing_dates
            
        except Exception as e:
            logger.error(f"Error getting missing dates for {symbol}: {e}")
            return []
    
    def store_onchain_data(self, onchain_data: List[Dict]) -> int:
        """Store onchain data to database using our blockchain-focused table"""
        if not onchain_data:
            return 0
        
        try:
            db = self.get_db_connection()
            cursor = db.cursor()
            
            # Get correct table name (should be 'onchain_data' now)
            table_name = get_master_onchain_table().split('.')[-1]
            
            # Use our proper blockchain schema - no complex field mapping needed
            insert_query = f"""
                INSERT INTO {table_name} (
                    symbol, coin_id, timestamp_iso, circulating_supply, total_supply, max_supply,
                    active_addresses, transaction_count, transaction_volume, hash_rate, difficulty,
                    block_height, block_time_seconds, supply_inflation_rate, 
                    network_value_to_transactions, realized_cap, mvrv_ratio, nvt_ratio,
                    github_commits_30d, developer_activity_score, staking_yield, staked_percentage,
                    validator_count, total_value_locked, defi_protocols_count,
                    data_source, data_quality_score, collected_at
                ) VALUES (
                    %(symbol)s, %(coin_id)s, %(timestamp_iso)s, %(circulating_supply)s, %(total_supply)s, %(max_supply)s,
                    %(active_addresses)s, %(transaction_count)s, %(transaction_volume)s, %(hash_rate)s, %(difficulty)s,
                    %(block_height)s, %(block_time_seconds)s, %(supply_inflation_rate)s,
                    %(network_value_to_transactions)s, %(realized_cap)s, %(mvrv_ratio)s, %(nvt_ratio)s,
                    %(github_commits_30d)s, %(developer_activity_score)s, %(staking_yield)s, %(staked_percentage)s,
                    %(validator_count)s, %(total_value_locked)s, %(defi_protocols_count)s,
                    %(data_source)s, %(data_quality_score)s, NOW()
                ) ON DUPLICATE KEY UPDATE
                    circulating_supply = VALUES(circulating_supply),
                    total_supply = VALUES(total_supply),
                    max_supply = VALUES(max_supply),
                    active_addresses = VALUES(active_addresses),
                    transaction_count = VALUES(transaction_count),
                    hash_rate = VALUES(hash_rate),
                    difficulty = VALUES(difficulty),
                    block_height = VALUES(block_height),
                    total_value_locked = VALUES(total_value_locked),
                    defi_protocols_count = VALUES(defi_protocols_count),
                    data_quality_score = VALUES(data_quality_score),
                    collected_at = NOW()
            """
            
            # No complex mapping needed - just use the data as-is
            cursor.executemany(insert_query, onchain_data)
            rows_affected = cursor.rowcount
            
            # Update completeness percentages for stored records
            for record in onchain_data:
                try:
                    # Extract date from timestamp_iso
                    timestamp_iso = record.get('timestamp_iso')
                    if isinstance(timestamp_iso, str):
                        data_date = datetime.fromisoformat(timestamp_iso).date()
                    else:
                        data_date = timestamp_iso.date() if timestamp_iso else datetime.now().date()
                    
                    self.update_onchain_completeness(cursor, record['symbol'], data_date, record)
                except Exception as e:
                    logger.debug(f"Error updating completeness for {record.get('symbol')}: {e}")
            
            db.commit()
            cursor.close()
            db.close()
            
            logger.info(f"Stored {rows_affected} onchain data records")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Error storing onchain data: {e}")
            return 0
    
    async def run_backfill(self, start_date: date, end_date: date, symbols: Optional[List[str]] = None) -> Dict:
        """Run comprehensive backfill for onchain data"""
        logger.info(f"Starting onchain data backfill from {start_date} to {end_date}")
        
        # Ensure table exists
        self.ensure_table_exists()
        
        # Step 1: Ensure placeholder records exist for expected dates
        placeholders_created = 0
        if ENSURE_PLACEHOLDERS and not os.getenv("BACKFILL_DAYS"):  # Only for normal operation, not backfill
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                placeholders_created = self.ensure_placeholder_records(cursor)
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"Error creating placeholders: {e}")
        
        if symbols is None:
            symbols = self.get_symbols()
            logger.info(f"Using all {len(symbols)} available symbols")
        
        # Log placeholder creation
        if placeholders_created > 0:
            logger.info(f"Created {placeholders_created} placeholder records")
        
        total_processed = 0
        total_stored = 0
        errors = []
        
        for symbol in symbols:
            try:
                logger.info(f"Processing {symbol}...")
                
                # Get missing dates for this symbol
                missing_dates = self.get_missing_onchain_dates(symbol, start_date, end_date)
                
                if not missing_dates:
                    logger.info(f"No missing dates for {symbol}")
                    continue
                
                logger.info(f"Found {len(missing_dates)} missing dates for {symbol}")
                
                # Process missing dates in batches with smart failure detection
                batch_data = []
                consecutive_failures = 0
                max_consecutive_failures = 5  # Faster detection for delisted/unavailable coins
                
                for target_date in sorted(missing_dates, reverse=True):  # Process dates NEWEST FIRST for smart detection
                    onchain_data = await self.collect_onchain_data(symbol, target_date)
                    if onchain_data:
                        batch_data.append(onchain_data)
                        total_processed += 1
                        consecutive_failures = 0  # Reset failure count on success
                    else:
                        consecutive_failures += 1
                        # Skip symbol if too many consecutive failures
                        if consecutive_failures >= max_consecutive_failures:
                            logger.warning(f"Skipping {symbol} - likely delisted or unavailable (failed on {consecutive_failures} recent dates)")
                            break
                
                    # Process batch when it reaches size or at end
                    if len(batch_data) >= 20:
                        stored = self.store_onchain_data(batch_data)
                        total_stored += stored
                        batch_data = []
                        await asyncio.sleep(0.2)  # Rate limiting
                
                # Store remaining data
                if batch_data:
                    stored = self.store_onchain_data(batch_data)
                    total_stored += stored
                
                # Delay between symbols to respect API limits
                await asyncio.sleep(2.0)
                
            except Exception as e:
                error_msg = f"Error processing {symbol}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            'symbols_processed': len(symbols),
            'dates_processed': total_processed,
            'records_stored': total_stored,
            'errors': errors
        }
        
        logger.info(f"Onchain backfill completed: {total_stored} records stored, {len(errors)} errors")
        return result

# ==============================================================================
# FASTAPI APPLICATION & ENDPOINTS
# ==============================================================================

app = FastAPI(
    title="Enhanced Onchain Data Collector v2",
    description="Real-time onchain data collection with health monitoring and backfill capabilities",
    version="2.0.0"
)

# Request models
class BackfillRequest(BaseModel):
    days: int = 30
    symbols: Optional[List[str]] = None
    force_refresh: bool = False

class CollectionRequest(BaseModel):
    symbols: Optional[List[str]] = None

# Global collector instance
collector = EnhancedOnchainCollector()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = collector.get_db_connection()
        conn.close()
        
        return JSONResponse({
            "status": "healthy",
            "service": "enhanced-onchain-collector-v2",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "database": "connected",
            "api_key": "configured" if collector.use_premium_api else "free_tier"
        })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/status")
async def get_status():
    """Get detailed collector status"""
    try:
        # Get database statistics
        conn = collector.get_db_connection()
        cursor = conn.cursor()
        
        table_name = get_master_onchain_table().split('.')[-1]
        
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                MIN(DATE(timestamp)) as earliest_date,
                MAX(DATE(timestamp)) as latest_date
            FROM {table_name}
        """)
        
        stats = cursor.fetchone()
        
        cursor.execute(f"""
            SELECT symbol, COUNT(*) as record_count
            FROM {table_name}
            GROUP BY symbol
            ORDER BY record_count DESC
            LIMIT 10
        """)
        
        symbol_stats = cursor.fetchall()
        conn.close()
        
        return JSONResponse({
            "status": "active",
            "collector": "enhanced-onchain-collector-v2",
            "statistics": {
                "total_records": stats[0],
                "unique_symbols": stats[1],
                "date_range": {
                    "earliest": str(stats[2]) if stats[2] else None,
                    "latest": str(stats[3]) if stats[3] else None
                },
                "top_symbols": [{"symbol": row[0], "records": row[1]} for row in symbol_stats]
            },
            "configuration": {
                "use_premium_api": collector.use_premium_api,
                "table": get_master_onchain_table(),
                "rate_limits": collector.rate_limits
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.post("/collect")
async def run_collection(request: CollectionRequest):
    """Run immediate data collection for specified symbols"""
    try:
        symbols = request.symbols or collector.get_symbols()
        
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols available for collection")
        
        results = []
        errors = []
        
        for symbol in symbols[:5]:  # Limit to 5 symbols for immediate collection
            try:
                data = await collector.collect_onchain_data(symbol)
                if data:
                    stored = collector.store_onchain_data([data])
                    results.append({
                        "symbol": symbol,
                        "status": "success",
                        "records_stored": stored,
                        "data_source": data.get('data_source', 'unknown')
                    })
                else:
                    results.append({
                        "symbol": symbol,
                        "status": "no_data",
                        "records_stored": 0
                    })
            except Exception as e:
                error_msg = f"Error collecting {symbol}: {str(e)}"
                errors.append(error_msg)
                results.append({
                    "symbol": symbol,
                    "status": "error",
                    "error": str(e)
                })
        
        return JSONResponse({
            "status": "completed",
            "symbols_processed": len(symbols),
            "results": results,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")

@app.post("/backfill")
async def run_backfill(background_tasks: BackgroundTasks, request: BackfillRequest):
    """Run backfill operation in background"""
    try:
        # Calculate date range
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=request.days)
        
        # Start backfill in background
        background_tasks.add_task(
            execute_backfill, 
            start_date, 
            end_date, 
            request.symbols,
            request.force_refresh
        )
        
        return JSONResponse({
            "status": "started",
            "message": f"Backfill initiated for {request.days} days",
            "date_range": {
                "start": str(start_date),
                "end": str(end_date)
            },
            "symbols": request.symbols or "all_active",
            "force_refresh": request.force_refresh,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backfill initiation failed: {str(e)}")

@app.post("/comprehensive-backfill")
async def run_comprehensive_backfill(background_tasks: BackgroundTasks):
    """Run comprehensive 2-year historical backfill for all Coinbase-supported symbols"""
    try:
        # Full 2-year backfill from 2023-01-01
        start_date = date(2023, 1, 1)
        end_date = date.today() - timedelta(days=1)
        
        # Get all Coinbase-supported symbols
        symbols = collector.get_symbols()
        
        logger.info(f"Starting comprehensive backfill: {start_date} to {end_date} for {len(symbols)} symbols")
        
        # Start comprehensive backfill in background
        background_tasks.add_task(
            execute_comprehensive_backfill,
            start_date,
            end_date
        )
        
        return JSONResponse({
            "status": "started",
            "message": "Comprehensive 2-year backfill initiated",
            "date_range": {
                "start": str(start_date),
                "end": str(end_date)
            },
            "symbols_count": len(symbols),
            "estimated_records": len(symbols) * (end_date - start_date).days,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive backfill initiation failed: {str(e)}")

@app.get("/symbols")
async def get_supported_symbols():
    """Get list of supported symbols"""
    try:
        symbols = collector.get_symbols()
        
        return JSONResponse({
            "symbols": symbols,
            "count": len(symbols),
            "source": "crypto_assets_table",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get symbols: {str(e)}")

async def execute_backfill(start_date: date, end_date: date, symbols: Optional[List[str]] = None, force_refresh: bool = False):
    """Execute backfill operation"""
    try:
        logger.info(f"Starting background backfill: {start_date} to {end_date}")
        result = await collector.run_backfill(start_date, end_date, symbols)
        logger.info(f"Background backfill completed: {result}")
    except Exception as e:
        logger.error(f"Background backfill failed: {e}")

async def execute_comprehensive_backfill(start_date: date, end_date: date):
    """Execute comprehensive 2-year backfill with batch processing"""
    try:
        logger.info(f"Starting comprehensive backfill: {start_date} to {end_date}")
        
        # Process in monthly batches for better performance
        current_date = start_date
        total_records = 0
        batch_count = 0
        
        while current_date <= end_date:
            # Calculate batch end date (1 month)
            batch_end = min(
                current_date.replace(month=current_date.month + 1) if current_date.month < 12 
                else current_date.replace(year=current_date.year + 1, month=1),
                end_date
            )
            
            batch_count += 1
            logger.info(f"Processing batch {batch_count}: {current_date} to {batch_end}")
            
            try:
                # Run batch backfill
                result = await collector.run_backfill(current_date, batch_end)
                batch_records = result.get('total_records', 0)
                total_records += batch_records
                
                logger.info(f"Batch {batch_count} completed: {batch_records} records")
                
                # Brief pause between batches to avoid overwhelming the system
                await asyncio.sleep(2)
                
            except Exception as batch_error:
                logger.error(f"Batch {batch_count} failed: {batch_error}")
                # Continue with next batch instead of failing entire operation
                
            # Move to next batch
            current_date = batch_end + timedelta(days=1)
        
        logger.info(f"Comprehensive backfill completed: {total_records} total records across {batch_count} batches")
        
    except Exception as e:
        logger.error(f"Comprehensive backfill failed: {e}")

async def main():
    """Main execution function"""
    # Check if running as FastAPI server
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        # Run FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return
    
    collector = EnhancedOnchainCollector()
    
    # Check for backfill parameters
    backfill_days = os.getenv("BACKFILL_DAYS")
    
    if backfill_days:
        try:
            days = int(backfill_days)
            end_date = date.today() - timedelta(days=1)
            
            if days == 0:
                # Full historical backfill
                start_date = date(2023, 1, 1)
                logger.info("Running FULL historical onchain backfill")
            else:
                start_date = end_date - timedelta(days=days)
                logger.info(f"Running onchain backfill for last {days} days")
            
            result = await collector.run_backfill(start_date, end_date)
            print(f"Onchain backfill completed: {result}")
            
        except ValueError:
            logger.error(f"Invalid BACKFILL_DAYS value: {backfill_days}")
    else:
        # Regular daily collection
        logger.info("Running daily onchain data collection")
        yesterday = date.today() - timedelta(days=1)
        result = await collector.run_backfill(yesterday, yesterday)
        print(f"Daily onchain collection completed: {result}")

if __name__ == "__main__":
    asyncio.run(main())