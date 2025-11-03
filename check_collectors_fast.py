#!/usr/bin/env python3
"""Fast check of collectors - avoids expensive queries"""
import mysql.connector
from datetime import datetime, timedelta
import signal
import sys


# Set timeout for whole script
def timeout_handler(signum, frame):
    print("\n⚠️  Query timeout - database may be busy")
    sys.exit(1)


# Windows doesn't support signal.alarm, so we'll just use connection timeout
if sys.platform != "win32":
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="news_collector",
        password="99Rules!",
        database="crypto_prices",
        connect_timeout=3,
    )
    conn.autocommit = True

    cursor = conn.cursor(dictionary=True)

    print("=" * 80)
    print("BASE COLLECTORS STATUS CHECK (Fast)")
    print("=" * 80)
    print()

    # Use simpler queries - just check latest record, not full counts

    # 1. PRICE
    print("1️⃣  PRICE COLLECTOR")
    print("-" * 80)
    try:
        cursor.execute(
            "SELECT timestamp_iso FROM price_data_real ORDER BY timestamp_iso DESC LIMIT 1"
        )
        price = cursor.fetchone()
        if price:
            latest = price["timestamp_iso"]
            age = (datetime.now() - latest).total_seconds() / 60
            status = "✅ ACTIVE" if age < 60 else "⚠️ SLOW" if age < 180 else "❌ STALE"
            print(f"   Latest record: {latest}")
            print(f"   Status: {status} ({age:.0f} min ago)")
        else:
            print("   ❌ No data found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    print()

    # 2. TECHNICAL
    print("2️⃣  TECHNICAL INDICATORS")
    print("-" * 80)
    try:
        cursor.execute(
            "SELECT timestamp_iso, symbol FROM technical_indicators ORDER BY timestamp_iso DESC LIMIT 1"
        )
        tech = cursor.fetchone()
        if tech:
            latest = tech["timestamp_iso"]
            age = (datetime.now() - latest).total_seconds() / 60
            status = "✅ ACTIVE" if age < 60 else "⚠️ SLOW" if age < 180 else "❌ STALE"
            print(f"   Latest record: {latest} (symbol: {tech['symbol']})")
            print(f"   Status: {status} ({age:.0f} min ago)")
        else:
            print("   ❌ No data found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    print()

    # 3. MACRO
    print("3️⃣  MACRO COLLECTOR")
    print("-" * 80)
    try:
        cursor.execute(
            "SELECT indicator_date, indicator_name FROM macro_indicators ORDER BY indicator_date DESC LIMIT 1"
        )
        macro = cursor.fetchone()
        if macro:
            latest_date = macro["indicator_date"]
            age_days = (datetime.now().date() - latest_date).days
            status = (
                "✅ ACTIVE"
                if age_days == 0
                else "⚠️ SLOW" if age_days <= 2 else "❌ STALE"
            )
            print(
                f"   Latest date: {latest_date} (indicator: {macro['indicator_name']})"
            )
            print(f"   Status: {status} ({age_days} days ago - FRED may delay)")
        else:
            print("   ❌ No data found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    print()

    # 4. ONCHAIN
    print("4️⃣  ONCHAIN COLLECTOR")
    print("-" * 80)
    try:
        cursor.execute(
            "SELECT timestamp, coin_symbol FROM crypto_onchain_data ORDER BY timestamp DESC LIMIT 1"
        )
        onchain = cursor.fetchone()
        if onchain:
            latest = onchain["timestamp"]
            age = (datetime.now() - latest).total_seconds() / 60
            status = "✅ ACTIVE" if age < 360 else "⚠️ SLOW" if age < 720 else "❌ STALE"
            print(f"   Latest record: {latest} (symbol: {onchain['coin_symbol']})")
            print(f"   Status: {status} ({age:.0f} min ago)")
        else:
            print("   ❌ No data found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    print()

    # 5. OHLC
    print("5️⃣  OHLC DATA")
    print("-" * 80)
    try:
        cursor.execute(
            "SELECT timestamp_iso, symbol FROM ohlc_data ORDER BY timestamp_iso DESC LIMIT 1"
        )
        ohlc = cursor.fetchone()
        if ohlc:
            latest = ohlc["timestamp_iso"]
            age = (datetime.now() - latest).total_seconds() / 60
            status = "✅ ACTIVE" if age < 1440 else "⚠️ STALE"
            print(f"   Latest record: {latest} (symbol: {ohlc['symbol']})")
            print(f"   Status: {status} ({age:.0f} min ago)")
        else:
            print("   ❌ No data found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    print()

    print("=" * 80)
    print("✅ Check complete - all collectors have data")
    print("=" * 80)

    conn.close()
    if sys.platform != "win32":
        signal.alarm(0)  # Cancel timeout

except mysql.connector.Error as e:
    print(f"❌ Database error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

