#!/usr/bin/env python3
"""
Centralized Table Configuration
Central registry of all database table names to prevent confusion and duplication
"""

# ==============================================================================
# MASTER TABLE REGISTRY - UPDATED POST-CONSOLIDATION
# Single Source of Truth for All Collection Tables
# ==============================================================================

# PRIMARY COLLECTION TABLES (Database.Table)
PRIMARY_COLLECTION_TABLES = {
    # Core Data Collection
    "NEWS": "crypto_news.news_data",              # Master news and sentiment data (323K records)
    "PRICES": "crypto_prices.price_data_real",     # Raw price data collection (4.1M records)
    "TECHNICAL": "crypto_prices.technical_indicators", # Technical analysis data (3.8M records)
    "OHLC": "crypto_prices.ohlc_data",            # OHLC candlestick data (498K records)
    "ONCHAIN": "crypto_prices.onchain_data", # Blockchain metrics for ML (NEW - real blockchain data)
    "MACRO": "crypto_prices.macro_indicators",     # Economic indicators (50K records)
    "SENTIMENT": "crypto_prices.real_time_sentiment_signals", # Sentiment analysis (112K records)
    
    # ML and Analytics
    "ML_FEATURES": "crypto_prices.ml_features_materialized", # ML feature store (3.6M records)
    "TRADING_SIGNALS": "crypto_prices.trading_signals",      # Trading recommendations (115K records)
    
    # Supporting Tables
    "ASSETS": "crypto_prices.crypto_assets",       # Asset registry (362 assets)
    "MONITORING": "crypto_transactions.service_monitoring", # System monitoring
}

# DEPRECATED TABLES (Still exist but should not be used)
DEPRECATED_ACTIVE_TABLES = {
    "crypto_prices.crypto_news": "crypto_news.news_data",           # 119K records - duplicate news
    "crypto_prices.sentiment_aggregation": "crypto_prices.real_time_sentiment_signals", # 67K records
    "crypto_news.stock_market_news_data": "crypto_news.news_data",  # 1.4K records
    "crypto_news.crypto_sentiment_data": "crypto_prices.real_time_sentiment_signals", # 33K records
    "crypto_news.macro_economic_data": "crypto_prices.macro_indicators", # 14K records
    "crypto_prices.crypto_onchain_data_old": "crypto_prices.onchain_data", # 153K records - price data misnamed as onchain
}

# ==============================================================================
# CRYPTO ASSETS & SYMBOL MANAGEMENT - MULTI-EXCHANGE COMPATIBLE
# ==============================================================================

# Master symbol registry table
SYMBOL_REGISTRY_TABLE = "crypto_prices.crypto_assets"

# Universal symbol format standards (forward-compatible with all exchanges)
SYMBOL_STANDARDS = {
    "internal_format": "BASEUSD",  # Our internal standard: BTCUSD, ETHUSD
    "base_currency": "USD",        # Primary quote currency
    "case_format": "UPPER",       # Always uppercase
    "separator": "",              # No separators in internal format
    "min_length": 6,              # Minimum symbol length (BTCUSD = 6)
    "max_length": 12,             # Maximum symbol length
    "required_suffix": "USD",     # All symbols must end with USD
    "allowed_chars": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
}

# Multi-Exchange Symbol Format Mapping (for API compatibility)
EXCHANGE_FORMATS = {
    "coinbase": {
        "format": "BASE-USD",
        "separator": "-", 
        "examples": {"BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD"}
    },
    "binance": {
        "format": "BASEUSDT", 
        "separator": "",
        "examples": {"BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT"}
    },
    "kraken": {
        "format": "BASEUSD",
        "separator": "",
        "examples": {"BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD"}
    },
    "internal": {
        "format": "BASEUSD",
        "separator": "", 
        "examples": {"BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD"}
    }
}

# Dynamic symbol management functions (replaces hardcoded mappings)
def get_exchange_symbol_mappings(exchange: str = "coinbase", use_cache: bool = True) -> dict:
    """Get symbol mappings from crypto_assets table dynamically"""
    import mysql.connector
    import os
    from datetime import datetime, timedelta
    
    # Simple caching to avoid repeated DB calls
    cache_key = f"_symbol_cache_{exchange}"
    cache_time_key = f"_symbol_cache_time_{exchange}"
    cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    # Check cache
    if use_cache and hasattr(get_exchange_symbol_mappings, cache_key):
        cache_time = getattr(get_exchange_symbol_mappings, cache_time_key, None)
        if cache_time and datetime.now() - cache_time < cache_duration:
            return getattr(get_exchange_symbol_mappings, cache_key)
    
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "172.22.32.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database="crypto_prices",
            charset='utf8mb4'
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # Get symbols based on exchange support
        if exchange == "coinbase":
            query = """
                SELECT symbol, name, coingecko_id, aliases 
                FROM crypto_assets 
                WHERE is_active = 1 AND coinbase_supported = 1
                ORDER BY symbol
            """
        else:
            # For other exchanges, get all active symbols
            query = """
                SELECT symbol, name, coingecko_id, aliases 
                FROM crypto_assets 
                WHERE is_active = 1
                ORDER BY symbol
            """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Build mapping dictionary
        mappings = {}
        for row in results:
            internal_symbol = row['symbol']
            
            # Generate exchange-specific format
            if exchange == "coinbase":
                if internal_symbol.endswith('USD'):
                    base = internal_symbol[:-3]
                    exchange_format = f"{base}-USD"
                else:
                    exchange_format = f"{internal_symbol}-USD"
            elif exchange == "binance":
                if internal_symbol.endswith('USD'):
                    base = internal_symbol[:-3]
                    exchange_format = f"{base}USDT"
                else:
                    exchange_format = f"{internal_symbol}USDT"
            else:
                exchange_format = internal_symbol
            
            mappings[exchange_format] = internal_symbol
        
        cursor.close()
        conn.close()
        
        # Cache results
        setattr(get_exchange_symbol_mappings, cache_key, mappings)
        setattr(get_exchange_symbol_mappings, cache_time_key, datetime.now())
        
        return mappings
        
    except Exception as e:
        print(f"Warning: Could not load symbols from database: {e}")
        # Fallback to empty dict if DB connection fails
        return {}

def get_supported_symbols(exchange: str = "coinbase", format_type: str = "internal") -> list:
    """Get list of supported symbols from crypto_assets table"""
    mappings = get_exchange_symbol_mappings(exchange)
    
    if format_type == "internal":
        return list(mappings.values())
    elif format_type == "exchange":
        return list(mappings.keys())
    else:
        return list(mappings.items())  # Return tuples of (exchange_format, internal_format)

def resolve_symbol_from_exchange(exchange_symbol: str, source_exchange: str = "auto") -> str:
    """Resolve exchange symbol to internal format using crypto_assets data"""
    # Auto-detect exchange format
    if source_exchange == "auto":
        if "-" in exchange_symbol:
            source_exchange = "coinbase"
        elif exchange_symbol.endswith("USDT"):
            source_exchange = "binance"
        else:
            source_exchange = "internal"
    
    if source_exchange == "internal":
        return exchange_symbol
    
    mappings = get_exchange_symbol_mappings(source_exchange)
    return mappings.get(exchange_symbol, exchange_symbol)  # Return original if not found

def get_symbol_registry_table() -> str:
    """Get the master symbol registry table name"""
    return SYMBOL_REGISTRY_TABLE

def normalize_symbol_for_exchange(symbol: str, exchange: str = "internal") -> str:
    """Convert symbol to specific exchange format using crypto_assets data"""
    if not symbol:
        return symbol
        
    # First normalize to internal format
    internal_symbol = normalize_symbol_to_internal(symbol)
    
    if exchange == "internal" or exchange not in EXCHANGE_FORMATS:
        return internal_symbol
        
    # Use dynamic mapping instead of hardcoded values
    if exchange == "coinbase":
        # Convert BTCUSD -> BTC-USD
        if internal_symbol.endswith("USD"):
            base = internal_symbol[:-3]
            return f"{base}-USD"
    elif exchange == "binance":
        # Convert BTCUSD -> BTCUSDT
        if internal_symbol.endswith("USD"):
            base = internal_symbol[:-3]
            return f"{base}USDT"
    elif exchange == "kraken":
        # Kraken uses same format as internal
        return internal_symbol
    
    return internal_symbol

def normalize_symbol_to_internal(symbol: str) -> str:
    """Normalize any symbol format to our internal standard (BASEUSD)"""
    if not symbol:
        return symbol
    
    # Convert to uppercase
    symbol = symbol.upper().strip()
    
    # Handle common exchange formats
    if "-" in symbol:
        # Coinbase format: BTC-USD -> BTCUSD
        symbol = symbol.replace("-", "")
    elif symbol.endswith("USDT"):
        # Binance format: BTCUSDT -> BTCUSD
        symbol = symbol[:-4] + "USD"
    elif "/" in symbol:
        # Some exchanges use BTC/USD -> BTCUSD
        symbol = symbol.replace("/", "")
    
    # Ensure USD suffix if not present
    if not symbol.endswith("USD"):
        symbol = symbol + "USD"
    
    return symbol

def validate_symbol(symbol: str) -> dict:
    """Comprehensive symbol validation against our standards"""
    validation_result = {
        "valid": True,
        "normalized_symbol": normalize_symbol_to_internal(symbol),
        "issues": [],
        "exchange_formats": {}
    }
    
    normalized = validation_result["normalized_symbol"]
    standards = SYMBOL_STANDARDS
    
    # Length validation
    if len(normalized) < standards["min_length"]:
        validation_result["valid"] = False
        validation_result["issues"].append(f"Symbol too short (min {standards['min_length']} chars)")
    
    if len(normalized) > standards["max_length"]:
        validation_result["valid"] = False
        validation_result["issues"].append(f"Symbol too long (max {standards['max_length']} chars)")
    
    # Format validation
    if not normalized.endswith(standards["required_suffix"]):
        validation_result["valid"] = False
        validation_result["issues"].append(f"Symbol must end with {standards['required_suffix']}")
    
    # Character validation
    for char in normalized:
        if char not in standards["allowed_chars"]:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Invalid character '{char}' in symbol")
    
    # Generate exchange format examples
    if validation_result["valid"]:
        for exchange, config in EXCHANGE_FORMATS.items():
            validation_result["exchange_formats"][exchange] = normalize_symbol_for_exchange(normalized, exchange)
    
    return validation_result

def get_supported_exchanges() -> list:
    """Get list of all supported exchange formats"""
    return list(EXCHANGE_FORMATS.keys())

def convert_symbol_batch(symbols: list, from_exchange: str = "auto", to_exchange: str = "internal") -> dict:
    """Convert multiple symbols between exchange formats using crypto_assets data"""
    results = {}
    
    for symbol in symbols:
        try:
            # Use dynamic symbol resolution
            internal = resolve_symbol_from_exchange(symbol, from_exchange)
            
            # Then convert to target exchange
            converted = normalize_symbol_for_exchange(internal, to_exchange)
            
            results[symbol] = {
                "success": True,
                "internal": internal,
                "converted": converted,
                "from_exchange": from_exchange if from_exchange != "auto" else "detected",
                "to_exchange": to_exchange
            }
        except Exception as e:
            results[symbol] = {
                "success": False,
                "error": str(e),
                "from_exchange": from_exchange,
                "to_exchange": to_exchange
            }
    
    return results

# Tables that have been archived with _Archive suffix
ARCHIVED_TABLES = {
    "price_data_old_Archive": "Archived old price data",
    "ml_trading_signals_old_Archive": "Archived old trading signals", 
    "technical_indicators_backup_20251104_214228_Archive": "Archived backup data",
    "technical_indicators_backup_20251104_214305_Archive": "Archived backup data",
    "technical_indicators_corrupted_backup_Archive": "Archived corrupted data",
    "assets_archived_Archive": "Archived asset data"
}

def get_collector_symbols(collector_type: str) -> list:
    """Get symbols for specific collector type from crypto_assets table"""
    try:
        import mysql.connector
        import os
        
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "172.22.32.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database="crypto_prices",
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # Different queries based on collector type
        if collector_type.lower() in ["coinbase", "price", "technical"]:
            # For price/technical collectors, prioritize coinbase-supported symbols
            cursor.execute(
                "SELECT symbol FROM crypto_assets WHERE is_active = 1 AND coinbase_supported = 1 ORDER BY market_cap_rank, symbol"
            )
        elif collector_type.lower() == "onchain":
            # For onchain, get top market cap symbols (onchain data availability)
            cursor.execute(
                "SELECT symbol FROM crypto_assets WHERE is_active = 1 AND market_cap_rank <= 100 ORDER BY market_cap_rank, symbol"
            )
        elif collector_type.lower() == "sentiment":
            # For sentiment, get symbols with high social media presence
            cursor.execute(
                "SELECT symbol FROM crypto_assets WHERE is_active = 1 AND (aliases IS NOT NULL OR name IS NOT NULL) ORDER BY market_cap_rank, symbol"
            )
        else:
            # Default: all active symbols
            cursor.execute(
                "SELECT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank, symbol"
            )
        
        symbols = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return symbols
        
    except Exception as e:
        print(f"Warning: Could not get symbols from database: {e}")
        return []  # Return empty list on error

def validate_symbol_exists(symbol: str) -> bool:
    """Check if symbol exists in crypto_assets table"""
    try:
        import mysql.connector
        import os
        
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "172.22.32.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database="crypto_prices",
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM crypto_assets WHERE symbol = %s AND is_active = 1",
            (symbol,)
        )
        
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return count > 0
        
    except Exception as e:
        print(f"Warning: Could not validate symbol {symbol}: {e}")
        return False  # Assume invalid on error

def get_symbol_metadata(symbol: str) -> dict:
    """Get metadata for a symbol from crypto_assets table"""
    try:
        import mysql.connector
        import os
        
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "172.22.32.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database="crypto_prices",
            charset='utf8mb4'
        )
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM crypto_assets WHERE symbol = %s AND is_active = 1",
            (symbol,)
        )
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result or {}
        
    except Exception as e:
        print(f"Warning: Could not get metadata for {symbol}: {e}")
        return {}

# ==============================================================================
# CONFIGURATION HELPERS
# ==============================================================================

def get_primary_table_by_type(table_type: str) -> str:
    """Get primary table name by type"""
    table_type_upper = table_type.upper()
    if table_type_upper not in PRIMARY_COLLECTION_TABLES:
        available = list(PRIMARY_COLLECTION_TABLES.keys())
        raise ValueError(f"Unknown table type: {table_type}. Available: {available}")
    
    return PRIMARY_COLLECTION_TABLES[table_type_upper]

def get_master_onchain_table() -> str:
    """Get the master onchain data table name"""
    return PRIMARY_COLLECTION_TABLES["ONCHAIN"]

def get_master_technical_table() -> str:
    """Get the master technical indicators table name"""
    return PRIMARY_COLLECTION_TABLES["TECHNICAL"]

def get_master_news_table() -> str:
    """Get the master news data table name"""
    return PRIMARY_COLLECTION_TABLES["NEWS"]

def get_master_price_table() -> str:
    """Get the master price data table name"""
    return PRIMARY_COLLECTION_TABLES["PRICES"]

def get_master_assets_table() -> str:
    """Get the master crypto assets table name (symbol registry)"""
    return PRIMARY_COLLECTION_TABLES["ASSETS"]

def validate_table_usage(table_name: str) -> dict:
    """Validate if a table name is in our centralized config"""
    # Check if table is a primary collection table
    for key, primary_table in PRIMARY_COLLECTION_TABLES.items():
        if table_name == primary_table:
            return {"status": "approved", "type": key, "table": primary_table}
    
    # Check if table is deprecated
    if table_name in DEPRECATED_ACTIVE_TABLES:
        replacement = DEPRECATED_ACTIVE_TABLES[table_name]
        return {
            "status": "deprecated", 
            "table": table_name,
            "replacement": replacement,
            "action": f"Use {replacement} instead"
        }
    
    # Unknown table
    return {"status": "unknown", "table": table_name}

def get_symbol_validation_query() -> str:
    """Get SQL query to validate symbols from crypto_assets table"""
    return f"""
    SELECT 
        symbol,
        name,
        is_active,
        coinbase_supported,
        coingecko_id,
        aliases
    FROM {get_symbol_registry_table()}
    WHERE is_active = 1
    AND symbol IS NOT NULL
    AND symbol != ''
    ORDER BY symbol
    """

def get_active_symbols_query() -> str:
    """Get SQL query to fetch all active symbols for collectors"""
    return f"""
    SELECT symbol 
    FROM {get_symbol_registry_table()}
    WHERE is_active = 1 
    AND symbol IS NOT NULL
    ORDER BY symbol
    """

def get_coinbase_symbols_query() -> str:
    """Get SQL query to fetch Coinbase-supported symbols"""
    return f"""
    SELECT symbol, coingecko_id, name
    FROM {get_symbol_registry_table()}
    WHERE is_active = 1
    AND coinbase_supported = 1
    AND symbol IS NOT NULL
    ORDER BY symbol
    """

# ==============================================================================
# COLLECTOR CONFIGURATION - POST-CONSOLIDATION
# ==============================================================================

# Current Active Collectors and Their Target Tables
COLLECTOR_TABLE_CONFIG = {
    "crypto-news-collector": {
        "target_table": "crypto_news.news_data",
        "status": "active",
        "description": "Collects crypto news and sentiment data",
        "records": "323K"
    },
    "enhanced-crypto-prices": {
        "target_table": "crypto_prices.price_data_real", 
        "status": "active",
        "description": "Collects real-time price data",
        "records": "4.1M"
    },
    "technical-calculator": {
        "target_table": "crypto_prices.technical_indicators",
        "status": "active", 
        "description": "Calculates technical analysis indicators",
        "records": "3.8M"
    },
    "onchain-collector": {
        "target_table": "crypto_prices.onchain_data",
        "status": "active",
        "description": "Collects blockchain metrics",
        "records": "12+"
    },
    "macro-collector": {
        "target_table": "crypto_prices.macro_indicators",
        "status": "active",
        "description": "Collects economic indicators", 
        "records": "50K"
    },
    "enhanced-sentiment-collector": {
        "target_table": "crypto_prices.real_time_sentiment_signals",
        "status": "active",
        "description": "Processes sentiment signals",
        "records": "112K"
    },
    "ml-feature-calculator": {
        "target_table": "crypto_prices.ml_features_materialized",
        "status": "active",
        "description": "Generates ML features",
        "records": "3.6M"
    }
}

# Tables that need final cleanup
FINAL_CLEANUP_NEEDED = [
    # CONSOLIDATION COMPLETED - All duplicates archived as of November 7, 2025
    # Tables below have been archived with _final_archive_YYYYMMDD_HHMMSS_old suffix
    # "crypto_prices.crypto_news",           # ARCHIVED
    # "crypto_prices.sentiment_aggregation", # ARCHIVED  
    # "crypto_news.stock_market_news_data",  # ARCHIVED
    # "crypto_news.crypto_sentiment_data",   # ARCHIVED
    # "crypto_news.macro_economic_data"      # ARCHIVED
]

# CONSOLIDATION STATUS
CONSOLIDATION_STATUS = {
    "completed": True,
    "completion_date": "2025-11-07",
    "primary_tables_count": 9,
    "duplicates_archived": True,
    "single_source_of_truth": True,
    "status": "PRODUCTION_READY"
}

def get_collector_config(collector_name: str) -> dict:
    """Get table configuration for a specific collector"""
    if collector_name not in COLLECTOR_TABLE_CONFIG:
        raise ValueError(f"Unknown collector: {collector_name}")
    
    return COLLECTOR_TABLE_CONFIG[collector_name]

def get_primary_collection_tables() -> dict:
    """Get all primary collection tables"""
    return PRIMARY_COLLECTION_TABLES

def is_consolidation_complete() -> bool:
    """Check if database consolidation is complete"""
    return CONSOLIDATION_STATUS["completed"]

def get_consolidation_status() -> dict:
    """Get full consolidation status"""
    return CONSOLIDATION_STATUS

def validate_table_is_primary(table_name: str) -> bool:
    """Check if a table is a primary collection table"""
    return table_name in PRIMARY_COLLECTION_TABLES.values()

if __name__ == "__main__":
    print("📋 CENTRALIZED TABLE REGISTRY & SYMBOL MANAGEMENT")
    print("=" * 70)
    
    print(f"\n🎯 CONSOLIDATION STATUS: {CONSOLIDATION_STATUS['status']}")
    print(f"📅 Completed: {CONSOLIDATION_STATUS['completion_date']}")
    print(f"📊 Primary tables: {CONSOLIDATION_STATUS['primary_tables_count']}")
    
    print(f"\n✅ PRIMARY COLLECTION TABLES:")
    for table_type, table_name in PRIMARY_COLLECTION_TABLES.items():
        print(f"   {table_type:<15}: {table_name}")
    
    print(f"\n🔗 SYMBOL REGISTRY: {get_symbol_registry_table()}")
    print(f"📏 Internal Format: {SYMBOL_STANDARDS['internal_format']} (e.g., BTCUSD)")
    
    print(f"\n🌐 SUPPORTED EXCHANGE FORMATS:")
    for exchange, config in EXCHANGE_FORMATS.items():
        example = list(config['examples'].values())[0] if config['examples'] else "N/A"
        print(f"   {exchange.upper():<10}: {config['format']:<10} (e.g., {example})")
    
    print(f"\n🔧 SYMBOL VALIDATION EXAMPLE:")
    test_symbols = ["BTC-USD", "ETHUSDT", "ADA/USD", "SOLUSD"]
    for symbol in test_symbols:
        result = validate_symbol(symbol)
        status = "✅ VALID" if result['valid'] else "❌ INVALID"
        print(f"   {symbol:<10} -> {result['normalized_symbol']:<8} {status}")
        if result['issues']:
            for issue in result['issues']:
                print(f"      Issue: {issue}")
    
    print(f"\n📋 COLLECTOR CONFIGURATIONS:")
    for collector, config in COLLECTOR_TABLE_CONFIG.items():
        print(f"   {collector:<25}: {config['target_table']} ({config['records']})")
    
    print(f"\n⚠️  DEPRECATED TABLES (use replacements):")
    for deprecated, replacement in DEPRECATED_ACTIVE_TABLES.items():
        print(f"   {deprecated} ->")
        print(f"      {replacement}")
    
    print(f"\n💡 QUICK REFERENCE:")
    print(f"   • Symbol Registry: {get_symbol_registry_table()}")
    print(f"   • Active Symbols Query: {get_active_symbols_query().strip().replace(chr(10), ' ')}")
    print(f"   • Coinbase Symbols Query: {get_coinbase_symbols_query().strip().replace(chr(10), ' ')}")
    
    print(f"\n🚀 SYMBOL CONVERSION EXAMPLES:")
    conversions = convert_symbol_batch(["BTC-USD", "ETHUSDT", "ADA-USD"], "auto", "internal")
    for original, result in conversions.items():
        if result['success']:
            print(f"   {original} -> {result['converted']} (via {result['from_exchange']})")
        else:
            print(f"   {original} -> ERROR: {result['error']}")
