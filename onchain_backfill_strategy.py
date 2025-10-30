"""
Onchain Metrics Backfill Strategy
Comprehensive backfill for all onchain metrics with real data sources
"""

import mysql.connector
import requests
import time
from datetime import datetime, timedelta
import json

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}


def analyze_onchain_gaps():
    """Analyze current onchain data gaps and identify missing records"""

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        print("=" * 80)
        print("ONCHAIN METRICS GAP ANALYSIS")
        print("=" * 80)
        print()

        # 1. Current coverage analysis
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as addr_count,
            SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as tx_count,
            SUM(CASE WHEN exchange_net_flow_24h IS NOT NULL THEN 1 ELSE 0 END) as flow_count,
            SUM(CASE WHEN price_volatility_7d IS NOT NULL THEN 1 ELSE 0 END) as vol_count
        FROM crypto_onchain_data
        """
        )

        result = cursor.fetchone()
        total = result[0]

        print(f"Total onchain records: {total:,}")
        print(f"Active Addresses: {result[1]:,} ({result[1]/total*100:.1f}%)")
        print(f"Transaction Count: {result[2]:,} ({result[2]/total*100:.1f}%)")
        print(f"Exchange Flow: {result[3]:,} ({result[3]/total*100:.1f}%)")
        print(f"Price Volatility: {result[4]:,} ({result[4]/total*100:.1f}%)")
        print()

        # 2. Missing records by symbol
        cursor.execute(
            """
        SELECT 
            coin_symbol,
            COUNT(*) as total,
            SUM(CASE WHEN active_addresses_24h IS NULL THEN 1 ELSE 0 END) as missing_addr,
            SUM(CASE WHEN transaction_count_24h IS NULL THEN 1 ELSE 0 END) as missing_tx,
            SUM(CASE WHEN exchange_net_flow_24h IS NULL THEN 1 ELSE 0 END) as missing_flow,
            SUM(CASE WHEN price_volatility_7d IS NULL THEN 1 ELSE 0 END) as missing_vol
        FROM crypto_onchain_data
        GROUP BY coin_symbol
        HAVING missing_addr > 0 OR missing_tx > 0 OR missing_flow > 0 OR missing_vol > 0
        ORDER BY missing_addr DESC
        LIMIT 20
        """
        )

        symbols = cursor.fetchall()
        print("TOP 20 SYMBOLS WITH MISSING ONCHAIN DATA:")
        print("-" * 80)
        print(
            f"{'Symbol':<10} | {'Total':<8} | {'Missing Addr':<13} | {'Missing Tx':<11} | {'Missing Flow':<13} | {'Missing Vol':<12}"
        )
        print("-" * 80)

        for sym in symbols:
            print(
                f"{sym[0]:<10} | {sym[1]:<8,} | {sym[2]:<13,} | {sym[3]:<11,} | {sym[4]:<13,} | {sym[5]:<12,}"
            )

        print()

        # 3. Time gaps analysis
        cursor.execute(
            """
        SELECT 
            DATE(collection_date) as date,
            COUNT(*) as total_records,
            SUM(CASE WHEN active_addresses_24h IS NULL THEN 1 ELSE 0 END) as missing_data
        FROM crypto_onchain_data
        WHERE collection_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(collection_date)
        ORDER BY date DESC
        LIMIT 10
        """
        )

        time_gaps = cursor.fetchall()
        print("RECENT TIME GAPS (Last 30 days):")
        print("-" * 50)
        print(f"{'Date':<12} | {'Total':<8} | {'Missing':<8}")
        print("-" * 50)

        for gap in time_gaps:
            print(f"{str(gap[0]):<12} | {gap[1]:<8,} | {gap[2]:<8,}")

        print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


def get_data_sources():
    """Identify available data sources for onchain metrics"""

    print("=" * 80)
    print("ONCHAIN DATA SOURCES ANALYSIS")
    print("=" * 80)
    print()

    print("AVAILABLE DATA SOURCES:")
    print("-" * 40)
    print("1. MESSARI API (messari.io)")
    print("   - Active addresses")
    print("   - Transaction counts")
    print("   - Price volatility")
    print("   - Rate limit: 20 requests/minute")
    print("   - Coverage: 200+ cryptocurrencies")
    print()

    print("2. BLOCKCHAIN.INFO API")
    print("   - Bitcoin-specific metrics")
    print("   - Active addresses")
    print("   - Transaction counts")
    print("   - Rate limit: 1 request/second")
    print("   - Coverage: Bitcoin only")
    print()

    print("3. ETHERSCAN API")
    print("   - Ethereum-specific metrics")
    print("   - Active addresses")
    print("   - Transaction counts")
    print("   - Rate limit: 5 requests/second")
    print("   - Coverage: Ethereum only")
    print()

    print("4. GLASSNODE API (Optional)")
    print("   - Comprehensive onchain data")
    print("   - Multiple cryptocurrencies")
    print("   - Rate limit: Varies by plan")
    print("   - Coverage: 30+ cryptocurrencies")
    print()

    print("RECOMMENDED STRATEGY:")
    print("-" * 40)
    print("1. Use Messari API for most cryptocurrencies")
    print("2. Use blockchain.info for Bitcoin-specific data")
    print("3. Use Etherscan for Ethereum-specific data")
    print("4. Implement rate limiting and error handling")
    print("5. Cache responses to minimize API calls")
    print()


def create_backfill_plan():
    """Create comprehensive backfill plan"""

    print("=" * 80)
    print("ONCHAIN BACKFILL PLAN")
    print("=" * 80)
    print()

    print("PHASE 1: DATA SOURCE SETUP")
    print("-" * 30)
    print("1. Configure API keys and endpoints")
    print("2. Implement rate limiting")
    print("3. Add error handling and retry logic")
    print("4. Create data validation functions")
    print()

    print("PHASE 2: HISTORICAL DATA COLLECTION")
    print("-" * 30)
    print("1. Identify missing date ranges per symbol")
    print("2. Collect historical data from APIs")
    print("3. Validate and clean data")
    print("4. Insert into database with proper error handling")
    print()

    print("PHASE 3: REAL-TIME DATA INTEGRATION")
    print("-" * 30)
    print("1. Update collector to use real APIs")
    print("2. Implement incremental updates")
    print("3. Add monitoring and alerting")
    print("4. Optimize for performance")
    print()

    print("EXPECTED RESULTS:")
    print("-" * 30)
    print("• 95%+ coverage for all onchain metrics")
    print("• Real-time data updates every 6 hours")
    print("• Historical data backfilled for 2+ years")
    print("• 200+ cryptocurrencies supported")
    print()


if __name__ == "__main__":
    analyze_onchain_gaps()
    get_data_sources()
    create_backfill_plan()


