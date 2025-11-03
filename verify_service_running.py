#!/usr/bin/env python3
"""Quick verification that service is running - no heavy queries"""
import mysql.connector
from datetime import datetime

try:
    # Quick connection test
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="news_collector",
        password="99Rules!",
        database="crypto_prices",
        connect_timeout=3,
    )

    cursor = conn.cursor(dictionary=True)

    print("=" * 60)
    print("SERVICE VERIFICATION")
    print("=" * 60)
    print()

    # Just check if table exists and has recent data (no heavy COUNT)
    cursor.execute(
        """
        SELECT 
            MAX(updated_at) as last_update,
            MAX(timestamp_iso) as latest_timestamp
        FROM ml_features_materialized
        WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        LIMIT 1
    """
    )
    result = cursor.fetchone()

    if result and result["last_update"]:
        print(f"✅ Service Status:")
        print(f"   Last update: {result['last_update']}")
        print(f"   Latest timestamp: {result['latest_timestamp']}")
        print()
        print("✅ Materialized table is accessible")
        print("✅ The updater service should be processing new records")
    else:
        print("⚠️  No recent updates found")
        print("   This may be normal if the updater just started")

    conn.close()

    print()
    print("=" * 60)
    print("To verify updater is working:")
    print(
        "1. Check Kubernetes logs: kubectl logs -n crypto-data-collection -l app=materialized-updater"
    )
    print("2. Wait 5-10 minutes and check for new records")
    print("3. Run: python check_updater_working.py")
    print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")
    print("   Make sure MySQL is running and accessible")

