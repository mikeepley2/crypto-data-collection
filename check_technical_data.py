import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("TECHNICAL INDICATORS COLLECTION STATUS")
print("=" * 80)

# Check price data
cursor.execute(
    "SELECT COUNT(*) as cnt, MAX(timestamp) as latest FROM price_data_real"
)
result = cursor.fetchone()
print(f"\nPrice Data (source for technical calculations):")
print(f"  Total records: {result['cnt']:,}")
print(f"  Latest: {result['latest']}")

# Check if technical indicators are being generated
cursor.execute(
    "SELECT COUNT(*) as cnt FROM technical_indicators WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)"
)
recent = cursor.fetchone()
print(f"\nTechnical Indicators (last 24 hours):")
print(f"  Records: {recent['cnt']:,}")

# Check total technical indicators
cursor.execute("SELECT COUNT(*) as cnt FROM technical_indicators")
total = cursor.fetchone()
print(f"\nTechnical Indicators (total):")
print(f"  Records: {total['cnt']:,}")

# Get sample of symbols with technical data
cursor.execute(
    "SELECT DISTINCT symbol FROM technical_indicators ORDER BY timestamp DESC LIMIT 10"
)
symbols = cursor.fetchall()
print(f"\nRecent symbols with technical data:")
for row in symbols:
    print(f"  • {row['symbol']}")

conn.close()

print("\n" + "=" * 80)
if result['cnt'] > 0 and total['cnt'] > 0:
    print("STATUS: Technical data collection is WORKING")
    print("Price data → Technical indicators pipeline ACTIVE")
else:
    print("STATUS: Technical data collection INACTIVE")
    print("Issue: No price data or no technical indicators generated")
