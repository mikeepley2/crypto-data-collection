#!/usr/bin/env python3
"""
Fix Asset Collection - Ensure All Assets Have CoinGecko IDs
Update crypto_assets table to have proper coingecko_id values for all assets
"""

import mysql.connector
import requests
import time
import json

def check_coingecko_mapping():
    """Check current coingecko_id mapping and identify missing ones"""
    
    print("🔍 COINGECKO ID MAPPING ANALYSIS")
    print("=" * 50)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Get assets without coingecko_id
            print("1️⃣ ASSETS WITHOUT COINGECKO_ID:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT symbol, name, market_cap_rank
                FROM crypto_assets 
                WHERE coingecko_id IS NULL 
                ORDER BY market_cap_rank
                LIMIT 20
            """)
            
            missing_ids = cursor.fetchall()
            
            print(f"   📊 Assets without coingecko_id: {len(missing_ids) if missing_ids else 0}")
            print("   📋 Top missing by market cap:")
            print("      Symbol | Name | Rank")
            print("      -------|------|-----")
            
            for symbol, name, rank in missing_ids:
                symbol_display = symbol or "NULL"
                name_display = (name[:20] + "...") if name and len(name) > 20 else (name or "NULL")
                rank_display = str(rank) if rank else "NULL"
                print(f"      {symbol_display:>6} | {name_display:>20} | {rank_display:>4}")
            
            # Get assets with coingecko_id
            print(f"\n2️⃣ ASSETS WITH COINGECKO_ID:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT symbol, coingecko_id, name
                FROM crypto_assets 
                WHERE coingecko_id IS NOT NULL 
                ORDER BY market_cap_rank
                LIMIT 10
            """)
            
            with_ids = cursor.fetchall()
            
            print(f"   📊 Assets with coingecko_id: {len(with_ids) if with_ids else 0}")
            print("   📋 Sample mappings:")
            print("      Symbol | CoinGecko ID | Name")
            print("      -------|--------------|-----")
            
            for symbol, cg_id, name in with_ids:
                symbol_display = symbol or "NULL"
                cg_id_display = cg_id or "NULL"
                name_display = (name[:15] + "...") if name and len(name) > 15 else (name or "NULL")
                print(f"      {symbol_display:>6} | {cg_id_display:>12} | {name_display}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def get_coingecko_coin_list():
    """Fetch the complete CoinGecko coin list to map symbols to IDs"""
    
    print(f"\n3️⃣ FETCHING COINGECKO COIN LIST:")
    print("-" * 40)
    
    try:
        print("   🌐 Fetching coin list from CoinGecko...")
        response = requests.get('https://api.coingecko.com/api/v3/coins/list', timeout=30)
        
        if response.status_code == 200:
            coins = response.json()
            print(f"   ✅ Retrieved {len(coins):,} coins from CoinGecko")
            
            # Create mapping dictionaries
            symbol_to_id = {}
            name_to_id = {}
            
            for coin in coins:
                symbol = coin['symbol'].upper()
                name = coin['name']
                coin_id = coin['id']
                
                # Map symbol to ID (handle duplicates by preferring first/most popular)
                if symbol not in symbol_to_id:
                    symbol_to_id[symbol] = coin_id
                
                # Map name to ID
                if name not in name_to_id:
                    name_to_id[name] = coin_id
            
            print(f"   📊 Created mapping for {len(symbol_to_id):,} unique symbols")
            print(f"   📊 Created mapping for {len(name_to_id):,} unique names")
            
            return symbol_to_id, name_to_id
            
        else:
            print(f"   ❌ Failed to fetch coin list: {response.status_code}")
            return {}, {}
            
    except Exception as e:
        print(f"   ❌ Error fetching coin list: {e}")
        return {}, {}

def update_missing_coingecko_ids():
    """Update crypto_assets table with missing coingecko_id values"""
    
    print(f"\n4️⃣ UPDATING MISSING COINGECKO IDS:")
    print("-" * 40)
    
    # Get CoinGecko mappings
    symbol_to_id, name_to_id = get_coingecko_coin_list()
    
    if not symbol_to_id:
        print("   ❌ No mapping data available, skipping updates")
        return
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Get assets without coingecko_id
            cursor.execute("""
                SELECT id, symbol, name
                FROM crypto_assets 
                WHERE coingecko_id IS NULL
            """)
            
            missing_assets = cursor.fetchall()
            
            print(f"   📊 Processing {len(missing_assets)} assets without coingecko_id...")
            
            updates_made = 0
            
            for asset_id, symbol, name in missing_assets:
                coingecko_id = None
                
                # Try to match by symbol first
                if symbol and symbol.upper() in symbol_to_id:
                    coingecko_id = symbol_to_id[symbol.upper()]
                    print(f"   ✅ Matched {symbol} -> {coingecko_id} (by symbol)")
                
                # If no symbol match, try by name
                elif name and name in name_to_id:
                    coingecko_id = name_to_id[name]
                    print(f"   ✅ Matched {name} -> {coingecko_id} (by name)")
                
                # Update if we found a match
                if coingecko_id:
                    cursor.execute("""
                        UPDATE crypto_assets 
                        SET coingecko_id = %s 
                        WHERE id = %s
                    """, (coingecko_id, asset_id))
                    updates_made += 1
                else:
                    print(f"   ⚠️  No match found for {symbol} / {name}")
            
            conn.commit()
            print(f"\n   ✅ Updated {updates_made} assets with coingecko_id")
            
    except Exception as e:
        print(f"   ❌ Error updating coingecko_ids: {e}")

def verify_updates():
    """Verify the updates and show final coverage"""
    
    print(f"\n5️⃣ VERIFICATION OF UPDATES:")
    print("-" * 40)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check final coverage
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN coingecko_id IS NOT NULL THEN 1 END) as with_id,
                    COUNT(CASE WHEN coingecko_id IS NULL THEN 1 END) as without_id
                FROM crypto_assets
            """)
            
            total, with_id, without_id = cursor.fetchone()
            coverage_pct = (with_id / total * 100) if total > 0 else 0
            
            print(f"   📊 Final Coverage:")
            print(f"   Total assets: {total}")
            print(f"   With coingecko_id: {with_id} ({coverage_pct:.1f}%)")
            print(f"   Without coingecko_id: {without_id}")
            
            # Show sample of updated assets
            cursor.execute("""
                SELECT symbol, coingecko_id, name
                FROM crypto_assets 
                WHERE coingecko_id IS NOT NULL
                ORDER BY market_cap_rank
                LIMIT 10
            """)
            
            updated_assets = cursor.fetchall()
            
            print(f"\n   📋 Sample updated assets:")
            print("      Symbol | CoinGecko ID | Name")
            print("      -------|--------------|-----")
            
            for symbol, cg_id, name in updated_assets:
                symbol_display = symbol or "NULL"
                cg_id_display = cg_id or "NULL"
                name_display = (name[:15] + "...") if name and len(name) > 15 else (name or "NULL")
                print(f"      {symbol_display:>6} | {cg_id_display:>12} | {name_display}")
                
    except Exception as e:
        print(f"❌ Error in verification: {e}")

def check_collector_config():
    """Check if the collector is configured to use all assets from the database"""
    
    print(f"\n6️⃣ COLLECTOR CONFIGURATION CHECK:")
    print("-" * 40)
    
    print("🔍 NEXT STEPS TO ENSURE FULL COLLECTION:")
    print("   1. ✅ Updated coingecko_id values in crypto_assets table")
    print("   2. 🔧 Need to verify collector reads from crypto_assets table")
    print("   3. 🔧 Remove any hardcoded symbol lists in collector")
    print("   4. 🔧 Ensure collector queries: SELECT symbol, coingecko_id FROM crypto_assets WHERE coingecko_id IS NOT NULL")
    print("   5. ⚡ Restart collector to pick up new asset list")
    
    print(f"\n💡 COLLECTOR SHOULD:")
    print("   • Query crypto_assets table for all symbols with coingecko_id")
    print("   • NOT use hardcoded lists of 'premium' symbols")
    print("   • Handle API rate limits for larger asset lists")
    print("   • Log which assets fail to collect data")

if __name__ == "__main__":
    check_coingecko_mapping()
    update_missing_coingecko_ids()
    verify_updates()
    check_collector_config()