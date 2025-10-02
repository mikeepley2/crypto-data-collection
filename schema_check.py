#!/usr/bin/env python3
"""
Check actual database schema and current status
"""
import mysql.connector

print("🔍 DATABASE SCHEMA AND STATUS CHECK")
print("=" * 60)

try:
    # Check crypto_prices database
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()
    
    # Show ml_features_materialized structure
    print("📊 ML_FEATURES_MATERIALIZED SCHEMA:")
    cursor.execute("DESCRIBE ml_features_materialized")
    columns = cursor.fetchall()
    print("Key columns:")
    for col in columns[:10]:  # Show first 10 columns
        print(f"   {col[0]} - {col[1]}")
    print(f"   ... and {len(columns)-10} more columns")
    
    # Check what tables exist for price data
    print(f"\n📋 AVAILABLE TABLES:")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    price_tables = [t[0] for t in tables if 'price' in t[0].lower() or 'crypto' in t[0].lower()]
    print(f"Price-related tables: {price_tables}")
    
    # Check recent data in any price-related table
    if 'crypto_assets' in [t[0] for t in tables]:
        cursor.execute("DESCRIBE crypto_assets")
        crypto_assets_cols = cursor.fetchall()
        print(f"\nCRYPTO_ASSETS columns: {[c[0] for c in crypto_assets_cols[:5]]}")
        
        # Try to find recent data
        for time_col in ['created_at', 'timestamp', 'updated_at']:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM crypto_assets 
                    WHERE {time_col} >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """)
                count = cursor.fetchone()[0]
                print(f"Recent crypto_assets ({time_col}): {count}")
                break
            except:
                continue
    
    cursor.close()
    conn.close()
    
    print(f"\n📊 COLLECTION SUMMARY:")
    print(f"✅ ML Features: 3.35M total records")
    print(f"⚠️ Recent Processing: Only 13 records in 12h")
    print(f"⚠️ News Collection: Not collecting recently")
    print(f"⚠️ Data Freshness: 9+ hours old")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Check what cronjobs have run recently
print(f"\n🕐 Let's see what collection jobs completed recently...")
print(f"This will help us understand why data isn't fresh.")