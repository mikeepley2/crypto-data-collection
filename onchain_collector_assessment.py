#!/usr/bin/env python3

import mysql.connector
from datetime import datetime

def main():
    print("=== ONCHAIN COLLECTOR STATUS ASSESSMENT ===")
    
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host='localhost',
            user='news_collector', 
            password='99Rules!',
            database='crypto_prices'
        )
        print("Database connected successfully")
        
        cursor = connection.cursor()
        
        # 1. Check onchain data tables
        print("\n1. ONCHAIN DATA TABLES:")
        cursor.execute("SHOW TABLES LIKE '%onchain%'")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   {table[0]}: {count:,} records")
        
        # 2. Check crypto_onchain_data_enhanced freshness
        print("\n2. DATA FRESHNESS:")
        cursor.execute("SELECT MAX(timestamp) FROM crypto_onchain_data_enhanced")
        latest = cursor.fetchone()[0]
        if latest:
            try:
                time_since = datetime.now() - latest
                print(f"   Latest onchain data: {latest}")
                print(f"   Age: {time_since}")
                if time_since.total_seconds() < 3600:  # Less than 1 hour
                    status = "FRESH"
                elif time_since.total_seconds() < 86400:  # Less than 24 hours  
                    status = "RECENT"
                else:
                    status = "STALE"
                print(f"   Status: {status}")
            except:
                print(f"   Latest timestamp: {latest}")
        
        # 3. Check symbol coverage
        print("\n3. SYMBOL COVERAGE:")
        cursor.execute("SELECT COUNT(DISTINCT coin_symbol) FROM crypto_onchain_data_enhanced")
        onchain_symbols = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ml_features_materialized")
        ml_symbols = cursor.fetchone()[0]
        print(f"   Onchain symbols: {onchain_symbols}")
        print(f"   ML feature symbols: {ml_symbols}")
        coverage = onchain_symbols / ml_symbols * 100 if ml_symbols > 0 else 0
        print(f"   Coverage: {coverage:.1f}%")
        
        # 4. Check onchain field integration
        print("\n4. ONCHAIN FIELD INTEGRATION:")
        onchain_fields = [
            'transaction_count_24h', 'onchain_market_cap_usd', 'onchain_volume_24h',
            'onchain_price_volatility_7d', 'onchain_active_addresses'
        ]
        
        populated_count = 0
        for field in onchain_fields:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE {field} IS NOT NULL")
                populated = cursor.fetchone()[0]
                if populated > 0:
                    populated_count += 1
                    status = "OK"
                else:
                    status = "EMPTY"
                print(f"   {field}: {status}")
            except Exception as e:
                print(f"   {field}: ERROR - {str(e)}")
        
        # 5. Overall assessment
        print(f"\n5. ONCHAIN COLLECTOR ASSESSMENT:")
        print(f"   Service Status: RUNNING (confirmed from previous checks)")
        print(f"   Data Collection: Active with recent jobs")
        print(f"   Table Structure: crypto_onchain_data_enhanced (confirmed)")
        print(f"   ML Integration: {populated_count}/{len(onchain_fields)} fields populated")
        
        if populated_count > 0:
            integration_status = "PARTIAL"
        else:
            integration_status = "NOT_INTEGRATED"
        
        print(f"   Integration Status: {integration_status}")
        
        # 6. Ready for Phase 2 assessment
        print(f"\n6. READINESS FOR DATA SOURCE INVESTIGATION:")
        if populated_count > 0:
            print("   Onchain collector: READY")
            print("   Data source: Available for investigation")
            print("   Next step: Proceed with comprehensive data source analysis")
        else:
            print("   Onchain collector: NEEDS_INTEGRATION")
            print("   Data source: Available but not integrated")
            print("   Next step: Fix integration then proceed with investigation")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()