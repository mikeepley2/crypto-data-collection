import mysql.connector
from datetime import datetime

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor(dictionary=True)

# Calculate cutoff same way as the backfill code
backfill_days = 365
cutoff_ms = int((datetime.utcnow().timestamp() - backfill_days * 86400) * 1000)

print(f"Cutoff for {backfill_days} days ago: {cutoff_ms}")
print(f"That equals: {datetime.utcfromtimestamp(cutoff_ms / 1000)}")

# Check how many symbols match
cursor.execute(f"SELECT COUNT(DISTINCT symbol) as cnt FROM price_data_real WHERE timestamp > {cutoff_ms}")
r = cursor.fetchone()
print(f"Symbols with data in last {backfill_days} days: {r['cnt']:,}")

# Check overall data range
cursor.execute("SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM price_data_real")
r = cursor.fetchone()
oldest_date = datetime.utcfromtimestamp(r["oldest"] / 1000) if r["oldest"] else None
newest_date = datetime.utcfromtimestamp(r["newest"] / 1000) if r["newest"] else None
print(f"Overall data range: {oldest_date} to {newest_date}")

# Check if we need to backfill all data
print(f"\n[NOTICE] Price data doesn't cover last {backfill_days} days!")
print(f"Consider backfilling ALL available data instead")

conn.close()
