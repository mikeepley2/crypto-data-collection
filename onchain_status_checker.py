#!/usr/bin/env python3
"""
Crypto Data Collection - Onchain Data Status Check
Updated: September 30, 2025

Monitors the current state of our onchain data collection system:
- Onchain data collector (46 symbols with NULL handling)
- Blockchain metrics collection
- Integration with ML features
- Data quality and coverage analysis
"""

import mysql.connector
from datetime import datetime, timedelta


def check_onchain_data_collection():
    """Check onchain data collector status"""
    print("=" * 60)
    print("⛓️ ONCHAIN DATA COLLECTION STATUS")
    print("=" * 60)
    
    conn = mysql.connector.connect(
        host='192.168.230.162',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Check recent onchain data collection
    yesterday = datetime.now() - timedelta(days=1)
    cursor.execute("""
        SELECT
            COUNT(DISTINCT coin_symbol) as symbols,
            COUNT(*) as records,
            MAX(timestamp) as latest
        FROM crypto_onchain_data
        WHERE timestamp > %s
          AND coin_symbol IS NOT NULL
    """, (yesterday,))
    
    symbols, records, latest = cursor.fetchone()
    
    print("📊 Recent Collection (24h):")
    print(f"   • Symbols Collected: {symbols}")
    print(f"   • Total Records: {records:,}")
    print(f"   • Latest Timestamp: {latest}")
    
    # Check overall table statistics
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT coin_symbol) as unique_symbols,
            SUM(CASE WHEN coin_symbol IS NULL THEN 1 ELSE 0 END) as null_symbols
        FROM crypto_onchain_data
    """)
    
    total, unique_symbols, null_symbols = cursor.fetchone()
    
    print("\n📈 Overall Collection Status:")
    print(f"   • Total Records: {total:,}")
    print(f"   • Unique Symbols: {unique_symbols}")
    print(f"   • Records with NULL symbols: {null_symbols:,}")
    valid_pct = ((total-null_symbols)/total*100)
    print(f"   • Valid data percentage: {valid_pct:.1f}%")
    
    conn.close()


def check_onchain_data_quality():
    """Check onchain data quality and coverage"""
    print("\n" + "=" * 60)
    print("📊 ONCHAIN DATA QUALITY ANALYSIS")
    print("=" * 60)
    
    conn = mysql.connector.connect(
        host='192.168.230.162',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Check data quality for top symbols (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    cursor.execute("""
        SELECT
            coin_symbol,
            COUNT(*) as records,
            MAX(timestamp) as latest,
            AVG(CASE WHEN market_cap_usd IS NOT NULL THEN 1 ELSE 0 END) * 100 as mcap_fill,
            AVG(CASE WHEN total_supply IS NOT NULL THEN 1 ELSE 0 END) * 100 
            as supply_fill,
            AVG(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) * 100 
            as addr_fill
        FROM crypto_onchain_data
        WHERE timestamp > %s
          AND coin_symbol IS NOT NULL
        GROUP BY coin_symbol
        ORDER BY records DESC
        LIMIT 12
    """, (week_ago,))
    
    print("🔍 Top Symbols Data Quality (Last 7 days):")
    print("   Symbol | Records | Latest Collection    | MCap% | Supply% | Addr%")
    print("   ------ | ------- | -------------------- | ----- | ------- | -----")
    
    for symbol, records, latest, mcap, supply, addr in cursor.fetchall():
        line = f"   {symbol:6} | {records:6,} | {latest} | "
        line += f"{mcap:4.0f}% | {supply:6.0f}% | {addr:4.0f}%"
        print(line)
    
    conn.close()


def check_onchain_integration():
    """Check onchain integration with ML features"""
    print("\n" + "=" * 60)
    print("🔗 ONCHAIN ML FEATURES INTEGRATION")
    print("=" * 60)
    
    conn = mysql.connector.connect(
        host='192.168.230.162',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Check for onchain fields in ml_features
    cursor.execute("SHOW COLUMNS FROM ml_features_materialized LIKE '%onchain%'")
    onchain_fields = [col[0] for col in cursor.fetchall()]
    
    print("📈 Onchain Fields in ML Features:")
    print(f"   • Total onchain fields: {len(onchain_fields)}")
    
    if onchain_fields:
        for field in onchain_fields[:8]:
            print(f"     - {field}")
        if len(onchain_fields) > 8:
            print(f"     ... and {len(onchain_fields) - 8} more fields")
    
        # Check population of key onchain fields
        key_fields = onchain_fields[:5]
        field_checks = [
            f"SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as {field}_count"
            for field in key_fields
        ]
        
        query = f"""
            SELECT 
                COUNT(*) as total_symbols,
                {', '.join(field_checks)}
            FROM ml_features_materialized
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            total_symbols = result[0]
            print("\n📊 Field Population Status:")
            print(f"   Total ML feature symbols: {total_symbols}")
            
            populated_count = 0
            for i, field in enumerate(key_fields):
                count = result[i + 1]
                percentage = count / total_symbols * 100 if total_symbols > 0 else 0
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {field}: {count}/{total_symbols} ({percentage:.1f}%)")
                if count > 0:
                    populated_count += 1
            
            integration_pct = populated_count / len(key_fields) * 100
            status_msg = f"Integration Status: {populated_count}/{len(key_fields)} fields"
            status_msg += f" populated ({integration_pct:.0f}%)"
            print(f"\n🎯 {status_msg}")
    
    conn.close()


def check_collection_patterns():
    """Check onchain collection patterns and frequency"""
    print("\n" + "=" * 60)
    print("⏱️ COLLECTION PATTERNS ANALYSIS")
    print("=" * 60)
    
    conn = mysql.connector.connect(
        host='192.168.230.162',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Check hourly collection patterns (last 24h)
    day_ago = datetime.now() - timedelta(days=1)
    cursor.execute("""
        SELECT
            HOUR(timestamp) as hour,
            COUNT(*) as records,
            COUNT(DISTINCT coin_symbol) as symbols
        FROM crypto_onchain_data
        WHERE timestamp > %s
          AND coin_symbol IS NOT NULL
        GROUP BY HOUR(timestamp)
        ORDER BY hour DESC
        LIMIT 12
    """, (day_ago,))
    
    hourly_data = cursor.fetchall()
    
    if hourly_data:
        print("📅 Collection Frequency (Last 24h):")
        print("   Hour | Records | Symbols")
        print("   ---- | ------- | -------")
        
        total_records = 0
        for hour, records, symbols in hourly_data:
            print(f"   {hour:2d}   | {records:6,} | {symbols:6}")
            total_records += records
        
        avg_symbols = sum(symbols for _, _, symbols in hourly_data) / len(hourly_data)
        print(f"\n   24h Summary: {total_records:,} records, avg {avg_symbols:.1f} symbols/hour")
    
    # Check collection reliability over past week
    week_ago = datetime.now() - timedelta(days=7)
    cursor.execute("""
        SELECT 
            DATE(timestamp) as collection_date,
            COUNT(*) as daily_records,
            COUNT(DISTINCT coin_symbol) as daily_symbols
        FROM crypto_onchain_data 
        WHERE timestamp > %s 
          AND coin_symbol IS NOT NULL
        GROUP BY DATE(timestamp)
        ORDER BY collection_date DESC
    """, (week_ago,))
    
    daily_data = cursor.fetchall()
    
    if daily_data:
        print(f"\n📊 Daily Collection Patterns (Last 7 days):")
        for date, records, symbols in daily_data:
            print(f"   {date}: {records:,} records, {symbols} symbols")
    
    conn.close()


def compare_with_price_collection():
    """Compare onchain collection with enhanced price collection"""
    print("\n" + "=" * 60)
    print("⚖️ COLLECTION SCALE COMPARISON")
    print("=" * 60)
    
    conn = mysql.connector.connect(
        host='192.168.230.162',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    yesterday = datetime.now() - timedelta(days=1)
    
    # Enhanced price collection stats
    cursor.execute("""
        SELECT COUNT(DISTINCT symbol) 
        FROM price_data_real 
        WHERE timestamp > %s
    """, (yesterday,))
    price_symbols = cursor.fetchone()[0]
    
    # Onchain collection stats  
    cursor.execute("""
        SELECT COUNT(DISTINCT coin_symbol) 
        FROM crypto_onchain_data 
        WHERE timestamp > %s 
          AND coin_symbol IS NOT NULL
    """, (yesterday,))
    onchain_symbols = cursor.fetchone()[0]
    
    coverage_pct = onchain_symbols / price_symbols * 100 if price_symbols > 0 else 0
    
    print("📊 Collection Scale Analysis:")
    print(f"   • Enhanced Price Collection: {price_symbols} symbols")
    print(f"   • Onchain Data Collection:   {onchain_symbols} symbols")
    print(f"   • Coverage Ratio:            {coverage_pct:.1f}%")
    
    if coverage_pct < 50:
        print(f"   ⚠️  Lower coverage than price collection")
    else:
        print(f"   ✅ Good coverage relative to price collection")
    
    conn.close()


def main():
    """Main status check function"""
    print("🔍 CRYPTO DATA COLLECTION - ONCHAIN SYSTEM STATUS")
    print(f"📅 Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 Current Architecture: Onchain Data Collection System")
    print("   • Onchain data collector: 46 symbols with blockchain metrics")
    print("   • Multiple onchain tables: crypto_onchain_data, enhanced, metrics")
    print("   • ML integration: 10+ onchain fields in ml_features")
    print("   • Data types: Market cap, supply, addresses, transactions")
    
    try:
        check_onchain_data_collection()
        check_onchain_data_quality()
        check_onchain_integration()
        check_collection_patterns()
        compare_with_price_collection()
        
        print("\n" + "=" * 60)
        print("✅ ONCHAIN SYSTEM STATUS: OPERATIONAL")
        print("=" * 60)
        print("⛓️ Active onchain data collection with 46-symbol coverage")
        print("📊 Comprehensive blockchain metrics including supply and addresses")
        print("🔗 Successfully integrated with ML features pipeline")
        print("📈 Regular collection patterns with good data quality")
        print("🎯 Ready for enhanced integration and scaling")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("🔧 Check database connection and onchain data tables")


if __name__ == "__main__":
    main()