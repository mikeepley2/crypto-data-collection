"""
Enhanced Placeholder Manager Configuration
Supports ALL data types: OHLC, Prices, Technicals, Onchain, Macro, Trading, Derivatives
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import timedelta

@dataclass
class CollectorConfig:
    """Configuration for each collector type"""
    table_name: str
    frequency: timedelta  # How often placeholders should be created
    key_fields: List[str]  # Fields that make each record unique
    required_fields: List[str]  # Fields that must be populated for completeness
    data_type: str  # Category of data
    priority: int = 5  # 1-10, higher = more important
    active: bool = True

# Comprehensive collector configurations for ALL data types
COLLECTOR_CONFIGS: Dict[str, CollectorConfig] = {
    # MACRO DATA
    "macro_economic": CollectorConfig(
        table_name="macro_economic_data",
        frequency=timedelta(days=1),
        key_fields=["indicator_name", "timestamp"],
        required_fields=["value", "indicator_name", "source"],
        data_type="macro",
        priority=8
    ),
    
    # TECHNICAL INDICATORS 
    "technical": CollectorConfig(
        table_name="technical_indicators",
        frequency=timedelta(days=1),  # Daily for historical, 5min for real-time
        key_fields=["symbol", "timestamp"],
        required_fields=["rsi", "macd", "bollinger_upper", "bollinger_lower"],
        data_type="technical",
        priority=7
    ),
    
    # ONCHAIN DATA (Primary)
    "onchain_primary": CollectorConfig(
        table_name="crypto_onchain_data",
        frequency=timedelta(days=1),
        key_fields=["symbol", "timestamp"],
        required_fields=["active_addresses", "transaction_count", "network_hash_rate"],
        data_type="onchain",
        priority=6
    ),
    
    # ONCHAIN DATA (Additional Tables)
    "onchain_secondary": CollectorConfig(
        table_name="onchain_data",
        frequency=timedelta(days=1),
        key_fields=["symbol", "timestamp"],
        required_fields=["active_addresses", "transaction_count"],
        data_type="onchain",
        priority=6
    ),
    
    "onchain_metrics": CollectorConfig(
        table_name="onchain_metrics",
        frequency=timedelta(days=1),
        key_fields=["symbol", "timestamp"],
        required_fields=["network_hash_rate", "difficulty"],
        data_type="onchain",
        priority=6
    ),
    
    # OHLC DATA
    "ohlc": CollectorConfig(
        table_name="ohlc_data",
        frequency=timedelta(minutes=5),  # 5-minute candles
        key_fields=["symbol", "timestamp"],
        required_fields=["open_price", "high_price", "low_price", "close_price", "volume"],
        data_type="ohlc",
        priority=9
    ),
    
    # PRICE DATA
    "crypto_prices": CollectorConfig(
        table_name="crypto_prices",
        frequency=timedelta(hours=1),  # Hourly price updates
        key_fields=["symbol", "timestamp"],
        required_fields=["price", "volume", "market_cap"],
        data_type="price",
        priority=10
    ),
    
    "price_data_real": CollectorConfig(
        table_name="price_data_real",
        frequency=timedelta(hours=1),
        key_fields=["symbol", "timestamp"],
        required_fields=["price", "volume"],
        data_type="price",
        priority=9
    ),
    
    # TRADING SIGNALS & MARKET DATA
    "trading_signals": CollectorConfig(
        table_name="trading_signals",
        frequency=timedelta(days=1),  # Daily signals
        key_fields=["symbol", "timestamp"],
        required_fields=["signal_type", "signal_strength", "confidence"],
        data_type="market",
        priority=7
    ),
    
    "enhanced_trading_signals": CollectorConfig(
        table_name="enhanced_trading_signals",
        frequency=timedelta(days=1),
        key_fields=["symbol", "timestamp"],
        required_fields=["signal_type", "signal_strength", "confidence", "ml_score"],
        data_type="market",
        priority=8
    ),
    
    # DERIVATIVES DATA
    "derivatives_ml": CollectorConfig(
        table_name="crypto_derivatives_ml",
        frequency=timedelta(days=1),  # Daily derivatives data
        key_fields=["symbol", "timestamp"],
        required_fields=["options_volume", "futures_volume", "open_interest", "implied_volatility"],
        data_type="derivatives",
        priority=6
    ),
    
    # NEWS & SENTIMENT (if needed)
    "crypto_news": CollectorConfig(
        table_name="crypto_news_data",
        frequency=timedelta(hours=4),  # Every 4 hours
        key_fields=["symbol", "timestamp", "article_url"],
        required_fields=["title", "content", "sentiment_score"],
        data_type="sentiment",
        priority=5,
        active=False  # Disabled by default
    ),
    
    "stock_sentiment": CollectorConfig(
        table_name="stock_sentiment_with_sources",
        frequency=timedelta(hours=6),  # Every 6 hours
        key_fields=["symbol", "timestamp", "source"],
        required_fields=["sentiment_score", "article_count"],
        data_type="sentiment",
        priority=5,
        active=False  # Disabled by default
    )
}

# Data type groupings for batch operations
DATA_TYPE_GROUPS = {
    "core_financial": ["ohlc", "price", "technical"],
    "market_analysis": ["market", "derivatives", "sentiment"],  
    "blockchain": ["onchain"],
    "economic": ["macro"],
    "all": list(COLLECTOR_CONFIGS.keys())
}

# Symbols to track (can be extended)
DEFAULT_SYMBOLS = [
    'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'SOL', 'AVAX', 'MATIC', 'ATOM', 'NEAR',
    'UNI', 'AAVE', 'COMP', 'MKR', 'YFI', 'CRV', 'BAL', 'SNX', 'SUSHI', 'GRT'
]

# Historical range configuration
HISTORICAL_CONFIG = {
    "start_date": "2023-01-01",
    "end_date": "now",
    "batch_size": 1000,  # Records to process at once
    "commit_frequency": 100,  # How often to commit transactions
    "max_symbols": 50  # Maximum symbols to process
}

def get_config_by_data_type(data_type: str) -> List[CollectorConfig]:
    """Get all collector configurations for a specific data type"""
    return [config for config in COLLECTOR_CONFIGS.values() 
            if config.data_type == data_type and config.active]

def get_high_priority_configs() -> List[CollectorConfig]:
    """Get configurations for high-priority data types (priority >= 7)"""
    return [config for config in COLLECTOR_CONFIGS.values() 
            if config.priority >= 7 and config.active]

def get_configs_by_frequency(max_frequency: timedelta) -> List[CollectorConfig]:
    """Get configurations that should run at or below specified frequency"""
    return [config for config in COLLECTOR_CONFIGS.values()
            if config.frequency <= max_frequency and config.active]