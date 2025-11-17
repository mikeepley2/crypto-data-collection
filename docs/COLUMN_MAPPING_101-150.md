# ML FEATURES MATERIALIZED - DATA SOURCE MAPPING
## Columns 101-150 of 211 Total Columns

| # | Column Name | Data Type | Data Source | Collector/Table | ML Value | Notes |
|---|-------------|-----------|-------------|-----------------|----------|-------|
| 101 | sentiment_volume_weighted | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Volume-weighted sentiment |
| 102 | sentiment_social_dominance | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Social dominance metric |
| 103 | sentiment_news_impact | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | News impact on sentiment |
| 104 | sentiment_whale_movement | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Whale movement sentiment |
| 105 | avg_ml_crypto_sentiment | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | ML crypto sentiment aggregate |
| 106 | avg_ml_stock_sentiment | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | ML stock sentiment aggregate |
| 107 | avg_ml_social_sentiment | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | ML social sentiment aggregate |
| 108 | avg_ml_overall_sentiment | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | ML overall sentiment aggregate |
| 109 | sentiment_volume | int | **Sentiment Collector** | sentiment_aggregation | LOW | Sentiment data volume count |
| 110 | sentiment_momentum | decimal | **Sentiment Collector** | sentiment_aggregation | LOW | Sentiment momentum indicator |
| 111 | onchain_active_addresses | bigint | **Blockchain APIs** | crypto_onchain_data | HIGH | Active addresses (on-chain) |
| 112 | onchain_transaction_volume | decimal | **Blockchain APIs** | crypto_onchain_data | HIGH | Transaction volume (on-chain) |
| 113 | onchain_avg_transaction_value | decimal | **Blockchain APIs** | crypto_onchain_data | MEDIUM | Average transaction value |
| 114 | onchain_nvt_ratio | decimal | **Blockchain APIs** | crypto_onchain_data | HIGH | Network Value to Transactions |
| 115 | onchain_mvrv_ratio | decimal | **Blockchain APIs** | crypto_onchain_data | HIGH | Market Value to Realized Value |
| 116 | onchain_whale_transactions | int | **Blockchain APIs** | crypto_onchain_data | HIGH | Large transaction count |
| 117 | gdp_growth | decimal | **FRED API** | macro_indicators | HIGH | GDP growth rate |
| 118 | cpi_inflation | decimal | **FRED API** | macro_indicators | HIGH | CPI inflation rate |
| 119 | interest_rate | decimal | **FRED API** | macro_indicators | HIGH | Interest rate |
| 120 | employment_rate | decimal | **FRED API** | macro_indicators | HIGH | Employment rate |
| 121 | consumer_confidence | decimal | **FRED API** | macro_indicators | HIGH | Consumer confidence index |
| 122 | retail_sales | decimal | **FRED API** | macro_indicators | HIGH | Retail sales data |
| 123 | industrial_production | decimal | **FRED API** | macro_indicators | HIGH | Industrial production index |
| **🆕 124** | **qqq_price** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **NASDAQ-100 ETF price** |
| **🆕 125** | **qqq_volume** | **bigint** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **QQQ trading volume** |
| **🆕 126** | **qqq_rsi** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **QQQ RSI indicator** |
| **🆕 127** | **arkk_price** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **ARK Innovation ETF price** |
| **🆕 128** | **arkk_rsi** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **ARKK RSI indicator** |
| **🆕 129** | **gold_futures** | **decimal** | **🤖 ML Market Collector** | **commodities** | **HIGH** | **Gold futures price** |
| **🆕 130** | **oil_wti** | **decimal** | **🤖 ML Market Collector** | **commodities** | **HIGH** | **WTI crude oil price** |
| **🆕 131** | **bond_10y_yield** | **decimal** | **🤖 ML Market Collector** | **bonds** | **HIGH** | **10-year bond yield** |
| **🆕 132** | **usd_index** | **decimal** | **🤖 ML Market Collector** | **currencies** | **HIGH** | **US Dollar Index** |
| **🆕 133** | **market_correlation_crypto** | **decimal** | **🤖 ML Market Collector** | **ml_indicators** | **HIGH** | **Crypto correlation composite** |
| **🆕 134** | **volatility_regime** | **decimal** | **🤖 ML Market Collector** | **ml_indicators** | **HIGH** | **Market volatility regime** |
| **🆕 135** | **momentum_composite** | **decimal** | **🤖 ML Market Collector** | **ml_indicators** | **HIGH** | **Market momentum composite** |
| **🆕 136** | **avg_funding_rate** | **decimal** | **⚡ Derivatives Collector** | **composite_indicators** | **HIGH** | **Average funding rate** |
| **🆕 137** | **total_open_interest** | **decimal** | **⚡ Derivatives Collector** | **composite_indicators** | **HIGH** | **Total open interest** |
| **🆕 138** | **liquidation_ratio** | **decimal** | **⚡ Derivatives Collector** | **composite_indicators** | **HIGH** | **Liquidation ratio** |
| **🆕 139** | **derivatives_momentum** | **decimal** | **⚡ Derivatives Collector** | **ml_indicators** | **HIGH** | **Derivatives momentum** |
| **🆕 140** | **leverage_sentiment** | **decimal** | **⚡ Derivatives Collector** | **ml_indicators** | **HIGH** | **Leverage sentiment** |
| **🆕 141** | **binance_btc_funding_rate** | **decimal** | **⚡ Derivatives Collector** | **binance_futures** | **HIGH** | **Binance BTC funding rate** |
| **🆕 142** | **binance_btc_open_interest** | **decimal** | **⚡ Derivatives Collector** | **binance_futures** | **HIGH** | **Binance BTC open interest** |
| **🆕 143** | **binance_eth_funding_rate** | **decimal** | **⚡ Derivatives Collector** | **binance_futures** | **HIGH** | **Binance ETH funding rate** |
| **🆕 144** | **binance_eth_open_interest** | **decimal** | **⚡ Derivatives Collector** | **binance_futures** | **HIGH** | **Binance ETH open interest** |
| **🆕 145** | **xle_price** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **Energy Sector ETF price** |
| **🆕 146** | **xle_volume** | **bigint** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **XLE trading volume** |
| **🆕 147** | **xle_rsi** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **XLE RSI indicator** |
| **🆕 148** | **xle_sma_20** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **XLE 20-period SMA** |
| **🆕 149** | **xle_ema_12** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **XLE 12-period EMA** |
| **🆕 150** | **xlf_price** | **decimal** | **🤖 ML Market Collector** | **traditional_markets** | **HIGH** | **Financial Sector ETF price** |

## Data Source Summary (Columns 101-150):
- **🤖 ML Market Collector**: 15 columns (NEW traditional markets & ML indicators)
- **⚡ Derivatives Collector**: 7 columns (NEW derivatives & funding data)
- **📈 FRED API**: 7 columns (comprehensive macro indicators)
- **🔗 Blockchain APIs**: 6 columns (advanced on-chain metrics)
- **📰 Sentiment Collector**: 10 columns (detailed sentiment breakdown)
- **🗃️ Legacy Systems**: 5 columns (existing aggregations)

## ML Value Distribution (Columns 101-150):
- **🔥 HIGH Value**: 32 columns (64%) - **Highest concentration yet!**
- **⚡ MEDIUM Value**: 1 column (2%)
- **🗑️ LOW Value**: 17 columns (34%)

## 🆕 NEW ML FEATURES INTRODUCED (Columns 124-150):
**🎯 This is where the magic happens!** Starting at column 124, we see the introduction of our new ML collectors:

### 🤖 **ML Market Collector Features** (Columns 124-135, 145-150):
- **Traditional ETFs**: QQQ (NASDAQ-100), ARKK (Innovation), XLE (Energy), XLF (Financials)
- **Commodities**: Gold futures, WTI oil  
- **Bonds**: 10-year yield
- **Currencies**: USD Index
- **ML Indicators**: Market correlation, volatility regime, momentum composite

### ⚡ **Derivatives Collector Features** (Columns 136-144):
- **Composite Metrics**: Average funding rate, total open interest, liquidation ratio
- **ML Indicators**: Derivatives momentum, leverage sentiment  
- **Exchange-Specific**: Binance BTC/ETH funding rates and open interest

---
*Next: Columns 151-200 of 211*