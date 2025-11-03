#!/usr/bin/env python3
"""Simple check to see if updater is working - quick queries only"""
import mysql.connector
from datetime import datetime, timedelta

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
    print("QUICK UPDATER STATUS CHECK")
    print("=" * 60)

    # Recent records created/updated
    cursor.execute(
        """
        SELECT 
            COUNT(*) as total,
            MAX(created_at) as latest_created,
            MAX(updated_at) as latest_updated
        FROM ml_features_materialized
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    """
    )
    stats = cursor.fetchone()
    print(f"\n📊 Last 24 hours:")
    print(f"   Total records: {stats['total']:,}")
    print(f"   Latest created: {stats['latest_created']}")
    print(f"   Latest updated: {stats['latest_updated']}")

    # Quick completeness check (just last day)
    print(f"\n🔍 Completeness (last 24h):")
    for col in ["rsi_14", "vix", "open_price", "active_addresses_24h"]:
        cursor.execute(
            f"""
            SELECT 
                COUNT({col}) as filled,
                COUNT(*) as total
            FROM ml_features_materialized
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """
        )
        r = cursor.fetchone()
        pct = (r["filled"] / r["total"] * 100) if r["total"] > 0 else 0
        status = "✅" if pct >= 50 else "⚠️" if pct > 0 else "❌"
        print(f"   {status} {col:25} {r['filled']:>6,}/{r['total']:>6,} ({pct:>5.1f}%)")

    conn.close()
    print("\n" + "=" * 60)
    print("✅ If you see recent updates, the updater is working")
    print("   Wait a few minutes after restart for new data to be processed")
    print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")

