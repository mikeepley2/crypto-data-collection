import mysql.connector

connection = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_prices'
)
print("Connected to database")

cursor = connection.cursor()

# Get latest values for key macro indicators
macro_updates = {}

# VIX
cursor.execute("SELECT value FROM macro_indicators WHERE indicator_name = 'VIX' ORDER BY indicator_date DESC LIMIT 1")
result = cursor.fetchone()
if result:
    vix_value = float(result[0])
    macro_updates['vix'] = vix_value
    macro_updates['vix_index'] = vix_value
    print(f"VIX: {vix_value}")

# DXY  
cursor.execute("SELECT value FROM macro_indicators WHERE indicator_name = 'DXY' ORDER BY indicator_date DESC LIMIT 1")
result = cursor.fetchone()
if result:
    dxy_value = float(result[0])
    macro_updates['dxy'] = dxy_value
    macro_updates['dxy_index'] = dxy_value
    print(f"DXY: {dxy_value}")

# Fed Funds Rate
cursor.execute("SELECT value FROM macro_indicators WHERE indicator_name = 'Fed_Funds_Rate' ORDER BY indicator_date DESC LIMIT 1")
result = cursor.fetchone()
if result:
    fed_value = float(result[0])
    macro_updates['fed_funds_rate'] = fed_value
    print(f"Fed Funds: {fed_value}")

# Treasury 10Y
cursor.execute("SELECT value FROM macro_indicators WHERE indicator_name = 'Treasury_10Y' ORDER BY indicator_date DESC LIMIT 1")
result = cursor.fetchone()
if result:
    treasury_value = float(result[0])
    macro_updates['treasury_10y'] = treasury_value
    print(f"Treasury 10Y: {treasury_value}")

# DGS10 (backup for Treasury 10Y)
cursor.execute("SELECT value FROM macro_indicators WHERE indicator_name = 'DGS10' ORDER BY indicator_date DESC LIMIT 1")
result = cursor.fetchone()
if result and 'treasury_10y' not in macro_updates:
    treasury_value = float(result[0])
    macro_updates['treasury_10y'] = treasury_value
    print(f"Treasury 10Y (from DGS10): {treasury_value}")

print(f"\nUpdating {len(macro_updates)} macro fields for all symbols...")

# Update all symbols with these values
for field, value in macro_updates.items():
    cursor.execute(f"UPDATE ml_features_materialized SET {field} = %s", (value,))
    print(f"Updated {field} = {value} for {cursor.rowcount} symbols")

connection.commit()

# Verify BTC values
cursor.execute("SELECT vix, dxy, fed_funds_rate, treasury_10y FROM ml_features_materialized WHERE symbol = 'BTC'")
btc_result = cursor.fetchone()
if btc_result:
    print(f"\nBTC verification:")
    print(f"  vix: {btc_result[0]}")
    print(f"  dxy: {btc_result[1]}")  
    print(f"  fed_funds_rate: {btc_result[2]}")
    print(f"  treasury_10y: {btc_result[3]}")

print("\nMacro expansion completed!")
cursor.close()
connection.close()