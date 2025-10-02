import mysql.connector

connection = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_prices'
)
print("Connected to database")

cursor = connection.cursor()

# Check what macro indicator types we have
cursor.execute("""
    SELECT 
        indicator_name,
        COUNT(*) as record_count,
        MIN(indicator_date) as first_date,
        MAX(indicator_date) as last_date,
        AVG(value) as avg_value
    FROM macro_indicators
    GROUP BY indicator_name
    ORDER BY record_count DESC
""")

indicators = cursor.fetchall()
print(f"Available macro indicators ({len(indicators)} types):")
for indicator_name, count, first_date, last_date, avg_val in indicators:
    print(f"  {indicator_name}: {count:,} records ({first_date} to {last_date}), avg={avg_val:.4f}")

# Check current macro field population in ml_features
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN vix IS NOT NULL THEN 1 ELSE 0 END) as has_vix,
        SUM(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) as has_dxy,
        SUM(CASE WHEN fed_funds_rate IS NOT NULL THEN 1 ELSE 0 END) as has_fed_funds,
        SUM(CASE WHEN treasury_10y IS NOT NULL THEN 1 ELSE 0 END) as has_treasury_10y,
        SUM(CASE WHEN vix_index IS NOT NULL THEN 1 ELSE 0 END) as has_vix_index,
        SUM(CASE WHEN dxy_index IS NOT NULL THEN 1 ELSE 0 END) as has_dxy_index
    FROM ml_features_materialized
""")

result = cursor.fetchone()
total, vix_count, dxy_count, fed_count, treasury_count, vix_idx_count, dxy_idx_count = result

print(f"\nCurrent macro field population (out of {total} symbols):")
print(f"  vix: {vix_count} ({vix_count/total*100:.1f}%)")
print(f"  dxy: {dxy_count} ({dxy_count/total*100:.1f}%)")
print(f"  fed_funds_rate: {fed_count} ({fed_count/total*100:.1f}%)")
print(f"  treasury_10y: {treasury_count} ({treasury_count/total*100:.1f}%)")
print(f"  vix_index: {vix_idx_count} ({vix_idx_count/total*100:.1f}%)")
print(f"  dxy_index: {dxy_idx_count} ({dxy_idx_count/total*100:.1f}%)")

populated_fields = sum([1 for count in [vix_count, dxy_count, fed_count, treasury_count, vix_idx_count, dxy_idx_count] if count > 0])
print(f"\nMacro category status: {populated_fields}/6 fields populated ({populated_fields/6*100:.1f}%)")

# Sample BTC values
cursor.execute("SELECT vix, dxy, fed_funds_rate, treasury_10y FROM ml_features_materialized WHERE symbol = 'BTC'")
btc_result = cursor.fetchone()
if btc_result:
    vix_val, dxy_val, fed_val, treasury_val = btc_result
    print(f"\nBTC sample values:")
    print(f"  vix: {vix_val}")
    print(f"  dxy: {dxy_val}")
    print(f"  fed_funds_rate: {fed_val}")
    print(f"  treasury_10y: {treasury_val}")

cursor.close()
connection.close()