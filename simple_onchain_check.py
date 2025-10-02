#!/usr/bin/env python3

import mysql.connector

def main():
    print("=== ONCHAIN DATA QUICK CHECK ===")
    
    try:
        connection = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector', 
            password='99Rules!',
            database='crypto_prices'
        )
        print("✅ Database connected")
        
        cursor = connection.cursor()
        
        # Check table structure
        cursor.execute("DESCRIBE crypto_onchain_data_enhanced")
        columns = cursor.fetchall()
        print(f"crypto_onchain_data_enhanced has {len(columns)} columns")
        
        # Check data count
        cursor.execute("SELECT COUNT(*) FROM crypto_onchain_data_enhanced")
        count = cursor.fetchone()[0]
        print(f"Total records: {count:,}")
        
        # Check symbol count
        cursor.execute("SELECT COUNT(DISTINCT coin_symbol) FROM crypto_onchain_data_enhanced")
        symbols = cursor.fetchone()[0]
        print(f"Unique symbols: {symbols}")
        
        # Check recent data
        cursor.execute("SELECT MAX(timestamp) FROM crypto_onchain_data_enhanced")
        latest = cursor.fetchone()[0]
        print(f"Latest timestamp: {latest}")
        
        # Check onchain fields in ml_features
        onchain_fields = [
            'transaction_count_24h', 'onchain_market_cap_usd', 'onchain_volume_24h'
        ]
        
        for field in onchain_fields:
            cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE {field} IS NOT NULL")
            count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
            total = cursor.fetchone()[0]
            percentage = count / total * 100 if total > 0 else 0
            print(f"{field}: {count}/{total} ({percentage:.1f}%)")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()