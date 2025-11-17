# ML FEATURES MATERIALIZED - DATA SOURCE MAPPING
## Columns 1-50 of 211 Total Columns

| # | Column Name | Data Type | Data Source | Collector/Table | ML Value | Notes |
|---|-------------|-----------|-------------|-----------------|----------|-------|
| 1 | id | bigint | **Database** | Primary Key | LOW | Auto-increment identifier |
| 2 | symbol | varchar | **Database** | Primary Key | LOW | Crypto symbol (BTC, ETH, etc.) |
| 3 | price_date | date | **Database** | Primary Key | LOW | Date component for partitioning |
| 4 | price_hour | tinyint | **Database** | Primary Key | LOW | Hour component (0-23) |
| 5 | timestamp_iso | datetime | **Database** | Primary Key | LOW | Full timestamp |
| 6 | current_price | decimal | **CoinGecko API** | Enhanced Crypto Prices | HIGH | Real-time crypto price |
| 7 | volume_24h | decimal | **CoinGecko API** | Enhanced Crypto Prices | HIGH | 24h trading volume |
| 8 | hourly_volume | decimal | **CoinGecko API** | Enhanced Crypto Prices | MEDIUM | Hourly volume breakdown |
| 9 | market_cap | bigint | **CoinGecko API** | Enhanced Crypto Prices | HIGH | Total market capitalization |
| 10 | price_change_24h | decimal | **CoinGecko API** | Enhanced Crypto Prices | HIGH | Absolute 24h price change |
| 11 | price_change_percentage_24h | decimal | **CoinGecko API** | Enhanced Crypto Prices | HIGH | Percentage 24h price change |
| 12 | rsi_14 | decimal | **Technical Calculator** | technical_indicators | HIGH | 14-period RSI |
| 13 | sma_20 | decimal | **Technical Calculator** | technical_indicators | HIGH | 20-period Simple Moving Average |
| 14 | sma_50 | decimal | **Technical Calculator** | technical_indicators | HIGH | 50-period Simple Moving Average |
| 15 | ema_12 | decimal | **Technical Calculator** | technical_indicators | HIGH | 12-period Exponential Moving Average |
| 16 | ema_26 | decimal | **Technical Calculator** | technical_indicators | HIGH | 26-period Exponential Moving Average |
| 17 | macd_line | decimal | **Technical Calculator** | technical_indicators | HIGH | MACD line (EMA12 - EMA26) |
| 18 | macd_signal | decimal | **Technical Calculator** | technical_indicators | HIGH | MACD signal line |
| 19 | macd_histogram | decimal | **Technical Calculator** | technical_indicators | HIGH | MACD histogram |
| 20 | bb_upper | decimal | **Technical Calculator** | technical_indicators | HIGH | Bollinger Band upper |
| 21 | bb_middle | decimal | **Technical Calculator** | technical_indicators | HIGH | Bollinger Band middle (SMA20) |
| 22 | bb_lower | decimal | **Technical Calculator** | technical_indicators | HIGH | Bollinger Band lower |
| 23 | stoch_k | decimal | **Technical Calculator** | technical_indicators | HIGH | Stochastic %K |
| 24 | stoch_d | decimal | **Technical Calculator** | technical_indicators | HIGH | Stochastic %D |
| 25 | atr_14 | decimal | **Technical Calculator** | technical_indicators | HIGH | 14-period Average True Range |
| 26 | vwap | decimal | **Technical Calculator** | technical_indicators | HIGH | Volume Weighted Average Price |
| 27 | vix | decimal | **Yahoo Finance** | macro_indicators | HIGH | CBOE Volatility Index |
| 28 | spx | decimal | **Yahoo Finance** | macro_indicators | HIGH | S&P 500 Index |
| 29 | dxy | decimal | **Yahoo Finance** | macro_indicators | HIGH | US Dollar Index |
| 30 | tnx | decimal | **Yahoo Finance** | macro_indicators | HIGH | 10-Year Treasury Yield |
| 31 | fed_funds_rate | decimal | **FRED API** | macro_indicators | HIGH | Federal Funds Rate |
| 32 | crypto_sentiment_count | int | **Sentiment Collector** | sentiment_aggregation | LOW | Count of crypto sentiment records |
| 33 | avg_cryptobert_score | decimal | **Sentiment Collector** | sentiment_aggregation | HIGH | CryptoBERT sentiment average |
| 34 | avg_vader_score | decimal | **Sentiment Collector** | sentiment_aggregation | HIGH | VADER sentiment average |
| 35 | avg_textblob_score | decimal | **Sentiment Collector** | sentiment_aggregation | MEDIUM | TextBlob sentiment average |
| 36 | avg_crypto_keywords_score | decimal | **Sentiment Collector** | sentiment_aggregation | MEDIUM | Crypto keywords sentiment |
| 37 | stock_sentiment_count | int | **Sentiment Collector** | sentiment_aggregation | LOW | Count of stock sentiment records |
| 38 | avg_finbert_sentiment_score | decimal | **Sentiment Collector** | sentiment_aggregation | HIGH | FinBERT sentiment for stocks |
| 39 | avg_fear_greed_score | decimal | **Fear & Greed API** | sentiment_aggregation | HIGH | Fear & Greed Index |
| 40 | avg_volatility_sentiment | decimal | **Sentiment Collector** | sentiment_aggregation | MEDIUM | Volatility-based sentiment |
| 41 | avg_risk_appetite | decimal | **Sentiment Collector** | sentiment_aggregation | MEDIUM | Risk appetite indicator |
| 42 | avg_crypto_correlation | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Legacy correlation metric |
| 43 | created_at | timestamp | **Database** | Auto-generated | LOW | Record creation timestamp |
| 44 | updated_at | timestamp | **Database** | Auto-generated | LOW | Record update timestamp |
| 45 | data_quality_score | decimal | **Database** | Computed | LOW | Data quality assessment |
| 46 | general_crypto_sentiment_count | int | **Sentiment Collector** | crypto_news | LOW | General news sentiment count |
| 47 | avg_general_cryptobert_score | float | **Sentiment Collector** | crypto_news | MEDIUM | General CryptoBERT sentiment |
| 48 | avg_general_vader_score | float | **Sentiment Collector** | crypto_news | MEDIUM | General VADER sentiment |
| 49 | avg_general_textblob_score | float | **Sentiment Collector** | crypto_news | MEDIUM | General TextBlob sentiment |
| 50 | avg_general_crypto_keywords_score | float | **Sentiment Collector** | crypto_news | MEDIUM | General crypto keywords sentiment |

## Data Source Summary (Columns 1-50):
- **🔗 CoinGecko API**: 6 columns (price, volume, market cap data)
- **🔧 Technical Calculator**: 15 columns (RSI, MACD, Bollinger Bands, etc.)
- **📊 Yahoo Finance**: 4 columns (VIX, SPX, DXY, TNX)
- **📈 FRED API**: 1 column (Fed funds rate)
- **📰 Sentiment Collector**: 12 columns (various sentiment scores)
- **🗃️ Database Metadata**: 7 columns (IDs, timestamps, quality)
- **🎯 Fear & Greed API**: 1 column (fear/greed index)

## ML Value Distribution (Columns 1-50):
- **🔥 HIGH Value**: 25 columns (50%)
- **⚡ MEDIUM Value**: 13 columns (26%)
- **🗑️ LOW Value**: 12 columns (24%)

---
*Next: Columns 51-100 of 211*