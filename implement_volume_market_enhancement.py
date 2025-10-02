#!/usr/bin/env python3
import mysql.connector

def implement_volume_market_enhancement():
    """Implement comprehensive volume/market data mapping"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== IMPLEMENTING VOLUME/MARKET DATA ENHANCEMENT ===\n")
    
    # Check available fields in price_data
    cursor.execute("DESCRIBE price_data")
    price_columns = {row['Field']: row['Type'] for row in cursor.fetchall()}
    print(f"📊 Available price_data columns: {len(price_columns)}")
    
    # Map available fields to materialized table fields
    field_mappings = {
        'volume': ['volume_24h', 'hourly_volume', 'total_volume_24h', 'ohlc_volume'],
        'market_cap_usd': ['market_cap', 'market_cap_usd', 'onchain_market_cap_usd'],
        'price_change_24h': ['price_change_24h'],
        'percent_change_24h': ['price_change_percentage_24h', 'percent_change_24h'],
        'percent_change_1h': ['percent_change_1h'],
        'percent_change_7d': ['percent_change_7d']
    }
    
    # Check which mappings we can implement
    available_mappings = {}
    for source_field, target_fields in field_mappings.items():
        if source_field in price_columns:
            available_mappings[source_field] = target_fields
            print(f"✅ {source_field} -> {target_fields}")
        else:
            print(f"❌ {source_field} not found in price_data")
    
    # Get recent BTC price records to enhance
    cursor.execute("""
        SELECT symbol, timestamp, volume, market_cap_usd, price_change_24h
        FROM price_data 
        WHERE symbol = 'BTC' 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    price_records = cursor.fetchall()
    print(f"\n🔄 Processing {len(price_records)} recent BTC records")
    
    for price_record in price_records:
        timestamp_iso = price_record['timestamp']
        print(f"\n📊 Processing {timestamp_iso}")
        
        # Build enhanced volume/market data
        volume_market_data = {}
        
        # Map volume data
        if price_record['volume']:
            volume_val = float(price_record['volume'])
            volume_market_data.update({
                'volume_24h': volume_val,
                'hourly_volume': volume_val,  # Use as proxy for hourly volume
                'total_volume_24h': volume_val,
                'volume_qty_24h': volume_val,
                'volume_24h_usd': volume_val
            })
            print(f"  💰 Volume mapping: {volume_val:.2f}")
        
        # Map market cap data
        if price_record['market_cap_usd']:
            market_cap_val = float(price_record['market_cap_usd'])
            volume_market_data.update({
                'market_cap': int(market_cap_val),
                'market_cap_usd': market_cap_val,
                'onchain_market_cap_usd': market_cap_val
            })
            print(f"  📈 Market cap mapping: ${market_cap_val:,.0f}")
        
        # Map price change data
        price_changes = {}
        if price_record['price_change_24h']:
            price_changes['price_change_24h'] = float(price_record['price_change_24h'])
        
        volume_market_data.update(price_changes)
        
        if price_changes:
            print(f"  📊 Price changes: 24h=${price_changes.get('price_change_24h'):.2f}")
        
        # Update the materialized record
        update_cursor = conn.cursor()
        
        # Check if record exists
        update_cursor.execute("""
            SELECT id FROM ml_features_materialized 
            WHERE symbol = %s AND price_date = %s AND price_hour = %s
        """, ('BTC', timestamp_iso.date(), timestamp_iso.hour))
        
        existing = update_cursor.fetchone()
        if existing:
            # Build update query
            set_clauses = []
            values = []
            
            for field, value in volume_market_data.items():
                if value is not None:
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            if set_clauses:
                update_sql = f"""
                    UPDATE ml_features_materialized 
                    SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = %s AND price_date = %s AND price_hour = %s
                """
                values.extend(['BTC', timestamp_iso.date(), timestamp_iso.hour])
                
                update_cursor.execute(update_sql, values)
                affected = update_cursor.rowcount
                print(f"  ✅ Updated {len(set_clauses)} fields ({affected} records affected)")
            else:
                print(f"  ⚠️  No non-null values to update")
        else:
            print(f"  ⚠️  No materialized record found")
        
        conn.commit()
    
    # Check our improvement
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        # Count volume/market fields that are now populated
        volume_market_fields = ['volume_24h', 'hourly_volume', 'market_cap', 'market_cap_usd', 'total_volume_24h',
                               'price_change_24h', 'price_change_percentage_24h', 'percent_change_1h', 
                               'percent_change_24h', 'percent_change_7d', 'volume_qty_24h', 'volume_24h_usd']
        
        populated_count = len([f for f in volume_market_fields if btc_record.get(f) is not None])
        total_populated = len([col for col, val in btc_record.items() if val is not None])
        total_cols = len(btc_record)
        rate = (total_populated / total_cols) * 100
        
        print(f"\n🎯 VOLUME/MARKET DATA ENHANCEMENT RESULTS:")
        print(f"   Volume/Market fields populated: {populated_count}/{len(volume_market_fields)}")
        print(f"   Overall population: {total_populated}/{total_cols} ({rate:.1f}%)")
        
        # Show sample values
        print(f"\n📋 SAMPLE VALUES:")
        sample_fields = ['volume_24h', 'market_cap_usd', 'price_change_24h', 'percent_change_24h']
        for field in sample_fields:
            value = btc_record.get(field)
            status = "✅" if value is not None else "❌"
            print(f"   {status} {field}: {value}")
    
    conn.close()

if __name__ == "__main__":
    implement_volume_market_enhancement()