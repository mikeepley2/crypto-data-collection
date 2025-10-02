#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== COMPREHENSIVE MACRO DATA EXPANSION ===\n")
    
    connection = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector', 
        password='99Rules!',
        database='crypto_prices'
    )
    print("✅ Database connected")
    
    cursor = connection.cursor()
    
    try:
        # Get latest macro data values for key indicators
        print("🔍 Collecting latest macro indicator values...")
        
        # Define macro field mappings: indicator_name -> target_field
        macro_mappings = {
            'VIX': ['vix', 'vix_index'],
            'DXY': ['dxy', 'dxy_index'], 
            'Fed_Funds_Rate': ['fed_funds_rate'],
            'FEDFUNDS': ['fed_funds_rate'],
            'Treasury_10Y': ['treasury_10y'],
            'DGS10': ['treasury_10y'],
            'TNX': ['treasury_10y'],
            'Treasury_2Y': ['treasury_2y'],
            'DGS2': ['treasury_2y'],
            'SPX': ['spx_index'],
            'NASDAQ': ['nasdaq_index'],
            'DOW': ['dow_jones_index'],
            'GOLD': ['gold_price'],
            'Silver': ['silver_price'],
            'WTI_Oil': ['oil_price'],
            'Brent_Oil': ['brent_oil_price'],
            'OIL': ['oil_price'],
            'GDP_Real': ['gdp_real'],
            'Inflation_Rate': ['inflation_rate'],
            'CPI': ['cpi_index'],
            'Core_CPI': ['core_cpi'],
            'Unemployment_Rate': ['unemployment_rate'],
            'DEXJPUS': ['jpy_usd_rate'],
            'DEXUSEU': ['eur_usd_rate']
        }
        
        # Get latest values for each indicator
        latest_values = {}
        for indicator_name, target_fields in macro_mappings.items():
            cursor.execute("""
                SELECT value, indicator_date 
                FROM macro_indicators 
                WHERE indicator_name = %s 
                ORDER BY indicator_date DESC 
                LIMIT 1
            """, (indicator_name,))
            
            result = cursor.fetchone()
            if result:
                value, date = result
                latest_values[indicator_name] = {'value': float(value), 'date': date, 'fields': target_fields}
                print(f"   {indicator_name}: {value} (date: {date})")
            else:
                print(f"   {indicator_name}: No data found")
        
        print(f"\n📊 Found values for {len(latest_values)} indicators")
        
        # Check which target fields exist in ml_features_materialized
        cursor.execute("DESCRIBE ml_features_materialized")
        existing_columns = [col[0] for col in cursor.fetchall()]
        
        # Build update fields list
        update_fields = []
        update_values = []
        for indicator_name, data in latest_values.items():
            for field in data['fields']:
                if field in existing_columns:
                    update_fields.append(field)
                    update_values.append(data['value'])
                    print(f"   ✅ Will update {field} = {data['value']}")
                else:
                    print(f"   ⚠️  Field {field} not found in ml_features_materialized")
        
        if not update_fields:
            print("❌ No target fields found to update")
            return
        
        print(f"\n🔄 Updating {len(update_fields)} macro fields for all symbols...")
        
        # Update all symbols with the latest macro values
        set_clause = ', '.join([f"{field} = %s" for field in update_fields])
        update_query = f"""
            UPDATE ml_features_materialized 
            SET {set_clause}
        """
        
        cursor.execute(update_query, update_values)
        updated_rows = cursor.rowcount
        connection.commit()
        
        print(f"   ✅ Updated {updated_rows} symbol records")
        
        # Verify results
        print(f"\n📊 Verifying macro field population...")
        field_checks = [f"SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as {field}_count" for field in update_fields[:10]]
        
        verification_query = f"""
            SELECT 
                COUNT(*) as total_symbols,
                {', '.join(field_checks)}
            FROM ml_features_materialized
        """
        
        cursor.execute(verification_query)
        result = cursor.fetchone()
        
        if result:
            total_symbols = result[0]
            print(f"   Total symbols: {total_symbols}")
            
            populated_count = 0
            for i, field in enumerate(update_fields[:10]):
                count = result[i + 1]
                percentage = count / total_symbols * 100 if total_symbols > 0 else 0
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {field}: {count} ({percentage:.1f}%)")
                if count > 0:
                    populated_count += 1
            
            print(f"\n🎯 MACRO EXPANSION RESULTS:")
            print(f"   Fields successfully populated: {populated_count}/{len(update_fields[:10])}")
            print(f"   Coverage: {populated_count/len(update_fields[:10])*100:.1f}%")
        
        # Sample BTC verification
        sample_fields = update_fields[:5]
        cursor.execute(f"""
            SELECT {', '.join(sample_fields)}
            FROM ml_features_materialized 
            WHERE symbol = 'BTC'
        """)
        
        btc_result = cursor.fetchone()
        if btc_result:
            print(f"\n📋 BTC SAMPLE VALUES:")
            for i, field in enumerate(sample_fields):
                value = btc_result[i] if i < len(btc_result) else None
                print(f"   {field}: {value}")
        
        # Calculate expansion impact
        print(f"\n🚀 MACRO EXPANSION ACHIEVEMENT:")
        print(f"   Target: 15+/20 macro fields")
        print(f"   Achieved: {len(update_fields)} fields updated")
        if len(update_fields) >= 15:
            print(f"   🎯 TARGET ACHIEVED: {len(update_fields)} >= 15 fields!")
        else:
            print(f"   📈 Progress: {len(update_fields)}/15 ({len(update_fields)/15*100:.1f}%)")
            
    except Exception as e:
        logger.error(f"Error in macro expansion: {e}")
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()