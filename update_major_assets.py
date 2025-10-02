#!/usr/bin/env python3
"""
Manually Update Major Asset CoinGecko IDs
Add coingecko_id for the most important missing assets
"""

import mysql.connector

def update_major_assets():
    """Manually update coingecko_id for major assets"""
    
    print("🔧 MANUALLY UPDATING MAJOR ASSET COINGECKO IDS")
    print("=" * 55)
    
    # Major asset mappings (symbol -> coingecko_id)
    major_mappings = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum', 
        'SOL': 'solana',
        'ADA': 'cardano',
        'LINK': 'chainlink',
        'MATIC': 'matic-network',
        'DOT': 'polkadot',
        'AVAX': 'avalanche-2',
        'UNI': 'uniswap',
        'ATOM': 'cosmos',
        'XLM': 'stellar',
        'ALGO': 'algorand',
        'VET': 'vechain',
        'FIL': 'filecoin',
        'THETA': 'theta-token',
        'XTZ': 'tezos',
        'EOS': 'eos',
        'AAVE': 'aave',
        'MKR': 'maker',
        'XMR': 'monero',
        'LTC': 'litecoin',
        'TRX': 'tron',
        'DOGE': 'dogecoin',
        'SHIB': 'shiba-inu',
        'ARB': 'arbitrum',
        'FTM': 'fantom',
        'NEAR': 'near',
        'APT': 'aptos',
        'COMP': 'compound-governance-token',
        'BAL': 'balancer',
        'CRV': 'curve-dao-token',
        'DASH': 'dash',
        'DCR': 'decred',
        'DGB': 'digibyte',
        'EGLD': 'elrond-erd-2'
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
            
            print("📊 Updating major assets:")
            print("   Symbol | CoinGecko ID")
            print("   -------|-------------")
            
            updated_count = 0
            
            for symbol, coingecko_id in major_mappings.items():
                # Check if this symbol exists and needs updating
                cursor.execute("""
                    SELECT id, coingecko_id FROM crypto_assets 
                    WHERE symbol = %s
                """, (symbol,))
                
                result = cursor.fetchone()
                if result:
                    asset_id, current_id = result
                    
                    if current_id is None:
                        # Update the coingecko_id
                        cursor.execute("""
                            UPDATE crypto_assets 
                            SET coingecko_id = %s 
                            WHERE id = %s
                        """, (coingecko_id, asset_id))
                        
                        print(f"   {symbol:>6} | {coingecko_id}")
                        updated_count += 1
                    else:
                        print(f"   {symbol:>6} | {coingecko_id} (already set)")
                else:
                    print(f"   {symbol:>6} | NOT FOUND in crypto_assets table")
            
            conn.commit()
            print(f"\n✅ Updated {updated_count} assets with coingecko_id")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def verify_final_coverage():
    """Check final coverage after manual updates"""
    
    print(f"\n📊 FINAL COVERAGE VERIFICATION:")
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
            
            # Check coverage
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN coingecko_id IS NOT NULL THEN 1 END) as with_id
                FROM crypto_assets
            """)
            
            total, with_id = cursor.fetchone()
            coverage_pct = (with_id / total * 100) if total > 0 else 0
            
            print(f"   Total assets: {total}")
            print(f"   With coingecko_id: {with_id} ({coverage_pct:.1f}%)")
            
            # Show top assets by market cap with coingecko_id
            cursor.execute("""
                SELECT symbol, coingecko_id, name, market_cap_rank
                FROM crypto_assets 
                WHERE coingecko_id IS NOT NULL
                ORDER BY market_cap_rank
                LIMIT 15
            """)
            
            top_assets = cursor.fetchall()
            
            print(f"\n   📋 Top assets now ready for collection:")
            print("      Symbol | CoinGecko ID | Name | Rank")
            print("      -------|--------------|------|-----")
            
            for symbol, cg_id, name, rank in top_assets:
                symbol_display = symbol or "NULL"
                cg_id_display = cg_id[:12] if cg_id else "NULL"
                name_display = (name[:12] + "...") if name and len(name) > 12 else (name or "NULL")
                rank_display = str(rank) if rank else "NULL"
                print(f"      {symbol_display:>6} | {cg_id_display:>12} | {name_display:>12} | {rank_display:>4}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def show_collector_requirements():
    """Show what the collector needs to do to collect all assets"""
    
    print(f"\n🎯 COLLECTOR REQUIREMENTS FOR FULL COLLECTION:")
    print("-" * 55)
    
    print("✅ DATABASE READY:")
    print("   • crypto_assets table now has coingecko_id for major assets")
    print("   • Assets can be queried with: SELECT symbol, coingecko_id FROM crypto_assets WHERE coingecko_id IS NOT NULL")
    
    print(f"\n🔧 COLLECTOR MUST:")
    print("   1. Query crypto_assets table (NOT hardcoded lists)")
    print("   2. Use: SELECT symbol, coingecko_id FROM crypto_assets WHERE coingecko_id IS NOT NULL")
    print("   3. Loop through ALL returned assets, not just 'premium' subset")
    print("   4. Handle API rate limits for larger requests")
    print("   5. Log any assets that fail to collect")
    
    print(f"\n⚠️  CURRENT ISSUE:")
    print("   • Collector appears to be using hardcoded 'premium' asset list")
    print("   • Only collecting ~50 assets instead of all available assets")
    print("   • Need to check collector source code and configuration")
    
    print(f"\n🚀 NEXT STEPS:")
    print("   1. ✅ Database assets updated with coingecko_id")
    print("   2. 🔧 Check collector source code for hardcoded asset lists")
    print("   3. 🔧 Update collector to read from crypto_assets table")
    print("   4. 🔧 Remove any 'premium only' filters")
    print("   5. ⚡ Restart collector to pick up all assets")

if __name__ == "__main__":
    update_major_assets()
    verify_final_coverage()
    show_collector_requirements()