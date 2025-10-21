import mysql.connector

config = {
    'host': 'mysql',
    'user': 'news_collector',
    'password': 'news_collector',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print("=" * 80)
print("BACKFILL COMPLETION VERIFICATION REPORT")
print("=" * 80)
print()

# 1. Technical Indicators
print("1 TECHNICAL INDICATORS STATUS")
print("-" * 80)
cursor.execute("""
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as with_sma_20,
    SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as with_rsi,
    SUM(CASE WHEN macd IS NOT NULL THEN 1 ELSE 0 END) as with_macd,
    MAX(timestamp_iso) as latest_update
FROM technical_indicators
""")

tech = cursor.fetchone()
total_tech = tech[0] or 0
sma20_pct = (tech[1] / total_tech * 100) if total_tech > 0 else 0
rsi_pct = (tech[2] / total_tech * 100) if total_tech > 0 else 0
macd_pct = (tech[3] / total_tech * 100) if total_tech > 0 else 0

print(f"Total Records: {total_tech:,}")
print(f"SMA 20:        {tech[1]:,} ({sma20_pct:.1f}%)")
print(f"RSI 14:        {tech[2]:,} ({rsi_pct:.1f}%)")
print(f"MACD:          {tech[3]:,} ({macd_pct:.1f}%)")
print(f"Latest Update: {tech[4]}")
print()

# 2. Macro Indicators
print("2 MACRO INDICATORS STATUS")
print("-" * 80)
cursor.execute("""
SELECT 
    indicator_name,
    COUNT(*) as total,
    SUM(CASE WHEN value IS NOT NULL THEN 1 ELSE 0 END) as with_data
FROM macro_indicators
GROUP BY indicator_name
ORDER BY with_data DESC
""")

macro_results = cursor.fetchall()
total_macro_records = sum(r[1] for r in macro_results) if macro_results else 0
total_macro_with_data = sum(r[2] for r in macro_results) if macro_results else 0

for row in macro_results:
    pct = (row[2] / row[1] * 100) if row[1] > 0 else 0
    print(f"{row[0]:25} {row[2]:8,} / {row[1]:8,}  ({pct:5.1f}%)")

macro_pct = (total_macro_with_data / total_macro_records * 100) if total_macro_records > 0 else 0
print(f"\nTotal Macro Coverage: {total_macro_with_data:,} / {total_macro_records:,} ({macro_pct:.1f}%)")
print()

# 3. Onchain Metrics
print("3 ONCHAIN METRICS STATUS")
print("-" * 80)
cursor.execute("""
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as with_addresses,
    SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as with_txn,
    MAX(collection_date) as latest_date
FROM crypto_onchain_data
""")

onchain = cursor.fetchone()
total_onchain = onchain[0] or 0
addr_pct = (onchain[1] / total_onchain * 100) if total_onchain > 0 else 0
txn_pct = (onchain[2] / total_onchain * 100) if total_onchain > 0 else 0

print(f"Total Records:         {total_onchain:,}")
print(f"Active Addresses 24h:  {onchain[1]:,} ({addr_pct:.1f}%)")
print(f"Transaction Count 24h: {onchain[2]:,} ({txn_pct:.1f}%)")
print(f"Latest Date: {onchain[3]}")
print()

# Summary
print("SUCCESS CRITERIA CHECK")
print("=" * 80)
print(f"{'Technical 95%+': <40} {'PASS' if sma20_pct >= 95 else 'FAIL'}")
print(f"{'Macro 95%+': <40} {'PASS' if macro_pct >= 95 else 'FAIL'}")
print(f"{'Onchain 40%+': <40} {'PASS' if addr_pct >= 40 else 'PARTIAL'}")
print()

cursor.close()
conn.close()
