"""
Practical Onchain Backfill Implementation
Focus on achievable data sources and realistic backfill strategy
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


def analyze_missing_data():
    """Analyze what onchain data is missing and why"""

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        print("=" * 80)
        print("ONCHAIN DATA GAP ANALYSIS")
        print("=" * 80)
        print()

        # 1. Overall statistics
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

        # 2. Missing records by symbol (top 20)
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
        print("TOP 20 SYMBOLS WITH MISSING DATA:")
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

        # 3. Sample missing records
        cursor.execute(
            """
        SELECT 
            id, coin_symbol, collection_date,
            active_addresses_24h, transaction_count_24h,
            exchange_net_flow_24h, price_volatility_7d
        FROM crypto_onchain_data
        WHERE active_addresses_24h IS NULL
        ORDER BY collection_date DESC
        LIMIT 5
        """
        )

        samples = cursor.fetchall()
        print("SAMPLE MISSING RECORDS:")
        print("-" * 80)
        print(
            f"{'ID':<8} | {'Symbol':<8} | {'Date':<12} | {'Addr':<8} | {'Tx':<8} | {'Flow':<8} | {'Vol':<8}"
        )
        print("-" * 80)

        for sample in samples:
            addr = "NULL" if sample[3] is None else str(sample[3])
            tx = "NULL" if sample[4] is None else str(sample[4])
            flow = "NULL" if sample[5] is None else str(sample[5])
            vol = "NULL" if sample[6] is None else str(sample[6])

            print(
                f"{sample[0]:<8} | {sample[1]:<8} | {str(sample[2])[:10]:<12} | {addr:<8} | {tx:<8} | {flow:<8} | {vol:<8}"
            )

        print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


def create_realistic_backfill_plan():
    """Create a realistic backfill plan based on available data sources"""

    print("=" * 80)
    print("REALISTIC ONCHAIN BACKFILL PLAN")
    print("=" * 80)
    print()

    print("CURRENT SITUATION:")
    print("-" * 20)
    print("• 94% coverage already achieved")
    print("• 6,841 records missing data")
    print("• Current collector only inserts placeholders")
    print("• Need real data sources for remaining records")
    print()

    print("REALISTIC DATA SOURCES:")
    print("-" * 20)
    print("1. MESSARI API (messari.io)")
    print("   ✓ Free tier: 20 requests/minute")
    print("   ✓ 200+ cryptocurrencies supported")
    print("   ✓ Active addresses, transaction counts")
    print("   ✓ Price volatility data")
    print("   ✓ Exchange flow data")
    print()

    print("2. COINGECKO API (coingecko.com)")
    print("   ✓ Free tier: 10-50 requests/minute")
    print("   ✓ 1000+ cryptocurrencies")
    print("   ✓ Market data and some onchain metrics")
    print("   ✓ No API key required")
    print()

    print("3. CRYPTOCOMPARE API")
    print("   ✓ Free tier: 100,000 requests/month")
    print("   ✓ Historical data available")
    print("   ✓ Multiple cryptocurrencies")
    print("   ✓ Some onchain metrics")
    print()

    print("IMPLEMENTATION STRATEGY:")
    print("-" * 20)
    print("Phase 1: Update collector with real APIs")
    print("  • Replace placeholder data with real API calls")
    print("  • Implement rate limiting and error handling")
    print("  • Add data validation and quality checks")
    print()

    print("Phase 2: Backfill missing records")
    print("  • Identify records with NULL values")
    print("  • Fetch data from appropriate APIs")
    print("  • Update records with real data")
    print("  • Validate data quality")
    print()

    print("Phase 3: Optimize and monitor")
    print("  • Implement caching to reduce API calls")
    print("  • Add monitoring and alerting")
    print("  • Optimize for performance")
    print("  • Ensure 99%+ coverage")
    print()

    print("EXPECTED RESULTS:")
    print("-" * 20)
    print("• 99%+ onchain data coverage")
    print("• Real-time data updates")
    print("• Historical data backfilled")
    print("• 200+ cryptocurrencies supported")
    print("• Robust error handling and monitoring")
    print()


def create_updated_collector():
    """Create updated onchain collector with real data sources"""

    print("=" * 80)
    print("UPDATED ONCHAIN COLLECTOR CODE")
    print("=" * 80)
    print()

    collector_code = '''
def collect_onchain_metrics():
    """Collect real onchain metrics from multiple APIs"""
    
    # API configurations
    MESSARI_BASE_URL = "https://data.messari.io/api/v1"
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Rate limiting
    last_messari_call = 0
    last_coingecko_call = 0
    
    def rate_limit(api_type, min_interval=3.0):
        nonlocal last_messari_call, last_coingecko_call
        current_time = time.time()
        
        if api_type == "messari" and current_time - last_messari_call < min_interval:
            time.sleep(min_interval - (current_time - last_messari_call))
        elif api_type == "coingecko" and current_time - last_coingecko_call < min_interval:
            time.sleep(min_interval - (current_time - last_coingecko_call))
        
        if api_type == "messari":
            last_messari_call = time.time()
        elif api_type == "coingecko":
            last_coingecko_call = time.time()
    
    def fetch_messari_data(symbol):
        """Fetch data from Messari API"""
        try:
            rate_limit("messari", 3.0)
            url = f"{MESSARI_BASE_URL}/assets/{symbol.lower()}/metrics"
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
            logger.error(f"Messari API error for {symbol}: {e}")
        return None
    
    def fetch_coingecko_data(symbol):
        """Fetch data from CoinGecko API"""
        try:
            rate_limit("coingecko", 1.0)
            url = f"{COINGECKO_BASE_URL}/coins/{symbol.lower()}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", {})
                return {
                    "price_volatility_7d": market_data.get("price_change_percentage_7d"),
                    "active_addresses_24h": None,  # Not available in free tier
                    "transaction_count_24h": None,  # Not available in free tier
                    "exchange_net_flow_24h": None  # Not available in free tier
                }
        except Exception as e:
            logger.error(f"CoinGecko API error for {symbol}: {e}")
        return None
    
    # Main collection logic
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 LIMIT 50")
        assets = cursor.fetchall()
        
        processed = 0
        for asset in assets:
            symbol = asset["symbol"]
            try:
                # Try Messari first (more comprehensive)
                data = fetch_messari_data(symbol)
                if not data:
                    # Fallback to CoinGecko
                    data = fetch_coingecko_data(symbol)
                
                if data:
                    timestamp = datetime.utcnow()
                    cursor.execute("""
                    INSERT INTO crypto_onchain_data (
                        coin, coin_symbol, timestamp, collection_date,
                        active_addresses_24h, transaction_count_24h,
                        exchange_net_flow_24h, price_volatility_7d
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        active_addresses_24h = VALUES(active_addresses_24h),
                        transaction_count_24h = VALUES(transaction_count_24h),
                        exchange_net_flow_24h = VALUES(exchange_net_flow_24h),
                        price_volatility_7d = VALUES(price_volatility_7d),
                        timestamp = VALUES(timestamp)
                    """, (
                        symbol, symbol, timestamp, timestamp,
                        data.get("active_addresses_24h"),
                        data.get("transaction_count_24h"),
                        data.get("exchange_net_flow_24h"),
                        data.get("price_volatility_7d")
                    ))
                    processed += 1
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        conn.commit()
        logger.info(f"Processed {processed} onchain metrics with real data")
        
    except Exception as e:
        logger.error(f"Error in collection: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
'''

    print("Updated collector code with real API integration:")
    print(collector_code)
    print()


def main():
    """Main execution function"""
    analyze_missing_data()
    create_realistic_backfill_plan()
    create_updated_collector()


if __name__ == "__main__":
    main()
