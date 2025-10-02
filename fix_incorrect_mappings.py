#!/usr/bin/env python3
"""
Fix Incorrect CoinGecko ID Mappings
Some of the automatic mappings were incorrect, let's fix the obvious ones
"""

import mysql.connector

def fix_incorrect_mappings():
    """Fix obviously incorrect CoinGecko ID mappings"""
    
    print("🔧 FIXING INCORRECT COINGECKO ID MAPPINGS")
    print("=" * 50)
    
    # Corrections for obviously wrong mappings
    corrections = {
        'ATOM-USD': 'cosmos',  # Was: axelar-bridged-usdc-cosmos
        'TRX-USD': 'tron',     # Was: biaoqing-tron  
        'CRV-USD': 'curve-dao-token',  # Was: ken
        'NEAR-USD': 'near',    # Was: 1art
        'SHIB-USD': 'shiba-inu',  # Was: h
        'EOS-USD': 'eos',      # Was: binance-peg-eos
        
        # Add some missing important ones that might be in the database
        'TON': 'the-open-network',
        'USDC': 'usd-coin',
        'USDT': 'tether', 
        'STETH': 'staked-ether',
        'WBTC': 'wrapped-bitcoin',
        'WETH': 'weth',
        'DAI': 'dai',
        'MATIC': 'matic-network',  # In case it wasn't updated
        'POLYGON': 'matic-network',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
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
            
            for symbol, correct_id in corrections.items():
                # Check if this symbol exists
                cursor.execute("""
                    SELECT id, coingecko_id FROM crypto_assets 
                    WHERE symbol = %s
                """, (symbol,))
                
                result = cursor.fetchone()
                if result:
                    asset_id, current_id = result
                    
                    if current_id != correct_id:
                        cursor.execute("""
                            UPDATE crypto_assets 
                            SET coingecko_id = %s 
                            WHERE id = %s
                        """, (correct_id, asset_id))
                        
                        print(f"   ✅ {symbol}: {current_id or 'NULL'} -> {correct_id}")
                        updated_count += 1
                    else:
                        print(f"   ✓ {symbol}: Already correct ({correct_id})")
                else:
                    print(f"   ⚠️  {symbol}: Not found in database")
            
            conn.commit()
            print(f"\n✅ Updated {updated_count} incorrect mappings")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_final_coverage():
    """Show final coverage after corrections"""
    
    print(f"\n📊 FINAL COVERAGE AFTER CORRECTIONS:")
    print("-" * 45)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
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
            
            # Show top assets that now have IDs
            cursor.execute("""
                SELECT symbol, coingecko_id, name
                FROM crypto_assets 
                WHERE coingecko_id IS NOT NULL
                ORDER BY market_cap_rank
                LIMIT 15
            """)
            
            top_assets = cursor.fetchall()
            
            print(f"\n   📋 Top assets ready for collection:")
            print("      Symbol | CoinGecko ID | Name")
            print("      -------|--------------|-----")
            
            for symbol, cg_id, name in top_assets:
                symbol_display = symbol or "NULL"
                cg_id_display = cg_id[:12] if cg_id else "NULL"
                name_display = (name[:12] + "...") if name and len(name) > 12 else (name or "NULL")
                print(f"      {symbol_display:>6} | {cg_id_display:>12} | {name_display}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def trigger_new_collection():
    """Suggest triggering a new collection to test the fixes"""
    
    print(f"\n🚀 READY FOR NEW COLLECTION TEST:")
    print("-" * 40)
    
    print("   📝 Command to test collection:")
    print("   kubectl exec unified-ohlc-collector-<pod-id> -n crypto-collectors \\")
    print("     -- python -c \"import requests; \\")
    print("     response = requests.post('http://localhost:8010/collect', \\")
    print("     json={'days': 1, 'skip_existing': False, 'force_update': True}); \\")
    print("     print('Status:', response.status_code); \\")
    print("     print('Response:', response.text)\"")
    
    print(f"\n   🎯 Expected improvements:")
    print("   • More assets successfully collected")
    print("   • Better success rate than previous 70.8%")
    print("   • Major USD pairs like ETH-USD, BTC-USD working")
    print("   • Coverage closer to 100+ assets")

if __name__ == "__main__":
    fix_incorrect_mappings()
    show_final_coverage()
    trigger_new_collection()
    
    print(f"\n" + "="*50)
    print("🎯 SUMMARY:")
    print("✅ Fixed incorrect CoinGecko ID mappings")
    print("✅ Database now has better quality asset mappings")
    print("⚡ Ready to test collection with improved data")
    print("="*50)