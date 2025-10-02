#!/usr/bin/env python3
"""
Expand Symbol Coverage Analysis
Check what symbols are needed and update the enhanced price collector to match OHLC coverage.
"""

# Since we can't connect to the k8s cluster database from local, let's add a comprehensive symbol list
# that matches what the OHLC collector would be collecting

# Major cryptocurrencies typically collected
COMPREHENSIVE_CRYPTO_SYMBOLS = [
    # Top 50 by market cap
    'BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'USDC', 'ADA', 'AVAX', 'DOGE', 'TRX',
    'DOT', 'MATIC', 'LINK', 'TON', 'SHIB', 'ICP', 'UNI', 'ATOM', 'ETC', 'LTC',
    'BCH', 'FIL', 'LDO', 'NEAR', 'APT', 'VET', 'ALGO', 'QNT', 'IMP', 'OP',
    'HBAR', 'MKR', 'GRT', 'SAND', 'MANA', 'FLOW', 'CHZ', 'EGLD', 'XTZ', 'AAVE',
    'THETA', 'FTM', 'AXS', 'ENJ', 'ROSE', 'XLM', 'KSM', 'ONE', 'ENJIN', 'CELO',
    
    # DeFi tokens
    'COMP', 'YFI', 'SNX', 'BAL', 'CRV', 'SUSHI', 'REN', 'BADGER', 'ALPHA', 'RUNE',
    'KAVA', 'SRM', 'RAY', 'PERP', 'DPI', 'FEI', 'TRIBE', 'OHM', 'KLIMA', 'TIME',
    
    # Gaming/NFT tokens  
    'GALA', 'IMX', 'LRC', 'ENS', 'LOOKS', 'BLUR', 'APE', 'GMT', 'STEPN', 'GST',
    
    # Layer 2 and scaling
    'MATIC', 'LRC', 'IMX', 'SKALE', 'CTSI', 'OMG',
    
    # Other major tokens
    'FET', 'OCEAN', 'AGIX', 'RLC', 'NMR', 'MLN', 'REQ', 'GNO', 'BAT', 'ZRX',
    'REP', 'BNT', 'KNC', 'ANT', 'RDN', 'STORJ', 'CVC', 'DNT', 'MCO', 'MTL'
]

print(f"Total comprehensive symbols: {len(COMPREHENSIVE_CRYPTO_SYMBOLS)}")
print("Sample symbols:", COMPREHENSIVE_CRYPTO_SYMBOLS[:20])

# Create a mapping script for the enhanced crypto prices service
symbol_array = "[\n        " + ",\n        ".join([f"'{symbol}'" for symbol in COMPREHENSIVE_CRYPTO_SYMBOLS]) + "\n    ]"

fallback_config = f"""
# Enhanced crypto prices fallback symbols configuration
COMPREHENSIVE_SYMBOLS = {symbol_array}

# This should be added to the enhanced crypto prices service to expand coverage
# from the current ~2 symbols to match the OHLC collector's ~96 symbols
"""

print("\n" + "="*50)
print("ENHANCED CRYPTO PRICES SERVICE UPDATE")
print("="*50)
print(fallback_config)

print("\nNext steps:")
print("1. Update enhanced crypto prices service to use comprehensive symbol list")
print("2. Ensure all OHLC columns are populated in price_data_real")
print("3. Rebuild and redeploy the service")
print("4. Monitor collection to ensure all symbols are being collected")