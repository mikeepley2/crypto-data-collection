#!/usr/bin/env python3
"""
Check Asset Collection Coverage
Verify if OHLC collector is collecting for all assets in crypto_assets table
"""

import mysql.connector
from datetime import datetime, timedelta

def check_asset_coverage():
    """Check if OHLC collector is collecting for all assets in the database"""
    
    print("🔍 ASSET COLLECTION COVERAGE ANALYSIS")
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
            
            # Get all assets in crypto_assets table
            print("1️⃣ ASSETS IN CRYPTO_ASSETS TABLE:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_assets,
                    COUNT(CASE WHEN symbol IS NOT NULL THEN 1 END) as with_symbol,
                    COUNT(CASE WHEN coingecko_id IS NOT NULL THEN 1 END) as with_coingecko_id
                FROM crypto_assets
            """)
            
            total_assets, with_symbol, with_coingecko = cursor.fetchone()
            
            print(f"   📊 Total assets in table: {total_assets:,}")
            print(f"   🔤 Assets with symbol: {with_symbol:,}")
            print(f"   🆔 Assets with coingecko_id: {with_coingecko:,}")
            
            # Get sample of assets
            cursor.execute("""
                SELECT symbol, coingecko_id, name
                FROM crypto_assets 
                WHERE symbol IS NOT NULL 
                ORDER BY market_cap_rank
                LIMIT 10
            """)
            
            sample_assets = cursor.fetchall()
            
            print(f"\n   📋 Sample assets (top 10 by market cap):")
            print("      Symbol | CoinGecko ID | Name")
            print("      -------|--------------|-----")
            
            for symbol, cg_id, name in sample_assets:
                symbol_display = symbol or "NULL"
                cg_id_display = cg_id or "NULL"
                name_display = (name[:20] + "...") if name and len(name) > 20 else (name or "NULL")
                print(f"      {symbol_display:>6} | {cg_id_display:>12} | {name_display}")
            
            # Check which assets are being collected in OHLC
            print(f"\n2️⃣ ASSETS BEING COLLECTED IN OHLC:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT DISTINCT symbol
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY symbol
            """)
            
            collected_symbols = [row[0] for row in cursor.fetchall()]
            
            print(f"   📊 Assets collected in last 7 days: {len(collected_symbols)}")
            print(f"   🔤 Symbols: {', '.join(collected_symbols[:20])}")
            if len(collected_symbols) > 20:
                print(f"   ... and {len(collected_symbols) - 20} more")
            
            # Check which assets from crypto_assets are NOT being collected
            print(f"\n3️⃣ ASSETS NOT BEING COLLECTED:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT ca.symbol, ca.coingecko_id, ca.name
                FROM crypto_assets ca
                LEFT JOIN (
                    SELECT DISTINCT symbol 
                    FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ) od ON ca.symbol = od.symbol
                WHERE ca.symbol IS NOT NULL 
                AND od.symbol IS NULL
                ORDER BY ca.market_cap_rank
                LIMIT 20
            """)
            
            missing_assets = cursor.fetchall()
            
            print(f"   ❌ Assets in crypto_assets but NOT in OHLC: {len(missing_assets) if missing_assets else 0}")
            
            if missing_assets:
                print("   📋 Top missing assets by market cap:")
                print("      Symbol | CoinGecko ID | Name")
                print("      -------|--------------|-----")
                
                for symbol, cg_id, name in missing_assets[:10]:
                    symbol_display = symbol or "NULL"
                    cg_id_display = cg_id or "NULL"
                    name_display = (name[:20] + "...") if name and len(name) > 20 else (name or "NULL")
                    print(f"      {symbol_display:>6} | {cg_id_display:>12} | {name_display}")
            
            # Check if there's a pattern in what's being collected
            print(f"\n4️⃣ COLLECTION PATTERN ANALYSIS:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT 
                    ca.market_cap_rank,
                    ca.symbol,
                    ca.coingecko_id,
                    CASE WHEN od.symbol IS NOT NULL THEN 'COLLECTED' ELSE 'NOT COLLECTED' END as status
                FROM crypto_assets ca
                LEFT JOIN (
                    SELECT DISTINCT symbol 
                    FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ) od ON ca.symbol = od.symbol
                WHERE ca.symbol IS NOT NULL 
                AND ca.market_cap_rank IS NOT NULL
                ORDER BY ca.market_cap_rank
                LIMIT 50
            """)
            
            pattern_data = cursor.fetchall()
            
            collected_count = sum(1 for row in pattern_data if row[3] == 'COLLECTED')
            not_collected_count = sum(1 for row in pattern_data if row[3] == 'NOT COLLECTED')
            
            print(f"   📊 Top 50 assets by market cap:")
            print(f"   ✅ Collected: {collected_count}")
            print(f"   ❌ Not collected: {not_collected_count}")
            
            # Check for potential filtering criteria
            print(f"\n5️⃣ POTENTIAL FILTERING ANALYSIS:")
            print("-" * 40)
            
            # Check if only certain market cap ranks are collected
            cursor.execute("""
                SELECT 
                    MIN(ca.market_cap_rank) as min_rank,
                    MAX(ca.market_cap_rank) as max_rank,
                    AVG(ca.market_cap_rank) as avg_rank
                FROM crypto_assets ca
                JOIN (
                    SELECT DISTINCT symbol 
                    FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ) od ON ca.symbol = od.symbol
                WHERE ca.market_cap_rank IS NOT NULL
            """)
            
            rank_stats = cursor.fetchone()
            if rank_stats and rank_stats[0]:
                min_rank, max_rank, avg_rank = rank_stats
                print(f"   📈 Market cap rank of collected assets:")
                print(f"      Minimum rank: {min_rank}")
                print(f"      Maximum rank: {max_rank}")
                print(f"      Average rank: {avg_rank:.1f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_ohlc_data_sources():
    """Check what data sources are being used in OHLC collection"""
    
    print(f"\n6️⃣ DATA SOURCE ANALYSIS:")
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
            
            cursor.execute("""
                SELECT 
                    data_source,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    COUNT(*) as total_records,
                    MIN(timestamp_iso) as earliest,
                    MAX(timestamp_iso) as latest
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY data_source
            """)
            
            sources = cursor.fetchall()
            
            for source, symbols, records, earliest, latest in sources:
                print(f"   📊 {source}:")
                print(f"      Unique symbols: {symbols}")
                print(f"      Total records: {records:,}")
                print(f"      Time range: {earliest} to {latest}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def recommend_solution():
    """Recommend how to ensure all assets are collected"""
    
    print(f"\n7️⃣ RECOMMENDATIONS:")
    print("-" * 40)
    
    print("🎯 TO ENSURE ALL ASSETS ARE COLLECTED:")
    print("   1. ✅ Verify collector reads from crypto_assets table")
    print("   2. ✅ Remove any hardcoded symbol lists")
    print("   3. ✅ Check for market cap rank filters")
    print("   4. ✅ Ensure all symbols have valid coingecko_id")
    print("   5. ✅ Monitor collection coverage regularly")
    
    print(f"\n🔧 POTENTIAL ISSUES TO CHECK:")
    print("   • Hardcoded 'premium' symbol lists")
    print("   • Market cap rank filters (e.g., top 100 only)")
    print("   • Missing coingecko_id values")
    print("   • API rate limiting affecting coverage")
    print("   • Collection timeouts for large asset lists")

if __name__ == "__main__":
    check_asset_coverage()
    check_ohlc_data_sources()
    recommend_solution()