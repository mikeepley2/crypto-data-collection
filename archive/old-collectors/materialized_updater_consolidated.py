#!/usr/bin/env python3
"""
Materialized Updater - CONSOLIDATED VERSION
Updated to use consolidated database structure and centralized configuration
"""

import os
import sys
import time
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, timedelta
import logging
from decimal import Decimal

# Import centralized configuration (if available)
try:
    sys.path.append('/app')
    from shared.table_config import CRYPTO_TABLES, TECHNICAL_TABLES, ML_TABLES, MARKET_TABLES
    USE_CENTRALIZED_CONFIG = True
    print("✅ Using centralized table configuration")
except ImportError:
    # Fallback to direct table names if centralized config not available
    CRYPTO_TABLES = {
        "ASSETS": "crypto_assets",
        "ONCHAIN_DATA": "crypto_onchain_data", 
        "NEWS": "crypto_news"
    }
    TECHNICAL_TABLES = {
        "INDICATORS": "technical_indicators"
    }
    ML_TABLES = {
        "FEATURES": "ml_features_materialized"
    }
    MARKET_TABLES = {
        "MACRO": "macro_indicators",
        "SENTIMENT": "sentiment_aggregation"
    }
    USE_CENTRALIZED_CONFIG = False
    print("⚠️ Using fallback table configuration")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('materialized-updater-consolidated')

# Database connection pool
pool = None

def init_pool():
    """Initialize database connection pool using centralized config"""
    global pool
    try:
        pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="materialized_pool",
            pool_size=5,
            pool_reset_session=True,
            host=os.getenv("MYSQL_HOST", "host.docker.internal"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database=os.getenv("MYSQL_DATABASE", "crypto_prices"),        
            charset="utf8mb4",
            autocommit=True
        )
        logger.info("✅ Database connection pool initialized with centralized config")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database pool: {e}")
        pool = None

def get_connection():
    """Get connection from pool"""
    try:
        if pool:
            return pool.get_connection()
        else:
            logger.error("❌ Database pool not initialized")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to get database connection: {e}")
        return None

def load_macro_indicators():
    """Load macro indicators from consolidated macro_indicators table"""
    indicators = {}
    try:
        conn = get_connection()
        if not conn:
            return indicators

        cursor = conn.cursor(dictionary=True)

        # Get the latest macro indicators using correct column names
        query = f"""
        SELECT indicator_name, value, indicator_date
        FROM {MARKET_TABLES['MACRO']}
        WHERE DATE(indicator_date) = CURDATE()
        ORDER BY indicator_name, indicator_date DESC
        """

        cursor.execute(query)
        results = cursor.fetchall()

        for row in results:
            indicators[row['indicator_name']] = row['value']

        cursor.close()
        conn.close()

        logger.info(f"✅ Loaded {len(indicators)} macro indicators: {list(indicators.keys())}")

    except Exception as e:
        logger.error(f"❌ Error loading macro indicators: {e}")

    return indicators

def get_sentiment_data(symbol, cursor):
    """Get sentiment data from consolidated crypto_news table"""
    try:
        sentiment_query = f"""
        SELECT AVG(COALESCE(ml_sentiment_score, 0)) as avg_sentiment, 
               COUNT(*) as sentiment_count,
               AVG(COALESCE(ml_sentiment_confidence, 0)) as avg_confidence
        FROM {CRYPTO_TABLES['NEWS']}
        WHERE (title LIKE %s OR content LIKE %s)
        AND DATE(created_at) = CURDATE()
        AND ml_sentiment_score IS NOT NULL
        """
        
        cursor.execute(sentiment_query, (f'%{symbol}%', f'%{symbol}%'))
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            return {
                'avg_sentiment': float(result[0]),
                'sentiment_count': int(result[1]),
                'avg_confidence': float(result[2]) if result[2] else 0.0
            }
        else:
            return {
                'avg_sentiment': None,
                'sentiment_count': 0,
                'avg_confidence': None
            }
    except Exception as e:
        logger.error(f"❌ Error getting sentiment data for {symbol}: {e}")
        return {
            'avg_sentiment': None,
            'sentiment_count': 0, 
            'avg_confidence': None
        }

def get_technical_indicators(symbol, cursor):
    """Get technical indicators from consolidated technical_indicators table"""
    try:
        tech_query = f"""
        SELECT current_price, price_change_24h, volume_usd_24h, market_cap,
               sma_20, rsi_14, macd_line, macd_signal, macd_histogram,
               bb_upper, bb_middle, bb_lower,
               high_24h, low_24h
        FROM {TECHNICAL_TABLES['INDICATORS']}
        WHERE symbol = %s
        AND DATE(timestamp_iso) = CURDATE()
        ORDER BY timestamp_iso DESC
        LIMIT 1
        """
        
        cursor.execute(tech_query, (symbol,))
        result = cursor.fetchone()
        
        if result:
            return {
                'current_price': result[0],
                'price_change_24h': result[1],
                'volume_24h': result[2],
                'market_cap': result[3],
                'sma_20': result[4],
                'rsi_14': result[5],
                'macd_line': result[6],
                'macd_signal': result[7],
                'macd_histogram': result[8],
                'bb_upper': result[9],
                'bb_middle': result[10],
                'bb_lower': result[11],
                'high_24h': result[12],
                'low_24h': result[13]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"❌ Error getting technical indicators for {symbol}: {e}")
        return None

def get_onchain_data(symbol, cursor):
    """Get onchain data from consolidated crypto_onchain_data table"""
    try:
        onchain_query = f"""
        SELECT active_addresses, transaction_count, volume_24h, 
               circulating_supply, market_cap
        FROM {CRYPTO_TABLES['ONCHAIN_DATA']}
        WHERE coin_symbol = %s
        AND DATE(timestamp) = CURDATE()
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        cursor.execute(onchain_query, (symbol,))
        result = cursor.fetchone()
        
        if result:
            return {
                'active_addresses': result[0],
                'transaction_count': result[1],
                'volume_24h': result[2],
                'circulating_supply': result[3],
                'onchain_market_cap': result[4]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"❌ Error getting onchain data for {symbol}: {e}")
        return None

def process_today_records():
    """Process today's records using consolidated database structure"""
    try:
        conn = get_connection()
        if not conn:
            logger.error("❌ Could not get database connection")
            return

        cursor = conn.cursor()

        # Load macro indicators
        macro_indicators = load_macro_indicators()
        logger.info(f"📊 Loaded macro indicators: {len(macro_indicators)} items")

        # Get unique symbols from technical_indicators table (our consolidated price source)
        symbols_query = f"""
        SELECT DISTINCT symbol 
        FROM {TECHNICAL_TABLES['INDICATORS']}
        WHERE DATE(timestamp_iso) = CURDATE()
        ORDER BY symbol
        """

        cursor.execute(symbols_query)
        symbols = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 Processing {len(symbols)} symbols for materialized features")

        # Process each symbol
        symbols_processed = 0
        for symbol in symbols:
            try:
                # Get all data for this symbol
                tech_data = get_technical_indicators(symbol, cursor)
                if not tech_data:
                    logger.debug(f"⚠️ No technical data for {symbol}")
                    continue

                sentiment_data = get_sentiment_data(symbol, cursor)
                onchain_data = get_onchain_data(symbol, cursor)

                # Prepare data for ml_features_materialized
                current_time = datetime.now()
                price_date = current_time.date()

                # Build the feature record
                feature_data = (
                    symbol,                                           # symbol
                    price_date,                                      # price_date
                    current_time.hour,                              # price_hour
                    current_time,                                   # timestamp_iso
                    tech_data.get('current_price'),                 # current_price
                    tech_data.get('price_change_24h'),              # price_change_24h
                    tech_data.get('volume_24h'),                    # volume_24h
                    tech_data.get('market_cap'),                    # market_cap
                    sentiment_data.get('avg_sentiment'),            # avg_ml_overall_sentiment
                    sentiment_data.get('sentiment_count'),          # sentiment_volume
                    onchain_data.get('active_addresses') if onchain_data else None,  # active_addresses_24h
                    onchain_data.get('transaction_count') if onchain_data else None, # transaction_count_24h
                    None,                                           # exchange_net_flow_24h (not available)
                    None,                                           # price_volatility_7d (calculate later)
                    tech_data.get('sma_20'),                        # sma_20
                    tech_data.get('rsi_14'),                        # rsi_14
                    tech_data.get('macd_line'),                     # macd_line
                    tech_data.get('macd_signal'),                   # macd_signal
                    tech_data.get('macd_histogram'),                # macd_histogram
                    tech_data.get('bb_upper'),                      # bb_upper
                    tech_data.get('bb_middle'),                     # bb_middle
                    tech_data.get('bb_lower'),                      # bb_lower
                    macro_indicators.get('VIX'),                    # vix
                    macro_indicators.get('DXY'),                    # dxy
                    macro_indicators.get('DGS10'),                  # treasury_10y
                    macro_indicators.get('UNEMPLOYMENT_RATE'),      # unemployment_rate
                    macro_indicators.get('INFLATION_RATE'),         # inflation_rate
                    macro_indicators.get('GOLD'),                   # gold_price
                    macro_indicators.get('OIL'),                    # oil_price
                    tech_data.get('current_price'),                 # close_price
                    tech_data.get('current_price'),                 # close
                    current_time,                                   # created_at
                    current_time                                    # updated_at
                )

                # Insert into ml_features_materialized table
                insert_query = f"""
                INSERT INTO {ML_TABLES['FEATURES']} (
                    symbol, price_date, price_hour, timestamp_iso, current_price,
                    price_change_24h, volume_24h, market_cap,
                    avg_ml_overall_sentiment, sentiment_volume,
                    active_addresses_24h, transaction_count_24h, exchange_net_flow_24h, price_volatility_7d,
                    sma_20, rsi_14, macd_line, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower,
                    vix, dxy, treasury_10y, unemployment_rate, inflation_rate, gold_price, oil_price,
                    close_price, close,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    current_price = VALUES(current_price),
                    price_change_24h = VALUES(price_change_24h),
                    volume_24h = VALUES(volume_24h),
                    market_cap = VALUES(market_cap),
                    avg_ml_overall_sentiment = VALUES(avg_ml_overall_sentiment),
                    sentiment_volume = VALUES(sentiment_volume),
                    active_addresses_24h = VALUES(active_addresses_24h),
                    transaction_count_24h = VALUES(transaction_count_24h),
                    exchange_net_flow_24h = VALUES(exchange_net_flow_24h),
                    price_volatility_7d = VALUES(price_volatility_7d),
                    sma_20 = VALUES(sma_20),
                    rsi_14 = VALUES(rsi_14),
                    macd_line = VALUES(macd_line),
                    macd_signal = VALUES(macd_signal),
                    macd_histogram = VALUES(macd_histogram),
                    bb_upper = VALUES(bb_upper),
                    bb_middle = VALUES(bb_middle),
                    bb_lower = VALUES(bb_lower),
                    vix = VALUES(vix),
                    dxy = VALUES(dxy),
                    treasury_10y = VALUES(treasury_10y),
                    unemployment_rate = VALUES(unemployment_rate),
                    inflation_rate = VALUES(inflation_rate),
                    gold_price = VALUES(gold_price),
                    oil_price = VALUES(oil_price),
                    close_price = VALUES(close_price),
                    close = VALUES(close),
                    updated_at = VALUES(updated_at)
                """

                cursor.execute(insert_query, feature_data)
                symbols_processed += 1

                if symbols_processed % 50 == 0:
                    logger.info(f"📊 Processed {symbols_processed}/{len(symbols)} symbols...")

            except Exception as e:
                logger.error(f"❌ Error processing symbol {symbol}: {e}")
                continue

        cursor.close()
        conn.close()

        logger.info(f"✅ Completed materialized feature update: {symbols_processed}/{len(symbols)} symbols processed")

    except Exception as e:
        logger.error(f"❌ Error processing today's records: {e}")

def validate_table_access():
    """Validate access to all required tables"""
    try:
        conn = get_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        
        # Test access to all consolidated tables
        tables_to_check = {
            'Technical Indicators': TECHNICAL_TABLES['INDICATORS'],
            'Crypto News': CRYPTO_TABLES['NEWS'],
            'Onchain Data': CRYPTO_TABLES['ONCHAIN_DATA'],
            'Macro Indicators': MARKET_TABLES['MACRO'],
            'ML Features': ML_TABLES['FEATURES']
        }
        
        for table_name, table in tables_to_check.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1")
                count = cursor.fetchone()[0]
                logger.info(f"✅ {table_name} ({table}): {count:,} records accessible")
            except Exception as e:
                logger.error(f"❌ {table_name} ({table}): {e}")
                
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Table validation failed: {e}")
        return False

def main():
    """Main function with consolidated database structure"""
    logger.info("🚀 Starting Materialized Updater - CONSOLIDATED VERSION")
    logger.info(f"📋 Using centralized config: {USE_CENTRALIZED_CONFIG}")
    logger.info(f"📊 Target tables: {TECHNICAL_TABLES['INDICATORS']}, {CRYPTO_TABLES['NEWS']}, {CRYPTO_TABLES['ONCHAIN_DATA']}")

    # Initialize database pool
    init_pool()

    if not pool:
        logger.error("❌ Failed to initialize database pool. Exiting.")
        return

    # Validate table access
    logger.info("🔍 Validating access to consolidated tables...")
    if not validate_table_access():
        logger.error("❌ Table validation failed. Check database structure.")
        return

    # Process today's records
    logger.info("📊 Processing materialized features with consolidated data...")
    process_today_records()

    logger.info("✅ Materialized updater completed successfully with consolidated structure")

if __name__ == "__main__":
    main()