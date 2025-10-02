#!/usr/bin/env python3
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

config = {
    'host': 'host.docker.internal',
    'user': 'news_collector', 
    'password': '99Rules!',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**config)

print("=== FEATURE COMPLETENESS ANALYSIS ===")

# Check feature completeness by symbol
query = '''
SELECT 
    symbol,
    COUNT(*) as total_records,
    COUNT(CASE WHEN current_price IS NOT NULL THEN 1 END) as has_price,
    COUNT(CASE WHEN volume_24h IS NOT NULL THEN 1 END) as has_volume,
    COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as has_rsi,
    COUNT(CASE WHEN macd_12_26_9 IS NOT NULL THEN 1 END) as has_macd,
    COUNT(CASE WHEN sentiment_score IS NOT NULL THEN 1 END) as has_sentiment,
    MIN(timestamp_iso) as earliest_data,
    MAX(timestamp_iso) as latest_data,
    DATEDIFF(MAX(timestamp_iso), MIN(timestamp_iso)) as days_coverage
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY symbol
ORDER BY total_records DESC
LIMIT 20
'''

df = pd.read_sql(query, conn)
print('TOP 20 SYMBOLS - FEATURE COVERAGE (Last 30 days):')
print(df.to_string(index=False))

# Check for symbols with gaps
query2 = '''
SELECT 
    symbol,
    COUNT(*) as records,
    COUNT(CASE WHEN current_price IS NULL THEN 1 END) as missing_price,
    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) as missing_sentiment,
    COUNT(CASE WHEN rsi_14 IS NULL THEN 1 END) as missing_rsi,
    COUNT(CASE WHEN macd_12_26_9 IS NULL THEN 1 END) as missing_macd
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY symbol
HAVING missing_price > 0 OR missing_sentiment > 5 OR missing_rsi > 10 OR missing_macd > 10
ORDER BY missing_price DESC, missing_sentiment DESC
LIMIT 15
'''

df2 = pd.read_sql(query2, conn)
print('\nSYMBOLS WITH DATA GAPS (Last 7 days):')
print(df2.to_string(index=False))

# Overall statistics
query3 = '''
SELECT 
    COUNT(DISTINCT symbol) as total_symbols,
    COUNT(*) as total_records,
    SUM(CASE WHEN current_price IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as price_completeness,
    SUM(CASE WHEN sentiment_score IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as sentiment_completeness,
    SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as rsi_completeness,
    SUM(CASE WHEN macd_12_26_9 IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) * 100 as macd_completeness
FROM ml_features_materialized 
WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
'''

df3 = pd.read_sql(query3, conn)
print('\nOVERALL FEATURE COMPLETENESS (Last 7 days):')
print(df3.to_string(index=False))

# Check symbols that need backfill
query4 = '''
SELECT 
    symbol,
    COUNT(*) as recent_records,
    MAX(timestamp_iso) as last_update,
    TIMESTAMPDIFF(HOUR, MAX(timestamp_iso), NOW()) as hours_since_last_update
FROM ml_features_materialized 
GROUP BY symbol
HAVING hours_since_last_update > 2
ORDER BY hours_since_last_update DESC
LIMIT 10
'''

df4 = pd.read_sql(query4, conn)
print('\nSYMBOLS NEEDING BACKFILL (>2 hours since last update):')
print(df4.to_string(index=False))

conn.close()
print("\n=== ANALYSIS COMPLETE ===")