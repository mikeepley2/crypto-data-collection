import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor(dictionary=True)

print("=" * 70)
print("PRICE DATA AVAILABILITY CHECK")
print("=" * 70)

# Check price_data_real
cursor.execute("SELECT COUNT(*) as cnt, MAX(timestamp) as latest FROM price_data_real")
r = cursor.fetchone()
print(f"\nprice_data_real table:")
print(f"  Records: {r['cnt']:,}")
print(f"  Latest: {r['latest']}")

# Check symbols available
cursor.execute("SELECT COUNT(DISTINCT symbol) as symbols FROM price_data_real")
r = cursor.fetchone()
print(f"  Symbols: {r['symbols']}")

# Get sample symbols
cursor.execute("SELECT DISTINCT symbol FROM price_data_real LIMIT 5")
symbols = cursor.fetchall()
print(f"  Sample symbols: {[s['symbol'] for s in symbols]}")

# Check date range
cursor.execute(
    "SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM price_data_real"
)
r = cursor.fetchone()
print(f"  Date range: {r['oldest']} to {r['newest']}")

conn.close()

if r["cnt"] == 0:
    print("\n[ERROR] No price data found in price_data_real!")
    print("Backfill cannot proceed without price data.")
else:
    print(f"\n[OK] Price data available: {r['cnt']:,} records")
    print("Backfill should process successfully")

