#!/usr/bin/env python3
import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor()

# Get column info
cursor.execute("DESCRIBE onchain_metrics")
cols = cursor.fetchall()

print("=" * 100)
print("ONCHAIN_METRICS TABLE SCHEMA")
print("=" * 100)
print()

required = []
optional = []

for i, col in enumerate(cols, 1):
    name = col[0]
    dtype = col[1]
    nullable = col[2]  # YES or NO
    key = col[3] if len(col) > 3 else ""
    default = col[4] if len(col) > 4 else ""
    extra = col[5] if len(col) > 5 else ""

    status = "OPTIONAL" if nullable == "YES" else "REQUIRED"
    has_default = "YES" if default else "NO"

    print(f"{i:2}. {name:<30} | {dtype:<20} | {status:<10} | Default: {has_default}")

    if nullable == "NO" and not default and name != "id":
        required.append(name)
    else:
        optional.append(name)

conn.close()

print()
print("=" * 100)
print("ANALYSIS FOR ONCHAIN COLLECTOR")
print("=" * 100)
print()
print(f"Required columns (NO DEFAULT, NOT NULL): {len(required)}")
for col in required:
    print(f"  • {col}")

print()
print(f"Optional/default columns: {len(optional)}")
for col in optional[:10]:
    print(f"  • {col}")
if len(optional) > 10:
    print(f"  ... and {len(optional)-10} more")

print()
print("RECOMMENDATION:")
print("-" * 100)
print("For INSERT, use MINIMAL required columns + id (auto)")
print("Suggested INSERT columns: coin_symbol, timestamp, collection_date")
print("All other columns can be NULL or default values")
