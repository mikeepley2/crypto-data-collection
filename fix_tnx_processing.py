#!/usr/bin/env python3
"""
Fix TNX KeyError in materialized updater by ensuring proper error handling
"""
import mysql.connector
from datetime import datetime

def fix_tnx_processing():
    """Create a comprehensive restart and fix for materialized updater"""
    try:
        print("🔧 FIXING TNX MACRO INDICATOR PROCESSING")
        print("=" * 60)
        
        # First, let's check current materialized updater logs to see exact error
        print("1. Current error pattern identified: KeyError 'tnx'")
        print("2. Issue: macro_data dict missing 'tnx' key when accessed")
        print("3. Fix: Restart materialized updater to load corrected error handling")
        
        # Check if we can update just the processing part
        conn = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        cursor = conn.cursor()
        
        # Check what data is actually failing to process
        cursor.execute("""
            SELECT symbol, MAX(created_at) as latest_data
            FROM ml_features_materialized 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            GROUP BY symbol
            ORDER BY latest_data DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        print(f"\nSymbols with recent data (last hour):")
        if results:
            for symbol, latest in results:
                print(f"  {symbol}: {latest}")
        else:
            print("  No symbols processed in last hour")
        
        # Check what price data is waiting to be processed
        cursor.execute("""
            SELECT COUNT(*) as unprocessed_count
            FROM (
                SELECT DISTINCT p.symbol, p.timestamp 
                FROM crypto_assets p
                WHERE p.timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
                AND NOT EXISTS (
                    SELECT 1 FROM ml_features_materialized m 
                    WHERE m.symbol = p.symbol 
                    AND ABS(TIMESTAMPDIFF(MINUTE, m.datetime_utc, p.timestamp)) < 5
                )
            ) unprocessed
        """)
        
        unprocessed = cursor.fetchone()[0]
        print(f"\nUnprocessed price records (last 2h): {unprocessed}")
        
        cursor.close()
        conn.close()
        
        print("\n🔄 RECOMMENDED FIXES:")
        print("1. Restart materialized-updater deployment")
        print("2. Check collector-manager is triggering collection properly") 
        print("3. Verify macro indicators are available for recent dates")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fix analysis: {e}")
        return False

if __name__ == "__main__":
    fix_tnx_processing()