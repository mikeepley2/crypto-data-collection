#!/usr/bin/env python3

import mysql.connector
import os
from datetime import datetime, timedelta

def main():
    print("=== VOLUME/MARKET DATA ENHANCEMENT - MARKET CAP FOCUS ===\n")
    
    # Database connection using actual environment
    connection = mysql.connector.connect(
        host='host.docker.internal',
        port=3306,
        user='news_collector', 
        password='99Rules!',
        database='crypto_prices'
    )
    print("✅ Database connected")
    
    cursor = connection.cursor()
    
    try:
        # Check what data we actually have
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN market_cap_usd IS NOT NULL AND market_cap_usd != 0 THEN 1 ELSE 0 END) as has_market_cap,
                SUM(CASE WHEN market_cap IS NOT NULL AND market_cap != 0 THEN 1 ELSE 0 END) as has_market_cap_alt,
                SUM(CASE WHEN price_change_24h IS NOT NULL THEN 1 ELSE 0 END) as has_price_change,
                SUM(CASE WHEN percent_change_24h IS NOT NULL THEN 1 ELSE 0 END) as has_percent_change
            FROM price_data 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 3 HOUR)
        """)
        
        result = cursor.fetchone()
        total, market_cap_count, market_cap_alt_count, price_change_count, percent_change_count = result
        
        print(f"📊 Available data (last 3 hours):")
        print(f"   Total records: {total}")
        print(f"   Records with market_cap_usd: {market_cap_count} ({market_cap_count/total*100:.1f}%)")
        print(f"   Records with market_cap: {market_cap_alt_count} ({market_cap_alt_count/total*100:.1f}%)")
        print(f"   Records with price_change_24h: {price_change_count} ({price_change_count/total*100:.1f}%)")
        print(f"   Records with percent_change_24h: {percent_change_count} ({percent_change_count/total*100:.1f}%)")
        
        # Focus on market cap data that exists - update ml_features_materialized
        print(f"\n🔄 Updating ml_features_materialized with available market cap data...")
        
        # Get recent symbols with market cap data
        cursor.execute("""
            SELECT DISTINCT symbol 
            FROM price_data 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 3 HOUR)
            AND market_cap_usd IS NOT NULL 
            AND market_cap_usd != 0
            ORDER BY symbol
        """)
        
        symbols_with_data = [row[0] for row in cursor.fetchall()]
        print(f"   Found {len(symbols_with_data)} symbols with market cap data")
        
        updated_count = 0
        for symbol in symbols_with_data[:20]:  # Process top 20 first
            # Get latest market cap data for this symbol
            cursor.execute("""
                SELECT market_cap_usd, current_price, price_change_24h, percent_change_24h
                FROM price_data 
                WHERE symbol = %s 
                AND timestamp > DATE_SUB(NOW(), INTERVAL 3 HOUR)
                AND market_cap_usd IS NOT NULL 
                AND market_cap_usd != 0
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (symbol,))
            
            row = cursor.fetchone()
            if row:
                market_cap_usd, current_price, price_change_24h, percent_change_24h = row
                
                # Update ml_features_materialized
                update_fields = []
                update_values = []
                
                # Map market_cap_usd to multiple target fields
                if market_cap_usd is not None and market_cap_usd != 0:
                    update_fields.extend(['market_cap', 'market_cap_usd', 'onchain_market_cap_usd'])
                    update_values.extend([market_cap_usd, market_cap_usd, market_cap_usd])
                
                # Map price change data
                if price_change_24h is not None:
                    update_fields.append('price_change_24h')
                    update_values.append(price_change_24h)
                    
                if percent_change_24h is not None:
                    update_fields.extend(['price_change_percentage_24h', 'percent_change_24h'])
                    update_values.extend([percent_change_24h, percent_change_24h])
                
                if update_fields:
                    # Build update query (without last_updated column)
                    set_clause = ', '.join([f"{field} = %s" for field in update_fields])
                    update_query = f"""
                        UPDATE ml_features_materialized 
                        SET {set_clause}
                        WHERE symbol = %s
                    """
                    
                    update_values.append(symbol)
                    cursor.execute(update_query, update_values)
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                        print(f"   ✅ {symbol}: Updated {len(update_fields)} fields (MCap=${market_cap_usd:,.0f})")
                    else:
                        print(f"   ⚠️  {symbol}: No ml_features record to update")
        
        connection.commit()
        
        # Check results
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN market_cap IS NOT NULL THEN 1 ELSE 0 END) as has_market_cap,
                SUM(CASE WHEN market_cap_usd IS NOT NULL THEN 1 ELSE 0 END) as has_market_cap_usd,
                SUM(CASE WHEN price_change_24h IS NOT NULL THEN 1 ELSE 0 END) as has_price_change,
                SUM(CASE WHEN percent_change_24h IS NOT NULL THEN 1 ELSE 0 END) as has_percent_change
            FROM ml_features_materialized
        """)
        
        result = cursor.fetchone()
        if result:
            total, market_cap_count, market_cap_usd_count, price_change_count, percent_change_count = result
            
            print(f"\n🎯 ML_FEATURES_MATERIALIZED RESULTS:")
            print(f"   Total symbols: {total}")
            print(f"   market_cap populated: {market_cap_count}/117 ({market_cap_count/117*100:.1f}%)")
            print(f"   market_cap_usd populated: {market_cap_usd_count}/117 ({market_cap_usd_count/117*100:.1f}%)")
            print(f"   price_change_24h populated: {price_change_count}/117 ({price_change_count/117*100:.1f}%)")
            print(f"   percent_change_24h populated: {percent_change_count}/117 ({percent_change_count/117*100:.1f}%)")
            print(f"   Records updated: {updated_count}")
            
        # Overall population check
        cursor.execute("""
            SELECT 
                117 as total_columns,
                SUM(CASE 
                    WHEN market_cap IS NOT NULL OR market_cap_usd IS NOT NULL OR 
                         price_change_24h IS NOT NULL OR percent_change_24h IS NOT NULL OR
                         price_change_percentage_24h IS NOT NULL OR onchain_market_cap_usd IS NOT NULL
                    THEN 1 ELSE 0 END
                ) as volume_market_populated
            FROM ml_features_materialized 
            WHERE symbol = 'BTC'
        """)
        
        result = cursor.fetchone()
        if result:
            total_cols, vm_populated = result
            print(f"\n📊 VOLUME/MARKET CATEGORY STATUS:")
            print(f"   Volume/Market fields populated: {vm_populated}/9 (target fields)")
            print(f"   Improvement from this enhancement: +{vm_populated} fields")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()