#!/usr/bin/env python3

# From database schema analysis, these are the actual columns that exist:
actual_columns = [
    'id', 'symbol', 'price_date', 'price_hour', 'timestamp_iso', 'current_price',
    'volume_24h', 'hourly_volume', 'market_cap', 'price_change_24h', 'price_change_percentage_24h',
    'rsi_14', 'sma_20', 'sma_50', 'ema_12', 'ema_26', 'macd_line', 'macd_signal', 'macd_histogram',
    'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d', 'atr_14', 'vwap',
    'vix', 'spx', 'dxy', 'tnx', 'fed_funds_rate',  # NOTE: These are wrong names, should be vix_index, spx_price, dxy_index, treasury_10y
    'crypto_sentiment_count', 'avg_cryptobert_score', 'avg_vader_score', 'avg_textblob_score', 'avg_crypto_keywords_score',
    'stock_sentiment_count', 'avg_finbert_sentiment_score', 'avg_fear_greed_score', 'avg_volatility_sentiment',
    'avg_risk_appetite', 'avg_crypto_correlation', 'created_at', 'updated_at', 'data_quality_score',
    'general_crypto_sentiment_count', 'avg_general_cryptobert_score', 'avg_general_vader_score',
    'avg_general_textblob_score', 'avg_general_crypto_keywords_score',
    'social_post_count', 'social_avg_sentiment', 'social_weighted_sentiment', 'social_engagement_weighted_sentiment',
    'social_verified_user_sentiment', 'social_total_engagement', 'social_unique_authors', 'social_avg_confidence',
    'treasury_10y', 'vix_index', 'dxy_index', 'spx_price', 'gold_price', 'oil_price', 'btc_fear_greed',
    'market_cap_usd', 'total_volume_24h', 'active_addresses_24h', 'transaction_count_24h', 'exchange_net_flow_24h',
    'price_volatility_7d', 'onchain_market_cap_usd', 'onchain_volume_24h', 'onchain_price_volatility_7d', 'market_cap_rank',
    'unemployment_rate', 'inflation_rate', 'social_sentiment', 'news_sentiment', 'reddit_sentiment',
    'open_price', 'high_price', 'low_price', 'close_price', 'ohlc_volume', 'ohlc_source',
    'price', 'open', 'high', 'low', 'close', 'volume_qty_24h', 'volume_24h_usd',
    'percent_change_1h', 'percent_change_24h', 'percent_change_7d',
    'sentiment_positive', 'sentiment_negative', 'sentiment_neutral', 'sentiment_fear_greed_index',
    'sentiment_volume_weighted', 'sentiment_social_dominance', 'sentiment_news_impact', 'sentiment_whale_movement',
    'onchain_active_addresses', 'onchain_transaction_volume', 'onchain_avg_transaction_value',
    'onchain_nvt_ratio', 'onchain_mvrv_ratio', 'onchain_whale_transactions',
    'gdp_growth', 'cpi_inflation', 'interest_rate', 'employment_rate', 'consumer_confidence',
    'retail_sales', 'industrial_production'
]

# From materialized_updater_enhanced.py these columns are referenced but don't exist:
non_existent_columns = [
    'ohlc_1h_open', 'ohlc_1h_high', 'ohlc_1h_low', 'ohlc_1h_close', 'ohlc_1h_volume',
    'ohlc_4h_open', 'ohlc_4h_high',
    'volatility_1h', 'volatility_4h', 'volatility_24h',
    'correlation_btc', 'correlation_eth', 'correlation_sp500', 'correlation_gold', 'correlation_dxy',
    'funding_rate', 'open_interest', 'long_short_ratio',
    'taker_buy_sell_ratio', 'orderbook_support_resistance',
    'whale_net_flow', 'exchange_net_flow', 'stablecoin_dominance',
    'defi_tvl_change', 'institutional_flow', 'retail_sentiment'
]

print("=== COLUMN CLEANUP NEEDED ===")
print(f"Non-existent columns that need to be removed: {len(non_existent_columns)}")
for col in non_existent_columns:
    print(f"  - {col}")

print(f"\nActual columns available: {len(actual_columns)}")