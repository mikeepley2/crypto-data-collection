"""
Onchain Metrics Backfill Script
Real data collection to achieve 100% onchain coverage
"""

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
                "exchange_net_flow_24h": metrics.get("exchange_net_flow_24h"),
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
                "exchange_net_flow_24h": None,
            }
    except Exception as e:
        print(f"CoinGecko API error for {symbol}: {e}")
    return None


def backfill_missing_records():
    """Backfill missing onchain records"""

    print("=" * 80)
    print("ONCHAIN METRICS BACKFILL")
    print("=" * 80)
    print()

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Get missing records
    cursor.execute(
        """
    SELECT id, coin_symbol, collection_date
    FROM crypto_onchain_data
    WHERE active_addresses_24h IS NULL 
       OR transaction_count_24h IS NULL 
       OR exchange_net_flow_24h IS NULL 
       OR price_volatility_7d IS NULL
    ORDER BY collection_date DESC
    LIMIT 1000
    """
    )

    missing_records = cursor.fetchall()
    print(f"Found {len(missing_records)} records to backfill")
    print()

    updated = 0
    failed = 0

    for i, (record_id, symbol, date) in enumerate(missing_records, 1):
        print(f"Processing {i}/{len(missing_records)}: {symbol} ({date})")

        # Try Messari first
        data = fetch_messari_data(symbol)
        if not data:
            # Fallback to CoinGecko
            data = fetch_coingecko_data(symbol)

        if data:
            try:
                cursor.execute(
                    """
                UPDATE crypto_onchain_data
                SET 
                    active_addresses_24h = %s,
                    transaction_count_24h = %s,
                    exchange_net_flow_24h = %s,
                    price_volatility_7d = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                    (
                        data.get("active_addresses_24h"),
                        data.get("transaction_count_24h"),
                        data.get("exchange_net_flow_24h"),
                        data.get("price_volatility_7d"),
                        record_id,
                    ),
                )

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
            print(
                f"  Progress: {i}/{len(missing_records)} processed, {updated} updated, {failed} failed"
            )

    print()
    print("=" * 80)
    print("BACKFILL COMPLETE")
    print("=" * 80)
    print(f"Total records processed: {len(missing_records)}")
    print(f"Successfully updated: {updated}")
    print(f"Failed: {failed}")
    print(f"Success rate: {updated/len(missing_records)*100:.1f}%")
    print()

    cursor.close()
    conn.close()


if __name__ == "__main__":
    backfill_missing_records()


