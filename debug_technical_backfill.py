import mysql.connector
from datetime import datetime, timedelta

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor(dictionary=True)

print("=" * 70)
print("DEBUG: TECHNICAL INDICATORS BACKFILL")
print("=" * 70)

# Check price_data_real
print("\n1. PRICE_DATA_REAL table:")
cursor.execute(
    "SELECT COUNT(*) as cnt, MIN(timestamp) as oldest, MAX(timestamp) as newest FROM price_data_real WHERE timestamp IS NOT NULL"
)
r = cursor.fetchone()
print(f"   Records: {r['cnt']:,}")
print(f"   Date range: {r['oldest']} to {r['newest']}")

# Check if timestamps are Unix milliseconds
if r["newest"] and r["newest"] > 9999999999:
    print("   Timestamp format: UNIX MILLISECONDS (needs division by 1000)")
elif r["newest"]:
    print("   Timestamp format: UNIX SECONDS or datetime")

# Check symbols in price data
cursor.execute("SELECT COUNT(DISTINCT symbol) as symbols FROM price_data_real")
print(f"   Symbols: {cursor.fetchone()['symbols']}")

# Check what's in technical_indicators
print("\n2. TECHNICAL_INDICATORS table:")
cursor.execute(
    "SELECT COUNT(*) as cnt, COUNT(DISTINCT symbol) as symbols FROM technical_indicators"
)
r = cursor.fetchone()
print(f"   Records: {r['cnt']:,}")
print(f"   Symbols: {r['symbols']:,}")

# Check last update time
cursor.execute(
    "SELECT MAX(updated_at) as latest FROM technical_indicators WHERE updated_at IS NOT NULL"
)
print(f"   Latest update: {cursor.fetchone()['latest']}")

# Sample technical data
print("\n3. SAMPLE TECHNICAL DATA:")
cursor.execute(
    "SELECT symbol, timestamp, sma_20, rsi_14 FROM technical_indicators WHERE sma_20 IS NOT NULL LIMIT 5"
)
for row in cursor.fetchall():
    print(
        f"   {row['symbol']}: ts={row['timestamp']}, sma={row['sma_20']:.2f}, rsi={row['rsi_14']:.2f}"
    )

# Check backfill query result
print("\n4. BACKFILL QUERY TEST (last 365 days):")
cursor.execute(
    """
    SELECT DISTINCT symbol FROM price_data_real
    WHERE timestamp > DATE_SUB(NOW(), INTERVAL 365 DAY)
    LIMIT 10
"""
)
symbols = cursor.fetchall()
print(f"   Query returned {len(symbols)} symbols")
for s in symbols[:5]:
    print(f"   - {s['symbol']}")

if len(symbols) == 0:
    print("\n   [PROBLEM] The DATE_SUB query is returning 0 symbols!")
    print("   This suggests timestamps in price_data_real are not in datetime format")
    print("   They appear to be Unix milliseconds (large integers)")

conn.close()

print("\n" + "=" * 70)
print("ISSUE FOUND: Timestamps in price_data_real are Unix milliseconds")
print("The backfill code needs to convert them or use a different filter")
print("=" * 70)

