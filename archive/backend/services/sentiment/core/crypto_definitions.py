# crypto_definitions.py
# Shared definitions for cryptocurrency types and mappings

CRYPTO_COINS = {
    'bitcoin': ['bitcoin', 'btc', 'bitcoins'],
    'ethereum': ['ethereum', 'eth', 'ether'],
    'solana': ['solana', 'sol'],
    'cardano': ['cardano', 'ada'],
    'polkadot': ['polkadot', 'dot'],
    'dogecoin': ['dogecoin', 'doge'],
    'chainlink': ['chainlink', 'link'],
    'polygon': ['polygon', 'matic'],
    'avalanche': ['avalanche', 'avax'],
    'cosmos': ['cosmos', 'atom'],
    'algorand': ['algorand', 'algo'],
    'tezos': ['tezos', 'xtz'],
    'fantom': ['fantom', 'ftm'],
    'near': ['near', 'near protocol'],
    'aptos': ['aptos', 'apt'],
    'arbitrum': ['arbitrum', 'arb'],
    'optimism': ['optimism', 'op'],
    'sui': ['sui'],
    'shiba': ['shiba', 'shib', 'shiba inu'],
    'litecoin': ['litecoin', 'ltc'],
    'binance_coin': ['binance coin', 'bnb', 'binance'],
    'ripple': ['ripple', 'xrp'],
    'uniswap': ['uniswap', 'uni'],
    'aave': ['aave'],
    'compound': ['compound', 'comp'],
    'maker': ['maker', 'mkr'],
    'yearn': ['yearn', 'yfi'],
    'sushi': ['sushi', 'sushiswap'],
    'curve': ['curve', 'crv'],
    'stellar': ['stellar', 'xlm'],
    'vechain': ['vechain', 'vet'],
    'filecoin': ['filecoin', 'fil'],
    'tron': ['tron', 'trx'],
    'monero': ['monero', 'xmr'],
    'eos': ['eos'],
    'ftx': ['ftx', 'ftt'],  # Historical
    'terra': ['terra', 'luna'],  # Historical
}

# Yahoo Finance symbol mappings (coin_id -> Yahoo symbol)
YAHOO_FINANCE_SYMBOLS = {
    'bitcoin': 'BTC-USD',
    'ethereum': 'ETH-USD',
    'binance_coin': 'BNB-USD',
    'cardano': 'ADA-USD',
    'solana': 'SOL-USD',
    'polkadot': 'DOT-USD',
    'avalanche': 'AVAX-USD',
    'chainlink': 'LINK-USD',
    'polygon': 'MATIC-USD',
    'litecoin': 'LTC-USD',
    'dogecoin': 'DOGE-USD',
    'ripple': 'XRP-USD',
    'uniswap': 'UNI-USD',
    'cosmos': 'ATOM-USD',
    'algorand': 'ALGO-USD',
    'tezos': 'XTZ-USD',
    'stellar': 'XLM-USD',
    'vechain': 'VET-USD',
    'filecoin': 'FIL-USD',
    'tron': 'TRX-USD',
    'monero': 'XMR-USD',
    'eos': 'EOS-USD',
    'aave': 'AAVE-USD',
    'compound': 'COMP-USD',
    'maker': 'MKR-USD',
    'curve': 'CRV-USD',
    'sushi': 'SUSHI-USD',
    'yearn': 'YFI-USD',
    'shiba': 'SHIB-USD',
    'near': 'NEAR-USD',
    'aptos': 'APT-USD',
    'arbitrum': 'ARB-USD',
    'optimism': 'OP-USD',
    'sui': 'SUI-USD',
    'fantom': 'FTM-USD',
}

# CoinGecko ID mappings (for API calls) - Enhanced with centralized symbol configuration
COINGECKO_IDS = {
    # Major cryptocurrencies  
    'BTC': 'bitcoin',
    'ETH': 'ethereum', 
    'BNB': 'binancecoin',
    'ADA': 'cardano',
    'SOL': 'solana',
    'DOT': 'polkadot',
    'AVAX': 'avalanche-2',
    'LINK': 'chainlink',
    'MATIC': 'polygon',
    'LTC': 'litecoin',
    'DOGE': 'dogecoin',
    'XRP': 'ripple',
    'UNI': 'uniswap',
    'ATOM': 'cosmos',
    'ALGO': 'algorand',
    'XTZ': 'tezos',
    'XLM': 'stellar',
    'VET': 'vechain',
    'FIL': 'filecoin',
    'TRX': 'tron',
    'XMR': 'monero',
    'EOS': 'eos',
    
    # DeFi tokens
    'AAVE': 'aave',
    'COMP': 'compound-governance-token',
    'MKR': 'maker',
    'CRV': 'curve-dao-token',
    'SUSHI': 'sushi',
    'YFI': 'yearn-finance',
    
    # Layer 1s and major alts
    'NEAR': 'near',
    'APT': 'aptos',
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'SUI': 'sui',
    'FTM': 'fantom',
    'THETA': 'theta-token',
    
    # Meme and trending tokens
    'SHIB': 'shiba-inu',
    'PEPE': 'pepe',
    'BONK': 'bonk',
    'WIF': 'dogwifcoin',
    'FLOKI': 'floki',
    'BOME': 'book-of-meme',
    
    # Exchange and ecosystem tokens (Note: Some may need verification)
    'PENGU': 'pudgy-penguins',
    'GOHOME': 'gohome',
    'FARTCOIN': 'fartcoin',
    'BRETT': 'brett',
    'SPX6900': 'spx6900',
    'BTFD': 'btfd',
    '888': '888-token',
    'APC': 'apc-token',
}

# Create reverse mapping (CoinGecko ID -> symbol)
COINGECKO_TO_SYMBOL = {v: k for k, v in COINGECKO_IDS.items()}

# Supply estimates for market cap calculations
SUPPLY_ESTIMATES = {
    'bitcoin': 19_800_000,        # ~19.8M BTC
    'ethereum': 120_000_000,      # ~120M ETH
    'binance_coin': 153_000_000,  # ~153M BNB
    'cardano': 45_000_000_000,    # ~45B ADA
    'solana': 420_000_000,        # ~420M SOL
    'polkadot': 1_300_000_000,    # ~1.3B DOT
    'avalanche': 400_000_000,     # ~400M AVAX
    'chainlink': 600_000_000,     # ~600M LINK
    'polygon': 10_000_000_000,    # ~10B MATIC
    'litecoin': 75_000_000,       # ~75M LTC
    'dogecoin': 140_000_000_000,  # ~140B DOGE
    'ripple': 100_000_000_000,    # ~100B XRP
    'uniswap': 1_000_000_000,     # ~1B UNI
    'cosmos': 300_000_000,        # ~300M ATOM
    'algorand': 10_000_000_000,   # ~10B ALGO
    'tezos': 1_000_000_000,       # ~1B XTZ
    'stellar': 50_000_000_000,    # ~50B XLM
    'vechain': 86_000_000_000,    # ~86B VET
    'filecoin': 400_000_000,      # ~400M FIL
    'tron': 90_000_000_000,       # ~90B TRX
    'monero': 18_000_000,         # ~18M XMR
    'eos': 1_100_000_000,         # ~1.1B EOS
    'aave': 16_000_000,           # ~16M AAVE
    'compound': 10_000_000,       # ~10M COMP
    'maker': 1_000_000,           # ~1M MKR
    'curve': 3_000_000_000,       # ~3B CRV
    'sushi': 250_000_000,         # ~250M SUSHI
    'yearn': 37_000,              # ~37K YFI
    'shiba': 589_000_000_000_000, # ~589T SHIB
    'near': 1_100_000_000,        # ~1.1B NEAR
    'aptos': 1_100_000_000,       # ~1.1B APT
    'arbitrum': 10_000_000_000,   # ~10B ARB
    'optimism': 4_000_000_000,    # ~4B OP
    'sui': 10_000_000_000,        # ~10B SUI
    'fantom': 3_200_000_000,      # ~3.2B FTM
}

# Standard symbol mappings (for display)
SYMBOL_MAPPINGS = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'binance_coin': 'BNB',
    'cardano': 'ADA',
    'solana': 'SOL',
    'polkadot': 'DOT',
    'avalanche': 'AVAX',
    'chainlink': 'LINK',
    'polygon': 'MATIC',
    'litecoin': 'LTC',
    'dogecoin': 'DOGE',
    'ripple': 'XRP',
    'uniswap': 'UNI',
    'cosmos': 'ATOM',
    'algorand': 'ALGO',
    'tezos': 'XTZ',
    'stellar': 'XLM',
    'vechain': 'VET',
    'filecoin': 'FIL',
    'tron': 'TRX',
    'monero': 'XMR',
    'eos': 'EOS',
    'aave': 'AAVE',
    'compound': 'COMP',
    'maker': 'MKR',
    'curve': 'CRV',
    'sushi': 'SUSHI',
    'yearn': 'YFI',
    'shiba': 'SHIB',
    'near': 'NEAR',
    'aptos': 'APT',
    'arbitrum': 'ARB',
    'optimism': 'OP',
    'sui': 'SUI',
    'fantom': 'FTM',
}

CRYPTO_MAPPING = {
    'bitcoin': 'bitcoin', 'btc': 'bitcoin', 'bitcoins': 'bitcoin', 'satoshi': 'bitcoin',
    'ethereum': 'ethereum', 'eth': 'ethereum', 'ether': 'ethereum',
    'solana': 'solana', 'sol': 'solana',
    'cardano': 'cardano', 'ada': 'cardano',
    'polkadot': 'polkadot', 'dot': 'polkadot',
    'chainlink': 'chainlink', 'link': 'chainlink',
    'uniswap': 'uniswap', 'uni': 'uniswap',
    'compound': 'compound', 'comp': 'compound',
    'aave': 'aave',
    'maker': 'maker', 'mkr': 'maker',
    'curve': 'curve', 'crv': 'curve',
    'binance coin': 'binance_coin', 'bnb': 'binance_coin', 'binance': 'binance_coin',
    'coinbase': 'coinbase_coin', 'coin': 'coinbase_coin',
    'kucoin': 'kucoin', 'kcs': 'kucoin',
    'ftx': 'ftx', 'ftt': 'ftx',
    'polygon': 'polygon', 'matic': 'polygon',
    'arbitrum': 'arbitrum', 'arb': 'arbitrum',
    'optimism': 'optimism', 'op': 'optimism',
    'dogecoin': 'dogecoin', 'doge': 'dogecoin',
    'shiba': 'shiba', 'shib': 'shiba', 'shiba inu': 'shiba',
    'ripple': 'ripple', 'xrp': 'ripple',
    'litecoin': 'litecoin', 'ltc': 'litecoin',
    'avalanche': 'avalanche', 'avax': 'avalanche',
    'fantom': 'fantom', 'ftm': 'fantom',
    'near': 'near', 'near protocol': 'near',
    'cosmos': 'cosmos', 'atom': 'cosmos',
    'terra': 'terra', 'luna': 'terra',
    'algorand': 'algorand', 'algo': 'algorand',
    'tezos': 'tezos', 'xtz': 'tezos',
    'stellar': 'stellar', 'xlm': 'stellar',
    'vechain': 'vechain', 'vet': 'vechain',
    'filecoin': 'filecoin', 'fil': 'filecoin',
    'tron': 'tron', 'trx': 'tron',
    'monero': 'monero', 'xmr': 'monero',
    'eos': 'eos',
    'yearn': 'yearn', 'yfi': 'yearn',
    'sushi': 'sushi', 'sushiswap': 'sushi',
    'sui': 'sui',
    'aptos': 'aptos', 'apt': 'aptos',
}

GENERIC_CRYPTO_TERMS = [
    'cryptocurrency', 'blockchain', 'defi', 'decentralized finance', 
    'altcoin', 'hodl', 'staking', 'smart contract', 
    'gas fees', 'stablecoin'
]

# Helper functions
def get_yahoo_symbols(coin_ids=None):
    """Get Yahoo Finance symbols for specified coins or all available"""
    if coin_ids is None:
        return list(YAHOO_FINANCE_SYMBOLS.values())
    return [YAHOO_FINANCE_SYMBOLS[coin_id] for coin_id in coin_ids if coin_id in YAHOO_FINANCE_SYMBOLS]

def get_coingecko_ids(coin_ids=None):
    """Get CoinGecko IDs for specified coins or all available"""
    if coin_ids is None:
        return list(COINGECKO_IDS.values())
    return [COINGECKO_IDS[coin_id] for coin_id in coin_ids if coin_id in COINGECKO_IDS]

def get_symbol_from_yahoo(yahoo_symbol):
    """Convert Yahoo symbol (e.g., 'BTC-USD') to standard symbol (e.g., 'BTC')"""
    return yahoo_symbol.replace('-USD', '')

def get_coin_id_from_symbol(symbol):
    """Convert symbol (e.g., 'BTC') to coin_id (e.g., 'bitcoin')"""
    symbol_lower = symbol.lower()
    for coin_id, std_symbol in SYMBOL_MAPPINGS.items():
        if std_symbol.lower() == symbol_lower:
            return coin_id
    return symbol_lower

def get_supply_estimate(coin_id):
    """Get supply estimate for market cap calculation"""
    return SUPPLY_ESTIMATES.get(coin_id, 1_000_000_000)  # Default 1B if unknown
