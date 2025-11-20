#!/usr/bin/env python3
"""
Create Missing Database Tables - ACCURATE PRODUCTION SCHEMAS
Creates all tables required by the integration test suite using EXACT production schemas
Generated from actual database structure analysis
"""

import mysql.connector
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from shared.database_config import get_db_connection

def create_missing_tables():
    """Create missing tables with EXACT production schemas"""
    
    print("🔧 Creating tables with accurate production schemas...")
    
    # EXACT schemas from production database analysis
    table_schemas = {
        "crypto_assets": """
        CREATE TABLE IF NOT EXISTS `crypto_assets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `symbol` varchar(16) NOT NULL,
  `name` varchar(64) NOT NULL,
  `aliases` json DEFAULT NULL,
  `category` varchar(32) DEFAULT 'crypto',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `coingecko_id` varchar(150) DEFAULT NULL,
  `description` text,
  `market_cap_rank` int DEFAULT NULL,
  `coingecko_score` decimal(5,2) DEFAULT NULL,
  `homepage` varchar(255) DEFAULT NULL,
  `last_metadata_update` timestamp NULL DEFAULT NULL,
  `coinbase_supported` tinyint(1) DEFAULT '1' COMMENT 'Whether asset is supported on Coinbase Advanced Trade API',
  `binance_us_supported` tinyint(1) DEFAULT '0' COMMENT 'Whether asset is supported on Binance.US',
  `kucoin_supported` tinyint(1) DEFAULT '0' COMMENT 'Whether asset is supported on KuCoin',
  `exchange_support_updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last time exchange support was updated',
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`),
  KEY `idx_crypto_assets_coinbase_supported` (`coinbase_supported`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "price_data_real": """
        CREATE TABLE IF NOT EXISTS `price_data_real` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `symbol` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `coin_id` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timestamp` bigint NOT NULL,
  `timestamp_iso` datetime(6) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `current_price` decimal(20,8) NOT NULL,
  `price_change_24h` decimal(20,8) DEFAULT NULL,
  `price_change_percentage_24h` decimal(10,4) DEFAULT NULL,
  `market_cap` decimal(25,2) DEFAULT NULL,
  `volume_usd_24h` decimal(25,2) DEFAULT NULL,
  `volume_qty_24h` decimal(25,8) DEFAULT NULL,
  `market_cap_rank` int DEFAULT NULL,
  `circulating_supply` decimal(25,2) DEFAULT NULL,
  `total_supply` decimal(25,2) DEFAULT NULL,
  `max_supply` decimal(25,2) DEFAULT NULL,
  `ath` decimal(20,8) DEFAULT NULL,
  `ath_date` datetime DEFAULT NULL,
  `atl` decimal(20,8) DEFAULT NULL,
  `atl_date` datetime DEFAULT NULL,
  `collection_interval` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_source` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `collector_container` tinyint(1) DEFAULT '1',
  `collection_run` bigint DEFAULT NULL,
  `data_quality_score` decimal(3,2) DEFAULT '1.00',
  `high_24h` decimal(20,8) DEFAULT NULL,
  `low_24h` decimal(20,8) DEFAULT NULL,
  `open_24h` decimal(20,8) DEFAULT NULL,
  `volume_30d` decimal(25,2) DEFAULT NULL,
  `bid_price` decimal(20,8) DEFAULT NULL,
  `ask_price` decimal(20,8) DEFAULT NULL,
  `spread` decimal(20,8) DEFAULT NULL,
  `hourly_volume_qty` decimal(25,8) DEFAULT NULL,
  `hourly_volume_usd` decimal(25,2) DEFAULT NULL,
  `hourly_volume` decimal(25,2) DEFAULT NULL,
  `rsi_14` decimal(10,4) DEFAULT NULL,
  `sma_20` decimal(20,8) DEFAULT NULL,
  `sma_50` decimal(20,8) DEFAULT NULL,
  `ema_12` decimal(20,8) DEFAULT NULL,
  `ema_26` decimal(20,8) DEFAULT NULL,
  `macd` decimal(20,8) DEFAULT NULL,
  `macd_signal` decimal(20,8) DEFAULT NULL,
  `macd_histogram` decimal(20,8) DEFAULT NULL,
  `bb_upper` decimal(20,8) DEFAULT NULL,
  `bb_lower` decimal(20,8) DEFAULT NULL,
  `bb_middle` decimal(20,8) DEFAULT NULL,
  `volume_sma_20` decimal(25,2) DEFAULT NULL,
  `volume_ratio` decimal(10,4) DEFAULT NULL,
  `data_completeness_percentage` decimal(5,2) DEFAULT '0.00' COMMENT 'Percentage of expected data fields that are populated (0-100)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_symbol_timestamp` (`symbol`,`timestamp`),
  KEY `idx_symbol_timestamp` (`symbol`,`timestamp`),
  KEY `idx_coin_id_timestamp` (`coin_id`,`timestamp`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_timestamp_iso` (`timestamp_iso`),
  KEY `idx_symbol_timestamp_iso` (`symbol`,`timestamp_iso`),
  KEY `idx_collection_run` (`collection_run`),
  KEY `idx_market_cap_rank` (`market_cap_rank`),
  KEY `idx_price_range` (`current_price`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "technical_indicators": """
        CREATE TABLE IF NOT EXISTS `technical_indicators` (
  `id` int NOT NULL AUTO_INCREMENT,
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timestamp_iso` datetime NOT NULL,
  `sma_20` decimal(20,8) DEFAULT NULL,
  `sma_50` decimal(20,8) DEFAULT NULL,
  `sma_200` decimal(20,8) DEFAULT NULL,
  `ema_12` decimal(20,8) DEFAULT NULL,
  `ema_26` decimal(20,8) DEFAULT NULL,
  `macd` decimal(20,8) DEFAULT NULL,
  `macd_signal` decimal(20,8) DEFAULT NULL,
  `macd_histogram` decimal(20,8) DEFAULT NULL,
  `rsi` decimal(10,4) DEFAULT NULL,
  `bollinger_upper` decimal(20,8) DEFAULT NULL,
  `bollinger_middle` decimal(20,8) DEFAULT NULL,
  `bollinger_lower` decimal(20,8) DEFAULT NULL,
  `bollinger_width` decimal(20,8) DEFAULT NULL,
  `stoch_k` decimal(10,4) DEFAULT NULL,
  `stoch_d` decimal(10,4) DEFAULT NULL,
  `williams_r` decimal(10,4) DEFAULT NULL,
  `atr` decimal(20,8) DEFAULT NULL,
  `adx` decimal(10,4) DEFAULT NULL,
  `cci` decimal(10,4) DEFAULT NULL,
  `momentum` decimal(20,8) DEFAULT NULL,
  `roc` decimal(10,4) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `timestamp` bigint DEFAULT NULL,
  `datetime_utc` datetime DEFAULT NULL,
  `rsi_14` decimal(10,4) DEFAULT NULL,
  `sma_10` decimal(20,8) DEFAULT NULL,
  `sma_30` decimal(20,8) DEFAULT NULL,
  `ema_20` decimal(20,8) DEFAULT NULL,
  `ema_50` decimal(20,8) DEFAULT NULL,
  `ema_200` decimal(20,8) DEFAULT NULL,
  `bb_upper` decimal(20,8) DEFAULT NULL,
  `bb_lower` decimal(20,8) DEFAULT NULL,
  `bb_middle` decimal(20,8) DEFAULT NULL,
  `volume_sma` decimal(20,8) DEFAULT NULL,
  `price_change_1d` decimal(10,4) DEFAULT NULL,
  `price_change_7d` decimal(10,4) DEFAULT NULL,
  `price_change_30d` decimal(10,4) DEFAULT NULL,
  `volatility` decimal(10,4) DEFAULT NULL,
  `macd_line` decimal(20,8) DEFAULT NULL,
  `vwap` decimal(20,8) DEFAULT NULL,
  `obv` decimal(20,8) DEFAULT NULL,
  `ppo` decimal(10,4) DEFAULT NULL,
  `tsi` decimal(10,4) DEFAULT NULL,
  `ultimate_oscillator` decimal(10,4) DEFAULT NULL,
  `mfi` decimal(10,4) DEFAULT NULL,
  `dmi_plus` decimal(10,4) DEFAULT NULL,
  `dmi_minus` decimal(10,4) DEFAULT NULL,
  `dx` decimal(10,4) DEFAULT NULL,
  `sar` decimal(20,8) DEFAULT NULL,
  `bb_percent` decimal(10,4) DEFAULT NULL,
  `ad_line` decimal(20,8) DEFAULT NULL,
  `accumulation_distribution` decimal(20,8) DEFAULT NULL,
  `chaikin_oscillator` decimal(20,8) DEFAULT NULL,
  `force_index` decimal(20,8) DEFAULT NULL,
  `ease_of_movement` decimal(20,8) DEFAULT NULL,
  `negative_volume_index` decimal(20,8) DEFAULT NULL,
  `positive_volume_index` decimal(20,8) DEFAULT NULL,
  `price_volume_trend` decimal(20,8) DEFAULT NULL,
  `volume_rate_of_change` decimal(10,4) DEFAULT NULL,
  `williams_ad` decimal(20,8) DEFAULT NULL,
  `volume_sma_20` decimal(20,8) DEFAULT NULL,
  `volume_sma_50` decimal(20,8) DEFAULT NULL,
  `volume_ema_20` decimal(20,8) DEFAULT NULL,
  `volume_ema_50` decimal(20,8) DEFAULT NULL,
  `volume_ratio` decimal(10,4) DEFAULT NULL,
  `price_volume_correlation` decimal(10,4) DEFAULT NULL,
  `volume_momentum` decimal(10,4) DEFAULT NULL,
  `volume_oscillator` decimal(10,4) DEFAULT NULL,
  `volume_weighted_rsi` decimal(10,4) DEFAULT NULL,
  `klinger_oscillator` decimal(20,8) DEFAULT NULL,
  `atr_14` decimal(20,8) DEFAULT NULL,
  `bb_bandwidth` decimal(20,8) DEFAULT NULL,
  `kc_upper` decimal(20,8) DEFAULT NULL,
  `kc_lower` decimal(20,8) DEFAULT NULL,
  `kc_middle` decimal(20,8) DEFAULT NULL,
  `donchian_upper` decimal(20,8) DEFAULT NULL,
  `donchian_lower` decimal(20,8) DEFAULT NULL,
  `donchian_middle` decimal(20,8) DEFAULT NULL,
  `ichimoku_base` decimal(20,8) DEFAULT NULL,
  `ichimoku_conversion` decimal(20,8) DEFAULT NULL,
  `ichimoku_span_a` decimal(20,8) DEFAULT NULL,
  `ichimoku_span_b` decimal(20,8) DEFAULT NULL,
  `bb_width` decimal(20,8) DEFAULT NULL,
  `true_range` decimal(20,8) DEFAULT NULL,
  `cci_14` decimal(20,8) DEFAULT NULL,
  `stoch_rsi_k` decimal(20,8) DEFAULT NULL,
  `stoch_rsi_d` decimal(20,8) DEFAULT NULL,
  `trix` decimal(20,8) DEFAULT NULL,
  `aroon_up` decimal(20,8) DEFAULT NULL,
  `aroon_down` decimal(20,8) DEFAULT NULL,
  `adl` decimal(20,8) DEFAULT NULL,
  `cmf` decimal(20,8) DEFAULT NULL,
  `volume_profile` decimal(20,8) DEFAULT NULL,
  `pvt` decimal(20,8) DEFAULT NULL,
  `nvi` decimal(20,8) DEFAULT NULL,
  `pvi` decimal(20,8) DEFAULT NULL,
  `support_level` decimal(20,8) DEFAULT NULL,
  `resistance_level` decimal(20,8) DEFAULT NULL,
  `pivot_point` decimal(20,8) DEFAULT NULL,
  `fibonaci_38` decimal(20,8) DEFAULT NULL,
  `fibonaci_50` decimal(20,8) DEFAULT NULL,
  `fibonaci_62` decimal(20,8) DEFAULT NULL,
  `candlestick_pattern` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trend_strength` decimal(10,4) DEFAULT NULL,
  `price_velocity` decimal(15,8) DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `price` decimal(20,8) DEFAULT NULL,
  `calculated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `data_completeness_percentage` decimal(5,2) DEFAULT '0.00' COMMENT 'Percentage of expected data fields that are populated (0-100)',
  `data_source` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Source of the technical indicator data',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_symbol_timestamp` (`symbol`,`timestamp_iso`),
  KEY `idx_symbol` (`symbol`),
  KEY `idx_timestamp` (`timestamp_iso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "macro_indicators": """
        CREATE TABLE IF NOT EXISTS `macro_indicators` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `indicator_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fred_series_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `indicator_date` date NOT NULL,
  `value` decimal(15,6) DEFAULT NULL,
  `unit` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `frequency` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_source` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'fred',
  `collected_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `data_completeness_percentage` decimal(5,2) DEFAULT '0.00' COMMENT 'Percentage of expected data fields that are populated (0-100)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_indicator_date` (`indicator_name`,`indicator_date`),
  UNIQUE KEY `unique_macro_indicator` (`indicator_name`,`indicator_date`),
  KEY `idx_indicator` (`indicator_name`),
  KEY `idx_date` (`indicator_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "crypto_news": """
        CREATE TABLE IF NOT EXISTS `crypto_news` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` text NOT NULL,
  `content` text,
  `url` text,
  `url_hash` varchar(32) DEFAULT NULL,
  `published_at` datetime DEFAULT NULL,
  `source` varchar(100) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `sentiment_score` decimal(5,4) DEFAULT NULL,
  `sentiment_confidence` decimal(5,4) DEFAULT NULL,
  `llm_sentiment_score` decimal(5,4) DEFAULT NULL,
  `llm_sentiment_confidence` decimal(5,4) DEFAULT NULL,
  `llm_sentiment_analysis` text,
  `market_type` varchar(50) DEFAULT 'crypto',
  `stock_sentiment_score` decimal(5,4) DEFAULT NULL,
  `stock_sentiment_confidence` decimal(5,4) DEFAULT NULL,
  `stock_sentiment_analysis` text,
  `crypto_mentions` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `collected_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `url_hash` (`url_hash`),
  KEY `idx_published_at` (`published_at`),
  KEY `idx_source` (`source`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "real_time_sentiment_signals": """
        CREATE TABLE IF NOT EXISTS `real_time_sentiment_signals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `symbol` varchar(20) NOT NULL,
  `signal_type` varchar(50) NOT NULL,
  `sentiment_score` decimal(10,6) DEFAULT NULL,
  `confidence` decimal(10,6) DEFAULT NULL,
  `metadata` json DEFAULT NULL,
  `signal_strength` decimal(10,6) DEFAULT '0.000000',
  PRIMARY KEY (`id`),
  KEY `idx_symbol_timestamp` (`symbol`,`timestamp`),
  KEY `idx_signal_type` (`signal_type`),
  KEY `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "trading_signals": """
        CREATE TABLE IF NOT EXISTS `trading_signals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL,
  `symbol` varchar(50) NOT NULL,
  `price` decimal(15,8) DEFAULT '0.00000000',
  `signal_type` enum('BUY','SELL','HOLD','STRONG_BUY','STRONG_SELL') NOT NULL,
  `model` varchar(50) DEFAULT 'default_model',
  `confidence` decimal(6,4) NOT NULL,
  `threshold` decimal(6,4) NOT NULL,
  `regime` enum('strong_bull','bull','sideways','bear','strong_bear') NOT NULL,
  `model_version` varchar(50) NOT NULL DEFAULT 'xgboost_4h',
  `features_used` int NOT NULL DEFAULT '0',
  `xgboost_confidence` decimal(6,4) NOT NULL,
  `data_source` varchar(50) NOT NULL DEFAULT 'database',
  `real_time_available` tinyint(1) DEFAULT '0',
  `volume_24h` decimal(20,8) DEFAULT NULL,
  `rsi` decimal(6,2) DEFAULT NULL,
  `crypto_sentiment` decimal(6,4) DEFAULT NULL,
  `vix` decimal(6,2) DEFAULT NULL,
  `llm_analysis` json DEFAULT NULL,
  `llm_confidence` decimal(6,4) DEFAULT NULL,
  `llm_reasoning` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `sentiment_boost` decimal(10,6) DEFAULT '0.000000' COMMENT 'Sentiment adjustment to XGBoost confidence',
  `sentiment_sources` json DEFAULT NULL COMMENT 'Array of sentiment sources (twitter, reddit, etc.)',
  `sentiment_score` decimal(10,6) DEFAULT NULL COMMENT 'Primary sentiment score used for boost',
  `sentiment_confidence` decimal(10,6) DEFAULT NULL COMMENT 'Confidence in sentiment analysis',
  `prediction_timestamp` timestamp NULL DEFAULT NULL,
  `features` json DEFAULT NULL,
  `prediction` decimal(10,6) DEFAULT NULL,
  `is_mock` tinyint(1) DEFAULT '1',
  `processed` tinyint(1) DEFAULT '0',
  `signal_id` varchar(128) DEFAULT NULL COMMENT 'Unique identifier for signal from K8s services',
  `signal_strength` decimal(6,4) DEFAULT '1.0000' COMMENT 'Signal strength score from ML models',
  `processed_at` timestamp NULL DEFAULT NULL COMMENT 'When signal was processed by trading bridge',
  `data_completeness_percentage` decimal(5,2) DEFAULT '0.00' COMMENT 'Percentage of expected data fields that are populated (0-100)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `signal_id` (`signal_id`),
  KEY `idx_symbol_timestamp` (`symbol`,`timestamp`),
  KEY `idx_signal_type` (`signal_type`),
  KEY `idx_confidence` (`confidence`),
  KEY `idx_regime` (`regime`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_symbol` (`symbol`),
  KEY `idx_sentiment_realtime` (`symbol`,`timestamp`,`real_time_available`),
  KEY `idx_signal_id` (`signal_id`),
  KEY `idx_processed_at` (`processed_at`),
  KEY `idx_timestamp_confidence` (`timestamp`,`confidence`),
  KEY `idx_unprocessed_signals` (`timestamp`,`confidence`,`processed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "trade_recommendations": """
        CREATE TABLE IF NOT EXISTS `trade_recommendations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `signal_id` int DEFAULT NULL,
  `symbol` varchar(50) NOT NULL,
  `signal_type` enum('BUY','SELL','HOLD','STRONG_BUY','STRONG_SELL') NOT NULL,
  `amount_usd` decimal(15,8) NOT NULL,
  `confidence` decimal(6,4) NOT NULL,
  `reasoning` text,
  `execution_status` varchar(50) DEFAULT NULL,
  `entry_price` decimal(15,8) DEFAULT NULL,
  `stop_loss` decimal(15,8) DEFAULT NULL,
  `take_profit` decimal(15,8) DEFAULT NULL,
  `position_size_percent` decimal(5,2) DEFAULT NULL,
  `amount_crypto` decimal(20,8) DEFAULT NULL,
  `is_mock` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `executed_at` timestamp NULL DEFAULT NULL,
  `llm_validation` varchar(20) DEFAULT NULL,
  `llm_confidence` decimal(3,2) DEFAULT NULL,
  `llm_reasoning` text,
  `risk_assessment` varchar(10) DEFAULT NULL,
  `suggested_amount` decimal(15,8) DEFAULT NULL,
  `validation_timestamp` timestamp NULL DEFAULT NULL,
  `error_message` text,
  `risk_score` decimal(5,4) DEFAULT NULL,
  `risk_level` varchar(20) DEFAULT NULL,
  `risk_approved` tinyint(1) DEFAULT NULL,
  `risk_reason` text,
  `risk_assessment_timestamp` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_signal_id` (`signal_id`),
  KEY `idx_symbol` (`symbol`),
  KEY `idx_status` (`execution_status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "backtesting_results": """
        CREATE TABLE IF NOT EXISTS `backtesting_results` (
  `id` int NOT NULL AUTO_INCREMENT,
  `strategy_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `initial_capital` decimal(15,2) NOT NULL,
  `final_capital` decimal(15,2) NOT NULL,
  `total_return` decimal(10,6) NOT NULL,
  `annualized_return` decimal(10,6) NOT NULL,
  `volatility` decimal(10,6) NOT NULL,
  `sharpe_ratio` decimal(10,6) NOT NULL,
  `max_drawdown` decimal(10,6) NOT NULL,
  `win_rate` decimal(10,6) NOT NULL,
  `total_trades` int NOT NULL,
  `profitable_trades` int NOT NULL,
  `parameters` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_strategy` (`strategy_name`),
  KEY `idx_symbol` (`symbol`),
  KEY `idx_start_date` (`start_date`),
  KEY `idx_sharpe_ratio` (`sharpe_ratio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        "backtesting_trades": """
        CREATE TABLE IF NOT EXISTS `backtesting_trades` (
  `id` int NOT NULL AUTO_INCREMENT,
  `backtesting_result_id` int NOT NULL,
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `trade_type` enum('BUY','SELL') COLLATE utf8mb4_unicode_ci NOT NULL,
  `entry_price` decimal(20,8) NOT NULL,
  `exit_price` decimal(20,8) DEFAULT NULL,
  `quantity` decimal(20,8) NOT NULL,
  `entry_date` timestamp NOT NULL,
  `exit_date` timestamp NULL DEFAULT NULL,
  `pnl` decimal(15,2) DEFAULT NULL,
  `return_pct` decimal(10,6) DEFAULT NULL,
  `strategy_signal` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_backtesting_result` (`backtesting_result_id`),
  KEY `idx_symbol` (`symbol`),
  KEY `idx_entry_date` (`entry_date`),
  KEY `idx_trade_type` (`trade_type`),
  CONSTRAINT `backtesting_trades_ibfk_1` FOREIGN KEY (`backtesting_result_id`) REFERENCES `backtesting_results` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

    }
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        print(f"📊 Creating {len(table_schemas)} core tables...")
        
        created_tables = []
        failed_tables = []
        
        for table_name, schema_sql in table_schemas.items():
            try:
                print(f"🔨 Creating table: {table_name}")
                cursor.execute(schema_sql)
                created_tables.append(table_name)
            except Exception as e:
                print(f"❌ Failed to create {table_name}: {e}")
                failed_tables.append(table_name)
        
        # Verify tables exist
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        print(f"\n✅ Tables created successfully: {created_tables}")
        if failed_tables:
            print(f"⚠️ Failed to create tables: {failed_tables}")
        print(f"📋 Total tables in database: {len(existing_tables)}")
        
        cursor.close()
        connection.close()
        
        return len(failed_tables) == 0
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Creating Missing Tables - Production Schemas")
    print("=" * 55)
    
    success = create_missing_tables()
    
    if success:
        print("\n🎉 All tables created successfully!")
        print("✅ Database schema now matches production structure")
    else:
        print("\n❌ Some tables failed to create")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
