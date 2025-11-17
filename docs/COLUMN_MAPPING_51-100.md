# ML FEATURES MATERIALIZED - DATA SOURCE MAPPING
## Columns 51-100 of 211 Total Columns

| # | Column Name | Data Type | Data Source | Collector/Table | ML Value | Notes |
|---|-------------|-----------|-------------|-----------------|----------|-------|
| 51 | social_post_count | int | **Social Media APIs** | social_sentiment_data | LOW | Count of social media posts |
| 52 | social_avg_sentiment | float | **Social Media APIs** | social_sentiment_data | MEDIUM | Average social sentiment |
| 53 | social_weighted_sentiment | float | **Social Media APIs** | social_sentiment_data | HIGH | Engagement-weighted sentiment |
| 54 | social_engagement_weighted_sentiment | float | **Social Media APIs** | social_sentiment_data | HIGH | Advanced weighted sentiment |
| 55 | social_verified_user_sentiment | float | **Social Media APIs** | social_sentiment_data | HIGH | Verified users sentiment |
| 56 | social_total_engagement | bigint | **Social Media APIs** | social_sentiment_data | LOW | Total engagement metrics |
| 57 | social_unique_authors | int | **Social Media APIs** | social_sentiment_data | LOW | Unique author count |
| 58 | social_avg_confidence | float | **Social Media APIs** | social_sentiment_data | LOW | Sentiment confidence score |
| 59 | treasury_10y | decimal | **FRED API** | macro_indicators | HIGH | 10-Year Treasury Rate |
| 60 | vix_index | decimal | **Yahoo Finance** | macro_indicators | HIGH | VIX Volatility Index (duplicate) |
| 61 | dxy_index | decimal | **Yahoo Finance** | macro_indicators | HIGH | Dollar Index (duplicate) |
| 62 | spx_price | decimal | **Yahoo Finance** | macro_indicators | HIGH | S&P 500 Price (duplicate) |
| 63 | gold_price | decimal | **Yahoo Finance** | macro_indicators | HIGH | Gold spot price |
| 64 | oil_price | decimal | **Yahoo Finance** | macro_indicators | HIGH | Oil (WTI) price |
| 65 | btc_fear_greed | decimal | **Fear & Greed API** | sentiment_aggregation | HIGH | BTC-specific Fear & Greed |
| 66 | market_cap_usd | decimal | **CoinGecko API** | crypto_assets | HIGH | Market cap in USD (duplicate) |
| 67 | total_volume_24h | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Total 24h volume (duplicate) |
| 68 | active_addresses_24h | int | **Blockchain APIs** | crypto_onchain_data | HIGH | Active wallet addresses |
| 69 | transaction_count_24h | int | **Blockchain APIs** | crypto_onchain_data | HIGH | Transaction count |
| 70 | exchange_net_flow_24h | decimal | **Blockchain APIs** | crypto_onchain_data | HIGH | Net flow to exchanges |
| 71 | price_volatility_7d | decimal | **Technical Calculator** | technical_indicators | HIGH | 7-day volatility |
| 72 | onchain_market_cap_usd | decimal | **Blockchain APIs** | crypto_onchain_data | MEDIUM | On-chain market cap |
| 73 | onchain_volume_24h | decimal | **Blockchain APIs** | crypto_onchain_data | MEDIUM | On-chain volume |
| 74 | onchain_price_volatility_7d | decimal | **Blockchain APIs** | crypto_onchain_data | MEDIUM | On-chain volatility |
| 75 | market_cap_rank | int | **CoinGecko API** | crypto_assets | MEDIUM | Market cap ranking |
| 76 | unemployment_rate | decimal | **FRED API** | macro_indicators | HIGH | US unemployment rate |
| 77 | inflation_rate | decimal | **FRED API** | macro_indicators | HIGH | US inflation rate |
| 78 | social_sentiment | decimal | **Social Media APIs** | social_sentiment_data | HIGH | Aggregated social sentiment |
| 79 | news_sentiment | decimal | **News APIs** | crypto_news | HIGH | News sentiment aggregate |
| 80 | reddit_sentiment | decimal | **Reddit API** | social_sentiment_data | MEDIUM | Reddit-specific sentiment |
| 81 | open_price | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Opening price |
| 82 | high_price | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Daily high price |
| 83 | low_price | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Daily low price |
| 84 | close_price | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Closing price |
| 85 | ohlc_volume | decimal | **CoinGecko API** | crypto_assets | LOW | OHLC volume (duplicate) |
| 86 | ohlc_source | varchar | **Database** | Metadata | LOW | OHLC data source indicator |
| 87 | price | decimal | **CoinGecko API** | crypto_assets | HIGH | Current price (duplicate) |
| 88 | open | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Open price (duplicate) |
| 89 | high | decimal | **CoinGecko API** | crypto_assets | MEDIUM | High price (duplicate) |
| 90 | low | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Low price (duplicate) |
| 91 | close | decimal | **CoinGecko API** | crypto_assets | MEDIUM | Close price (duplicate) |
| 92 | volume_qty_24h | decimal | **CoinGecko API** | crypto_assets | MEDIUM | 24h volume quantity |
| 93 | volume_24h_usd | decimal | **CoinGecko API** | crypto_assets | HIGH | 24h volume in USD |
| 94 | percent_change_1h | decimal | **CoinGecko API** | crypto_assets | HIGH | 1-hour percentage change |
| 95 | percent_change_24h | decimal | **CoinGecko API** | crypto_assets | HIGH | 24-hour percentage change |
| 96 | percent_change_7d | decimal | **CoinGecko API** | crypto_assets | HIGH | 7-day percentage change |
| 97 | sentiment_positive | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Positive sentiment breakdown |
| 98 | sentiment_negative | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Negative sentiment breakdown |
| 99 | sentiment_neutral | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Neutral sentiment breakdown |
| 100 | sentiment_fear_greed_index | decimal | **Fear & Greed API** | sentiment_aggregation | HIGH | Fear/Greed index (duplicate) |

## Data Source Summary (Columns 51-100):
- **🔗 CoinGecko API**: 17 columns (OHLC, volume, price changes)
- **📱 Social Media APIs**: 10 columns (Twitter, Reddit, engagement)
- **📊 Yahoo Finance**: 5 columns (indices, commodities)
- **📈 FRED API**: 3 columns (treasury, unemployment, inflation)
- **🔗 Blockchain APIs**: 6 columns (on-chain metrics)
- **📰 News/Sentiment APIs**: 7 columns (news, sentiment aggregation)
- **🔧 Technical Calculator**: 1 column (volatility)
- **🗃️ Database Metadata**: 1 column (source tracking)

## ML Value Distribution (Columns 51-100):
- **🔥 HIGH Value**: 25 columns (50%)
- **⚡ MEDIUM Value**: 15 columns (30%)
- **🗑️ LOW Value**: 10 columns (20%)

## Notable Observations (Columns 51-100):
- **Duplicates**: Several price/volume columns have multiple versions
- **High-Value On-chain**: Active addresses, transaction counts, exchange flows
- **Social Sentiment**: Mix of raw counts (LOW) and weighted scores (HIGH)
- **Macro Coverage**: Strong macro economic indicators (unemployment, inflation)

---
*Next: Columns 101-150 of 211*