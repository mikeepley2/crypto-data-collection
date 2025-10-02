import mysql.connector

# Quick fix to populate macro data in existing materialized records
db_config = {
    'host': '127.0.0.1',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

print("🔧 POPULATING MACRO DATA IN MATERIALIZED TABLE")
print("="*60)

try:
    # Get latest macro indicators and update materialized table
    print("📈 Updating VIX data...")
    cursor.execute("""
        UPDATE ml_features_materialized 
        SET vix = (
            SELECT value FROM macro_indicators 
            WHERE indicator_name = 'VIX' 
            ORDER BY indicator_date DESC LIMIT 1
        ),
        updated_at = NOW()
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        AND vix IS NULL
    """)
    vix_updated = cursor.rowcount
    
    print("📈 Updating SPX data...")
    cursor.execute("""
        UPDATE ml_features_materialized 
        SET spx = (
            SELECT value FROM macro_indicators 
            WHERE indicator_name = 'SPX' 
            ORDER BY indicator_date DESC LIMIT 1
        ),
        updated_at = NOW()
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        AND spx IS NULL
    """)
    spx_updated = cursor.rowcount
    
    print("📈 Updating DXY data...")  
    cursor.execute("""
        UPDATE ml_features_materialized 
        SET dxy = (
            SELECT value FROM macro_indicators 
            WHERE indicator_name = 'DXY' 
            ORDER BY indicator_date DESC LIMIT 1
        ),
        updated_at = NOW()
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        AND dxy IS NULL
    """)
    dxy_updated = cursor.rowcount
    
    print("📈 Updating Treasury 10Y data...")
    cursor.execute("""
        UPDATE ml_features_materialized 
        SET treasury_10y = (
            SELECT value FROM macro_indicators 
            WHERE indicator_name = 'Treasury_10Y' 
            ORDER BY indicator_date DESC LIMIT 1
        ),
        updated_at = NOW()
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        AND treasury_10y IS NULL
    """)
    treasury_updated = cursor.rowcount
    
    conn.commit()
    
    total_updated = vix_updated + spx_updated + dxy_updated + treasury_updated
    print(f"✅ Updated macro data: VIX({vix_updated}), SPX({spx_updated}), DXY({dxy_updated}), Treasury({treasury_updated})")
    print(f"📊 Total records enhanced: {total_updated}")
    
    # Check improvement
    cursor.execute("SELECT * FROM ml_features_materialized WHERE symbol = 'BTC' ORDER BY timestamp_iso DESC LIMIT 1")
    result = cursor.fetchone()
    if result:
        columns = [desc[0] for desc in cursor.description]
        record_dict = dict(zip(columns, result))
        populated = len([col for col, val in record_dict.items() if val is not None])
        print(f"🎯 BTC now has: {populated}/86 columns populated ({populated/86*100:.1f}%)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
    
finally:
    cursor.close()
    conn.close()

print("✅ Macro data population complete!")
print("🔄 Next: Deploy enhanced materialized updater...")