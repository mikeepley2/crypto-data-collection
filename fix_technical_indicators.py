#!/usr/bin/env python3
import mysql.connector

def fix_technical_indicators():
    """Fix technical indicators timestamp issue and generate fresh data"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    print("=== FIXING TECHNICAL INDICATORS ===\n")
    
    # First, diagnose the timestamp issue
    cursor.execute("""
        SELECT symbol, timestamp, created_at, rsi_14, sma_20, COUNT(*) as count
        FROM technical_indicators 
        WHERE symbol = 'BTC' 
        GROUP BY symbol, timestamp, created_at, rsi_14, sma_20
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    recent_tech = cursor.fetchall()
    print(f"🔍 Recent BTC technical indicators:")
    for row in recent_tech:
        ts_status = "NULL" if row['timestamp'] is None else str(row['timestamp'])
        print(f"  Created: {row['created_at']}, Timestamp: {ts_status}, RSI: {row['rsi_14']}, Count: {row['count']}")
    
    # Check if we can update NULL timestamps using created_at
    if recent_tech and recent_tech[0]['timestamp'] is None:
        print(f"\n🔧 FIXING NULL TIMESTAMPS...")
        
        # Update NULL timestamps to use created_at values
        cursor.execute("""
            UPDATE technical_indicators 
            SET timestamp = created_at 
            WHERE timestamp IS NULL 
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        updated_count = cursor.rowcount
        print(f"✅ Updated {updated_count} records with NULL timestamps")
        conn.commit()
    
    # Now test technical indicators integration
    print(f"\n🧪 TESTING TECHNICAL INDICATORS INTEGRATION...")
    
    # Get latest price record
    cursor.execute("""
        SELECT * FROM price_data 
        WHERE symbol = 'BTC' 
        ORDER BY timestamp DESC 
        LIMIT 1
    """)
    
    price_record = cursor.fetchone()
    if not price_record:
        print("❌ No price data found")
        return
        
    timestamp_iso = price_record['timestamp']
    print(f"📊 Latest price record: {timestamp_iso}")
    
    # Try to find matching technical indicators using both timestamp approaches
    cursor.execute("""
        SELECT rsi_14, sma_20, sma_50, ema_12, ema_26, macd_line, vwap, timestamp, created_at
        FROM technical_indicators 
        WHERE symbol = 'BTC' 
        AND (
            (timestamp IS NOT NULL AND DATE(timestamp) = %s) OR
            (timestamp IS NULL AND DATE(created_at) = %s) OR
            DATE(created_at) = %s
        )
        ORDER BY 
            CASE WHEN timestamp IS NOT NULL THEN timestamp ELSE created_at END DESC
        LIMIT 1
    """, (timestamp_iso.date(), timestamp_iso.date(), timestamp_iso.date()))
    
    tech_data = cursor.fetchone()
    if tech_data:
        print(f"✅ Found technical indicators:")
        print(f"   RSI: {tech_data['rsi_14']}")
        print(f"   SMA20: {tech_data['sma_20']}")  
        print(f"   VWAP: {tech_data['vwap']}")
        print(f"   Source timestamp: {tech_data['timestamp'] or tech_data['created_at']}")
    else:
        print(f"❌ No technical indicators found for {timestamp_iso.date()}")
        
        # Check what dates we have available
        cursor.execute("""
            SELECT DISTINCT DATE(COALESCE(timestamp, created_at)) as tech_date, COUNT(*) as count
            FROM technical_indicators 
            WHERE symbol = 'BTC' 
            GROUP BY tech_date
            ORDER BY tech_date DESC 
            LIMIT 5
        """)
        
        available_dates = cursor.fetchall()
        print(f"📅 Available technical indicator dates:")
        for row in available_dates:
            print(f"   {row['tech_date']}: {row['count']} records")
    
    conn.close()

if __name__ == "__main__":
    fix_technical_indicators()