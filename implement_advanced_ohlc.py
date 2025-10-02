#!/usr/bin/env python3
import mysql.connector

def implement_advanced_ohlc():
    """Implement advanced OHLC processing with multiple timeframe integration"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== IMPLEMENTING ADVANCED OHLC PROCESSING ===\n")
    
    # First, check available OHLC data sources
    cursor.execute("DESCRIBE ohlc_data")
    ohlc_columns = cursor.fetchall()
    print("📊 OHLC data table columns:")
    for col in ohlc_columns[:10]:  # First 10 columns
        print(f"   {col['Field']} ({col['Type']})")
    
    # Check ohlc_data availability
    cursor.execute("""
        SELECT symbol, COUNT(*) as records, MAX(created_at) as latest
        FROM ohlc_data 
        WHERE symbol = 'BTC'
        GROUP BY symbol
    """)
    
    ohlc_availability = cursor.fetchone()
    if ohlc_availability:
        print(f"\n📈 BTC OHLC data: {ohlc_availability['records']} records, latest: {ohlc_availability['latest']}")
    else:
        print(f"\n❌ No BTC OHLC data found in ohlc_data table")
    
    # Get recent BTC price records and enhance with OHLC data
    cursor.execute("""
        SELECT symbol, timestamp, open, high, low, close, volume
        FROM price_data 
        WHERE symbol = 'BTC' 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    price_records = cursor.fetchall()
    print(f"\n🔄 Processing {len(price_records)} recent BTC records for OHLC enhancement")
    
    for price_record in price_records:
        timestamp_iso = price_record['timestamp']
        print(f"\n📊 Processing {timestamp_iso}")
        
        # Enhanced OHLC data from multiple sources
        ohlc_data = {
            'open_price': price_record['open'],
            'high_price': price_record['high'], 
            'low_price': price_record['low'],
            'close_price': price_record['close'],
            'ohlc_volume': price_record['volume'],
            'ohlc_source': 'price_data'
        }
        
        print(f"  💰 Price data OHLC: O:{ohlc_data['open_price']} H:{ohlc_data['high_price']} L:{ohlc_data['low_price']} C:{ohlc_data['close_price']}")
        
        # Try to get additional OHLC data from ohlc_data table for different timeframes
        try:
            cursor.execute("""
                SELECT open, high, low, close, volume, timeframe
                FROM ohlc_data 
                WHERE symbol = %s 
                AND DATE(created_at) = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, ('BTC', timestamp_iso.date()))
            
            ohlc_result = cursor.fetchone()
            if ohlc_result:
                # Use ohlc_data as fallback or for validation
                print(f"  📈 OHLC table data: O:{ohlc_result['open']} H:{ohlc_result['high']} ({ohlc_result['timeframe']})")
                
                # If price_data has null values, use ohlc_data
                for field_map in [('open', 'open_price'), ('high', 'high_price'), ('low', 'low_price'), ('close', 'close_price')]:
                    ohlc_field, price_field = field_map
                    if ohlc_data[price_field] is None and ohlc_result[ohlc_field] is not None:
                        ohlc_data[price_field] = ohlc_result[ohlc_field]
                        ohlc_data['ohlc_source'] = 'ohlc_data_fallback'
                        print(f"    🔄 Using ohlc_data fallback for {price_field}")
            else:
                print(f"  📊 No OHLC table data for {timestamp_iso.date()}")
        except Exception as e:
            print(f"  ⚠️  OHLC table lookup failed: {e}")
        
        # Calculate additional OHLC-based metrics
        try:
            if all(ohlc_data[f] is not None for f in ['open_price', 'high_price', 'low_price', 'close_price']):
                open_val = float(ohlc_data['open_price'])
                high_val = float(ohlc_data['high_price'])
                low_val = float(ohlc_data['low_price'])
                close_val = float(ohlc_data['close_price'])
                
                # Calculate additional metrics
                daily_range = high_val - low_val
                daily_range_pct = (daily_range / open_val) * 100 if open_val > 0 else 0
                body_size = abs(close_val - open_val)
                body_pct = (body_size / daily_range) * 100 if daily_range > 0 else 0
                
                print(f"  📏 Daily range: {daily_range:.2f} ({daily_range_pct:.2f}%), Body: {body_pct:.1f}%")
                
                # Add calculated fields (if columns exist)
                ohlc_data.update({
                    'price_volatility_7d': daily_range_pct,  # Use daily range as proxy
                })
            else:
                print(f"  ⚠️  Incomplete OHLC data, skipping calculations")
        except Exception as e:
            print(f"  ⚠️  OHLC calculations failed: {e}")
        
        # Update the materialized record
        update_cursor = conn.cursor()
        
        # Check if record exists
        update_cursor.execute("""
            SELECT id FROM ml_features_materialized 
            WHERE symbol = %s AND price_date = %s AND price_hour = %s
        """, ('BTC', timestamp_iso.date(), timestamp_iso.hour))
        
        existing = update_cursor.fetchone()
        if existing:
            # Build update query for OHLC fields
            set_clauses = []
            values = []
            
            for field, value in ohlc_data.items():
                set_clauses.append(f"{field} = %s")
                values.append(value)
                
            update_sql = f"""
                UPDATE ml_features_materialized 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = %s AND price_date = %s AND price_hour = %s
            """
            values.extend(['BTC', timestamp_iso.date(), timestamp_iso.hour])
            
            update_cursor.execute(update_sql, values)
            affected = update_cursor.rowcount
            print(f"  ✅ Updated materialized record ({affected} affected)")
        else:
            print(f"  ⚠️  No materialized record found")
        
        conn.commit()
    
    # Check our improvement
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        # Count OHLC fields that are now populated
        ohlc_fields = ['open_price', 'high_price', 'low_price', 'close_price', 'ohlc_volume', 'ohlc_source']
        price_fields = ['current_price', 'volume_24h', 'market_cap', 'price_change_24h']
        
        ohlc_populated = len([f for f in ohlc_fields if btc_record.get(f) is not None])
        price_populated = len([f for f in price_fields if btc_record.get(f) is not None])
        
        total_populated = len([col for col, val in btc_record.items() if val is not None])
        total_cols = len(btc_record)
        rate = (total_populated / total_cols) * 100
        
        print(f"\n🎯 ADVANCED OHLC PROCESSING RESULTS:")
        print(f"   OHLC fields populated: {ohlc_populated}/{len(ohlc_fields)}")
        print(f"   Price fields populated: {price_populated}/{len(price_fields)}")
        print(f"   Overall population: {total_populated}/{total_cols} ({rate:.1f}%)")
        print(f"   OHLC source: {btc_record.get('ohlc_source')}")
        print(f"   Sample OHLC: O:{btc_record.get('open_price')} H:{btc_record.get('high_price')}")
    
    conn.close()

if __name__ == "__main__":
    implement_advanced_ohlc()