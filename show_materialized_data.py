#!/usr/bin/env python3

import mysql.connector

try:
    # Connect to the database
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Query the latest materialized data
    query = """
    SELECT symbol, timestamp_iso, current_price, volume_24h, data_quality_score 
    FROM ml_features_materialized 
    WHERE symbol IN ('BTC', 'ETH') 
    ORDER BY timestamp_iso DESC 
    LIMIT 10
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("=== Latest Materialized Data ===")
    print("Symbol | Timestamp | Price | Volume 24h | Quality Score")
    print("-" * 65)
    
    for row in results:
        symbol, timestamp, price, volume, quality = row
        vol_str = f"{volume:,.0f}" if volume else "N/A"
        quality_str = f"{quality:.1f}" if quality else "N/A"
        price_str = f"${price:,.2f}" if price else "N/A"
        print(f"{symbol:6s} | {timestamp} | {price_str:>10s} | {vol_str:>12s} | {quality_str:>7s}")
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
    total_count = cursor.fetchone()[0]
    print(f"\nTotal materialized records: {total_count:,}")
    
    cursor.close()
    conn.close()
    print("\n✅ Query completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")