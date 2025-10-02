import mysql.connector

try:
    connection = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector', 
        password='99Rules!',
        database='crypto_prices'
    )
    
    cursor = connection.cursor()
    
    # Check BTC macro values
    cursor.execute("SELECT vix, dxy, fed_funds_rate, treasury_10y, vix_index, dxy_index FROM ml_features_materialized WHERE symbol = 'BTC'")
    result = cursor.fetchone()
    
    print("BTC Macro Values:")
    if result:
        vix, dxy, fed, treasury, vix_idx, dxy_idx = result
        print(f"  VIX: {vix}")
        print(f"  DXY: {dxy}")
        print(f"  Fed Funds: {fed}")
        print(f"  Treasury 10Y: {treasury}")
        print(f"  VIX Index: {vix_idx}")
        print(f"  DXY Index: {dxy_idx}")
    
    # Count populated macro fields
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN vix IS NOT NULL THEN 1 ELSE 0 END) as vix_count,
            SUM(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) as dxy_count,
            SUM(CASE WHEN fed_funds_rate IS NOT NULL THEN 1 ELSE 0 END) as fed_count,
            SUM(CASE WHEN treasury_10y IS NOT NULL THEN 1 ELSE 0 END) as treasury_count,
            COUNT(*) as total
        FROM ml_features_materialized
    """)
    
    result = cursor.fetchone()
    if result:
        vix_count, dxy_count, fed_count, treasury_count, total = result
        print(f"\nMacro Field Population:")
        print(f"  VIX: {vix_count}/{total} ({vix_count/total*100:.1f}%)")
        print(f"  DXY: {dxy_count}/{total} ({dxy_count/total*100:.1f}%)")
        print(f"  Fed Funds: {fed_count}/{total} ({fed_count/total*100:.1f}%)")
        print(f"  Treasury 10Y: {treasury_count}/{total} ({treasury_count/total*100:.1f}%)")
        
    cursor.close()
    connection.close()
    print("\nMacro verification completed!")
    
except Exception as e:
    print(f"Error: {e}")