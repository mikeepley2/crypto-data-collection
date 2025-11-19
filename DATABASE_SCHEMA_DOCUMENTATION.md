# Complete Database Schema Documentation

## Production Database Tables

**Total Tables:** 31


### Core Data Tables

- **crypto_assets** (17 columns)
- **macro_indicators** (13 columns)
- **ohlc_data** (13 columns)
- **onchain_data** (32 columns)
- **portfolio_optimizations** (8 columns)

### Price & Market Data

- **crypto_prices** (11 columns)
- **crypto_prices_view** (11 columns)
- **crypto_prices_working** (11 columns)
- **price_data_real** (50 columns)

### Technical Analysis

- **technical_indicators** (113 columns)

### Sentiment & News

- **crypto_news** (21 columns)
- **real_time_sentiment_signals** (8 columns)

### Trading & Signals

- **enhanced_trading_signals** (17 columns)
- **trade_recommendations** (29 columns)
- **trading_signals** (35 columns)

### ML & Analytics

- **backtesting_results** (17 columns)
- **backtesting_trades** (13 columns)
- **crypto_derivatives_ml** (28 columns)
- **enhanced_derivatives_data** (27 columns)
- **ml_features_materialized** (258 columns)

### System & Monitoring

- **service_monitoring** (7 columns)

### Archive & Backup

- **assets_archived_archive_old** (6 columns)
- **crypto_news_archive_20251107_100457_old** (26 columns)
- **crypto_onchain_data_old** (35 columns)
- **market_conditions_history_archive_20251107_100457_old** (11 columns)
- **ml_trading_signals_old_archive_old** (12 columns)
- **sentiment_aggregation_final_archive_20251107_113856_old** (21 columns)
- **social_sentiment_metrics_final_archive_20251107_113856_old** (18 columns)
- **technical_indicators_backup_20251104_214228_archive_old** (109 columns)
- **technical_indicators_backup_20251104_214305_archive_old** (109 columns)
- **technical_indicators_corrupted_backup_archive_old** (109 columns)

## Key Table Schemas

### crypto_assets

| Column | Type | Null | Key | Default | Extra |
|--------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| symbol | varchar(16) | NO | UNI |  |  |
| name | varchar(64) | NO |  |  |  |
| aliases | json | YES |  |  |  |
| category | varchar(32) | YES |  | crypto |  |
| is_active | tinyint(1) | YES |  | 1 |  |
| created_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| coingecko_id | varchar(150) | YES |  |  |  |
| description | text | YES |  |  |  |
| market_cap_rank | int | YES |  |  |  |
| coingecko_score | decimal(5,2) | YES |  |  |  |
| homepage | varchar(255) | YES |  |  |  |
| last_metadata_update | timestamp | YES |  |  |  |
| coinbase_supported | tinyint(1) | YES | MUL | 1 |  |
| binance_us_supported | tinyint(1) | YES |  | 0 |  |
| kucoin_supported | tinyint(1) | YES |  | 0 |  |
| exchange_support_updated_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |

### price_data_real

| Column | Type | Null | Key | Default | Extra |
|--------|------|------|-----|---------|-------|
| id | bigint | NO | PRI |  | auto_increment |
| symbol | varchar(100) | NO | MUL |  |  |
| coin_id | varchar(150) | NO | MUL |  |  |
| name | varchar(300) | NO |  |  |  |
| timestamp | bigint | NO | MUL |  |  |
| timestamp_iso | datetime(6) | NO | MUL |  |  |
| created_at | timestamp | YES | MUL | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| current_price | decimal(20,8) | NO | MUL |  |  |
| price_change_24h | decimal(20,8) | YES |  |  |  |
| price_change_percentage_24h | decimal(10,4) | YES |  |  |  |
| market_cap | decimal(25,2) | YES |  |  |  |
| volume_usd_24h | decimal(25,2) | YES |  |  |  |
| volume_qty_24h | decimal(25,8) | YES |  |  |  |
| market_cap_rank | int | YES | MUL |  |  |
| circulating_supply | decimal(25,2) | YES |  |  |  |
| total_supply | decimal(25,2) | YES |  |  |  |
| max_supply | decimal(25,2) | YES |  |  |  |
| ath | decimal(20,8) | YES |  |  |  |
| ath_date | datetime | YES |  |  |  |
| atl | decimal(20,8) | YES |  |  |  |
| atl_date | datetime | YES |  |  |  |
| collection_interval | varchar(20) | YES |  |  |  |
| data_source | varchar(100) | YES |  |  |  |
| collector_container | tinyint(1) | YES |  | 1 |  |
| collection_run | bigint | YES | MUL |  |  |
| data_quality_score | decimal(3,2) | YES |  | 1.00 |  |
| high_24h | decimal(20,8) | YES |  |  |  |
| low_24h | decimal(20,8) | YES |  |  |  |
| open_24h | decimal(20,8) | YES |  |  |  |
| volume_30d | decimal(25,2) | YES |  |  |  |
| bid_price | decimal(20,8) | YES |  |  |  |
| ask_price | decimal(20,8) | YES |  |  |  |
| spread | decimal(20,8) | YES |  |  |  |
| hourly_volume_qty | decimal(25,8) | YES |  |  |  |
| hourly_volume_usd | decimal(25,2) | YES |  |  |  |
| hourly_volume | decimal(25,2) | YES |  |  |  |
| rsi_14 | decimal(10,4) | YES |  |  |  |
| sma_20 | decimal(20,8) | YES |  |  |  |
| sma_50 | decimal(20,8) | YES |  |  |  |
| ema_12 | decimal(20,8) | YES |  |  |  |
| ema_26 | decimal(20,8) | YES |  |  |  |
| macd | decimal(20,8) | YES |  |  |  |
| macd_signal | decimal(20,8) | YES |  |  |  |
| macd_histogram | decimal(20,8) | YES |  |  |  |
| bb_upper | decimal(20,8) | YES |  |  |  |
| bb_lower | decimal(20,8) | YES |  |  |  |
| bb_middle | decimal(20,8) | YES |  |  |  |
| volume_sma_20 | decimal(25,2) | YES |  |  |  |
| volume_ratio | decimal(10,4) | YES |  |  |  |
| data_completeness_percentage | decimal(5,2) | YES |  | 0.00 |  |

### technical_indicators

| Column | Type | Null | Key | Default | Extra |
|--------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| symbol | varchar(20) | NO | MUL |  |  |
| timestamp_iso | datetime | NO | MUL |  |  |
| sma_20 | decimal(20,8) | YES |  |  |  |
| sma_50 | decimal(20,8) | YES |  |  |  |
| sma_200 | decimal(20,8) | YES |  |  |  |
| ema_12 | decimal(20,8) | YES |  |  |  |
| ema_26 | decimal(20,8) | YES |  |  |  |
| macd | decimal(20,8) | YES |  |  |  |
| macd_signal | decimal(20,8) | YES |  |  |  |
| macd_histogram | decimal(20,8) | YES |  |  |  |
| rsi | decimal(10,4) | YES |  |  |  |
| bollinger_upper | decimal(20,8) | YES |  |  |  |
| bollinger_middle | decimal(20,8) | YES |  |  |  |
| bollinger_lower | decimal(20,8) | YES |  |  |  |
| bollinger_width | decimal(20,8) | YES |  |  |  |
| stoch_k | decimal(10,4) | YES |  |  |  |
| stoch_d | decimal(10,4) | YES |  |  |  |
| williams_r | decimal(10,4) | YES |  |  |  |
| atr | decimal(20,8) | YES |  |  |  |
| adx | decimal(10,4) | YES |  |  |  |
| cci | decimal(10,4) | YES |  |  |  |
| momentum | decimal(20,8) | YES |  |  |  |
| roc | decimal(10,4) | YES |  |  |  |
| created_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| timestamp | bigint | YES |  |  |  |
| datetime_utc | datetime | YES |  |  |  |
| rsi_14 | decimal(10,4) | YES |  |  |  |
| sma_10 | decimal(20,8) | YES |  |  |  |
| sma_30 | decimal(20,8) | YES |  |  |  |
| ema_20 | decimal(20,8) | YES |  |  |  |
| ema_50 | decimal(20,8) | YES |  |  |  |
| ema_200 | decimal(20,8) | YES |  |  |  |
| bb_upper | decimal(20,8) | YES |  |  |  |
| bb_lower | decimal(20,8) | YES |  |  |  |
| bb_middle | decimal(20,8) | YES |  |  |  |
| volume_sma | decimal(20,8) | YES |  |  |  |
| price_change_1d | decimal(10,4) | YES |  |  |  |
| price_change_7d | decimal(10,4) | YES |  |  |  |
| price_change_30d | decimal(10,4) | YES |  |  |  |
| volatility | decimal(10,4) | YES |  |  |  |
| macd_line | decimal(20,8) | YES |  |  |  |
| vwap | decimal(20,8) | YES |  |  |  |
| obv | decimal(20,8) | YES |  |  |  |
| ppo | decimal(10,4) | YES |  |  |  |
| tsi | decimal(10,4) | YES |  |  |  |
| ultimate_oscillator | decimal(10,4) | YES |  |  |  |
| mfi | decimal(10,4) | YES |  |  |  |
| dmi_plus | decimal(10,4) | YES |  |  |  |
| dmi_minus | decimal(10,4) | YES |  |  |  |
| dx | decimal(10,4) | YES |  |  |  |
| sar | decimal(20,8) | YES |  |  |  |
| bb_percent | decimal(10,4) | YES |  |  |  |
| ad_line | decimal(20,8) | YES |  |  |  |
| accumulation_distribution | decimal(20,8) | YES |  |  |  |
| chaikin_oscillator | decimal(20,8) | YES |  |  |  |
| force_index | decimal(20,8) | YES |  |  |  |
| ease_of_movement | decimal(20,8) | YES |  |  |  |
| negative_volume_index | decimal(20,8) | YES |  |  |  |
| positive_volume_index | decimal(20,8) | YES |  |  |  |
| price_volume_trend | decimal(20,8) | YES |  |  |  |
| volume_rate_of_change | decimal(10,4) | YES |  |  |  |
| williams_ad | decimal(20,8) | YES |  |  |  |
| volume_sma_20 | decimal(20,8) | YES |  |  |  |
| volume_sma_50 | decimal(20,8) | YES |  |  |  |
| volume_ema_20 | decimal(20,8) | YES |  |  |  |
| volume_ema_50 | decimal(20,8) | YES |  |  |  |
| volume_ratio | decimal(10,4) | YES |  |  |  |
| price_volume_correlation | decimal(10,4) | YES |  |  |  |
| volume_momentum | decimal(10,4) | YES |  |  |  |
| volume_oscillator | decimal(10,4) | YES |  |  |  |
| volume_weighted_rsi | decimal(10,4) | YES |  |  |  |
| klinger_oscillator | decimal(20,8) | YES |  |  |  |
| atr_14 | decimal(20,8) | YES |  |  |  |
| bb_bandwidth | decimal(20,8) | YES |  |  |  |
| kc_upper | decimal(20,8) | YES |  |  |  |
| kc_lower | decimal(20,8) | YES |  |  |  |
| kc_middle | decimal(20,8) | YES |  |  |  |
| donchian_upper | decimal(20,8) | YES |  |  |  |
| donchian_lower | decimal(20,8) | YES |  |  |  |
| donchian_middle | decimal(20,8) | YES |  |  |  |
| ichimoku_base | decimal(20,8) | YES |  |  |  |
| ichimoku_conversion | decimal(20,8) | YES |  |  |  |
| ichimoku_span_a | decimal(20,8) | YES |  |  |  |
| ichimoku_span_b | decimal(20,8) | YES |  |  |  |
| bb_width | decimal(20,8) | YES |  |  |  |
| true_range | decimal(20,8) | YES |  |  |  |
| cci_14 | decimal(20,8) | YES |  |  |  |
| stoch_rsi_k | decimal(20,8) | YES |  |  |  |
| stoch_rsi_d | decimal(20,8) | YES |  |  |  |
| trix | decimal(20,8) | YES |  |  |  |
| aroon_up | decimal(20,8) | YES |  |  |  |
| aroon_down | decimal(20,8) | YES |  |  |  |
| adl | decimal(20,8) | YES |  |  |  |
| cmf | decimal(20,8) | YES |  |  |  |
| volume_profile | decimal(20,8) | YES |  |  |  |
| pvt | decimal(20,8) | YES |  |  |  |
| nvi | decimal(20,8) | YES |  |  |  |
| pvi | decimal(20,8) | YES |  |  |  |
| support_level | decimal(20,8) | YES |  |  |  |
| resistance_level | decimal(20,8) | YES |  |  |  |
| pivot_point | decimal(20,8) | YES |  |  |  |
| fibonaci_38 | decimal(20,8) | YES |  |  |  |
| fibonaci_50 | decimal(20,8) | YES |  |  |  |
| fibonaci_62 | decimal(20,8) | YES |  |  |  |
| candlestick_pattern | varchar(100) | YES |  |  |  |
| trend_strength | decimal(10,4) | YES |  |  |  |
| price_velocity | decimal(15,8) | YES |  |  |  |
| updated_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |
| price | decimal(20,8) | YES |  |  |  |
| calculated_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| data_completeness_percentage | decimal(5,2) | YES |  | 0.00 |  |
| data_source | varchar(100) | YES |  |  |  |

### crypto_news

| Column | Type | Null | Key | Default | Extra |
|--------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| title | text | NO |  |  |  |
| content | text | YES |  |  |  |
| url | text | YES |  |  |  |
| url_hash | varchar(32) | YES | UNI |  |  |
| published_at | datetime | YES | MUL |  |  |
| source | varchar(100) | YES | MUL |  |  |
| category | varchar(100) | YES |  |  |  |
| sentiment_score | decimal(5,4) | YES |  |  |  |
| sentiment_confidence | decimal(5,4) | YES |  |  |  |
| llm_sentiment_score | decimal(5,4) | YES |  |  |  |
| llm_sentiment_confidence | decimal(5,4) | YES |  |  |  |
| llm_sentiment_analysis | text | YES |  |  |  |
| market_type | varchar(50) | YES |  | crypto |  |
| stock_sentiment_score | decimal(5,4) | YES |  |  |  |
| stock_sentiment_confidence | decimal(5,4) | YES |  |  |  |
| stock_sentiment_analysis | text | YES |  |  |  |
| crypto_mentions | text | YES |  |  |  |
| created_at | timestamp | YES | MUL | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| updated_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED on update CURRENT_TIMESTAMP |
| collected_at | timestamp | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |

### trading_signals

| Column | Type | Null | Key | Default | Extra |
|--------|------|------|-----|---------|-------|
| id | int | NO | PRI |  | auto_increment |
| timestamp | datetime | NO | MUL |  |  |
| symbol | varchar(50) | NO | MUL |  |  |
| price | decimal(15,8) | YES |  | 0.00000000 |  |
| signal_type | enum('BUY','SELL','HOLD','STRONG_BUY','STRONG_SELL') | NO | MUL |  |  |
| model | varchar(50) | YES |  | default_model |  |
| confidence | decimal(6,4) | NO | MUL |  |  |
| threshold | decimal(6,4) | NO |  |  |  |
| regime | enum('strong_bull','bull','sideways','bear','strong_bear') | NO | MUL |  |  |
| model_version | varchar(50) | NO |  | xgboost_4h |  |
| features_used | int | NO |  | 0 |  |
| xgboost_confidence | decimal(6,4) | NO |  |  |  |
| data_source | varchar(50) | NO |  | database |  |
| real_time_available | tinyint(1) | YES |  | 0 |  |
| volume_24h | decimal(20,8) | YES |  |  |  |
| rsi | decimal(6,2) | YES |  |  |  |
| crypto_sentiment | decimal(6,4) | YES |  |  |  |
| vix | decimal(6,2) | YES |  |  |  |
| llm_analysis | json | YES |  |  |  |
| llm_confidence | decimal(6,4) | YES |  |  |  |
| llm_reasoning | text | YES |  |  |  |
| created_at | datetime | YES |  | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| sentiment_boost | decimal(10,6) | YES |  | 0.000000 |  |
| sentiment_sources | json | YES |  |  |  |
| sentiment_score | decimal(10,6) | YES |  |  |  |
| sentiment_confidence | decimal(10,6) | YES |  |  |  |
| prediction_timestamp | timestamp | YES |  |  |  |
| features | json | YES |  |  |  |
| prediction | decimal(10,6) | YES |  |  |  |
| is_mock | tinyint(1) | YES |  | 1 |  |
| processed | tinyint(1) | YES |  | 0 |  |
| signal_id | varchar(128) | YES | UNI |  |  |
| signal_strength | decimal(6,4) | YES |  | 1.0000 |  |
| processed_at | timestamp | YES | MUL |  |  |
| data_completeness_percentage | decimal(5,2) | YES |  | 0.00 |  |

