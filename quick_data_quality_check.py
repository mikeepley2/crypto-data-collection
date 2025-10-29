#!/usr/bin/env python3
import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    user=os.getenv("DB_USER", "news_collector"),
    password=os.getenv("DB_PASSWORD", "99Rules!"),
    database=os.getenv("DB_NAME", "crypto_prices"),
)
cursor = conn.cursor()

print("MATERIALIZED TABLE DATA QUALITY QUICK CHECK")
print("=" * 70)

# Total records
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
total = cursor.fetchone()[0]
print(f"Total Records: {total:,}\n")

# Core columns check
columns_to_check = [
    ("current_price", "Price"),
    ("volume_24h", "Volume"),
    ("market_cap", "Market Cap"),
    ("rsi_14", "RSI"),
    ("sma_20", "SMA20"),
    ("bb_upper", "Bollinger"),
    ("avg_ml_overall_sentiment", "ML Sentiment"),
    ("sentiment_volume", "Sent Volume"),
    ("active_addresses_24h", "Onchain Addr"),
    ("transaction_count_24h", "Onchain Tx"),
    ("vix", "VIX"),
    ("spx", "S&P500"),
    ("social_post_count", "Social Posts"),
]

print("COLUMN POPULATION")
print("-" * 70)
populated = 0
for col, label in columns_to_check:
    cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL")
    count = cursor.fetchone()[0]
    pct = (count / total * 100) if total > 0 else 0
    status = "OK" if pct > 50 else "LOW" if pct > 10 else "BAD"
    print(f"{label:<20} {count:>10,} / {total:>10,} ({pct:>5.1f}%) [{status}]")
    if pct > 10:
        populated += 1

print(f"\nPopulated columns (>10%): {populated}/{len(columns_to_check)}")

# Recent data (last 24h)
print(f"\n\nRECENT DATA QUALITY (Last 24 Hours)")
print("-" * 70)
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
recent_total = cursor.fetchone()[0]
print(f"Recent records: {recent_total:,}\n")

for col, label in [("current_price", "Price"), ("avg_ml_overall_sentiment", "Sentiment"), ("active_addresses_24h", "Onchain"), ("sma_20", "Technical")]:
    cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR) AND {col} IS NOT NULL")
    count = cursor.fetchone()[0]
    pct = (count / recent_total * 100) if recent_total > 0 else 0
    print(f"{label:<20} {count:>6,} / {recent_total:>6,} ({pct:>5.1f}%)")

# Completeness
cursor.execute("""SELECT COUNT(*) FROM ml_features_materialized 
    WHERE current_price IS NOT NULL AND avg_ml_overall_sentiment IS NOT NULL 
    AND active_addresses_24h IS NOT NULL AND sma_20 IS NOT NULL""")
complete = cursor.fetchone()[0]
print(f"\nComplete records (all 4 core types): {complete:,} ({complete/total*100:.1f}%)")

conn.close()
print("\n" + "=" * 70)

