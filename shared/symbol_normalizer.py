#!/usr/bin/env python3
"""
Standardized Symbol Normalization Utility
Ensures exchange-independent symbol handling across all collectors

This utility provides a consistent approach to symbol normalization using the crypto_assets table,
ensuring that all collectors use standardized symbols regardless of the exchange API being used.

Usage Example:
    from shared.symbol_normalizer import StandardSymbolNormalizer
    
    normalizer = StandardSymbolNormalizer()
    symbols = normalizer.get_active_symbols()
    coingecko_id = normalizer.get_coingecko_id('BTC')
    coin_name = normalizer.get_coin_name('ETH')
"""

import logging
import time
from typing import List, Dict, Optional, Any
from shared.database_config import get_db_connection

logger = logging.getLogger(__name__)

class StandardSymbolNormalizer:
    """
    Standardized symbol normalization using crypto_assets table
    
    This class provides exchange-independent symbol handling by:
    1. Using crypto_assets table as the single source of truth
    2. Mapping external exchange symbols to our standard format
    3. Providing efficient cached lookups
    4. Handling fallbacks for essential cryptocurrencies
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize the symbol normalizer
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._symbol_cache = {}
        self._cache_timestamp = 0
        
        # Fallback mappings for essential symbols (when database is unavailable)
        self.fallback_coingecko_ids = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'BCH': 'bitcoin-cash', 'LTC': 'litecoin',
            'ADA': 'cardano', 'DOT': 'polkadot', 'LINK': 'chainlink', 'ATOM': 'cosmos',
            'SOL': 'solana', 'AVAX': 'avalanche-2', 'MATIC': 'polygon', 'ALGO': 'algorand',
            'XTZ': 'tezos', 'FLOW': 'flow', 'ICP': 'internet-computer', 'NEAR': 'near',
            'FTM': 'fantom', 'ONE': 'harmony', 'LUNA': 'terra-luna', 'KSM': 'kusama',
            'EGLD': 'elrond-erd-2', 'XLM': 'stellar', 'XRP': 'ripple', 'BNB': 'binancecoin',
            'DOGE': 'dogecoin', 'SHIB': 'shiba-inu', 'TRX': 'tron', 'USDT': 'tether',
            'USDC': 'usd-coin', 'DAI': 'dai', 'UNI': 'uniswap', 'AAVE': 'aave'
        }
        
    def _is_cache_valid(self) -> bool:
        """Check if symbol cache is still valid"""
        return (time.time() - self._cache_timestamp) < self.cache_ttl and bool(self._symbol_cache)
    
    def get_active_symbols(self, coinbase_only: bool = True, limit: Optional[int] = None) -> List[str]:
        """
        Get active symbols from crypto_assets table
        
        Args:
            coinbase_only: If True, only return Coinbase-supported symbols
            limit: Optional limit on number of symbols returned (ordered by market cap rank)
            
        Returns:
            List of standardized symbol strings
        """
        if self._is_cache_valid():
            symbols = list(self._symbol_cache.keys())
            if limit:
                # Re-sort by market cap rank and limit
                symbol_ranks = [(s, self._symbol_cache[s].get('market_cap_rank', 9999)) for s in symbols]
                symbol_ranks.sort(key=lambda x: x[1])
                symbols = [s[0] for s in symbol_ranks[:limit]]
            logger.debug(f"[CACHE] Using cached symbols: {len(symbols)} symbols")
            return symbols
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build query based on parameters
            query = """
                SELECT symbol, coingecko_id, name, market_cap_rank, coinbase_supported
                FROM crypto_assets 
                WHERE is_active = 1
                AND symbol NOT LIKE '%-%'  -- Skip USD pairs
                AND symbol IS NOT NULL
                AND symbol != ''
            """
            
            if coinbase_only:
                query += " AND coinbase_supported = 1"
                
            query += """
                ORDER BY 
                    CASE WHEN market_cap_rank IS NOT NULL THEN market_cap_rank ELSE 9999 END,
                    symbol ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            symbol_data = cursor.fetchall()
            
            # Cache the symbol mappings
            self._symbol_cache = {}
            symbols = []
            
            for symbol, coingecko_id, name, rank, coinbase_supported in symbol_data:
                symbols.append(symbol)
                self._symbol_cache[symbol] = {
                    'coingecko_id': coingecko_id,
                    'name': name,
                    'market_cap_rank': rank,
                    'coinbase_supported': bool(coinbase_supported)
                }
            
            # Update cache timestamp
            self._cache_timestamp = time.time()
            
            logger.info(f"[SYMBOLS] Retrieved {len(symbols)} active symbols from crypto_assets")
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting active symbols from crypto_assets: {e}")
            # Fallback to essential symbols
            fallback_symbols = list(self.fallback_coingecko_ids.keys())[:20]
            if coinbase_only:
                # Filter to known Coinbase symbols
                coinbase_essentials = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'ATOM', 'AVAX', 'MATIC', 'ALGO']
                fallback_symbols = [s for s in fallback_symbols if s in coinbase_essentials]
            
            logger.warning(f"[SYMBOLS] Using fallback symbols: {len(fallback_symbols)} symbols")
            return fallback_symbols[:limit] if limit else fallback_symbols
            
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def get_coingecko_id(self, symbol: str) -> str:
        """
        Get CoinGecko ID for a symbol using standardized lookup
        
        Args:
            symbol: The standardized symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            CoinGecko ID string (e.g., 'bitcoin', 'ethereum')
        """
        # Check cache first
        if self._is_cache_valid() and symbol in self._symbol_cache:
            coingecko_id = self._symbol_cache[symbol]['coingecko_id']
            if coingecko_id:
                return coingecko_id
        
        # Query database if not in cache
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT coingecko_id 
                FROM crypto_assets 
                WHERE symbol = %s 
                AND is_active = 1
                LIMIT 1
            """, (symbol.upper(),))
            
            result = cursor.fetchone()
            if result and result[0]:
                logger.debug(f"[MAPPING] Database lookup for {symbol}: {result[0]}")
                return result[0]
                
        except Exception as e:
            logger.warning(f"[MAPPING] Database lookup failed for {symbol}: {e}")
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        
        # Fallback mapping
        coingecko_id = self.fallback_coingecko_ids.get(symbol.upper())
        if coingecko_id:
            logger.debug(f"[MAPPING] Fallback mapping for {symbol}: {coingecko_id}")
            return coingecko_id
        
        # Ultimate fallback
        fallback_id = symbol.lower()
        logger.warning(f"[MAPPING] Using lowercase fallback for {symbol}: {fallback_id}")
        return fallback_id
    
    def get_coin_name(self, symbol: str) -> str:
        """
        Get human-readable coin name for a symbol
        
        Args:
            symbol: The standardized symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Human-readable coin name (e.g., 'Bitcoin', 'Ethereum')
        """
        # Check cache first
        if self._is_cache_valid() and symbol in self._symbol_cache:
            name = self._symbol_cache[symbol]['name']
            if name:
                return name
        
        # Query database if not in cache
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name 
                FROM crypto_assets 
                WHERE symbol = %s 
                AND is_active = 1
                LIMIT 1
            """, (symbol.upper(),))
            
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
                
        except Exception as e:
            logger.warning(f"[MAPPING] Database name lookup failed for {symbol}: {e}")
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        
        # Fallback to formatted symbol
        return symbol.replace('_', ' ').title()
    
    def is_coinbase_supported(self, symbol: str) -> bool:
        """
        Check if a symbol is supported on Coinbase
        
        Args:
            symbol: The standardized symbol
            
        Returns:
            True if supported on Coinbase, False otherwise
        """
        # Check cache first
        if self._is_cache_valid() and symbol in self._symbol_cache:
            return self._symbol_cache[symbol].get('coinbase_supported', False)
        
        # Query database
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT coinbase_supported 
                FROM crypto_assets 
                WHERE symbol = %s 
                AND is_active = 1
                LIMIT 1
            """, (symbol.upper(),))
            
            result = cursor.fetchone()
            if result:
                return bool(result[0])
                
        except Exception as e:
            logger.warning(f"[MAPPING] Coinbase support lookup failed for {symbol}: {e}")
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        
        # Fallback - assume major symbols are supported
        return symbol.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'ATOM', 'AVAX']
    
    def normalize_exchange_symbol(self, exchange_symbol: str, exchange: str) -> str:
        """
        Normalize an exchange-specific symbol to our standard format
        
        Args:
            exchange_symbol: Symbol as returned by exchange API
            exchange: Exchange identifier ('coinbase', 'binance', etc.)
            
        Returns:
            Standardized symbol
        """
        # Handle different exchange formats
        if exchange.lower() == 'coinbase':
            # Coinbase uses standard symbols mostly
            return exchange_symbol.upper().replace('-USD', '').replace('USD', '')
        elif exchange.lower() == 'binance':
            # Binance uses different formats
            return exchange_symbol.upper().replace('USDT', '').replace('BUSD', '')
        else:
            # Generic normalization
            return exchange_symbol.upper().split('-')[0].split('/')[0]
    
    def get_symbol_metadata(self, symbol: str) -> Dict[str, Any]:
        """
        Get complete metadata for a symbol
        
        Args:
            symbol: The standardized symbol
            
        Returns:
            Dictionary with symbol metadata
        """
        return {
            'symbol': symbol,
            'coingecko_id': self.get_coingecko_id(symbol),
            'name': self.get_coin_name(symbol),
            'coinbase_supported': self.is_coinbase_supported(symbol),
            'market_cap_rank': self._symbol_cache.get(symbol, {}).get('market_cap_rank') if self._is_cache_valid() else None
        }

# Global instance for easy importing
symbol_normalizer = StandardSymbolNormalizer()