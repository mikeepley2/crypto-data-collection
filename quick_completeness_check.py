#!/usr/bin/env python3
"""Quick completeness check for key columns"""
import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("QUICK MATERIALIZED TABLE COMPLETENESS CHECK")
print("=" * 80)

# Get total records
cursor.execute(
    """
    SELECT COUNT(*) as total
    FROM ml_features_materialized
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
total = cursor.fetchone()["total"]
print(f"\nTotal records (last 7 days): {total:,}")

# Check key columns
columns = [
    ("rsi_14", "Technical Indicators"),
    ("sma_20", "Technical Indicators"),
    ("vix", "Macro Indicators"),
    ("spx", "Macro Indicators"),
    ("open_price", "OHLC Data"),
    ("high_price", "OHLC Data"),
    ("active_addresses_24h", "Onchain Data"),
    ("transaction_count_24h", "Onchain Data"),
]

print("\nKey Column Completeness:")
print("-" * 80)
for col, category in columns:
    cursor.execute(
        f"""
        SELECT 
            COUNT({col}) as non_null,
            COUNT(*) as total,
            ROUND(COUNT({col}) * 100.0 / COUNT(*), 2) as pct
        FROM ml_features_materialized
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """
    )
    result = cursor.fetchone()
    status = "✅" if result["pct"] >= 50 else "⚠️" if result["pct"] > 0 else "❌"
    print(
        f"{status} {category:<25} {col:<25} {result['non_null']:>10,}/{result['total']:>10,} ({result['pct']:>6.2f}%)"
    )

print("\n" + "=" * 80)
conn.close()
