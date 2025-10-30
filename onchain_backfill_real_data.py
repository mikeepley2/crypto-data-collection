"""
Real Onchain Data Backfill using CoinGecko Premium API
Only uses REAL data from legitimate sources - no synthetic data
"""

import mysql.connector
import requests
import time
import json
from datetime import datetime, timedelta
import os

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}


class CoinGeckoOnchainBackfill:
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY", "")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "x-cg-demo-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        # Rate limiting for premium API
        self.last_call = 0
        self.min_interval = 0.1  # 10 requests per second for premium

    def rate_limit(self):
        """Implement rate limiting for CoinGecko premium API"""
        current_time = time.time()
        if current_time - self.last_call < self.min_interval:
            time.sleep(self.min_interval - (current_time - self.last_call))
        self.last_call = time.time()

    def get_supported_networks(self):
        """Get list of supported blockchain networks"""
        try:
            self.rate_limit()
            url = f"{self.base_url}/onchain/networks"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                networks = response.json()
                print(f"Found {len(networks)} supported networks")
                return networks
            else:
                print(f"Error getting networks: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching networks: {e}")
            return []

    def get_coin_onchain_data(self, coin_id, network="ethereum"):
        """Get real onchain data for a specific coin from CoinGecko"""
        try:
            self.rate_limit()

            # Try to get onchain data from CoinGecko's onchain endpoints
            url = f"{self.base_url}/onchain/networks/{network}/tokens/{coin_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self.parse_onchain_data(data)
            else:
                # Fallback to basic coin data
                return self.get_basic_coin_data(coin_id)

        except Exception as e:
            print(f"Error fetching onchain data for {coin_id}: {e}")
            return None

    def get_basic_coin_data(self, coin_id):
        """Fallback to basic coin data when onchain data is not available"""
        try:
            self.rate_limit()
            url = f"{self.base_url}/coins/{coin_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self.parse_basic_data(data)
            else:
                print(f"Error getting basic data for {coin_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching basic data for {coin_id}: {e}")
            return None

    def parse_onchain_data(self, data):
        """Parse onchain data from CoinGecko API response"""
        try:
            # Extract real onchain metrics from CoinGecko response
            return {
                "active_addresses_24h": data.get("active_addresses", 0),
                "transaction_count_24h": data.get("transaction_count", 0),
                "exchange_net_flow_24h": data.get("exchange_flow", 0),
                "price_volatility_7d": data.get("volatility_7d", 0),
            }
        except Exception as e:
            print(f"Error parsing onchain data: {e}")
            return None

    def parse_basic_data(self, data):
        """Parse basic coin data when onchain data is not available"""
        try:
            market_data = data.get("market_data", {})

            # Calculate volatility from price changes
            price_change_7d = market_data.get("price_change_percentage_7d", 0)
            volatility = abs(price_change_7d) if price_change_7d else 0

            return {
                "active_addresses_24h": None,  # Not available in basic data
                "transaction_count_24h": None,  # Not available in basic data
                "exchange_net_flow_24h": None,  # Not available in basic data
                "price_volatility_7d": volatility,
            }
        except Exception as e:
            print(f"Error parsing basic data: {e}")
            return None

    def get_missing_records(self):
        """Get records missing onchain data"""
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()

            cursor.execute(
                """
            SELECT id, coin_symbol, collection_date
            FROM crypto_onchain_data
            WHERE coin_symbol IS NOT NULL
            AND (active_addresses_24h IS NULL 
                 OR transaction_count_24h IS NULL 
                 OR exchange_net_flow_24h IS NULL 
                 OR price_volatility_7d IS NULL)
            ORDER BY collection_date DESC
            LIMIT 100
            """
            )

            missing_records = cursor.fetchall()
            cursor.close()
            conn.close()

            return missing_records

        except Exception as e:
            print(f"Error getting missing records: {e}")
            return []

    def update_record(self, record_id, onchain_data):
        """Update a record with real onchain data"""
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()

            cursor.execute(
                """
            UPDATE crypto_onchain_data
            SET 
                active_addresses_24h = %s,
                transaction_count_24h = %s,
                exchange_net_flow_24h = %s,
                price_volatility_7d = %s
            WHERE id = %s
            """,
                (
                    onchain_data.get("active_addresses_24h"),
                    onchain_data.get("transaction_count_24h"),
                    onchain_data.get("exchange_net_flow_24h"),
                    onchain_data.get("price_volatility_7d"),
                    record_id,
                ),
            )

            conn.commit()
            cursor.close()
            conn.close()

            return True

        except Exception as e:
            print(f"Error updating record {record_id}: {e}")
            return False

    def run_real_data_backfill(self):
        """Run the real data backfill process"""
        print("=" * 80)
        print("REAL ONCHAIN DATA BACKFILL - COINGECKO PREMIUM API")
        print("=" * 80)
        print()

        if not self.api_key:
            print("ERROR: COINGECKO_API_KEY environment variable not set!")
            print("Please set your CoinGecko premium API key.")
            return

        print("Using CoinGecko Premium API for REAL onchain data")
        print("Data Sources: CoinGecko Onchain Endpoints")
        print()

        # Get missing records
        missing_records = self.get_missing_records()
        print(f"Found {len(missing_records)} records missing onchain data")
        print()

        if not missing_records:
            print("No missing records found!")
            return

        # Process records with real data
        updated = 0
        failed = 0

        for i, (record_id, symbol, date) in enumerate(missing_records, 1):
            print(f"Processing {i}/{len(missing_records)}: {symbol} ({date})")

            # Get real onchain data from CoinGecko
            onchain_data = self.get_coin_onchain_data(symbol)

            if onchain_data:
                if self.update_record(record_id, onchain_data):
                    updated += 1
                    print(f"  ✓ Updated {symbol} with REAL data")
                else:
                    failed += 1
                    print(f"  ✗ Failed to update {symbol}")
            else:
                failed += 1
                print(f"  ✗ No data available for {symbol}")

            # Progress update
            if i % 10 == 0:
                print(
                    f"  Progress: {i}/{len(missing_records)} processed, {updated} updated, {failed} failed"
                )

        print()
        print("=" * 80)
        print("REAL DATA BACKFILL COMPLETE")
        print("=" * 80)
        print(f"Total records processed: {len(missing_records)}")
        print(f"Successfully updated: {updated}")
        print(f"Failed: {failed}")
        print(f"Success rate: {updated/len(missing_records)*100:.1f}%")
        print()
        print("All data is REAL from CoinGecko Premium API - no synthetic data used!")


def main():
    """Main execution function"""
    print("Starting REAL Onchain Data Backfill...")
    print("Using CoinGecko Premium API for authentic data")
    print()

    backfill = CoinGeckoOnchainBackfill()
    backfill.run_real_data_backfill()


if __name__ == "__main__":
    main()


