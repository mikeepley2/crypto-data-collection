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

print("=== COMPREHENSIVE FEATURE COMPLETENESS ANALYSIS ===")

# Basic feature analysis with correct column names
cursor.execute("""
SELECT 
    symbol,
    COUNT(*) as total_records,
    COUNT(CASE WHEN current_price IS NOT NULL THEN 1 END) as has_price,
    COUNT(CASE WHEN volume_24h IS NOT NULL THEN 1 END) as has_volume,
    COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_rsi,
    COUNT(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 END) as has_sentiment,
    COUNT(CASE WHEN macd_line IS NOT NULL THEN 1 END) as has_macd,
    COUNT(CASE WHEN vwap IS NOT NULL THEN 1 END) as has_vwap,
    MAX(timestamp_iso) as latest_data,
    TIMESTAMPDIFF(HOUR, MAX(timestamp_iso), NOW()) as hours_old
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY symbol
ORDER BY total_records DESC
LIMIT 20
""")

results = cursor.fetchall()
print(f"\n=== TOP 20 SYMBOLS - FEATURE COVERAGE (Last 7 days) ===")
print(f"{'Symbol':<12} {'Recs':<6} {'Price%':<7} {'Vol%':<7} {'RSI%':<7} {'Sent%':<7} {'MACD%':<7} {'VWAP%':<7} {'HrsOld':<7}")
print("-" * 85)

for row in results:
    symbol, total, price, volume, rsi, sentiment, macd, vwap, latest, hours_old = row
    if total > 0:
        price_pct = price/total*100
        vol_pct = volume/total*100
        rsi_pct = rsi/total*100
        sent_pct = sentiment/total*100
        macd_pct = macd/total*100
        vwap_pct = vwap/total*100
        
        print(f"{symbol:<12} {total:<6} {price_pct:<6.1f}% {vol_pct:<6.1f}% {rsi_pct:<6.1f}% {sent_pct:<6.1f}% {macd_pct:<6.1f}% {vwap_pct:<6.1f}% {hours_old or 0:<7}")

# Check for symbols needing backfill
cursor.execute("""
SELECT 
    symbol,
    COUNT(*) as records,
    MAX(timestamp_iso) as last_update,
    TIMESTAMPDIFF(HOUR, MAX(timestamp_iso), NOW()) as hours_since_last,
    COUNT(CASE WHEN current_price IS NULL THEN 1 END) as missing_price,
    COUNT(CASE WHEN rsi_14 IS NULL THEN 1 END) as missing_rsi
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY symbol
HAVING hours_since_last > 2 OR missing_price > 0
ORDER BY hours_since_last DESC
LIMIT 15
""")

gaps = cursor.fetchall()
print(f"\n=== SYMBOLS NEEDING BACKFILL (>2 hours old or missing data) ===")
print(f"{'Symbol':<12} {'Records':<8} {'HrsOld':<8} {'MissPx':<8} {'MissRSI':<8} {'Last Update'}")
print("-" * 75)

for row in gaps:
    symbol, records, last_update, hours_old, miss_price, miss_rsi = row
    print(f"{symbol:<12} {records:<8} {hours_old or 0:<8} {miss_price:<8} {miss_rsi:<8} {last_update}")

# Count symbols by completeness level
cursor.execute("""
SELECT 
    'Excellent (>95% complete)' as category,
    COUNT(*) as symbol_count
FROM (
    SELECT symbol,
        AVG(CASE WHEN current_price IS NOT NULL THEN 100.0 ELSE 0 END) as completeness
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY symbol
    HAVING completeness > 95
) t
UNION ALL
SELECT 
    'Good (80-95% complete)' as category,
    COUNT(*) as symbol_count
FROM (
    SELECT symbol,
        AVG(CASE WHEN current_price IS NOT NULL THEN 100.0 ELSE 0 END) as completeness
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY symbol
    HAVING completeness BETWEEN 80 AND 95
) t
UNION ALL
SELECT 
    'Needs Work (<80% complete)' as category,
    COUNT(*) as symbol_count
FROM (
    SELECT symbol,
        AVG(CASE WHEN current_price IS NOT NULL THEN 100.0 ELSE 0 END) as completeness
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY symbol
    HAVING completeness < 80
) t
""")

categories = cursor.fetchall()
print(f"\n=== SYMBOL COMPLETENESS DISTRIBUTION (Last 24 hours) ===")
for cat, count in categories:
    print(f"{cat}: {count} symbols")

# Overall stats
cursor.execute("""
SELECT 
    COUNT(DISTINCT symbol) as total_symbols,
    COUNT(*) as total_records,
    AVG(CASE WHEN current_price IS NOT NULL THEN 100.0 ELSE 0 END) as price_coverage,
    AVG(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 100.0 ELSE 0 END) as sentiment_coverage,
    AVG(CASE WHEN rsi_14 IS NOT NULL THEN 100.0 ELSE 0 END) as technical_coverage,
    MIN(timestamp_iso) as earliest,
    MAX(timestamp_iso) as latest
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
""")

stats = cursor.fetchone()
print(f"\n=== OVERALL STATISTICS (Last 7 days) ===")
print(f"Total Symbols: {stats[0]}")
print(f"Total Records: {stats[1]:,}")
print(f"Price Coverage: {stats[2]:.1f}%")
print(f"Sentiment Coverage: {stats[3]:.1f}%")
print(f"Technical Coverage: {stats[4]:.1f}%")
print(f"Data Range: {stats[5]} to {stats[6]}")

conn.close()
print("\n=== ANALYSIS COMPLETE - Ready for Backfill ===")