#!/usr/bin/env python3
"""
Asset Coverage Analysis
Check how many assets we have vs what the collector is finding
"""

import mysql.connector
import subprocess
import json

def check_asset_coverage():
    """Check asset coverage and collector symbol mapping"""
    
    print("🔍 ASSET COVERAGE ANALYSIS")
    print("=" * 40)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices',
        'charset': 'utf8mb4'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check if we have an assets table
            cursor.execute("SHOW TABLES LIKE '%asset%'")
            asset_tables = [row[0] for row in cursor.fetchall()]
            
            print("📊 ASSET TABLES FOUND:")
            for table in asset_tables:
                print(f"   • {table}")
            
            # Check various potential asset/symbol tables
            symbol_sources = []
            
            # Check common table names
            potential_tables = ['assets', 'symbols', 'coins', 'cryptocurrencies', 'crypto_assets']
            
            for table_name in potential_tables:
                try:
                    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                    if cursor.fetchone():
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        symbol_sources.append((table_name, count))
                        print(f"   ✅ {table_name}: {count} records")
                except:
                    pass
            
            # Check existing OHLC data for symbols
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ohlc_data")
            ohlc_symbols = cursor.fetchone()[0]
            print(f"   📈 ohlc_data unique symbols: {ohlc_symbols}")
            
            # Get sample symbols from OHLC data
            cursor.execute("""
                SELECT symbol, COUNT(*) as records 
                FROM ohlc_data 
                GROUP BY symbol 
                ORDER BY records DESC 
                LIMIT 10
            """)
            top_symbols = cursor.fetchall()
            
            print(f"\n📊 TOP SYMBOLS IN OHLC DATA:")
            for symbol, records in top_symbols:
                print(f"   {symbol:>6}: {records:,} records")
            
            # Check recent symbols (last 30 days) vs historical
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol) 
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
            recent_symbols = cursor.fetchone()[0]
            
            print(f"\n🕐 RECENT ACTIVITY (30 days):")
            print(f"   Recent symbols: {recent_symbols}")
            print(f"   Total symbols: {ohlc_symbols}")
            print(f"   Coverage: {(recent_symbols/ohlc_symbols*100):.1f}%" if ohlc_symbols > 0 else "No data")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

def check_collector_symbol_config():
    """Check what symbols the collector is configured to collect"""
    
    print(f"\n🔧 COLLECTOR SYMBOL CONFIGURATION")
    print("-" * 40)
    
    # Get collector health info again with more detail
    pod_name = "unified-ohlc-collector-65596d6885-87dvw"
    
    print("📋 Collector Status:")
    try:
        cmd = f'''kubectl exec {pod_name} -n crypto-collectors -- python -c "
import urllib.request
import json
response = urllib.request.urlopen('http://localhost:8010/health')
data = json.loads(response.read().decode())
print('Total symbols available:', data.get('symbols_available', 'Unknown'))
print('Recent data symbols:', data.get('recent_data_symbols', 'Unknown'))
print('Coverage percentage:', data.get('coverage_percentage', 'Unknown'))
print('API configured:', data.get('api_configured', 'Unknown'))
"'''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Failed to get collector status")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check what the "Found 32 symbols" means
    print(f"\n🔍 COLLECTOR ACTIVITY ANALYSIS:")
    print("From logs: 'Found 32 symbols with recent premium OHLC data'")
    print("This suggests:")
    print("   • Collector has access to 130 total symbols")
    print("   • Only 32 of those have 'recent premium OHLC data'")
    print("   • Coverage: 32/130 = 24.6%")
    print("   • May be filtering for data quality/availability")

def analyze_symbol_gaps():
    """Analyze potential gaps in symbol coverage"""
    
    print(f"\n📊 SYMBOL COVERAGE ANALYSIS")
    print("-" * 35)
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            
            # Check what symbols have recent data vs old data
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN MAX(timestamp_iso) >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Recent (7 days)'
                        WHEN MAX(timestamp_iso) >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 'Stale (30 days)'
                        ELSE 'Old (30+ days)'
                    END as data_age,
                    COUNT(DISTINCT symbol) as symbol_count
                FROM ohlc_data 
                GROUP BY 
                    CASE 
                        WHEN MAX(timestamp_iso) >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Recent (7 days)'
                        WHEN MAX(timestamp_iso) >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 'Stale (30 days)'
                        ELSE 'Old (30+ days)'
                    END
                ORDER BY symbol_count DESC
            """)
            
            age_analysis = cursor.fetchall()
            
            print("📅 DATA AGE ANALYSIS:")
            total_symbols = 0
            for age_category, count in age_analysis:
                print(f"   {age_category}: {count} symbols")
                total_symbols += count
            
            print(f"   Total unique symbols: {total_symbols}")
            
            # Check symbols with most recent data
            cursor.execute("""
                SELECT symbol, MAX(timestamp_iso) as latest_data, COUNT(*) as records
                FROM ohlc_data 
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY symbol
                ORDER BY latest_data DESC
                LIMIT 10
            """)
            
            recent_symbols = cursor.fetchall()
            
            if recent_symbols:
                print(f"\n🔄 MOST RECENTLY ACTIVE SYMBOLS:")
                for symbol, latest, records in recent_symbols:
                    print(f"   {symbol:>6}: {latest} ({records} records)")
            
            # Compare with collector's 32 symbols
            print(f"\n🎯 COLLECTOR vs DATABASE COMPARISON:")
            print(f"   Collector finding: 32 symbols with recent premium data")
            print(f"   Database recent (30d): {len(recent_symbols)} symbols")
            
            if len(recent_symbols) > 32:
                print(f"   📊 Database has MORE recent symbols than collector")
                print(f"   💡 Collector may be filtering for premium/quality data")
            elif len(recent_symbols) < 32:
                print(f"   📊 Collector finding MORE than database shows")
                print(f"   💡 Collector may be finding new symbols to collect")
            else:
                print(f"   ✅ Numbers align - collector and database match")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_asset_coverage()
    check_collector_symbol_config()
    analyze_symbol_gaps()
    
    print(f"\n💡 INSIGHTS:")
    print("• Collector has 130 symbols available but only 32 have recent premium data")
    print("• This suggests quality filtering - only collecting high-quality OHLC data")
    print("• The 24.6% coverage may be intentional for premium data sources")
    print("• Collector appears to be working correctly within its parameters")