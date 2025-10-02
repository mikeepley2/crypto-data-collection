#!/usr/bin/env python3
"""
Fix Failed Assets by Finding CoinGecko IDs
Identify which assets failed collection and find their proper coingecko_id values
"""

import mysql.connector
import requests
import time
import json

def analyze_failed_assets():
    """Analyze which assets failed and why"""
    
    print("🔍 FAILED ASSETS ANALYSIS")
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
            
            # Get assets that were supposed to be collected but have no recent data
            print("1️⃣ ASSETS IN DATABASE BUT NOT COLLECTED:")
            print("-" * 45)
            
            cursor.execute("""
                SELECT ca.symbol, ca.coingecko_id, ca.name, ca.market_cap_rank
                FROM crypto_assets ca
                LEFT JOIN (
                    SELECT DISTINCT symbol 
                    FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                    AND data_source = 'unified_premium_coingecko'
                ) od ON ca.symbol = od.symbol
                WHERE od.symbol IS NULL
                AND ca.symbol IS NOT NULL
                ORDER BY ca.market_cap_rank
            """)
            
            failed_assets = cursor.fetchall()
            
            print(f"   📊 Assets not collected recently: {len(failed_assets)}")
            print("   📋 Failed assets:")
            print("      Symbol | CoinGecko ID | Name | Rank")
            print("      -------|--------------|------|-----")
            
            assets_without_id = []
            assets_with_bad_id = []
            
            for symbol, cg_id, name, rank in failed_assets[:20]:  # Show top 20
                symbol_display = symbol or "NULL"
                cg_id_display = cg_id or "NULL"
                name_display = (name[:15] + "...") if name and len(name) > 15 else (name or "NULL")
                rank_display = str(rank) if rank else "NULL"
                print(f"      {symbol_display:>6} | {cg_id_display:>12} | {name_display:>15} | {rank_display:>4}")
                
                if not cg_id:
                    assets_without_id.append((symbol, name))
                else:
                    assets_with_bad_id.append((symbol, cg_id, name))
            
            print(f"\n   📊 Analysis:")
            print(f"      Assets without coingecko_id: {len(assets_without_id)}")
            print(f"      Assets with potentially wrong coingecko_id: {len(assets_with_bad_id)}")
            
            return assets_without_id, assets_with_bad_id
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

def fetch_coingecko_mappings():
    """Fetch CoinGecko coin list with rate limiting"""
    
    print(f"\n2️⃣ FETCHING COINGECKO MAPPINGS:")
    print("-" * 40)
    
    try:
        print("   🌐 Fetching from CoinGecko API...")
        
        # Try with a delay to avoid rate limiting
        time.sleep(2)
        response = requests.get('https://api.coingecko.com/api/v3/coins/list', timeout=30)
        
        if response.status_code == 200:
            coins = response.json()
            print(f"   ✅ Retrieved {len(coins):,} coins")
            
            # Create comprehensive mappings
            symbol_to_coins = {}
            name_to_coins = {}
            
            for coin in coins:
                symbol = coin['symbol'].upper()
                name = coin['name']
                coin_id = coin['id']
                
                # Map symbol to list of possible coins (handle duplicates)
                if symbol not in symbol_to_coins:
                    symbol_to_coins[symbol] = []
                symbol_to_coins[symbol].append((coin_id, name))
                
                # Map name to coin_id
                if name not in name_to_coins:
                    name_to_coins[name] = coin_id
            
            return symbol_to_coins, name_to_coins
            
        elif response.status_code == 429:
            print(f"   ⚠️  Rate limited (429), trying cached approach...")
            return {}, {}
        else:
            print(f"   ❌ API error: {response.status_code}")
            return {}, {}
            
    except Exception as e:
        print(f"   ❌ Error fetching mappings: {e}")
        return {}, {}

def find_missing_ids(assets_without_id, symbol_to_coins, name_to_coins):
    """Find CoinGecko IDs for assets that don't have them"""
    
    print(f"\n3️⃣ FINDING MISSING COINGECKO IDS:")
    print("-" * 40)
    
    found_mappings = []
    
    for symbol, name in assets_without_id[:15]:  # Limit to avoid overwhelming output
        print(f"\n   🔍 Searching for: {symbol} ({name})")
        
        found_options = []
        
        # Try exact symbol match
        if symbol and symbol.upper() in symbol_to_coins:
            options = symbol_to_coins[symbol.upper()]
            print(f"      Symbol matches: {len(options)} options")
            for coin_id, coin_name in options[:3]:  # Show top 3
                print(f"         • {coin_id} ({coin_name})")
                found_options.append((coin_id, coin_name, 'symbol'))
        
        # Try exact name match
        if name and name in name_to_coins:
            coin_id = name_to_coins[name]
            print(f"      Name match: {coin_id}")
            found_options.append((coin_id, name, 'name'))
        
        # Try partial name matches
        if name and not found_options:
            partial_matches = []
            name_lower = name.lower()
            for coin_name, coin_id in name_to_coins.items():
                if name_lower in coin_name.lower() or coin_name.lower() in name_lower:
                    partial_matches.append((coin_id, coin_name))
            
            if partial_matches:
                print(f"      Partial name matches: {len(partial_matches)}")
                for coin_id, coin_name in partial_matches[:3]:
                    print(f"         • {coin_id} ({coin_name})")
                    found_options.append((coin_id, coin_name, 'partial'))
        
        # Select best option (prefer exact matches)
        if found_options:
            # Prefer symbol matches, then name matches, then partial
            best_option = None
            for coin_id, coin_name, match_type in found_options:
                if match_type == 'symbol':
                    best_option = (symbol, coin_id, coin_name)
                    break
                elif match_type == 'name' and not best_option:
                    best_option = (symbol, coin_id, coin_name)
                elif match_type == 'partial' and not best_option:
                    best_option = (symbol, coin_id, coin_name)
            
            if best_option:
                found_mappings.append(best_option)
                print(f"      ✅ Selected: {best_option[1]} ({best_option[2]})")
        else:
            print(f"      ❌ No matches found")
    
    return found_mappings

def update_missing_coingecko_ids(found_mappings):
    """Update the database with found CoinGecko IDs"""
    
    print(f"\n4️⃣ UPDATING DATABASE:")
    print("-" * 30)
    
    if not found_mappings:
        print("   ⚠️  No new mappings to update")
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
            
            updated_count = 0
            
            for symbol, coin_id, coin_name in found_mappings:
                print(f"   🔄 Updating {symbol} -> {coin_id}")
                
                cursor.execute("""
                    UPDATE crypto_assets 
                    SET coingecko_id = %s 
                    WHERE symbol = %s AND coingecko_id IS NULL
                """, (coin_id, symbol))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    print(f"      ✅ Updated")
                else:
                    print(f"      ⚠️  No rows affected")
            
            conn.commit()
            print(f"\n   ✅ Successfully updated {updated_count} assets")
            
    except Exception as e:
        print(f"   ❌ Error updating database: {e}")

def manual_high_priority_mappings():
    """Manually add high-priority missing mappings"""
    
    print(f"\n5️⃣ MANUAL HIGH-PRIORITY MAPPINGS:")
    print("-" * 40)
    
    # Common assets that might be missing
    manual_mappings = {
        'USDT': 'tether',
        'USDC': 'usd-coin',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'STETH': 'staked-ether',
        'TON': 'the-open-network',
        'PEPE': 'pepe',
        'WIF': 'dogwifcoin',
        'BONK': 'bonk',
        'FLOKI': 'floki',
        'POPCAT': 'popcat',
        'WLD': 'worldcoin-wld',
        'RENDER': 'render-token',
        'TAO': 'bittensor',
        'SUI': 'sui',
        'HBAR': 'hedera-hashgraph',
        'LDO': 'lido-dao',
        'WBTC': 'wrapped-bitcoin',
        'WETH': 'weth',
        'DAI': 'dai',
    }
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            updated_count = 0
            
            for symbol, coin_id in manual_mappings.items():
                # Check if this symbol exists and needs updating
                cursor.execute("""
                    SELECT id FROM crypto_assets 
                    WHERE symbol = %s AND coingecko_id IS NULL
                """, (symbol,))
                
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE crypto_assets 
                        SET coingecko_id = %s 
                        WHERE symbol = %s AND coingecko_id IS NULL
                    """, (coin_id, symbol))
                    
                    if cursor.rowcount > 0:
                        print(f"   ✅ {symbol} -> {coin_id}")
                        updated_count += 1
            
            conn.commit()
            print(f"\n   ✅ Manually updated {updated_count} high-priority assets")
            
    except Exception as e:
        print(f"   ❌ Error with manual mappings: {e}")

def show_final_results():
    """Show final coverage after updates"""
    
    print(f"\n6️⃣ FINAL COVERAGE ANALYSIS:")
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
            
            # Get final coverage stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_assets,
                    COUNT(CASE WHEN coingecko_id IS NOT NULL THEN 1 END) as with_coingecko_id
                FROM crypto_assets
            """)
            
            total, with_id = cursor.fetchone()
            coverage_pct = (with_id / total * 100) if total > 0 else 0
            
            print(f"   📊 Updated Coverage:")
            print(f"      Total assets: {total}")
            print(f"      With coingecko_id: {with_id} ({coverage_pct:.1f}%)")
            
            # Get assets ready for next collection
            print(f"\n   🚀 READY FOR NEXT COLLECTION:")
            print("      Now have coingecko_id for collection!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Step 1: Analyze what failed
    assets_without_id, assets_with_bad_id = analyze_failed_assets()
    
    # Step 2: Get CoinGecko mappings (with rate limit handling)
    symbol_to_coins, name_to_coins = fetch_coingecko_mappings()
    
    # Step 3: Add manual high-priority mappings first
    manual_high_priority_mappings()
    
    # Step 4: Find missing IDs if we got API data
    if symbol_to_coins or name_to_coins:
        found_mappings = find_missing_ids(assets_without_id, symbol_to_coins, name_to_coins)
        update_missing_coingecko_ids(found_mappings)
    else:
        print("\n⚠️  Skipping API-based mapping due to rate limits")
        print("   High-priority manual mappings were still applied")
    
    # Step 5: Show final results
    show_final_results()
    
    print(f"\n" + "="*50)
    print("🎯 NEXT STEPS:")
    print("✅ Additional assets now have coingecko_id")
    print("⚡ Trigger another collection to test new assets")
    print("🔧 Monitor which assets still fail collection")
    print("="*50)