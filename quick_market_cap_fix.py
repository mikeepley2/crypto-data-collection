import mysql.connector

connection = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_prices'
)
print("Connected to database")

cursor = connection.cursor()

# Get symbols with market cap data
cursor.execute("""
    SELECT DISTINCT symbol 
    FROM price_data 
    WHERE timestamp > DATE_SUB(NOW(), INTERVAL 3 HOUR)
    AND market_cap_usd IS NOT NULL 
    AND market_cap_usd != 0
    ORDER BY symbol LIMIT 10
""")

symbols = [row[0] for row in cursor.fetchall()]
print(f"Found {len(symbols)} symbols with market cap data: {symbols}")

updated_count = 0
for symbol in symbols:
    # Get latest market cap for symbol
    cursor.execute("""
        SELECT market_cap_usd, price_change_24h, percent_change_24h
        FROM price_data 
        WHERE symbol = %s 
        AND market_cap_usd IS NOT NULL 
        ORDER BY timestamp DESC LIMIT 1
    """, (symbol,))
    
    row = cursor.fetchone()
    if row:
        market_cap_usd, price_change_24h, percent_change_24h = row
        
        # Update ml_features_materialized
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET market_cap_usd = %s,
                market_cap = %s,
                price_change_24h = %s,
                percent_change_24h = %s
            WHERE symbol = %s
        """, (market_cap_usd, market_cap_usd, price_change_24h, percent_change_24h, symbol))
        
        if cursor.rowcount > 0:
            updated_count += 1
            print(f"Updated {symbol}: MCap=${market_cap_usd:,.0f}, Change24h={price_change_24h}, %Change={percent_change_24h}")

connection.commit()

# Check results
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN market_cap_usd IS NOT NULL THEN 1 ELSE 0 END) as has_market_cap_usd,
           SUM(CASE WHEN market_cap IS NOT NULL THEN 1 ELSE 0 END) as has_market_cap
    FROM ml_features_materialized
""")

result = cursor.fetchone()
total, market_cap_usd_count, market_cap_count = result

print(f"\nResults: {updated_count} symbols updated")
print(f"Market cap fields: {market_cap_usd_count}/117 market_cap_usd, {market_cap_count}/117 market_cap")

cursor.close()
connection.close()