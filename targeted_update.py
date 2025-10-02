#!/usr/bin/env python3
import mysql.connector
from datetime import datetime, timedelta

def run_targeted_materialized_update():
    """Run a targeted update focusing on fixing the specific data gaps we identified"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== TARGETED MATERIALIZED UPDATE ===\n")
    
    # Get latest BTC price records
    cursor.execute("""
        SELECT * FROM price_data 
        WHERE symbol = 'BTC' 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        ORDER BY timestamp DESC 
        LIMIT 3
    """)
    
    price_records = cursor.fetchall()
    print(f"📊 Processing {len(price_records)} recent BTC price records")
    
    for price_record in price_records:
        timestamp_iso = price_record['timestamp']
        current_price = price_record['close']
        
        print(f"\n🔄 Processing {timestamp_iso}")
        
        # Build the record with OHLC data from price_data
        record = {
            'symbol': 'BTC',
            'price_date': timestamp_iso.date(),
            'price_hour': timestamp_iso.hour,
            'timestamp_iso': timestamp_iso,
            'current_price': current_price,
            'open_price': price_record['open'],
            'high_price': price_record['high'], 
            'low_price': price_record['low'],
            'close_price': price_record['close'],
            'ohlc_volume': price_record['volume'],
            'volume_24h': price_record['volume'],
            'market_cap': price_record['market_cap_usd'],
            'price_change_24h': price_record['price_change_24h'],
            'price_change_percentage_24h': price_record.get('percent_change_24h'),
            'ohlc_source': 'price_data'
        }
        
        # Try to get technical indicators (handle NULL timestamp issue)
        tech_cursor = conn.cursor(dictionary=True)
        # Use created_at or updated_at instead of timestamp if timestamp is NULL
        tech_cursor.execute("""
            SELECT rsi_14, sma_20, sma_50, ema_12, ema_26, macd_line, macd_signal, macd_histogram, vwap
            FROM technical_indicators 
            WHERE symbol = 'BTC' 
            AND (
                (timestamp IS NOT NULL AND DATE(timestamp) = %s) OR
                (timestamp IS NULL AND DATE(created_at) = %s)
            )
            ORDER BY 
                CASE WHEN timestamp IS NOT NULL THEN timestamp ELSE created_at END DESC
            LIMIT 1
        """, (timestamp_iso.date(), timestamp_iso.date()))
        
        tech_data = tech_cursor.fetchone()
        if tech_data:
            record.update({
                'rsi_14': tech_data['rsi_14'],
                'sma_20': tech_data['sma_20'],
                'sma_50': tech_data['sma_50'],
                'ema_12': tech_data['ema_12'],
                'ema_26': tech_data['ema_26'],
                'macd_line': tech_data['macd_line'],
                'macd_signal': tech_data['macd_signal'],
                'macd_histogram': tech_data['macd_histogram'],
                'vwap': tech_data['vwap']
            })
            print(f"  ✅ Technical indicators: RSI={tech_data['rsi_14']}")
        else:
            print(f"  ❌ No technical indicators found")
        
        # Get macro data
        macro_cursor = conn.cursor(dictionary=True)
        macro_cursor.execute("""
            SELECT indicator_name, value
            FROM macro_indicators
            WHERE indicator_name IN ('VIX', 'SPX') 
            AND indicator_date = %s
        """, (timestamp_iso.date(),))
        
        macro_data = macro_cursor.fetchall()
        if macro_data:
            for macro_row in macro_data:
                if macro_row['indicator_name'] == 'VIX':
                    record['vix'] = macro_row['value']
                elif macro_row['indicator_name'] == 'SPX':
                    record['spx'] = macro_row['value']
            print(f"  ✅ Macro data: VIX={record.get('vix')}, SPX={record.get('spx')}")
        else:
            print(f"  ❌ No macro data found")
        
        # Insert or update the record
        upsert_cursor = conn.cursor()
        
        # Check if record exists
        upsert_cursor.execute("""
            SELECT id FROM ml_features_materialized 
            WHERE symbol = %s AND price_date = %s AND price_hour = %s
        """, (record['symbol'], record['price_date'], record['price_hour']))
        
        existing = upsert_cursor.fetchone()
        
        if existing:
            # Update existing record
            set_fields = []
            values = []
            for key, value in record.items():
                if key not in ['symbol', 'price_date', 'price_hour']:
                    set_fields.append(f"{key} = %s")
                    values.append(value)
            
            if set_fields:
                update_sql = f"""
                    UPDATE ml_features_materialized 
                    SET {', '.join(set_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = %s AND price_date = %s AND price_hour = %s
                """
                values.extend([record['symbol'], record['price_date'], record['price_hour']])
                upsert_cursor.execute(update_sql, values)
                print(f"  ✅ Updated existing record")
        else:
            # Insert new record
            columns = list(record.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            values = list(record.values())
            
            insert_sql = f"""
                INSERT INTO ml_features_materialized ({', '.join(columns)}) 
                VALUES ({placeholders})
            """
            upsert_cursor.execute(insert_sql, values)
            print(f"  ✅ Inserted new record")
        
        conn.commit()
    
    # Now check our improvement
    print(f"\n🎯 CHECKING IMPROVEMENTS...")
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    btc_record = cursor.fetchone()
    
    if btc_record:
        populated = len([col for col, val in btc_record.items() if val is not None])
        total = len(btc_record)
        rate = (populated / total) * 100
        
        print(f"📈 IMPROVEMENT: BTC now has {populated}/{total} columns populated ({rate:.1f}%)")
        print(f"   Price fields: current={btc_record.get('current_price')}, open={btc_record.get('open_price')}")
        print(f"   Technical: rsi_14={btc_record.get('rsi_14')}, sma_20={btc_record.get('sma_20')}")  
        print(f"   Macro: vix={btc_record.get('vix')}, spx={btc_record.get('spx')}")
    
    conn.close()

if __name__ == "__main__":
    run_targeted_materialized_update()