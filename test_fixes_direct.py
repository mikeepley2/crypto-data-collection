#!/usr/bin/env python3
"""Test fixes by directly checking if joins work correctly"""
import mysql.connector
from datetime import datetime, timedelta

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("TESTING FIXES - VERIFYING JOINS WORK")
print("=" * 80)
print()

# Test 1: Technical Indicators Join (by symbol, date)
print("1️⃣  Testing Technical Indicators Join (symbol, date)")
cursor.execute(
    """
    SELECT 
        m.symbol,
        DATE(m.timestamp_iso) as date,
        COUNT(*) as materialized_count,
        COUNT(t.rsi_14) as tech_matched_count,
        MAX(t.rsi_14) as sample_rsi,
        MAX(t.sma_20) as sample_sma20
    FROM ml_features_materialized m
    LEFT JOIN technical_indicators t
        ON BINARY m.symbol = BINARY t.symbol
        AND DATE(m.timestamp_iso) = DATE(t.timestamp_iso)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY m.symbol, DATE(m.timestamp_iso)
    HAVING tech_matched_count > 0
    ORDER BY materialized_count DESC
    LIMIT 5
"""
)
tech_test = cursor.fetchall()
print(f"   Samples where join works:")
for t in tech_test:
    pct = (
        (t["tech_matched_count"] / t["materialized_count"] * 100)
        if t["materialized_count"] > 0
        else 0
    )
    print(
        f"      {t['symbol']} on {t['date']}: {t['tech_matched_count']}/{t['materialized_count']} matched ({pct:.1f}%)"
    )
    print(f"         Sample data: rsi={t['sample_rsi']}, sma20={t['sample_sma20']}")
print()

# Test 2: Macro Indicators Join (by date)
print("2️⃣  Testing Macro Indicators Join (date only)")
cursor.execute(
    """
    SELECT 
        DATE(m.timestamp_iso) as date,
        COUNT(*) as materialized_count,
        COUNT(DISTINCT mi.indicator_name) as macro_indicators_found,
        MAX(CASE WHEN mi.indicator_name = 'VIX' THEN mi.value END) as vix,
        MAX(CASE WHEN mi.indicator_name = 'SPX' THEN mi.value END) as spx,
        MAX(CASE WHEN mi.indicator_name = 'DXY' THEN mi.value END) as dxy
    FROM ml_features_materialized m
    LEFT JOIN macro_indicators mi
        ON DATE(m.timestamp_iso) = mi.indicator_date
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY DATE(m.timestamp_iso)
    ORDER BY date DESC
"""
)
macro_test = cursor.fetchall()
print(f"   Macro indicators by date:")
for m in macro_test:
    print(
        f"      {m['date']}: {m['materialized_count']:,} records, {m['macro_indicators_found']} indicators"
    )
    if m["vix"]:
        print(f"         VIX={m['vix']}, SPX={m['spx']}, DXY={m['dxy']}")
print()

# Test 3: OHLC Join
print("3️⃣  Testing OHLC Join (symbol, date)")
cursor.execute(
    """
    SELECT 
        m.symbol,
        DATE(m.timestamp_iso) as date,
        COUNT(*) as materialized_count,
        COUNT(o.open_price) as ohlc_matched,
        MAX(o.open_price) as sample_open,
        MAX(o.close_price) as sample_close
    FROM ml_features_materialized m
    LEFT JOIN ohlc_data o
        ON BINARY m.symbol = BINARY o.symbol
        AND DATE(m.timestamp_iso) = DATE(o.timestamp_iso)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY m.symbol, DATE(m.timestamp_iso)
    HAVING ohlc_matched > 0
    ORDER BY materialized_count DESC
    LIMIT 5
"""
)
ohlc_test = cursor.fetchall()
print(f"   Samples where OHLC join works:")
for o in ohlc_test:
    pct = (
        (o["ohlc_matched"] / o["materialized_count"] * 100)
        if o["materialized_count"] > 0
        else 0
    )
    print(
        f"      {o['symbol']} on {o['date']}: {o['ohlc_matched']}/{o['materialized_count']} matched ({pct:.1f}%)"
    )
    print(f"         Sample: O={o['sample_open']}, C={o['sample_close']}")
if len(ohlc_test) == 0:
    print("      ⚠️  No OHLC matches found")
print()

# Test 4: Onchain Join
print("4️⃣  Testing Onchain Join (symbol, date)")
cursor.execute(
    """
    SELECT 
        m.symbol,
        DATE(m.timestamp_iso) as date,
        COUNT(*) as materialized_count,
        COUNT(o.active_addresses_24h) as onchain_matched,
        MAX(o.active_addresses_24h) as sample_addresses
    FROM ml_features_materialized m
    LEFT JOIN crypto_onchain_data o
        ON BINARY m.symbol = BINARY o.coin_symbol
        AND DATE(m.timestamp_iso) = DATE(o.timestamp)
    WHERE m.timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY m.symbol, DATE(m.timestamp_iso)
    HAVING onchain_matched > 0
    ORDER BY materialized_count DESC
    LIMIT 5
"""
)
onchain_test = cursor.fetchall()
print(f"   Samples where onchain join works:")
for o in onchain_test:
    pct = (
        (o["onchain_matched"] / o["materialized_count"] * 100)
        if o["materialized_count"] > 0
        else 0
    )
    print(
        f"      {o['symbol']} on {o['date']}: {o['onchain_matched']}/{o['materialized_count']} matched ({pct:.1f}%)"
    )
    print(f"         Sample addresses: {o['sample_addresses']:,}")
print()

print("=" * 80)
print("SUMMARY - What Should Be Populated:")
print("=" * 80)
print(f"Technical: {len(tech_test)} symbol-date combinations have matching data")
print(
    f"Macro: {sum(1 for m in macro_test if m['macro_indicators_found'] > 0)} dates have macro data"
)
print(f"OHLC: {len(ohlc_test)} symbol-date combinations have matching data")
print(f"Onchain: {len(onchain_test)} symbol-date combinations have matching data")
print()
print("If joins work but materialized table isn't updated, updater may not be")
print("processing existing records or may need to be restarted with fixes.")
print("=" * 80)

conn.close()


