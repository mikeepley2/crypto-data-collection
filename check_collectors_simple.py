#!/usr/bin/env python3
"""Simple check of all collectors - with timeouts"""
import mysql.connector
from datetime import datetime, timedelta

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="news_collector",
        password="99Rules!",
        database="crypto_prices",
        connect_timeout=5,
    )

    cursor = conn.cursor(dictionary=True)

    print("=" * 80)
    print("BASE COLLECTORS STATUS CHECK")
    print("=" * 80)
    print()

    recent_cutoff = datetime.now() - timedelta(hours=6)

    # 1. PRICE
    print("1️⃣  PRICE COLLECTOR")
    print("-" * 80)
    cursor.execute(
        "SELECT MAX(timestamp_iso) as latest, COUNT(*) as total FROM price_data_real LIMIT 1"
    )
    price = cursor.fetchone()
    print(f"   Total records: {price['total']:,}")
    print(f"   Latest: {price['latest']}")
    if price["latest"]:
        age = (datetime.now() - price["latest"]).total_seconds() / 60
        status = "✅ ACTIVE" if age < 60 else "⚠️ SLOW" if age < 180 else "❌ STALE"
        print(f"   Status: {status} ({age:.0f} min ago)")
    print()

    # 2. TECHNICAL
    print("2️⃣  TECHNICAL INDICATORS")
    print("-" * 80)
    cursor.execute(
        "SELECT MAX(timestamp_iso) as latest, COUNT(*) as total FROM technical_indicators LIMIT 1"
    )
    tech = cursor.fetchone()
    print(f"   Total records: {tech['total']:,}")
    print(f"   Latest: {tech['latest']}")
    if tech["latest"]:
        age = (datetime.now() - tech["latest"]).total_seconds() / 60
        status = "✅ ACTIVE" if age < 60 else "⚠️ SLOW" if age < 180 else "❌ STALE"
        print(f"   Status: {status} ({age:.0f} min ago)")
    print()

    # 3. MACRO
    print("3️⃣  MACRO COLLECTOR")
    print("-" * 80)
    cursor.execute(
        "SELECT MAX(indicator_date) as latest, COUNT(*) as total, COUNT(DISTINCT indicator_name) as indicators FROM macro_indicators LIMIT 1"
    )
    macro = cursor.fetchone()
    print(f"   Total records: {macro['total']:,}")
    print(f"   Unique indicators: {macro['indicators']}")
    print(f"   Latest date: {macro['latest']}")
    if macro["latest"]:
        age_days = (datetime.now().date() - macro["latest"]).days
        status = (
            "✅ ACTIVE" if age_days == 0 else "⚠️ SLOW" if age_days <= 2 else "❌ STALE"
        )
        print(f"   Status: {status} ({age_days} days ago - FRED may delay)")
    print()

    # 4. ONCHAIN
    print("4️⃣  ONCHAIN COLLECTOR")
    print("-" * 80)
    cursor.execute(
        "SELECT MAX(timestamp) as latest, COUNT(*) as total FROM crypto_onchain_data LIMIT 1"
    )
    onchain = cursor.fetchone()
    print(f"   Total records: {onchain['total']:,}")
    print(f"   Latest: {onchain['latest']}")
    if onchain["latest"]:
        age = (datetime.now() - onchain["latest"]).total_seconds() / 60
        status = "✅ ACTIVE" if age < 360 else "⚠️ SLOW" if age < 720 else "❌ STALE"
        print(f"   Status: {status} ({age:.0f} min ago)")
    print()

    # 5. OHLC
    print("5️⃣  OHLC DATA")
    print("-" * 80)
    cursor.execute(
        "SELECT MAX(timestamp_iso) as latest, COUNT(*) as total FROM ohlc_data LIMIT 1"
    )
    ohlc = cursor.fetchone()
    print(f"   Total records: {ohlc['total']:,}")
    if ohlc["latest"]:
        print(f"   Latest: {ohlc['latest']}")
        age = (datetime.now() - ohlc["latest"]).total_seconds() / 60
        status = "✅ ACTIVE" if age < 1440 else "⚠️ STALE"
        print(f"   Status: {status} ({age:.0f} min ago)")
    else:
        print("   Status: ❌ NO DATA")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    active_count = 0
    total_count = 4  # Price, Technical, Macro, Onchain

    if price["total"] > 0:
        print("✅ Price: Working")
        active_count += 1
    else:
        print("❌ Price: No data")

    if tech["total"] > 0:
        print("✅ Technical: Working")
        active_count += 1
    else:
        print("❌ Technical: No data")

    if macro["total"] > 0:
        print("✅ Macro: Working")
        active_count += 1
    else:
        print("❌ Macro: No data")

    if onchain["total"] > 0:
        print("✅ Onchain: Working")
        active_count += 1
    else:
        print("❌ Onchain: No data")

    print()
    print(f"✅ {active_count}/{total_count} collectors have data")
    print("=" * 80)

    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

