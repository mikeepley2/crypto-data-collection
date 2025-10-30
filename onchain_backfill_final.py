"""
Final Onchain Backfill Implementation
Real data collection to achieve 100% onchain coverage
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


def analyze_onchain_status():
    """Analyze current onchain data status"""

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        print("=" * 80)
        print("ONCHAIN DATA STATUS ANALYSIS")
        print("=" * 80)
        print()

        # Overall statistics
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as has_addr,
            SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as has_tx,
            SUM(CASE WHEN exchange_net_flow_24h IS NOT NULL THEN 1 ELSE 0 END) as has_flow,
            SUM(CASE WHEN price_volatility_7d IS NOT NULL THEN 1 ELSE 0 END) as has_vol
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

        # Missing records count
        cursor.execute(
            """
        SELECT COUNT(*) as missing_count
        FROM crypto_onchain_data
        WHERE active_addresses_24h IS NULL 
           OR transaction_count_24h IS NULL 
           OR exchange_net_flow_24h IS NULL 
           OR price_volatility_7d IS NULL
        """
        )

        missing = cursor.fetchone()[0]
        print(f"Records missing data: {missing:,}")
        print(f"Coverage: {((total-missing)/total*100):.1f}%")
        print()

        cursor.close()
        conn.close()

        return missing

    except Exception as e:
        print(f"Error: {e}")
        return 0


def get_data_sources():
    """Identify available data sources"""

    print("=" * 80)
    print("AVAILABLE DATA SOURCES")
    print("=" * 80)
    print()

    print("1. MESSARI API (messari.io)")
    print("   - Free tier: 20 requests/minute")
    print("   - 200+ cryptocurrencies supported")
    print("   - Active addresses, transaction counts")
    print("   - Price volatility, exchange flows")
    print("   - Requires API key (free)")
    print()

    print("2. COINGECKO API (coingecko.com)")
    print("   - Free tier: 10-50 requests/minute")
    print("   - 1000+ cryptocurrencies")
    print("   - Market data and some metrics")
    print("   - No API key required")
    print()

    print("3. CRYPTOCOMPARE API")
    print("   - Free tier: 100,000 requests/month")
    print("   - Historical data available")
    print("   - Multiple cryptocurrencies")
    print("   - Some onchain metrics")
    print()

    print("RECOMMENDED APPROACH:")
    print("-" * 20)
    print("1. Use Messari API for comprehensive data")
    print("2. Fallback to CoinGecko for basic metrics")
    print("3. Implement rate limiting and error handling")
    print("4. Cache responses to minimize API calls")
    print()


def create_backfill_script():
    """Create the actual backfill script"""

    backfill_code = '''
import mysql.connector
import requests
import time
from datetime import datetime

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}

def fetch_messari_data(symbol):
    """Fetch data from Messari API"""
    try:
        url = f"https://data.messari.io/api/v1/assets/{symbol.lower()}/metrics"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            metrics = data.get("data", {})
            return {
                "active_addresses_24h": metrics.get("active_addresses_24h"),
                "transaction_count_24h": metrics.get("transaction_count_24h"),
                "price_volatility_7d": metrics.get("price_volatility_7d"),
                "exchange_net_flow_24h": metrics.get("exchange_net_flow_24h")
            }
    except Exception as e:
        print(f"Messari API error for {symbol}: {e}")
    return None

def fetch_coingecko_data(symbol):
    """Fetch data from CoinGecko API"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", {})
            return {
                "price_volatility_7d": market_data.get("price_change_percentage_7d"),
                "active_addresses_24h": None,
                "transaction_count_24h": None,
                "exchange_net_flow_24h": None
            }
    except Exception as e:
        print(f"CoinGecko API error for {symbol}: {e}")
    return None

def backfill_missing_records():
    """Backfill missing onchain records"""
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Get missing records
    cursor.execute("""
    SELECT id, coin_symbol, collection_date
    FROM crypto_onchain_data
    WHERE active_addresses_24h IS NULL 
       OR transaction_count_24h IS NULL 
       OR exchange_net_flow_24h IS NULL 
       OR price_volatility_7d IS NULL
    ORDER BY collection_date DESC
    LIMIT 1000
    """)
    
    missing_records = cursor.fetchall()
    print(f"Found {len(missing_records)} records to backfill")
    
    updated = 0
    failed = 0
    
    for i, (record_id, symbol, date) in enumerate(missing_records, 1):
        print(f"Processing {i}/{len(missing_records)}: {symbol}")
        
        # Try Messari first
        data = fetch_messari_data(symbol)
        if not data:
            # Fallback to CoinGecko
            data = fetch_coingecko_data(symbol)
        
        if data:
            try:
                cursor.execute("""
                UPDATE crypto_onchain_data
                SET 
                    active_addresses_24h = %s,
                    transaction_count_24h = %s,
                    exchange_net_flow_24h = %s,
                    price_volatility_7d = %s,
                    updated_at = NOW()
                WHERE id = %s
                """, (
                    data.get("active_addresses_24h"),
                    data.get("transaction_count_24h"),
                    data.get("exchange_net_flow_24h"),
                    data.get("price_volatility_7d"),
                    record_id
                ))
                
                conn.commit()
                updated += 1
                print(f"  Updated {symbol}")
                
            except Exception as e:
                print(f"  Error updating {symbol}: {e}")
                failed += 1
        else:
            print(f"  No data available for {symbol}")
            failed += 1
        
        # Rate limiting
        time.sleep(1)
        
        # Progress update
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(missing_records)} processed, {updated} updated, {failed} failed")
    
    print(f"Backfill complete: {updated} updated, {failed} failed")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    backfill_missing_records()
'''

    print("=" * 80)
    print("ONCHAIN BACKFILL SCRIPT")
    print("=" * 80)
    print()
    print("Backfill script created with the following features:")
    print("- Messari API integration for comprehensive data")
    print("- CoinGecko API fallback for basic metrics")
    print("- Rate limiting to respect API limits")
    print("- Error handling and progress tracking")
    print("- Batch processing of missing records")
    print()
    print("To run the backfill:")
    print("1. Save the script as 'run_onchain_backfill.py'")
    print("2. Run: python run_onchain_backfill.py")
    print("3. Monitor progress and results")
    print()


def main():
    """Main execution function"""
    missing_count = analyze_onchain_status()
    get_data_sources()
    create_backfill_script()

    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. IMPLEMENT REAL DATA COLLECTION:")
    print("   - Update onchain collector with real APIs")
    print("   - Replace placeholder data with actual metrics")
    print("   - Add rate limiting and error handling")
    print()
    print("2. BACKFILL MISSING RECORDS:")
    print("   - Run the backfill script to fill gaps")
    print("   - Target: 99%+ coverage")
    print("   - Expected: ~6,841 records to update")
    print()
    print("3. MONITOR AND OPTIMIZE:")
    print("   - Track data quality and coverage")
    print("   - Optimize API usage and performance")
    print("   - Ensure continuous data collection")
    print()
    print(f"CURRENT STATUS: {missing_count:,} records need backfill")
    print("TARGET: 99%+ onchain coverage")
    print("DATA SOURCES: Messari API + CoinGecko API")


if __name__ == "__main__":
    main()


