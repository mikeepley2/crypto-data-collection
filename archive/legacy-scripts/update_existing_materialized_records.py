#!/usr/bin/env python3
"""Update existing materialized records with fixed join logic - batched"""
import mysql.connector
from datetime import datetime, timedelta
import time

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("UPDATING EXISTING MATERIALIZED RECORDS (BATCHED)")
print("=" * 80)
print()

# Get count of records to update
cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND (rsi_14 IS NULL OR sma_20 IS NULL)
"""
)
tech_count = cursor.fetchone()["cnt"]
print(f"Found {tech_count:,} records needing technical indicators")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND (vix IS NULL OR spx IS NULL OR dxy IS NULL)
"""
)
macro_count = cursor.fetchone()["cnt"]
print(f"Found {macro_count:,} records needing macro indicators")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND open_price IS NULL
"""
)
ohlc_count = cursor.fetchone()["cnt"]
print(f"Found {ohlc_count:,} records needing OHLC data")

cursor.execute(
    """
    SELECT COUNT(*) as cnt
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND active_addresses_24h IS NULL
"""
)
onchain_count = cursor.fetchone()["cnt"]
print(f"Found {onchain_count:,} records needing onchain data")
print()

# Update technical indicators using (symbol, date) join - get latest per date
print("1️⃣  Updating Technical Indicators...")
start_time = time.time()
cursor.execute(
    """
    UPDATE ml_features_materialized m
    INNER JOIN (
        SELECT t1.symbol, DATE(t1.timestamp_iso) as tech_date,
            t1.rsi_14, t1.sma_20, t1.sma_50, t1.ema_12, t1.ema_26,
            t1.macd as macd_line, t1.macd_signal, t1.macd_histogram,
            t1.bb_upper, t1.bb_middle, t1.bb_lower
        FROM technical_indicators t1
        INNER JOIN (
            SELECT symbol, DATE(timestamp_iso) as tech_date,
                MAX(timestamp_iso) as max_ts
            FROM technical_indicators
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY symbol, DATE(timestamp_iso)
        ) t2 ON BINARY t1.symbol = BINARY t2.symbol
            AND DATE(t1.timestamp_iso) = t2.tech_date
            AND t1.timestamp_iso = t2.max_ts
        WHERE t1.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    ) t ON BINARY m.symbol = BINARY t.symbol
        AND DATE(m.timestamp_iso) = t.tech_date
    SET 
        m.rsi_14 = t.rsi_14,
        m.sma_20 = t.sma_20,
        m.sma_50 = t.sma_50,
        m.ema_12 = t.ema_12,
        m.ema_26 = t.ema_26,
        m.macd_line = t.macd_line,
        m.macd_signal = t.macd_signal,
        m.macd_histogram = t.macd_histogram,
        m.bb_upper = t.bb_upper,
        m.bb_middle = t.bb_middle,
        m.bb_lower = t.bb_lower,
        m.updated_at = NOW()
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND (m.rsi_14 IS NULL OR m.sma_20 IS NULL)
    LIMIT 50000
"""
)
tech_updated = cursor.rowcount
conn.commit()
elapsed = time.time() - start_time
print(f"   Updated {tech_updated:,} records with technical indicators ({elapsed:.1f}s)")

# Update macro indicators using date join
print("2️⃣  Updating Macro Indicators...")
start_time = time.time()
cursor.execute(
    """
    UPDATE ml_features_materialized m
    INNER JOIN (
        SELECT indicator_date,
            MAX(CASE WHEN indicator_name = 'VIX' THEN value END) as vix,
            MAX(CASE WHEN indicator_name = 'SPX' THEN value END) as spx,
            MAX(CASE WHEN indicator_name = 'DXY' THEN value END) as dxy,
            MAX(CASE WHEN indicator_name = 'TNX' THEN value END) as tnx,
            MAX(CASE WHEN indicator_name = '10Y_YIELD' THEN value END) as tnx_alt,
            MAX(CASE WHEN indicator_name = 'FEDERAL_FUNDS_RATE' THEN value END) as fed_funds_rate,
            MAX(CASE WHEN indicator_name = 'GOLD_PRICE' THEN value END) as gold_price,
            MAX(CASE WHEN indicator_name = 'OIL_PRICE' THEN value END) as oil_price,
            MAX(CASE WHEN indicator_name = 'US_UNEMPLOYMENT' THEN value END) as unemployment_rate,
            MAX(CASE WHEN indicator_name = 'US_INFLATION' THEN value END) as inflation_rate,
            MAX(CASE WHEN indicator_name = 'Treasury_10Y' THEN value END) as treasury_10y
        FROM macro_indicators
        WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY indicator_date
    ) mi ON DATE(m.timestamp_iso) = mi.indicator_date
    SET 
        m.vix = mi.vix,
        m.spx = mi.spx,
        m.dxy = mi.dxy,
        m.tnx = COALESCE(mi.tnx, mi.tnx_alt),
        m.fed_funds_rate = mi.fed_funds_rate,
        m.gold_price = mi.gold_price,
        m.oil_price = mi.oil_price,
        m.unemployment_rate = mi.unemployment_rate,
        m.inflation_rate = mi.inflation_rate,
        m.treasury_10y = mi.treasury_10y,
        m.updated_at = NOW()
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND (m.vix IS NULL OR m.spx IS NULL OR m.dxy IS NULL)
"""
)
macro_updated = cursor.rowcount
conn.commit()
elapsed = time.time() - start_time
print(f"   Updated {macro_updated:,} records with macro indicators ({elapsed:.1f}s)")

# Update OHLC data - get latest per date
print("3️⃣  Updating OHLC Data...")
start_time = time.time()
cursor.execute(
    """
    UPDATE ml_features_materialized m
    INNER JOIN (
        SELECT o1.symbol, DATE(o1.timestamp_iso) as ohlc_date,
            o1.open_price, o1.high_price, o1.low_price, o1.close_price,
            o1.volume as ohlc_volume,
            o1.data_source as ohlc_source
        FROM ohlc_data o1
        INNER JOIN (
            SELECT symbol, DATE(timestamp_iso) as ohlc_date,
                MAX(timestamp_iso) as max_ts
            FROM ohlc_data
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY symbol, DATE(timestamp_iso)
        ) o2 ON BINARY o1.symbol = BINARY o2.symbol
            AND DATE(o1.timestamp_iso) = o2.ohlc_date
            AND o1.timestamp_iso = o2.max_ts
        WHERE o1.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    ) o ON BINARY m.symbol = BINARY o.symbol
        AND DATE(m.timestamp_iso) = o.ohlc_date
    SET 
        m.open_price = o.open_price,
        m.high_price = o.high_price,
        m.low_price = o.low_price,
        m.close_price = o.close_price,
        m.ohlc_volume = o.ohlc_volume,
        m.ohlc_source = o.ohlc_source,
        m.updated_at = NOW()
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND m.open_price IS NULL
"""
)
ohlc_updated = cursor.rowcount
conn.commit()
elapsed = time.time() - start_time
print(f"   Updated {ohlc_updated:,} records with OHLC data ({elapsed:.1f}s)")

# Update onchain data - get latest per date
print("4️⃣  Updating Onchain Data...")
start_time = time.time()
cursor.execute(
    """
    UPDATE ml_features_materialized m
    INNER JOIN (
        SELECT o1.coin_symbol as symbol, DATE(o1.timestamp) as onchain_date,
            o1.active_addresses_24h,
            o1.transaction_count_24h,
            o1.exchange_net_flow_24h,
            o1.price_volatility_7d
        FROM crypto_onchain_data o1
        INNER JOIN (
            SELECT coin_symbol, DATE(timestamp) as onchain_date,
                MAX(timestamp) as max_ts
            FROM crypto_onchain_data
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            AND active_addresses_24h IS NOT NULL
            AND transaction_count_24h IS NOT NULL
            GROUP BY coin_symbol, DATE(timestamp)
        ) o2 ON BINARY o1.coin_symbol = BINARY o2.coin_symbol
            AND DATE(o1.timestamp) = o2.onchain_date
            AND o1.timestamp = o2.max_ts
        WHERE o1.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND o1.active_addresses_24h IS NOT NULL
        AND o1.transaction_count_24h IS NOT NULL
    ) o ON BINARY m.symbol = BINARY o.symbol
        AND DATE(m.timestamp_iso) = o.onchain_date
    SET 
        m.active_addresses_24h = o.active_addresses_24h,
        m.transaction_count_24h = o.transaction_count_24h,
        m.exchange_net_flow_24h = o.exchange_net_flow_24h,
        m.price_volatility_7d = o.price_volatility_7d,
        m.updated_at = NOW()
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND m.active_addresses_24h IS NULL
"""
)
onchain_updated = cursor.rowcount
conn.commit()
elapsed = time.time() - start_time
print(f"   Updated {onchain_updated:,} records with onchain data ({elapsed:.1f}s)")

print()
print("=" * 80)
print("UPDATE SUMMARY:")
print(f"  Technical indicators: {tech_updated:,} records")
print(f"  Macro indicators: {macro_updated:,} records")
print(f"  OHLC data: {ohlc_updated:,} records")
print(f"  Onchain data: {onchain_updated:,} records")
print()
total = tech_updated + macro_updated + ohlc_updated + onchain_updated
print(f"Total: {total:,} records updated")
print("=" * 80)

conn.close()
