#!/usr/bin/env python3
"""
Comprehensive backfill verification script
Checks technical, macro, and onchain data coverage after backfill
"""

import os
import sys

# Database config from environment
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'news_collector')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'news_collector')
DB_NAME = 'crypto_prices'

try:
    import mysql.connector
    
    config = {
        'host': DB_HOST,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'database': DB_NAME
    }
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("BACKFILL COMPLETION VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    # 1. Technical Indicators
    print("1️⃣  TECHNICAL INDICATORS STATUS")
    print("-" * 80)
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as with_sma_20,
        SUM(CASE WHEN sma_50 IS NOT NULL THEN 1 ELSE 0 END) as with_sma_50,
        SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as with_rsi,
        SUM(CASE WHEN macd IS NOT NULL THEN 1 ELSE 0 END) as with_macd,
        SUM(CASE WHEN bollinger_upper IS NOT NULL THEN 1 ELSE 0 END) as with_bollinger,
        MAX(timestamp_iso) as latest_update
    FROM technical_indicators
    """)
    
    tech = cursor.fetchone()
    total_tech = tech[0]
    sma20_pct = (tech[1] / total_tech * 100) if total_tech > 0 else 0
    sma50_pct = (tech[2] / total_tech * 100) if total_tech > 0 else 0
    rsi_pct = (tech[3] / total_tech * 100) if total_tech > 0 else 0
    macd_pct = (tech[4] / total_tech * 100) if total_tech > 0 else 0
    bb_pct = (tech[5] / total_tech * 100) if total_tech > 0 else 0
    
    print(f"Total Records: {total_tech:,}")
    print(f"SMA 20:        {tech[1]:,} ({sma20_pct:.1f}%)")
    print(f"SMA 50:        {tech[2]:,} ({sma50_pct:.1f}%)")
    print(f"RSI 14:        {tech[3]:,} ({rsi_pct:.1f}%)")
    print(f"MACD:          {tech[4]:,} ({macd_pct:.1f}%)")
    print(f"Bollinger:     {tech[5]:,} ({bb_pct:.1f}%)")
    print(f"Latest Update: {tech[6]}")
    print()
    
    # 2. Macro Indicators
    print("2️⃣  MACRO INDICATORS STATUS")
    print("-" * 80)
    cursor.execute("""
    SELECT 
        indicator_name,
        COUNT(*) as total,
        SUM(CASE WHEN value IS NOT NULL THEN 1 ELSE 0 END) as with_data,
        ROUND(100.0 * SUM(CASE WHEN value IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as pct,
        ROUND(AVG(value), 4) as avg_value,
        MAX(indicator_date) as latest_date
    FROM macro_indicators
    GROUP BY indicator_name
    ORDER BY with_data DESC
    """)
    
    macro_results = cursor.fetchall()
    total_macro_records = sum(r[1] for r in macro_results)
    total_macro_with_data = sum(r[2] for r in macro_results)
    
    for row in macro_results:
        print(f"{row[0]:25} {row[2]:8,} / {row[1]:8,}  ({row[3]:5.1f}%)  Avg: {row[4]:10.4f}  Latest: {row[5]}")
    
    macro_pct = (total_macro_with_data / total_macro_records * 100) if total_macro_records > 0 else 0
    print(f"\nTotal Macro Coverage: {total_macro_with_data:,} / {total_macro_records:,} ({macro_pct:.1f}%)")
    print()
    
    # 3. Onchain Metrics
    print("3️⃣  ONCHAIN METRICS STATUS")
    print("-" * 80)
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as with_addresses,
        SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as with_txn,
        SUM(CASE WHEN exchange_net_flow_24h IS NOT NULL THEN 1 ELSE 0 END) as with_flow,
        SUM(CASE WHEN price_volatility_7d IS NOT NULL THEN 1 ELSE 0 END) as with_volatility,
        MAX(collection_date) as latest_date
    FROM crypto_onchain_data
    """)
    
    onchain = cursor.fetchone()
    total_onchain = onchain[0]
    addr_pct = (onchain[1] / total_onchain * 100) if total_onchain > 0 else 0
    txn_pct = (onchain[2] / total_onchain * 100) if total_onchain > 0 else 0
    flow_pct = (onchain[3] / total_onchain * 100) if total_onchain > 0 else 0
    vol_pct = (onchain[4] / total_onchain * 100) if total_onchain > 0 else 0
    
    print(f"Total Records:         {total_onchain:,}")
    print(f"Active Addresses 24h:  {onchain[1]:,} ({addr_pct:.1f}%)")
    print(f"Transaction Count 24h: {onchain[2]:,} ({txn_pct:.1f}%)")
    print(f"Exchange Net Flow 24h: {onchain[3]:,} ({flow_pct:.1f}%)")
    print(f"Price Volatility 7d:   {onchain[4]:,} ({vol_pct:.1f}%)")
    print(f"Latest Date: {onchain[5]}")
    print()
    
    # 4. ML Features Materialized Impact
    print("4️⃣  ML FEATURES MATERIALIZED TABLE IMPACT")
    print("-" * 80)
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as with_technical,
        SUM(CASE WHEN unemployment_rate IS NOT NULL THEN 1 ELSE 0 END) as with_macro,
        SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as with_onchain,
        SUM(CASE WHEN ml_sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as with_sentiment
    FROM ml_features_materialized
    """)
    
    ml = cursor.fetchone()
    total_ml = ml[0]
    tech_pct = (ml[1] / total_ml * 100) if total_ml > 0 else 0
    macro_pct = (ml[2] / total_ml * 100) if total_ml > 0 else 0
    onchain_pct = (ml[3] / total_ml * 100) if total_ml > 0 else 0
    sentiment_pct = (ml[4] / total_ml * 100) if total_ml > 0 else 0
    
    print(f"Total Records:     {total_ml:,}")
    print(f"With Technical:    {ml[1]:,} ({tech_pct:.1f}%)")
    print(f"With Macro:        {ml[2]:,} ({macro_pct:.1f}%)")
    print(f"With Onchain:      {ml[3]:,} ({onchain_pct:.1f}%)")
    print(f"With Sentiment:    {ml[4]:,} ({sentiment_pct:.1f}%)")
    print()
    
    # 5. Summary
    print("5️⃣  OVERALL SUMMARY")
    print("=" * 80)
    print(f"✅ Technical Indicators:   {sma20_pct:.1f}% coverage ({tech[1]:,} / {total_tech:,})")
    print(f"✅ Macro Indicators:       {macro_pct:.1f}% coverage ({total_macro_with_data:,} / {total_macro_records:,})")
    print(f"✅ Onchain Metrics:        {addr_pct:.1f}% coverage ({onchain[1]:,} / {total_onchain:,})")
    print(f"✅ ML Features Sentiment:  {sentiment_pct:.1f}% coverage ({ml[4]:,} / {total_ml:,})")
    print()
    
    # Success criteria
    print("SUCCESS CRITERIA:")
    print("-" * 80)
    print(f"{'Technical 95%+': <40} {'✅ PASS' if sma20_pct >= 95 else '❌ FAIL'}")
    print(f"{'Macro 95%+': <40} {'✅ PASS' if macro_pct >= 95 else '❌ FAIL'}")
    print(f"{'Onchain 40%+': <40} {'✅ PASS' if addr_pct >= 40 else '⚠️  PARTIAL'}")
    print(f"{'Materialized 80%+ complete': <40} {'✅ PASS' if tech_pct >= 80 else '❌ FAIL'}")
    print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
