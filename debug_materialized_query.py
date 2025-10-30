import mysql.connector

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print("=== DEBUG MATERIALIZED UPDATER QUERY ===")
print()

# Test the exact query that the materialized updater uses
print("1. TESTING MATERIALIZED UPDATER ONCHAIN QUERY")
print("-" * 50)
try:
    # Get a sample symbol and timestamp from recent price data
    cursor.execute(
        """
    SELECT symbol, timestamp_iso 
    FROM price_data_real 
    WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR) 
    AND symbol IN ('BTC', 'ETH', 'SOL', 'ADA', 'LINK')
    ORDER BY timestamp_iso DESC
    LIMIT 1
    """
    )
    sample_price = cursor.fetchone()
    if sample_price:
        symbol, timestamp_iso = sample_price
        print(f"Testing with symbol: {symbol}, timestamp: {timestamp_iso}")

        # Test the exact onchain query from materialized updater
        cursor.execute(
            """
        SELECT 
            active_addresses_24h,
            transaction_count_24h,
            exchange_net_flow_24h,
            price_volatility_7d
        FROM crypto_onchain_data 
        WHERE coin_symbol COLLATE utf8mb4_unicode_ci = %s 
        AND collection_date >= DATE_SUB(%s, INTERVAL 24 HOUR)
        ORDER BY collection_date DESC
        LIMIT 1
        """,
            (symbol, timestamp_iso),
        )

        onchain_result = cursor.fetchone()
        if onchain_result:
            active, tx, flow, vol = onchain_result
            print(
                f"Onchain query result: active={active}, tx={tx}, flow={flow}, vol={vol}"
            )
        else:
            print("No onchain data found for this symbol/timestamp")

            # Check what onchain data exists for this symbol
            cursor.execute(
                """
            SELECT collection_date, active_addresses_24h, transaction_count_24h
            FROM crypto_onchain_data 
            WHERE coin_symbol COLLATE utf8mb4_unicode_ci = %s 
            ORDER BY collection_date DESC
            LIMIT 3
            """,
                (symbol,),
            )

            available_data = cursor.fetchall()
            print(f"Available onchain data for {symbol}:")
            for date, active, tx in available_data:
                print(f"  {date}: active={active}, tx={tx}")

except Exception as e:
    print(f"Error testing onchain query: {e}")

print()

print("2. CHECKING TIMING MISMATCH")
print("-" * 50)
try:
    cursor.execute(
        """
    SELECT 
        p.symbol,
        p.timestamp_iso,
        DATE(p.timestamp_iso) as price_date,
        o.collection_date,
        o.active_addresses_24h
    FROM price_data_real p
    LEFT JOIN crypto_onchain_data o ON p.symbol COLLATE utf8mb4_unicode_ci = o.coin_symbol COLLATE utf8mb4_unicode_ci
        AND DATE(p.timestamp_iso) = DATE(o.collection_date)
    WHERE p.timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR) 
    AND p.symbol IN ('BTC', 'ETH', 'SOL')
    ORDER BY p.timestamp_iso DESC
    LIMIT 5
    """
    )
    timing_check = cursor.fetchall()
    print("Price vs Onchain timing check:")
    for symbol, timestamp, price_date, onchain_date, active in timing_check:
        print(
            f"  {symbol}: price_date={price_date}, onchain_date={onchain_date}, active={active}"
        )

except Exception as e:
    print(f"Error checking timing: {e}")

cursor.close()
conn.close()


