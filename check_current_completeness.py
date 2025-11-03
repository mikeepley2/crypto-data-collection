#!/usr/bin/env python3
"""Check current completeness without any updates"""
import mysql.connector

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="news_collector",
        password="99Rules!",
        database="crypto_prices",
        connect_timeout=5,
    )

    cursor = conn.cursor(dictionary=True)

    print("=" * 60)
    print("CURRENT COMPLETENESS STATUS")
    print("=" * 60)

    # Total records
    cursor.execute(
        """
        SELECT COUNT(*) as total
        FROM ml_features_materialized
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """
    )
    total = cursor.fetchone()["total"]
    print(f"\nTotal records (last 7 days): {total:,}\n")

    # Key columns
    checks = [
        ("rsi_14", "Technical"),
        ("sma_20", "Technical"),
        ("vix", "Macro"),
        ("open_price", "OHLC"),
        ("active_addresses_24h", "Onchain"),
    ]

    for col, cat in checks:
        cursor.execute(
            f"""
            SELECT 
                COUNT({col}) as filled,
                COUNT(*) as total,
                ROUND(COUNT({col}) * 100.0 / COUNT(*), 1) as pct
            FROM ml_features_materialized
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """
        )
        r = cursor.fetchone()
        status = "✅" if r["pct"] >= 50 else "⚠️" if r["pct"] > 0 else "❌"
        print(
            f"{status} {cat:12} {col:25} {r['filled']:>8,}/{r['total']:>8,} ({r['pct']:>5.1f}%)"
        )

    conn.close()
    print("\n" + "=" * 60)

except Exception as e:
    print(f"Error: {e}")

