import mysql.connector

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print("=== ONCHAIN INTEGRATION TEST (WITH COLLATION FIX) ===")
print()

# Check if onchain data is now flowing to materialized table
print("1. RECENT ONCHAIN DATA IN MATERIALIZED TABLE")
print("-" * 50)
try:
    cursor.execute(
        """
    SELECT 
        COUNT(*) as total_records,
        SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as has_active_addresses,
        SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as has_transaction_count,
        SUM(CASE WHEN exchange_net_flow_24h IS NOT NULL THEN 1 ELSE 0 END) as has_exchange_flow,
        SUM(CASE WHEN price_volatility_7d IS NOT NULL THEN 1 ELSE 0 END) as has_price_volatility,
        MAX(updated_at) as latest_update
    FROM ml_features_materialized
    WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    """
    )
    recent_data = cursor.fetchone()
    total = recent_data[0]
    print(f"Recent materialized records (last 1 hour): {total:,}")
    print(f"Active Addresses: {recent_data[1]:,} ({recent_data[1]/total*100:.1f}%)")
    print(f"Transaction Count: {recent_data[2]:,} ({recent_data[2]/total*100:.1f}%)")
    print(f"Exchange Flow: {recent_data[3]:,} ({recent_data[3]/total*100:.1f}%)")
    print(f"Price Volatility: {recent_data[4]:,} ({recent_data[4]/total*100:.1f}%)")
    print(f"Latest update: {recent_data[5]}")

except Exception as e:
    print(f"Error checking recent data: {e}")

print()

# Check sample onchain data
print("2. SAMPLE ONCHAIN DATA IN MATERIALIZED TABLE")
print("-" * 50)
try:
    cursor.execute(
        """
    SELECT 
        symbol,
        active_addresses_24h,
        transaction_count_24h,
        exchange_net_flow_24h,
        price_volatility_7d,
        updated_at
    FROM ml_features_materialized
    WHERE active_addresses_24h IS NOT NULL
    AND updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    ORDER BY updated_at DESC
    LIMIT 5
    """
    )
    sample_data = cursor.fetchall()
    print("Sample records with onchain data:")
    for symbol, active, tx, flow, vol, updated in sample_data:
        print(
            f"  {symbol}: active={active}, tx={tx}, flow={flow}, vol={vol}, updated={updated}"
        )

except Exception as e:
    print(f"Error checking sample data: {e}")

print()

# Test the collation fix directly
print("3. COLLATION FIX TEST")
print("-" * 50)
try:
    cursor.execute(
        """
    SELECT 
        p.symbol,
        p.timestamp_iso,
        o.active_addresses_24h,
        o.transaction_count_24h
    FROM price_data_real p
    LEFT JOIN crypto_onchain_data o ON p.symbol COLLATE utf8mb4_unicode_ci = o.coin_symbol COLLATE utf8mb4_unicode_ci
        AND DATE(p.timestamp_iso) = DATE(o.collection_date)
    WHERE p.timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR) 
    AND p.symbol IN ('BTC', 'ETH', 'SOL', 'ADA', 'LINK')
    ORDER BY p.timestamp_iso DESC
    LIMIT 5
    """
    )
    collation_test = cursor.fetchall()
    print("Collation fix test results:")
    for symbol, timestamp, active, tx in collation_test:
        print(f"  {symbol}: {timestamp} -> active={active}, tx={tx}")

except Exception as e:
    print(f"Error testing collation fix: {e}")

cursor.close()
conn.close()


