"""
Universal Symbol Normalizer for Cross-Exchange Compatibility
============================================================

This module provides symbol normalization for cryptocurrency data collection,
using traditional ticker symbols (BTC, ETH, ADA, SOL) that are universally
recognized across ALL major exchanges including:

- Binance: BTC, ETH, ADA, SOL
- Coinbase: BTC, ETH, ADA, SOL  
- Kraken: BTC, ETH, ADA, SOL
- KuCoin: BTC, ETH, ADA, SOL
- Gemini: BTC, ETH, ADA, SOL

This ensures maximum compatibility and prevents duplicates caused by
mixed symbol formats (BTC vs bitcoin, ETH vs ethereum, etc.)
"""

import mysql.connector
from typing import Dict, Set, Optional
import logging

class UniversalSymbolNormalizer:
    """
    Universal symbol normalizer using traditional ticker symbols
    for maximum cross-exchange compatibility.
    """
    
    def __init__(self, db_config: Dict):
        """
        Initialize normalizer with database configuration
        
        Args:
            db_config: Database connection parameters
        """
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        self._old_to_canonical_cache = None
        self._canonical_symbols_cache = None
        
    def get_old_to_canonical_map(self) -> Dict[str, str]:
        """
        Get mapping from old/alternative symbols to canonical ticker symbols
        
        Returns:
            Dict mapping old symbols to canonical ticker symbols
            
        Example:
            {
                'BITCOIN': 'BTC',
                'bitcoin': 'BTC', 
                'ETHEREUM': 'ETH',
                'ethereum': 'ETH',
                'CARDANO': 'ADA',
                'cardano': 'ADA'
            }
        """
        if self._old_to_canonical_cache is not None:
            return self._old_to_canonical_cache
            
        connection = None
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Get mapping from crypto_assets: various formats -> ticker symbol
            cursor.execute("""
                SELECT symbol, coingecko_id, name
                FROM crypto_assets 
                WHERE is_active = 1 
                AND symbol IS NOT NULL
                AND symbol != ''
            """)
            
            mapping = {}
            
            for symbol, coingecko_id, name in cursor.fetchall():
                canonical_symbol = symbol.upper()  # Use ticker symbol as canonical
                
                # Map coingecko_id variations to ticker symbol
                if coingecko_id:
                    mapping[coingecko_id.lower()] = canonical_symbol
                    mapping[coingecko_id.upper()] = canonical_symbol
                    mapping[coingecko_id] = canonical_symbol
                
                # Map name variations to ticker symbol  
                if name:
                    mapping[name.upper()] = canonical_symbol
                    mapping[name.lower()] = canonical_symbol
                    
                # Map symbol variations
                mapping[symbol.lower()] = canonical_symbol
                mapping[symbol.upper()] = canonical_symbol
                
            # Add common variations
            common_mappings = {
                'BITCOIN': 'BTC',
                'bitcoin': 'BTC',
                'ETHEREUM': 'ETH', 
                'ethereum': 'ETH',
                'CARDANO': 'ADA',
                'cardano': 'ADA', 
                'SOLANA': 'SOL',
                'solana': 'SOL',
                'CHAINLINK': 'LINK',
                'chainlink': 'LINK',
                'POLKADOT': 'DOT', 
                'polkadot': 'DOT',
                'UNISWAP': 'UNI',
                'uniswap': 'UNI',
                'BINANCECOIN': 'BNB',
                'binancecoin': 'BNB',
                'TETHER': 'USDT',
                'tether': 'USDT'
            }
            
            mapping.update(common_mappings)
            
            self._old_to_canonical_cache = mapping
            self.logger.info(f"Loaded {len(mapping)} symbol mappings for universal compatibility")
            
            return mapping
            
        except Exception as e:
            self.logger.error(f"Error loading symbol mappings: {e}")
            return {}
        finally:
            if connection:
                connection.close()
    
    def get_canonical_symbols(self) -> Set[str]:
        """
        Get set of canonical ticker symbols (BTC, ETH, ADA, SOL, etc.)
        
        Returns:
            Set of canonical ticker symbols for active cryptocurrencies
        """
        if self._canonical_symbols_cache is not None:
            return self._canonical_symbols_cache
            
        connection = None
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Get all active ticker symbols
            cursor.execute("""
                SELECT DISTINCT symbol
                FROM crypto_assets 
                WHERE is_active = 1 
                AND symbol IS NOT NULL
                AND symbol != ''
            """)
            
            symbols = {row[0].upper() for row in cursor.fetchall()}
            
            self._canonical_symbols_cache = symbols
            self.logger.info(f"Loaded {len(symbols)} canonical ticker symbols")
            
            return symbols
            
        except Exception as e:
            self.logger.error(f"Error loading canonical symbols: {e}")
            return set()
        finally:
            if connection:
                connection.close()
    
    def normalize_symbol(self, symbol: str) -> Optional[str]:
        """
        Normalize a single symbol to canonical ticker format
        
        Args:
            symbol: Symbol to normalize (e.g., 'bitcoin', 'ETHEREUM', 'cardano')
            
        Returns:
            Canonical ticker symbol (e.g., 'BTC', 'ETH', 'ADA') or None if not found
        """
        if not symbol:
            return None
            
        # Check if already canonical
        canonical_symbols = self.get_canonical_symbols()
        if symbol.upper() in canonical_symbols:
            return symbol.upper()
            
        # Check mapping
        mapping = self.get_old_to_canonical_map()
        return mapping.get(symbol)
    
    def normalize_symbols(self, symbols: list) -> list:
        """
        Normalize a list of symbols to canonical ticker format
        
        Args:
            symbols: List of symbols to normalize
            
        Returns:
            List of canonical ticker symbols, removing duplicates
        """
        normalized = []
        seen = set()
        
        for symbol in symbols:
            canonical = self.normalize_symbol(symbol)
            if canonical and canonical not in seen:
                normalized.append(canonical)
                seen.add(canonical)
                
        return normalized
    
    def is_canonical(self, symbol: str) -> bool:
        """
        Check if symbol is already in canonical ticker format
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if symbol is canonical ticker format
        """
        canonical_symbols = self.get_canonical_symbols()
        return symbol.upper() in canonical_symbols
    
    def clear_cache(self):
        """Clear cached data to force reload from database"""
        self._old_to_canonical_cache = None
        self._canonical_symbols_cache = None

# Backward compatibility alias
SymbolNormalizer = UniversalSymbolNormalizer
