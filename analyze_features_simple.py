#!/usr/bin/env python3
import mysql.connector

config = {
    'host': 'host.docker.internal',
    'user': 'news_collector', 
    'password': '99Rules!',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print("=== FEATURE COMPLETENESS ANALYSIS ===")

# Get column names first
cursor.execute("SHOW COLUMNS FROM ml_features_materialized")
columns = cursor.fetchall()
print("\nAvailable columns:")
for col in columns:
    print(f"- {col[0]}")

# Basic feature analysis
cursor.execute("""
SELECT 
    symbol,
    COUNT(*) as total_records,
    COUNT(CASE WHEN current_price IS NOT NULL THEN 1 END) as has_price,
    COUNT(CASE WHEN volume_24h IS NOT NULL THEN 1 END) as has_volume,
    COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_rsi,
    COUNT(CASE WHEN sentiment_score IS NOT NULL THEN 1 END) as has_sentiment,
    MAX(timestamp_iso) as latest_data
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY symbol
ORDER BY total_records DESC
LIMIT 15
""")

results = cursor.fetchall()
print(f"\n=== TOP 15 SYMBOLS (Last 7 days) ===")
print(f"{'Symbol':<12} {'Records':<8} {'Price%':<8} {'Vol%':<8} {'RSI%':<8} {'Sent%':<8} {'Latest Data'}")
print("-" * 80)

for row in results:
    symbol, total, price, volume, rsi, sentiment, latest = row
    price_pct = (price/total*100) if total > 0 else 0
    vol_pct = (volume/total*100) if total > 0 else 0
    rsi_pct = (rsi/total*100) if total > 0 else 0
    sent_pct = (sentiment/total*100) if total > 0 else 0
    
    print(f"{symbol:<12} {total:<8} {price_pct:<7.1f}% {vol_pct:<7.1f}% {rsi_pct:<7.1f}% {sent_pct:<7.1f}% {latest}")

# Check for symbols with significant gaps
cursor.execute("""
SELECT 
    symbol,
    COUNT(*) as records,
    COUNT(CASE WHEN current_price IS NULL THEN 1 END) as missing_price,
    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) as missing_sentiment,
    MAX(timestamp_iso) as last_update,
    TIMESTAMPDIFF(HOUR, MAX(timestamp_iso), NOW()) as hours_since_last
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 3 DAY)
GROUP BY symbol
HAVING missing_price > 0 OR missing_sentiment > 5 OR hours_since_last > 3
ORDER BY hours_since_last DESC, missing_price DESC
LIMIT 20
""")

gaps = cursor.fetchall()
print(f"\n=== SYMBOLS WITH GAPS OR STALE DATA ===")
print(f"{'Symbol':<12} {'Records':<8} {'MissPx':<8} {'MissSent':<8} {'HrsOld':<8} {'Last Update'}")
print("-" * 80)

for row in gaps:
    symbol, records, miss_price, miss_sent, last_update, hours_old = row
    print(f"{symbol:<12} {records:<8} {miss_price:<8} {miss_sent:<8} {hours_old:<8} {last_update}")

# Overall stats
cursor.execute("""
SELECT 
    COUNT(DISTINCT symbol) as total_symbols,
    COUNT(*) as total_records,
    AVG(CASE WHEN current_price IS NOT NULL THEN 100.0 ELSE 0 END) as avg_price_coverage,
    AVG(CASE WHEN sentiment_score IS NOT NULL THEN 100.0 ELSE 0 END) as avg_sentiment_coverage,
    MIN(timestamp_iso) as earliest,
    MAX(timestamp_iso) as latest
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
""")

stats = cursor.fetchone()
print(f"\n=== OVERALL STATISTICS (Last 7 days) ===")
print(f"Total Symbols: {stats[0]}")
print(f"Total Records: {stats[1]:,}")
print(f"Avg Price Coverage: {stats[2]:.1f}%")
print(f"Avg Sentiment Coverage: {stats[3]:.1f}%")
print(f"Data Range: {stats[4]} to {stats[5]}")

conn.close()
print("\n=== ANALYSIS COMPLETE ===")