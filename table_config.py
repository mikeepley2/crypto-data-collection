#!/usr/bin/env python3
"""
Mock table_config module for unit tests
"""

def get_collector_symbols():
    """Mock function returning test symbols"""
    return ['BTC', 'ETH', 'ADA', 'SOL']

def get_supported_symbols():
    """Mock function returning supported symbols"""
    return ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']

def normalize_symbol_for_exchange(symbol, exchange):
    """Mock function for symbol normalization"""
    if exchange.lower() == 'binance':
        return f"{symbol}USDT" if not symbol.endswith('USDT') else symbol
    return symbol

def validate_symbol_exists(symbol):
    """Mock function for symbol validation"""
    valid_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'BTCUSDT', 'ETHUSDT']
    return symbol.upper() in valid_symbols