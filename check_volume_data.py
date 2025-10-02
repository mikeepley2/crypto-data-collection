#!/usr/bin/env python3

import mysql.connector

try:
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Check recent price_data records
    cursor.execute("""
        SELECT symbol, timestamp, close, volume, market_cap_usd 
        FROM price_data 
        WHERE symbol IN ('BTC', 'ETH') 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    results = cursor.fetchall()
    
    print("=== Recent price_data Records ===")
    print("Symbol | Timestamp           | Price      | Volume       | Market Cap")
    print("-" * 70)
    
    for row in results:
        symbol, timestamp, price, volume, market_cap = row
        vol_str = f"{volume:,.0f}" if volume else "NULL"
        price_str = f"${price:,.2f}" if price else "NULL"
        mc_str = f"${market_cap:,.0f}" if market_cap else "NULL"
        print(f"{symbol:6s} | {timestamp} | {price_str:>10s} | {vol_str:>12s} | {mc_str:>12s}")
    
    cursor.close()
    conn.close()
    print("\n✅ Query completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")