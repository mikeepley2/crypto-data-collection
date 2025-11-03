#!/usr/bin/env python3
"""Quick status check without hanging queries"""
import mysql.connector

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="news_collector",
        password="99Rules!",
        database="crypto_prices",
        connect_timeout=3,
    )

    cursor = conn.cursor(dictionary=True)

    print("=" * 60)
    print("QUICK STATUS CHECK")
    print("=" * 60)

    # Check if updater is updating records
    cursor.execute(
        """
        SELECT 
            MAX(updated_at) as last_update,
            COUNT(*) as total_today
        FROM ml_features_materialized
        WHERE DATE(timestamp_iso) = CURDATE()
        LIMIT 1
    """
    )
    status = cursor.fetchone()
    print(f"\n✅ Materialized table status:")
    print(f"   Records today: {status['total_today']:,}")
    print(f"   Last update: {status['last_update']}")

    # Quick completeness check (sample of recent records)
    cursor.execute(
        """
        SELECT 
            COUNT(*) as total,
            COUNT(rsi_14) as has_rsi,
            COUNT(sma_20) as has_sma,
            COUNT(vix) as has_vix,
            COUNT(open_price) as has_ohlc
        FROM ml_features_materialized
        WHERE DATE(timestamp_iso) = CURDATE()
        AND updated_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        LIMIT 10000
    """
    )
    comp = cursor.fetchone()

    if comp["total"] > 0:
        print(f"\n📊 Completeness (recent updates, last 2h):")
        print(f"   Total records: {comp['total']:,}")
        print(
            f"   RSI_14: {comp['has_rsi']:,} ({comp['has_rsi']/comp['total']*100:.1f}%)"
        )
        print(
            f"   SMA_20: {comp['has_sma']:,} ({comp['has_sma']/comp['total']*100:.1f}%)"
        )
        print(f"   VIX: {comp['has_vix']:,} ({comp['has_vix']/comp['total']*100:.1f}%)")
        print(
            f"   OHLC: {comp['has_ohlc']:,} ({comp['has_ohlc']/comp['total']*100:.1f}%)"
        )

    # Check source data availability
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM technical_indicators WHERE DATE(timestamp_iso) = CURDATE() LIMIT 1"
    )
    tech_avail = cursor.fetchone()["cnt"]
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM macro_indicators WHERE indicator_date = CURDATE() LIMIT 1"
    )
    macro_avail = cursor.fetchone()["cnt"]
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM ohlc_data WHERE DATE(timestamp_iso) = CURDATE() LIMIT 1"
    )
    ohlc_avail = cursor.fetchone()["cnt"]

    print(f"\n📦 Source Data Available (today):")
    print(f"   Technical indicators: {tech_avail:,}")
    print(f"   Macro indicators: {macro_avail:,}")
    print(f"   OHLC data: {ohlc_avail:,}")

    conn.close()

    print("\n" + "=" * 60)
    if status["last_update"]:
        from datetime import datetime

        last = datetime.fromisoformat(str(status["last_update"]).replace(" ", "T"))
        age = (datetime.now() - last).total_seconds() / 60
        if age < 10:
            print("✅ Updater is actively working!")
        elif age < 30:
            print("⚠️  Last update was {:.0f} minutes ago".format(age))
        else:
            print("❌ Last update was {:.0f} minutes ago - may be stuck".format(age))
    print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")

