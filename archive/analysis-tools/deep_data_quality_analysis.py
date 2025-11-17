#!/usr/bin/env python3
"""
Deep Data Quality Analysis for Materialized Table
Analyzes real data vs nulls, consistency, and provides actionable recommendations
"""

import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", os.getenv("DB_HOST", "127.0.0.1")),
    user=os.getenv("MYSQL_USER", os.getenv("DB_USER", "news_collector")),
    password=os.getenv("MYSQL_PASSWORD", os.getenv("DB_PASSWORD", "99Rules!")),
    database=os.getenv("MYSQL_DATABASE", os.getenv("DB_NAME", "crypto_prices")),
)
cursor = conn.cursor()

print("=" * 80)
print("DEEP DATA QUALITY ANALYSIS - MATERIALIZED TABLE")
print("=" * 80)

# Get total records
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
total_records = cursor.fetchone()[0]
print(f"\nTotal Records: {total_records:,}\n")

# Define column groups for analysis
column_groups = {
    "Core Price Data": ["current_price", "volume_24h", "market_cap", "price_change_24h"],
    "Technical Indicators": ["rsi_14", "sma_20", "sma_50", "macd_line", "bb_upper"],
    "Sentiment Data": ["avg_ml_overall_sentiment", "sentiment_volume", "avg_ml_crypto_sentiment"],
    "Onchain Data": ["active_addresses_24h", "transaction_count_24h", "exchange_net_flow_24h"],
    "Macro Data": ["vix", "spx", "dxy", "fed_funds_rate", "treasury_10y"],
    "Social Data": ["social_post_count", "social_avg_sentiment", "social_total_engagement"]
}

results = {}

print("COLUMN GROUP ANALYSIS")
print("-" * 80)

for group_name, columns in column_groups.items():
    print(f"\n{group_name}:")
    group_stats = []
    
    for col in columns:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL")
            non_null = cursor.fetchone()[0]
            pct = (non_null / total_records * 100) if total_records > 0 else 0
            
            # Get sample values to check for real data
            cursor.execute(f"SELECT {col} FROM ml_features_materialized WHERE {col} IS NOT NULL LIMIT 5")
            samples = [row[0] for row in cursor.fetchall()]
            
            group_stats.append({
                'column': col,
                'non_null': non_null,
                'pct': pct,
                'samples': samples
            })
            
            print(f"  {col:<35} {non_null:>10,} / {total_records:>10,} ({pct:>5.1f}%)")
        except Exception as e:
            print(f"  {col:<35} ERROR: {e}")
    
    results[group_name] = group_stats

# Recent data quality check (last 24 hours)
print(f"\n\nRECENT DATA QUALITY (Last 24 Hours)")
print("-" * 80)

cursor.execute("""
    SELECT COUNT(*) FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
""")
recent_total = cursor.fetchone()[0]
print(f"Total recent records: {recent_total:,}\n")

if recent_total > 0:
    for group_name, columns in column_groups.items():
        print(f"{group_name}:")
        for col in columns:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM ml_features_materialized 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                    AND {col} IS NOT NULL
                """)
                recent_non_null = cursor.fetchone()[0]
                recent_pct = (recent_non_null / recent_total * 100) if recent_total > 0 else 0
                print(f"  {col:<35} {recent_non_null:>6,} / {recent_total:>6,} ({recent_pct:>5.1f}%)")
            except Exception as e:
                print(f"  {col:<35} ERROR")
        print()

# Data consistency checks
print("DATA CONSISTENCY CHECKS")
print("-" * 80)

# Check for records with no price data
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE current_price IS NULL")
no_price = cursor.fetchone()[0]
print(f"Records with NO price data: {no_price:,} ({no_price/total_records*100:.1f}%)")

# Check for records with no sentiment
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NULL")
no_sentiment = cursor.fetchone()[0]
print(f"Records with NO sentiment: {no_sentiment:,} ({no_sentiment/total_records*100:.1f}%)")

# Check for records with no onchain
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE active_addresses_24h IS NULL")
no_onchain = cursor.fetchone()[0]
print(f"Records with NO onchain: {no_onchain:,} ({no_onchain/total_records*100:.1f}%)")

# Check for records with no technical indicators
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE sma_20 IS NULL")
no_technical = cursor.fetchone()[0]
print(f"Records with NO technical: {no_technical:,} ({no_technical/total_records*100:.1f}%)")

# Complete records (have all core data types)
cursor.execute("""
    SELECT COUNT(*) FROM ml_features_materialized 
    WHERE current_price IS NOT NULL 
    AND avg_ml_overall_sentiment IS NOT NULL
    AND active_addresses_24h IS NOT NULL
    AND sma_20 IS NOT NULL
""")
complete_records = cursor.fetchone()[0]
print(f"\nRecords with ALL core data: {complete_records:,} ({complete_records/total_records*100:.1f}%)")

conn.close()

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

