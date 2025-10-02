#!/usr/bin/env python3

import mysql.connector
import sys

def get_db_connection():
    """Create database connection"""
    try:
        # Try to connect through local docker network
        return mysql.connector.connect(
            host='localhost',  # Try localhost first
            port=3306,
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
    except Exception as e:
        print(f"Local connection failed: {e}")
        # Fallback to docker internal
        return mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )

def check_materialized_table():
    """Check materialized table status"""
    try:
        print("Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        print("\n=== MATERIALIZED TABLE STATUS ===")
        
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total = cursor.fetchone()[0]
        print(f"Total records: {total:,}")
        
        # Check recent records using timestamp
        cursor.execute("""
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        recent = cursor.fetchone()[0]
        print(f"Records from last 24h: {recent:,}")
        
        # Check OHLC population
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) as open_count,
                SUM(CASE WHEN close_price IS NOT NULL THEN 1 ELSE 0 END) as close_count,
                ROUND(SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as open_pct
            FROM ml_features_materialized
        """)
        ohlc = cursor.fetchone()
        print(f"OHLC data populated: {ohlc[0]:,} records ({ohlc[2]}%)")
        
        # Check macro indicators
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) as dxy_count,
                SUM(CASE WHEN vix IS NOT NULL THEN 1 ELSE 0 END) as vix_count
            FROM ml_features_materialized
        """)
        macro = cursor.fetchone()
        print(f"Macro indicators - DXY: {macro[0]:,}, VIX: {macro[1]:,}")
        
        # Check recent updates
        cursor.execute("""
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        updated = cursor.fetchone()[0]
        print(f"Updated in last hour: {updated:,}")
        
        # Top symbols by recent activity
        cursor.execute("""
            SELECT symbol, MAX(timestamp) as latest, COUNT(*) as total
            FROM ml_features_materialized 
            GROUP BY symbol 
            ORDER BY latest DESC 
            LIMIT 5
        """)
        
        top_symbols = cursor.fetchall()
        print(f"\nTop 5 most recent symbols:")
        for row in top_symbols:
            print(f"  {row[0]}: {row[1]} ({row[2]:,} records)")
        
        # Date range
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM ml_features_materialized")
        dates = cursor.fetchone()
        print(f"\nDate range: {dates[0]} to {dates[1]}")
        
        conn.close()
        print("\n✅ Analysis completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_materialized_table()
    sys.exit(0 if success else 1)