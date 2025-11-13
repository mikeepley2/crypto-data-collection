#!/usr/bin/env python3
"""Check current onchain data collection status"""

import mysql.connector
import os
from datetime import datetime, date
import sys

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'crypto_user'),
        password=os.getenv('DB_PASS', 'CryptoData2024!'),
        database=os.getenv('DB_NAME', 'crypto_data'),
        charset='utf8mb4'
    )

def check_onchain_data():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Check table structure
        cursor.execute("DESCRIBE onchain_data")
        columns = cursor.fetchall()
        print(f"🏗️ Table has {len(columns)} columns")
        
        # Check recent data
        cursor.execute("""
            SELECT symbol, timestamp_iso, data_source, 
                   circulating_supply, total_value_locked, 
                   social_volume_24h, github_commits_30d,
                   active_addresses, transaction_count
            FROM onchain_data 
            ORDER BY timestamp_iso DESC 
            LIMIT 10
        """)
        
        recent_data = cursor.fetchall()
        print(f"\n📊 Recent onchain data ({len(recent_data)} records):")
        
        for record in recent_data:
            symbol, timestamp, data_source, supply, tvl, social, commits, addresses, tx_count = record
            print(f"  {symbol}: {timestamp} | Source: {data_source}")
            print(f"    Supply: {supply:,.0f if supply else 'N/A'} | TVL: ${tvl:,.0f if tvl else 'N/A'}")
            print(f"    Social: {social or 'N/A'} | Commits: {commits or 'N/A'} | Active Addr: {addresses or 'N/A'}")
            print()
        
        # Count by symbol
        cursor.execute("""
            SELECT symbol, COUNT(*) as count, 
                   MAX(timestamp_iso) as latest,
                   COUNT(DISTINCT DATE(timestamp_iso)) as unique_dates
            FROM onchain_data 
            GROUP BY symbol 
            ORDER BY latest DESC
        """)
        
        symbol_counts = cursor.fetchall()
        print(f"📈 Data by symbol:")
        for symbol, count, latest, unique_dates in symbol_counts:
            print(f"  {symbol}: {count} records | Latest: {latest} | {unique_dates} unique dates")
        
        # Check data completeness
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN circulating_supply IS NOT NULL THEN 1 ELSE 0 END) * 100 as supply_pct,
                AVG(CASE WHEN total_value_locked IS NOT NULL THEN 1 ELSE 0 END) * 100 as tvl_pct,
                AVG(CASE WHEN social_volume_24h IS NOT NULL THEN 1 ELSE 0 END) * 100 as social_pct,
                AVG(CASE WHEN github_commits_30d IS NOT NULL THEN 1 ELSE 0 END) * 100 as dev_pct,
                AVG(CASE WHEN active_addresses IS NOT NULL THEN 1 ELSE 0 END) * 100 as addr_pct
            FROM onchain_data
        """)
        
        completeness = cursor.fetchone()
        if completeness:
            supply_pct, tvl_pct, social_pct, dev_pct, addr_pct = completeness
            print(f"\n📋 Data completeness:")
            print(f"  Supply data: {supply_pct:.1f}%")
            print(f"  TVL data: {tvl_pct:.1f}%")
            print(f"  Social data: {social_pct:.1f}%")
            print(f"  Developer data: {dev_pct:.1f}%")
            print(f"  Address data: {addr_pct:.1f}%")
        
        cursor.close()
        db.close()
        
    except Exception as e:
        print(f"❌ Error checking data: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Checking enhanced onchain data collection...")
    check_onchain_data()